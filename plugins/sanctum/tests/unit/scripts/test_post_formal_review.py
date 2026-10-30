"""post_formal_review.py posts one formal review, not loose comments.

/pr-review fell back to plain PR comments whenever GitHub refused a second
review: a pending draft review by the same user blocks creating one. Lines
outside the diff also fell back, to a general comment. GitHub's GraphQL API
adds threads to a pending review by id and takes file-level threads, and
GitLab publishes draft notes as a batch with a reviewer state, so both can
carry every finding in one review.

The fake runner stands in for the gh and glab processes. It records every
call, so each test can assert what reached the platform.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "post_formal_review.py"
_spec = importlib.util.spec_from_file_location("post_formal_review", SCRIPT)
assert _spec and _spec.loader
pfr = importlib.util.module_from_spec(_spec)
# A dataclass resolves its module through sys.modules while the class builds.
sys.modules[_spec.name] = pfr
_spec.loader.exec_module(pfr)

PATCH = "@@ -1,3 +1,4 @@\n a\n+b\n c\n d\n"


class FakeCLI:
    """Answer gh and glab calls from a table, and record what was sent."""

    def __init__(self, responder: Callable[[list[str], dict[str, Any] | None], Any]):
        self.responder = responder
        self.calls: list[tuple[list[str], dict[str, Any] | None]] = []

    def __call__(self, argv: list[str], stdin: str | None = None) -> str:
        payload = json.loads(stdin) if stdin else None
        self.calls.append((argv, payload))
        answer = self.responder(argv, payload)
        return answer if isinstance(answer, str) else json.dumps(answer)

    def graphql(self, word: str) -> list[dict[str, Any]]:
        return [p for a, p in self.calls if p and word in p.get("query", "")]


def _github(
    *, author: str = "bob", pending: list[dict[str, Any]] | None = None
) -> FakeCLI:
    def respond(argv: list[str], payload: dict[str, Any] | None) -> Any:
        if argv[:3] == ["gh", "api", "user"]:
            return "alice\n"
        if argv[:2] == ["gh", "api"] and "/files" in argv[2]:
            return [{"filename": "src/app.py", "patch": PATCH}]
        query = (payload or {}).get("query", "")
        if "pullRequest(number" in query:
            return {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "id": "PR_1",
                            "headRefOid": "abc123",
                            "author": {"login": author},
                            "reviews": {"nodes": pending or []},
                        }
                    }
                }
            }
        if "addPullRequestReview(" in query:
            return {
                "data": {"addPullRequestReview": {"pullRequestReview": {"id": "R_new"}}}
            }
        if "addPullRequestReviewThread" in query:
            return {"data": {"addPullRequestReviewThread": {"thread": {"id": "T"}}}}
        if "submitPullRequestReview" in query:
            return {
                "data": {
                    "submitPullRequestReview": {
                        "pullRequestReview": {
                            "url": "https://x/review",
                            "state": "CHANGES_REQUESTED",
                        }
                    }
                }
            }
        raise AssertionError(f"unexpected call {argv} {query[:60]}")

    return FakeCLI(respond)


def _findings(*items: tuple[str, str, str, int | None]) -> list[Any]:
    return [
        pfr.Finding(id=i, severity=s, path=p, line=n, body=f"body {i}")
        for i, s, p, n in items
    ]


class TestChooseEvent:
    @pytest.mark.parametrize(
        ("severities", "own", "event"),
        [
            (["blocking", "suggestion"], False, "REQUEST_CHANGES"),
            (["critical"], False, "REQUEST_CHANGES"),
            (["important"], False, "COMMENT"),
            (["suggestion"], False, "APPROVE"),
            (["important", "suggestion"], False, "COMMENT"),
            ([], False, "APPROVE"),
            (["blocking"], True, "COMMENT"),
            ([], True, "COMMENT"),
        ],
    )
    def test_event_follows_severity_and_authorship(
        self, severities: list[str], own: bool, event: str
    ) -> None:
        findings = [pfr.Finding("x", s, "a.py", 1, "b") for s in severities]
        assert pfr.choose_event(findings, own_pr=own) == event


class TestGitHub:
    def test_one_review_carries_line_and_file_threads_then_is_submitted(self) -> None:
        cli = _github()
        result = pfr.post_github(
            cli,
            repo="o/r",
            pr=7,
            request=pfr.ReviewRequest(
                findings=_findings(
                    ("B1", "blocking", "src/app.py", 2),
                    ("S1", "suggestion", "src/app.py", 40),
                ),
                summary="Summary",
                pending="abort",
            ),
        )
        assert result["status"] == "submitted"
        threads = [p["variables"] for p in cli.graphql("addPullRequestReviewThread")]
        assert threads[0]["subjectType"] == "LINE" and threads[0]["line"] == 2
        assert threads[1]["subjectType"] == "FILE" and "line" not in threads[1]
        assert "line 40" in threads[1]["body"]
        assert all(t["pullRequestReviewId"] == "R_new" for t in threads)
        submit = cli.graphql("submitPullRequestReview")[0]["variables"]
        assert submit["event"] == "REQUEST_CHANGES"
        assert not any("pr comment" in " ".join(a) for a, _ in cli.calls)

    def test_a_finding_in_a_file_the_pr_does_not_touch_goes_in_the_body(self) -> None:
        cli = _github()
        pfr.post_github(
            cli,
            repo="o/r",
            pr=7,
            request=pfr.ReviewRequest(
                findings=_findings(("S2", "important", "docs/other.md", 3)),
                summary="Summary",
                pending="abort",
            ),
        )
        assert cli.graphql("addPullRequestReviewThread") == []
        body = cli.graphql("submitPullRequestReview")[0]["variables"]["body"]
        assert "docs/other.md:3" in body and "body S2" in body

    def test_an_own_pr_is_submitted_as_a_comment(self) -> None:
        cli = _github(author="alice")
        pfr.post_github(
            cli,
            repo="o/r",
            pr=7,
            request=pfr.ReviewRequest(
                findings=_findings(("B1", "blocking", "src/app.py", 2)),
                summary="s",
                pending="abort",
            ),
        )
        assert (
            cli.graphql("submitPullRequestReview")[0]["variables"]["event"] == "COMMENT"
        )

    def test_a_pending_draft_stops_the_review_by_default(self) -> None:
        """Submitting would publish the reviewer's own unsent comments."""
        draft = {
            "id": "R_draft",
            "author": {"login": "alice"},
            "comments": {"totalCount": 3},
        }
        cli = _github(pending=[draft])
        result = pfr.post_github(
            cli,
            repo="o/r",
            pr=7,
            request=pfr.ReviewRequest(
                findings=_findings(("B1", "blocking", "src/app.py", 2)),
                summary="s",
                pending="abort",
            ),
        )
        assert result == {
            "status": "pending-draft",
            "review_id": "R_draft",
            "draft_comments": 3,
        }
        assert cli.graphql("addPullRequestReview") == []
        assert cli.graphql("submitPullRequestReview") == []

    def test_join_adds_to_the_pending_draft_and_submits_it(self) -> None:
        draft = {
            "id": "R_draft",
            "author": {"login": "alice"},
            "comments": {"totalCount": 3},
        }
        cli = _github(pending=[draft])
        result = pfr.post_github(
            cli,
            repo="o/r",
            pr=7,
            request=pfr.ReviewRequest(
                findings=_findings(("B1", "blocking", "src/app.py", 2)),
                summary="s",
                pending="join",
            ),
        )
        assert result["status"] == "submitted"
        assert cli.graphql("addPullRequestReview(") == []
        thread = cli.graphql("addPullRequestReviewThread")[0]["variables"]
        assert thread["pullRequestReviewId"] == "R_draft"
        submit = cli.graphql("submitPullRequestReview")[0]["variables"]
        assert submit["pullRequestReviewId"] == "R_draft"

    def test_another_users_pending_review_does_not_block(self) -> None:
        other = {
            "id": "R_x",
            "author": {"login": "carol"},
            "comments": {"totalCount": 1},
        }
        cli = _github(pending=[other])
        result = pfr.post_github(
            cli,
            repo="o/r",
            pr=7,
            request=pfr.ReviewRequest(findings=[], summary="s", pending="abort"),
        )
        assert result["status"] == "submitted"
        assert cli.graphql("addPullRequestReview(")


