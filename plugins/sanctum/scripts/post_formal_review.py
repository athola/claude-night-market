#!/usr/bin/env python3
"""Post /pr-review findings as one formal review on GitHub or GitLab.

The review the platform records as a review, with a verdict, rather than a
scatter of PR comments. GitHub: a pending review gets one thread per
finding (on its diff line, or on the file when the line is outside the
diff), then is submitted with APPROVE, COMMENT or REQUEST_CHANGES. GitLab:
one draft note per finding, published together with a reviewer state, plus
an approval when nothing needs fixing.

A pending draft review the reviewer already has on the PR blocks a second
one on GitHub, and GitLab's bulk publish sends every draft the user holds.
Either way, finishing the review would publish comments the reviewer has
not sent. The default is to stop and report the draft (exit 3); rerun with
``--pending join`` to add these findings to it and submit them together.

Findings file: a JSON list of ``{id, severity, path, line, body}``, where
severity is one of blocking, critical, important, suggestion and ``line``
may be null for a file-level finding.

Usage (one command each, wrapped here):
    post_formal_review.py --platform github --repo OWNER/REPO --pr N
        --findings findings.json [--summary summary.md] [--pending join]
    post_formal_review.py --platform gitlab --project GROUP/PROJECT --pr N
        --findings findings.json [--summary summary.md] [--pending join]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

Runner = Callable[..., str]
Spans = dict[str, list[tuple[int, int]]]

_REQUEST_CHANGES = {"blocking", "critical"}
_HUNK = re.compile(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", re.M)


@dataclass(frozen=True)
class ReviewRequest:
    """What to post: the findings, the review body, and the draft policy.

    ``pending`` is ``abort`` (stop when a draft of yours exists) or ``join``.
    """

    findings: list[Finding]
    summary: str
    pending: str


@dataclass(frozen=True)
class Finding:
    """One review finding, anchored to a file and, when known, a line."""

    id: str
    severity: str
    path: str
    line: int | None
    body: str

    def text(self) -> str:
        """Render the comment body, labeled with severity and id."""
        return f"**[{self.severity}] {self.id}**\n\n{self.body.strip()}"


def run_cli(argv: list[str], stdin: str | None = None) -> str:
    """Run gh or glab and return stdout; a failed call raises."""
    return subprocess.run(
        argv, input=stdin, capture_output=True, text=True, check=True
    ).stdout


def choose_event(findings: list[Finding], *, own_pr: bool) -> str:
    """Pick the review verdict. A PR's author can only comment on it."""
    if own_pr:
        return "COMMENT"
    if any(f.severity in _REQUEST_CHANGES for f in findings):
        return "REQUEST_CHANGES"
    # Suggestions alone do not hold a PR back, matching /pr-review's table.
    if any(f.severity == "important" for f in findings):
        return "COMMENT"
    return "APPROVE"


def hunk_spans(patch: str) -> list[tuple[int, int]]:
    """New-side line ranges a review comment may anchor to."""
    spans = []
    for match in _HUNK.finditer(patch or ""):
        start, count = int(match.group(1)), int(match.group(2) or 1)
        if count:  # "+N,0" is a pure deletion with no new-side line
            spans.append((start, start + count - 1))
    return spans


def _in_diff(spans: Spans, finding: Finding) -> bool:
    return finding.line is not None and any(
        a <= finding.line <= b for a, b in spans.get(finding.path, [])
    )


def _location(finding: Finding) -> str:
    return finding.path if finding.line is None else f"{finding.path}:{finding.line}"


def _with_outside(summary: str, outside: list[Finding]) -> str:
    """Append findings for files the PR does not touch, which have no thread."""
    if not outside:
        return summary
    parts = [summary.rstrip(), "", "### Findings outside the changed files", ""]
    for finding in outside:
        parts += [f"`{_location(finding)}`", "", finding.text(), ""]
    return "\n".join(parts).rstrip() + "\n"


def _graphql(run: Runner, query: str, **variables: Any) -> dict[str, Any]:
    out = run(
        ["gh", "api", "graphql", "--input", "-"],
        json.dumps({"query": query, "variables": variables}),
    )
    response: dict[str, Any] = json.loads(out)
    if response.get("errors"):
        raise RuntimeError(json.dumps(response["errors"])[:500])
    return response["data"]


