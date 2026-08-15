#!/usr/bin/env python3
"""Gate: reconcile the GitHub Discussions board against the commit log.

The board is this project's review backlog. The Insight Engine opens a
discussion per PR finding, and the house convention is that a comment
on a finding means somebody has triaged it. 28 of the findings carry
one. 46 did not.

Treating those 46 as open work is what the 2026-08-02 sweep did, and
roughly half were already fixed. #512 became moot when the repo moved
to Python 3.12. #522, #535, #543 and the eight-discussion #559-#566
cluster were all repaired in the ordinary course of work. Nobody was
negligent; there is simply no step anywhere in this repo's workflows
that tells the board a finding is done. A fixed finding and an ignored
finding are indistinguishable from the board's side, so every sweep
re-verifies the same fixed findings by hand. Discussions #271, #222 and
#302 each asked for this loop to be closed.

The commit log is the ledger, and it needs no new file to maintain. The
evidence is an explicit trailer::

    Addresses-Discussion: #654

A trailer rather than prose, because prose cannot carry the signal.
Three commits here name a discussion three different ways: ``509bffaf``
resolves #542, ``6b28aa1a`` *opened* #424 by posting it, and
``c9a53ab2`` cites #614 as precedent for an unrelated bug. No verb list
separates them, since #654's fixing commit opens with "reported" and
#542's says "De-tautologize". A reconciler guessing from prose would
announce "Addressed" on discussions a commit had just created.

This script joins the two sides:

``triaged``
    The discussion carries a comment. Nothing to do.

``needs_writeback``
    A commit claims it via the trailer, but the board was never told.
    This is the defect the script exists to remove: post the comment,
    close it.

``mentioned``
    Prose names it with no resolution claim. Reported as a lead for a
    human, never posted, and not counted as backlog either: a mention
    is evidence somebody already looked.

``untriaged``
    No comment, no commit, no mention. Real backlog.

Bare ``#N`` is deliberately not treated as a reference at all. The board
and the issue tracker share a number space, so "closes #609" would
otherwise implicate discussion 609 on the strength of an unrelated
issue.

Exit codes follow the house gate convention: ``0`` clean, ``1`` when
the gate finds work, ``2`` on a usage or environment error. The
untriaged count is a ratchet, which existed because 41 pre-existing
findings would have held a hard gate red permanently. Those 41 are
answered, so the ratchet now sits at zero and behaves as the hard gate
it was always meant to become. Pending write-backs are not ratcheted:
one is a bug, and it is cheap to fix.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO = "athola/claude-night-market"

# Baseline for the untriaged backlog. Lower it in the same change that
# reduces the backlog; never raise it to make a red gate green.
#
# Zero as of 2026-08-06: the backlog this ratchet was invented to
# tolerate is gone, so it is now a hard gate. That means a newly posted
# finding turns this red until somebody answers it, which is the
# intended pressure and not a defect -- the gate runs from a make
# target, not from pre-commit or CI, so it blocks no commit and no PR.
DEFAULT_RATCHET = 0

# Generated daily digests are observability output, not a backlog.
DIGEST_TITLE = re.compile(r"^\[Learning\] \d{4}-\d{2}-\d{2}$")

# `discussion #654`, `discussions #604, #610 and #623`. The keyword must
# sit immediately before the first number, which keeps prose like "this
# discussion went on ... rose to #1200" from matching.
_REF = re.compile(
    r"discussions?\s+(#\d+(?:\s*(?:,|and|,\s*and|\s)\s*#\d+)*)",
    re.IGNORECASE,
)
_NUM = re.compile(r"#(\d+)")

# The one form that means "this commit resolved it". A trailer on its
# own line, git-trailer shaped, so it cannot be produced by accident.
#
# Prose cannot carry this signal. Three commits in this repo reference a
# discussion three different ways: 509bffaf resolves #542, 6b28aa1a
# *opened* #424 by posting it, and c9a53ab2 cites #614 as precedent. No
# verb list separates them -- #654's fixing commit opens with "reported"
# and #542's says "De-tautologize". Guessing would have the reconciler
# announce "Addressed" on discussions a commit had just created.
_TRAILER = re.compile(
    r"^Addresses-Discussion:\s*(#\d+(?:\s*(?:,|and|,\s*and|\s)\s*#\d+)*)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# git log field/record separators, chosen so commit bodies pass through
# intact; neither byte occurs in prose.
FIELD_SEP = "\x1f"
RECORD_SEP = "\x1e"


def read_commit_log(since: str | None = None) -> str:
    """Return the commit log in the field/record format this parses."""
    cmd = ["git", "log", f"--format=%h{FIELD_SEP}%B{RECORD_SEP}"]
    if since:
        cmd.append(since)
    return subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _scan(log_text: str, pattern: re.Pattern[str]) -> dict[int, list[tuple[str, str]]]:
    refs: dict[int, list[tuple[str, str]]] = {}
    for record in log_text.split(RECORD_SEP):
        if FIELD_SEP not in record:
            continue
        sha, body = record.split(FIELD_SEP, 1)
        sha = sha.strip()
        subject = body.strip().splitlines()[0] if body.strip() else ""
        for group in pattern.findall(body):
            for number in _NUM.findall(group):
                refs.setdefault(int(number), []).append((sha, subject))
    return refs


def discussion_refs(log_text: str) -> dict[int, list[tuple[str, str]]]:
    """Every commit that names a discussion, whatever it meant by it."""
    return _scan(log_text, _REF)


def resolution_refs(log_text: str) -> dict[int, list[tuple[str, str]]]:
    """Only commits claiming a resolution, via the explicit trailer."""
    return _scan(log_text, _TRAILER)


def mention_refs(log_text: str) -> dict[int, list[tuple[str, str]]]:
    """Prose references that make no resolution claim: leads, not proof."""
    resolutions = resolution_refs(log_text)
    return {
        number: commits
        for number, commits in discussion_refs(log_text).items()
        if number not in resolutions
    }


def in_scope(discussion: dict[str, Any]) -> bool:
    """Daily digests are excluded; every other discussion is reviewable."""
    return not DIGEST_TITLE.match(discussion.get("title", ""))


def classify(
    board: list[dict[str, Any]],
    refs: dict[int, list[tuple[str, str]]],
    mentions: dict[int, list[tuple[str, str]]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Split the board by what the commit log can actually prove.

    ``refs`` are resolution trailers and are the only input that earns a
    write-back. ``mentions`` are prose references: reported as leads for
    a human, never posted, and not counted as backlog either, since a
    mention is evidence somebody has already looked.
    """
    mentions = mentions or {}
    result: dict[str, list[dict[str, Any]]] = {
        "triaged": [],
        "needs_writeback": [],
        "mentioned": [],
        "untriaged": [],
        "closed": [],
    }
    for discussion in board:
        if not in_scope(discussion):
            continue
        if discussion.get("closed"):
            result["closed"].append(discussion)
            continue
        has_comment = bool(discussion.get("comments", {}).get("nodes"))
        number = discussion["number"]
        if has_comment:
            result["triaged"].append(discussion)
        elif number in refs:
            enriched = dict(discussion)
            enriched["commits"] = refs[number]
            result["needs_writeback"].append(enriched)
        elif number in mentions:
            enriched = dict(discussion)
            enriched["commits"] = mentions[number]
            result["mentioned"].append(enriched)
        else:
            result["untriaged"].append(discussion)
    return result


