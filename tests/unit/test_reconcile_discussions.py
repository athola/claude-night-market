"""Unit tests for the discussion reconciliation gate.

The board carries 137 discussions. 46 of the PR Findings had no comment
on them, which the 2026-08-02 sweep treated as "untriaged" -- and about
half of those turned out to be fixed in the tree months earlier. #512
was obsolete the day this repo moved to Python 3.12. #522, #535, #543,
#559 through #566 were all repaired and never spoken of again.

Nothing was wrong with the fixes. What was missing is the write-back:
no workflow ever posted "done, see <sha>" to the discussion, so a fixed
finding and an ignored finding are the same shape from the board's
side. Every sweep therefore re-verifies the same fixed findings by
hand, which is what discussions #271, #222, and #302 each asked to
automate.

The commit history is the ledger, and the evidence is an explicit
``Addresses-Discussion:`` trailer rather than prose. Prose cannot carry
it: `509bffaf` resolves #542, `6b28aa1a` *opened* #424 by posting it,
and `c9a53ab2` cites #614 as precedent, and no verb list tells those
apart. Half these tests exist to pin that separation, because getting
it wrong means announcing "Addressed" on findings nobody has read.

The GitHub calls live behind a seam these tests do not cross.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "reconcile_discussions.py"


def _load():
    spec = importlib.util.spec_from_file_location("reconcile_discussions", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rd = _load()


# --- reference parsing -------------------------------------------------


def test_parses_explicit_discussion_reference() -> None:
    log = "abc1234\x1fDiscussion #654 reported published skill digests\x1e"
    refs = rd.discussion_refs(log)
    assert list(refs) == [654]
    ((sha, subject),) = refs[654]
    assert sha == "abc1234"
    assert subject.startswith("Discussion #654 reported")


def test_parses_plural_and_inline_forms() -> None:
    log = (
        "deadbee\x1fAddress the backlog. discussions #604, #610 and #623 are "
        "five instances of one bug.\x1e"
    )
    refs = rd.discussion_refs(log)
    assert sorted(refs) == [604, 610, 623]


def test_ignores_bare_hash_numbers() -> None:
    """`#417` alone is a PR or issue, not a discussion reference.

    The board and the issue tracker share a number space. Treating any
    `#N` as a discussion would mark findings addressed on the strength
    of an unrelated PR number in a commit body.
    """
    log = "cafe123\x1fFixed what PR #417 found, closes #609\x1e"
    assert rd.discussion_refs(log) == {}


def test_requires_the_keyword_within_a_short_window() -> None:
    """`discussion` must be near the number, not anywhere in the body."""
    log = (
        "beef999\x1fThis discussion went on for a while. Unrelatedly the "
        "count rose to #1200 items.\x1e"
    )
    assert rd.discussion_refs(log) == {}


def test_collects_multiple_commits_per_discussion() -> None:
    log = (
        "aaa1111\x1fdiscussion #302 part one\x1ebbb2222\x1fdiscussion #302 part two\x1e"
    )
    assert len(rd.discussion_refs(log)[302]) == 2


# --- classification ----------------------------------------------------


def _disc(number: int, *, comments: int = 0, closed: bool = False, title: str = "x"):
    return {
        "number": number,
        "title": f"[PR Finding] {title}",
        "closed": closed,
        "comments": {"nodes": [{"body": "b"} for _ in range(comments)]},
    }


def test_trailer_marks_a_resolution() -> None:
    log = "abc1234\x1fsubject\n\nAddresses-Discussion: #654\x1e"
    assert list(rd.resolution_refs(log)) == [654]


def test_trailer_accepts_several_numbers() -> None:
    log = "abc1234\x1fsubject\n\nAddresses-Discussion: #604, #610 and #623\x1e"
    assert sorted(rd.resolution_refs(log)) == [604, 610, 623]


def test_trailer_must_start_its_own_line() -> None:
    """Prose that happens to contain the word is not a trailer."""
    log = "abc1234\x1fThis addresses-discussion: #999 in passing.\x1e"
    assert rd.resolution_refs(log) == {}


def test_prose_mention_is_not_a_resolution() -> None:
    """A commit that *opened* a discussion must never read as fixing it.

    `6b28aa1a` says "posted 13 insights to discussions #424-#436". A
    reconciler that treated any mention as a fix would comment
    "Addressed" on the very discussions that commit created.
    """
    log = "6b28aa1a\x1fDogfood: posted insights to discussions #424 and #436\x1e"
    assert rd.resolution_refs(log) == {}
    assert sorted(rd.discussion_refs(log)) == [424, 436]


def test_resolution_without_comment_is_a_writeback() -> None:
    board = [_disc(654)]
    refs = {654: [("abc1234", "Discussion #654 reported")]}
    result = rd.classify(board, refs)
    assert [d["number"] for d in result["needs_writeback"]] == [654]
    assert result["untriaged"] == []


def test_mention_only_is_reported_but_never_written_back() -> None:
    board = [_disc(614)]
    result = rd.classify(board, {}, mentions={614: [("c9a53ab2", "cited it")]})
    assert result["needs_writeback"] == []
    assert [d["number"] for d in result["mentioned"]] == [614]


def test_mentions_do_not_count_against_the_untriaged_ratchet() -> None:
    """A mention is a lead for a human, not a resolution and not backlog."""
    board = [_disc(614)]
    result = rd.classify(board, {}, mentions={614: [("c9a53ab2", "s")]})
    assert result["untriaged"] == []
    assert rd.gate_status(result, ratchet=0)[0] == 0


def test_existing_comment_counts_as_triaged() -> None:
    board = [_disc(530, comments=1)]
    result = rd.classify(board, {})
    assert result["triaged"] and not result["untriaged"]


def test_no_comment_and_no_commit_is_untriaged() -> None:
    board = [_disc(630)]
    result = rd.classify(board, {})
    assert [d["number"] for d in result["untriaged"]] == [630]


def test_closed_discussion_never_needs_writeback() -> None:
    board = [_disc(654, closed=True)]
    refs = {654: [("abc1234", "subject")]}
    result = rd.classify(board, refs)
    assert result["needs_writeback"] == []


def test_daily_learning_digests_are_excluded() -> None:
    """52 of 137 are generated digests, not a review backlog."""
    board = [
        {
            "number": 658,
            "title": "[Learning] 2026-08-03",
            "closed": False,
            "comments": {"nodes": []},
        }
    ]
    result = rd.classify(board, {})
    assert result["untriaged"] == []


# --- gate behavior -----------------------------------------------------


def test_gate_passes_when_untriaged_within_ratchet() -> None:
    board = [_disc(n) for n in range(600, 610)]
    assert rd.gate_status(rd.classify(board, {}), ratchet=10)[0] == 0


def test_gate_fails_when_untriaged_exceeds_ratchet() -> None:
    board = [_disc(n) for n in range(600, 610)]
    assert rd.gate_status(rd.classify(board, {}), ratchet=9)[0] == 1


def test_gate_fails_on_pending_writeback_regardless_of_ratchet() -> None:
    """A fixed finding the board has not been told about is the defect."""
    board = [_disc(654)]
    result = rd.classify(board, {654: [("abc1234", "s")]})
    code, reasons = rd.gate_status(result, ratchet=999)
    assert code == 1
    assert any("write-back" in r for r in reasons)


@pytest.mark.parametrize("ratchet", [0, 1, 46])
def test_ratchet_is_a_cap_not_a_target(ratchet: int) -> None:
    """Fewer untriaged than the cap always passes."""
    assert rd.gate_status(rd.classify([], {}), ratchet=ratchet)[0] == 0


def test_writeback_body_cites_the_commits_and_the_opt_out() -> None:
    """The comment must be checkable and reversible by a human.

    A write-back that says "fixed" and nothing else is the same dead
    end as no comment at all: the next reader still has to go read the
    code. And an automated closer with no stated opt-out invites people
    to distrust the whole loop.
    """
    body = rd.writeback_body([("00459d48", "docs(discussions): record evidence")])
    assert "00459d48" in body
    assert "docs(discussions): record evidence" in body
    assert "Addresses-Discussion:" in body
    assert "reopen" in body