_PR_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      id headRefOid author { login }
      reviews(states: PENDING, first: 20) {
        nodes { id author { login } comments { totalCount } }
      }
    }
  }
}"""
_ADD_REVIEW = """
mutation($pr: ID!, $commit: GitObjectID) {
  addPullRequestReview(input: {pullRequestId: $pr, commitOID: $commit}) {
    pullRequestReview { id }
  }
}"""
_ADD_THREAD = """
mutation($pullRequestReviewId: ID!, $path: String!, $body: String!,
         $subjectType: PullRequestReviewThreadSubjectType,
         $line: Int, $side: DiffSide) {
  addPullRequestReviewThread(input: {pullRequestReviewId: $pullRequestReviewId,
    path: $path, body: $body, subjectType: $subjectType, line: $line,
    side: $side}) { thread { id } }
}"""
_SUBMIT = """
mutation($pullRequestReviewId: ID!, $event: PullRequestReviewEvent!,
         $body: String) {
  submitPullRequestReview(input: {pullRequestReviewId: $pullRequestReviewId,
    event: $event, body: $body}) { pullRequestReview { url state } }
}"""


def post_github(
    run: Runner,
    *,
    repo: str,
    pr: int,
    request: ReviewRequest,
) -> dict[str, Any]:
    """Post the request's findings as one submitted GitHub review."""
    findings, summary, pending = request.findings, request.summary, request.pending
    owner, name = repo.split("/", 1)
    viewer = run(["gh", "api", "user", "--jq", ".login"]).strip()
    data = _graphql(run, _PR_QUERY, owner=owner, name=name, number=pr)
    pull = data["repository"]["pullRequest"]
    mine = [r for r in pull["reviews"]["nodes"] if r["author"]["login"] == viewer]
    if mine and pending != "join":
        return {
            "status": "pending-draft",
            "review_id": mine[0]["id"],
            "draft_comments": mine[0]["comments"]["totalCount"],
        }

    files = json.loads(
        run(["gh", "api", f"repos/{repo}/pulls/{pr}/files", "--paginate", "--slurp"])
    )
    pages = files if files and isinstance(files[0], list) else [files]
    spans: Spans = {
        f["filename"]: hunk_spans(f.get("patch", "")) for p in pages for f in p
    }

    if mine:
        review_id = mine[0]["id"]
    else:
        added = _graphql(run, _ADD_REVIEW, pr=pull["id"], commit=pull["headRefOid"])
        review_id = added["addPullRequestReview"]["pullRequestReview"]["id"]

    outside = []
    for finding in findings:
        if finding.path not in spans:
            outside.append(finding)
            continue
        thread: dict[str, Any] = {
            "pullRequestReviewId": review_id,
            "path": finding.path,
            "body": finding.text(),
        }
        if _in_diff(spans, finding):
            thread.update(subjectType="LINE", line=finding.line, side="RIGHT")
        else:
            thread["subjectType"] = "FILE"
            if finding.line is not None:
                thread["body"] = (
                    f"_(line {finding.line}, outside the diff)_\n\n{thread['body']}"
                )
        _graphql(run, _ADD_THREAD, **thread)

    event = choose_event(findings, own_pr=pull["author"]["login"] == viewer)
    submitted = _graphql(
        run,
        _SUBMIT,
        pullRequestReviewId=review_id,
        event=event,
        body=_with_outside(summary, outside),
    )
    review = submitted["submitPullRequestReview"]["pullRequestReview"]
    return {"status": "submitted", "event": event, "url": review["url"]}


def _glab(
    run: Runner, method: str, path: str, body: dict[str, Any] | None = None
) -> Any:
    argv = ["glab", "api", path, "-X", method]
    if body is None:
        out = run(argv)
    else:
        argv += ["-H", "Content-Type: application/json", "--input", "-"]
        out = run(argv, json.dumps(body))
    return json.loads(out) if out.strip() else None