def _gitlab(
    *, author: str = "bob", drafts: list[dict[str, Any]] | None = None
) -> FakeCLI:
    mr = {"author": {"username": author}, "web_url": "https://gl/mr/7"}
    versions = [
        {"base_commit_sha": "b", "head_commit_sha": "h", "start_commit_sha": "s"}
    ]
    diffs = [{"new_path": "src/app.py", "old_path": "src/app.py", "diff": PATCH}]
    # (method, path suffix) -> answer; the first match wins.
    table: list[tuple[str, str, Any]] = [
        ("GET", "user", {"username": "alice"}),
        ("GET", "/versions", versions),
        ("GET", "/diffs", diffs),
        ("GET", "/draft_notes", drafts or []),
        ("POST", "/draft_notes", {"id": 1}),
        ("POST", "/bulk_publish", ""),
        ("POST", "/approve", {"approved": True}),
        ("GET", "/merge_requests/7", mr),
    ]

    def respond(argv: list[str], payload: dict[str, Any] | None) -> Any:
        path = next(
            (a for a in argv[2:] if a.startswith("projects/") or a == "user"), ""
        )
        method = argv[argv.index("-X") + 1] if "-X" in argv else "GET"
        for want_method, suffix, answer in table:
            if method == want_method and path.endswith(suffix):
                return answer
        raise AssertionError(f"unexpected call {argv}")

    return FakeCLI(respond)