def gate_status(
    result: dict[str, list[dict[str, Any]]],
    ratchet: int = DEFAULT_RATCHET,
) -> tuple[int, list[str]]:
    """Return the gate exit code and the reasons behind it."""
    reasons: list[str] = []
    pending = result["needs_writeback"]
    if pending:
        numbers = ", ".join(f"#{d['number']}" for d in pending)
        reasons.append(
            f"{len(pending)} discussion(s) fixed in commits but awaiting "
            f"write-back: {numbers}. Run with --apply."
        )
    untriaged = result["untriaged"]
    if len(untriaged) > ratchet:
        reasons.append(
            f"{len(untriaged)} untriaged discussions exceeds the ratchet of "
            f"{ratchet}. Triage the excess or fix the findings."
        )
    return (1 if reasons else 0), reasons


# --- GitHub seam -------------------------------------------------------

_QUERY = """
query($endCursor: String) {
  repository(owner: "athola", name: "claude-night-market") {
    discussions(first: 50, after: $endCursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id number title closed
        category { name }
        comments(first: 1) { nodes { body } }
      }
    }
  }
}
"""


def fetch_board() -> list[dict[str, Any]]:
    """Fetch every discussion. Raises if `gh` is missing or unauthenticated."""
    proc = subprocess.run(
        ["gh", "api", "graphql", "--paginate", "-f", f"query={_QUERY}"],
        capture_output=True,
        text=True,
        check=True,
    )
    nodes: list[dict[str, Any]] = []
    decoder = json.JSONDecoder()
    text = proc.stdout.strip()
    index = 0
    while index < len(text):
        payload, offset = decoder.raw_decode(text, index)
        nodes.extend(payload["data"]["repository"]["discussions"]["nodes"])
        index = offset
        while index < len(text) and text[index] in " \n\r\t":
            index += 1
    return nodes