def post_gitlab(
    run: Runner,
    *,
    project: str,
    mr: int,
    request: ReviewRequest,
) -> dict[str, Any]:
    """Post the request's findings as draft notes, published as one review."""
    findings, summary, pending = request.findings, request.summary, request.pending
    base = f"projects/{quote(project, safe='')}/merge_requests/{mr}"
    viewer = _glab(run, "GET", "user")["username"]
    request = _glab(run, "GET", base)
    drafts = _glab(run, "GET", f"{base}/draft_notes") or []
    if drafts and pending != "join":
        return {"status": "pending-draft", "draft_comments": len(drafts)}

    version = _glab(run, "GET", f"{base}/versions")[0]
    diffs = _glab(run, "GET", f"{base}/diffs") or []
    spans: Spans = {d["new_path"]: hunk_spans(d.get("diff", "")) for d in diffs}
    old_paths = {d["new_path"]: d.get("old_path", d["new_path"]) for d in diffs}

    outside = []
    for finding in findings:
        if finding.path not in spans:
            outside.append(finding)
            continue
        position: dict[str, Any] = {
            "base_sha": version["base_commit_sha"],
            "head_sha": version["head_commit_sha"],
            "start_sha": version["start_commit_sha"],
            "new_path": finding.path,
            "old_path": old_paths[finding.path],
        }
        note = finding.text()
        if _in_diff(spans, finding):
            position.update(position_type="text", new_line=finding.line)
        else:
            position["position_type"] = "file"
            if finding.line is not None:
                note = f"_(line {finding.line}, outside the diff)_\n\n{note}"
        _glab(run, "POST", f"{base}/draft_notes", {"note": note, "position": position})

    event = choose_event(findings, own_pr=request["author"]["username"] == viewer)
    state = "requested_changes" if event == "REQUEST_CHANGES" else "reviewed"
    _glab(
        run,
        "POST",
        f"{base}/draft_notes/bulk_publish",
        {"note": _with_outside(summary, outside), "reviewer_state": state},
    )
    if event == "APPROVE":
        _glab(run, "POST", f"{base}/approve")
    return {"status": "submitted", "event": event, "url": request.get("web_url", "")}


def _load_findings(path: str) -> list[Finding]:
    with open(path, encoding="utf-8") as handle:
        items = json.load(handle)
    return [
        Finding(
            id=str(item["id"]),
            severity=str(item["severity"]).lower(),
            path=str(item["path"]),
            line=None if item.get("line") is None else int(item["line"]),
            body=str(item["body"]),
        )
        for item in items
    ]


def main(argv: list[str] | None = None) -> int:
    """Post the review; exit 3 when a pending draft needs a decision."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--platform", choices=("github", "gitlab"), required=True)
    parser.add_argument("--repo", help="GitHub OWNER/REPO")
    parser.add_argument("--project", help="GitLab GROUP/PROJECT or numeric id")
    parser.add_argument("--pr", type=int, required=True, help="PR or MR number")
    parser.add_argument("--findings", required=True, help="JSON list of findings")
    parser.add_argument("--summary", help="Markdown file for the review body")
    parser.add_argument(
        "--pending",
        choices=("abort", "join"),
        default="abort",
        help="what to do with a pending draft review you already have",
    )
    args = parser.parse_args(argv)

    findings = _load_findings(args.findings)
    summary = ""
    if args.summary:
        with open(args.summary, encoding="utf-8") as handle:
            summary = handle.read()

    request = ReviewRequest(findings=findings, summary=summary, pending=args.pending)
    if args.platform == "github":
        if not args.repo:
            parser.error("--repo is required for github")
        result = post_github(
            run_cli,
            repo=args.repo,
            pr=args.pr,
            request=request,
        )
    else:
        if not args.project:
            parser.error("--project is required for gitlab")
        result = post_gitlab(
            run_cli,
            project=args.project,
            mr=args.pr,
            request=request,
        )

    if result["status"] == "pending-draft":
        sys.stderr.write(
            f"You have a pending draft review with {result['draft_comments']} "
            "unsent comment(s) on this PR. Submitting would publish them too. "
            "Review them, then rerun with --pending join to add these findings "
            "and submit together, or submit or discard the draft first.\n"
        )
        print(json.dumps(result))
        return 3
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