def _posted(cli: FakeCLI, suffix: str) -> list[dict[str, Any]]:
    return [
        p or {}
        for a, p in cli.calls
        if any(x.endswith(suffix) for x in a)
        and "-X" in a
        and a[a.index("-X") + 1] == "POST"
    ]


class TestGitLab:
    def test_drafts_are_published_with_requested_changes(self) -> None:
        cli = _gitlab()
        result = pfr.post_gitlab(
            cli,
            project="grp/proj",
            mr=7,
            request=pfr.ReviewRequest(
                findings=_findings(
                    ("B1", "blocking", "src/app.py", 2),
                    ("S1", "suggestion", "src/app.py", 40),
                ),
                summary="Summary",
                pending="abort",
            ),
        )
        assert result["status"] == "submitted"
        drafts = _posted(cli, "/draft_notes")
        assert drafts[0]["position"]["position_type"] == "text"
        assert drafts[0]["position"]["new_line"] == 2
        assert drafts[0]["position"]["head_sha"] == "h"
        assert drafts[1]["position"]["position_type"] == "file"
        publish = _posted(cli, "/bulk_publish")[0]
        assert publish["reviewer_state"] == "requested_changes"
        assert publish["note"].startswith("Summary")
        assert _posted(cli, "/approve") == []

    def test_a_clean_mr_by_someone_else_is_approved(self) -> None:
        cli = _gitlab()
        pfr.post_gitlab(
            cli,
            project="grp/proj",
            mr=7,
            request=pfr.ReviewRequest(findings=[], summary="s", pending="abort"),
        )
        assert _posted(cli, "/bulk_publish")[0]["reviewer_state"] == "reviewed"
        assert len(_posted(cli, "/approve")) == 1

    def test_an_own_mr_is_never_approved(self) -> None:
        cli = _gitlab(author="alice")
        pfr.post_gitlab(
            cli,
            project="grp/proj",
            mr=7,
            request=pfr.ReviewRequest(findings=[], summary="s", pending="abort"),
        )
        assert _posted(cli, "/approve") == []

    def test_existing_drafts_stop_the_review_by_default(self) -> None:
        """bulk_publish publishes every draft the user has on the MR."""
        cli = _gitlab(drafts=[{"id": 9}, {"id": 10}])
        result = pfr.post_gitlab(
            cli,
            project="grp/proj",
            mr=7,
            request=pfr.ReviewRequest(findings=[], summary="s", pending="abort"),
        )
        assert result == {"status": "pending-draft", "draft_comments": 2}
        assert _posted(cli, "/draft_notes") == []
        assert _posted(cli, "/bulk_publish") == []

    def test_the_project_path_is_url_encoded(self) -> None:
        cli = _gitlab()
        pfr.post_gitlab(
            cli,
            project="grp/proj",
            mr=7,
            request=pfr.ReviewRequest(findings=[], summary="s", pending="abort"),
        )
        assert any(
            "projects/grp%2Fproj/merge_requests/7" in " ".join(a) for a, _ in cli.calls
        )


class TestCommandLine:
    def test_a_pending_draft_exits_3_and_names_the_rerun_flag(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        draft = {
            "id": "R_draft",
            "author": {"login": "alice"},
            "comments": {"totalCount": 3},
        }
        monkeypatch.setattr(pfr, "run_cli", _github(pending=[draft]))
        findings = tmp_path / "f.json"
        findings.write_text(json.dumps([]))
        code = pfr.main(
            [
                "--platform",
                "github",
                "--repo",
                "o/r",
                "--pr",
                "7",
                "--findings",
                str(findings),
            ]
        )
        assert code == 3
        assert "--pending join" in capsys.readouterr().err