def writeback_body(commits: list[tuple[str, str]]) -> str:
    """The comment posted when a commit has addressed a finding."""
    lines = ["Addressed. Commits carrying the resolution trailer:", ""]
    lines.extend(f"- `{sha}` {subject}" for sha, subject in commits)
    lines.extend(
        [
            "",
            "Posted by `scripts/reconcile_discussions.py`, which joins this "
            "board against commits carrying an `Addresses-Discussion:` "
            "trailer. A commit that merely names a discussion in prose is "
            "read as a mention and never written back.",
            "",
            "If this is wrong, reopen and say why. A comment of any kind "
            "stops the reconciler from touching the discussion again, so "
            "your reply is the whole opt-out.",
        ]
    )
    return "\n".join(lines)


def apply_writeback(
    pending: list[dict[str, Any]], *, close: bool, dry_run: bool
) -> int:
    """Post the resolution comment and optionally close. Returns count."""
    done = 0
    for discussion in pending:
        number = discussion["number"]
        body = writeback_body(discussion["commits"])
        if dry_run:
            print(
                f"  [dry-run] would comment on #{number} and "
                f"{'close' if close else 'leave open'}"
            )
            done += 1
            continue
        subprocess.run(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                "query=mutation($id: ID!, $body: String!) { "
                "addDiscussionComment(input: {discussionId: $id, body: $body}) "
                "{ comment { id } } }",
                "-f",
                f"id={discussion['id']}",
                "-f",
                f"body={body}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        if close:
            subprocess.run(
                [
                    "gh",
                    "api",
                    "graphql",
                    "-f",
                    "query=mutation($id: ID!) { closeDiscussion(input: "
                    "{discussionId: $id, reason: RESOLVED}) { discussion { id } } }",
                    "-f",
                    f"id={discussion['id']}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        print(f"  wrote back to #{number}" + (" and closed it" if close else ""))
        done += 1
    return done


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile the Discussions board against the commit log."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Post resolution comments for findings a commit already fixed.",
    )
    parser.add_argument(
        "--no-close",
        action="store_true",
        help="With --apply: comment but leave the discussion open.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --apply: print what would be posted, write nothing.",
    )
    parser.add_argument(
        "--ratchet",
        type=int,
        default=DEFAULT_RATCHET,
        help=f"Untriaged cap (default {DEFAULT_RATCHET}).",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        board = fetch_board()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"error: could not reach the discussion board: {exc}", file=sys.stderr)
        return 2

    log = read_commit_log()
    result = classify(board, resolution_refs(log), mentions=mention_refs(log))
    code, reasons = gate_status(result, ratchet=args.ratchet)

    if args.json:
        print(
            json.dumps(
                {k: [d["number"] for d in v] for k, v in result.items()}
                | {"exit": code, "reasons": reasons},
                indent=2,
            )
        )
        return code

    print(
        f"board: {len(result['triaged'])} triaged, "
        f"{len(result['needs_writeback'])} pending write-back, "
        f"{len(result['mentioned'])} mentioned in prose, "
        f"{len(result['untriaged'])} untriaged, "
        f"{len(result['closed'])} closed"
    )
    if args.apply and result["needs_writeback"]:
        print(f"applying write-back to {len(result['needs_writeback'])}:")
        apply_writeback(
            result["needs_writeback"],
            close=not args.no_close,
            dry_run=args.dry_run,
        )
        return 0 if not args.dry_run else code
    for reason in reasons:
        print(f"  {reason}")
    return code


if __name__ == "__main__":
    sys.exit(main())
