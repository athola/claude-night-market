"""Tests for post_insights_to_discussions posting flow."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from insight_types import Finding
from post_insights_to_discussions import (
    format_insight_body,
    format_insight_title,
)


def _make_finding(**overrides) -> Finding:
    defaults = {
        "type": "Trend",
        "severity": "medium",
        "skill": "abstract:skill-auditor",
        "summary": "success rate dropped from 92% to 71%",
        "evidence": "- Previous: 92%\n- Current: 71%",
        "recommendation": "Investigate error pattern",
        "source": "trend_lens",
    }
    defaults.update(overrides)
    return Finding(**defaults)


def test_format_insight_title():
    f = _make_finding()
    title = format_insight_title(f)
    assert (
        title == "[Trend] abstract:skill-auditor: success rate dropped from 92% to 71%"
    )


def test_format_insight_title_no_skill():
    f = _make_finding(skill="", summary="12 skills unused")
    title = format_insight_title(f)
    assert title == "[Trend] 12 skills unused"


def test_format_insight_body_has_sections():
    f = _make_finding()
    body = format_insight_body(f)
    assert "## Finding" in body
    assert "## Evidence" in body
    assert "## Recommended Action" in body
    assert "Severity" in body


def test_format_insight_body_has_metadata():
    f = _make_finding(severity="high", source="delta-lens")
    body = format_insight_body(f)
    assert "high" in body
    assert "delta-lens" in body


def test_format_insight_body_has_footer():
    f = _make_finding()
    body = format_insight_body(f)
    assert "Insight Engine" in body
    assert "fire" in body.lower() or "\U0001f525" in body


def test_format_insight_body_with_related_files():
    """GIVEN a finding with related_files set,
    WHEN formatting the body,
    THEN a Related Files section lists each file.
    """
    f = _make_finding(
        related_files=["src/abstract/foo.py", "scripts/bar.py"],
    )
    body = format_insight_body(f)
    assert "## Related Files" in body
    assert "`src/abstract/foo.py`" in body
    assert "`scripts/bar.py`" in body


def test_format_insight_body_without_related_files():
    """GIVEN a finding with no related_files,
    WHEN formatting the body,
    THEN no Related Files section appears.
    """
    f = _make_finding()
    body = format_insight_body(f)
    assert "## Related Files" not in body


def test_format_insight_body_no_skill():
    """GIVEN a finding with an empty skill field,
    WHEN formatting the body,
    THEN no Skill line appears.
    """
    f = _make_finding(skill="")
    body = format_insight_body(f)
    assert "**Skill:**" not in body


# ── post_findings tests (mocked external calls) ───────────


from unittest.mock import MagicMock, patch

# All external calls live in post_insights_to_discussions
_MODULE = "post_insights_to_discussions"


def test_post_findings_empty_list_returns_empty():
    """GIVEN an empty findings list,
    WHEN post_findings is called,
    THEN it returns empty without calling any APIs.
    """
    from post_insights_to_discussions import post_findings

    result = post_findings([])
    assert result == []


def test_post_findings_no_repo_detected():
    """GIVEN detect_target_repo returns None,
    WHEN post_findings is called,
    THEN it returns empty.
    """
    from post_insights_to_discussions import post_findings

    finding = _make_finding()
    with patch(f"{_MODULE}.detect_target_repo", return_value=None):
        result = post_findings([finding])
    assert result == []


def test_post_findings_no_category_found():
    """GIVEN no matching discussion category exists,
    WHEN post_findings is called,
    THEN it returns empty.
    """
    from post_insights_to_discussions import post_findings

    finding = _make_finding()
    with (
        patch(f"{_MODULE}.detect_target_repo", return_value=("o", "r")),
        patch(f"{_MODULE}.resolve_category_id", return_value=None),
    ):
        result = post_findings([finding])
    assert result == []


def test_post_findings_fallback_to_learnings_category():
    """GIVEN 'insights' category not found but 'learnings' exists,
    WHEN post_findings is called,
    THEN it falls back to 'learnings' and posts.
    """
    from post_insights_to_discussions import post_findings

    finding = _make_finding()

    def category_side_effect(owner, name, slug):
        if slug == "insights":
            return None
        if slug == "learnings":
            return "LEARN_CAT_ID"
        return None

    registry = MagicMock()
    registry.check_local.return_value = "create"

    with (
        patch(f"{_MODULE}.detect_target_repo", return_value=("o", "r")),
        patch(f"{_MODULE}.resolve_category_id", side_effect=category_side_effect),
        patch(f"{_MODULE}.PostedRecord.load", return_value=MagicMock()),
        patch(f"{_MODULE}.get_repo_node_id", return_value="REPO_ID"),
        patch(
            f"{_MODULE}.create_discussion",
            return_value="https://github.com/o/r/discussions/1",
        ),
    ):
        result = post_findings([finding], registry=registry)
    assert len(result) == 1
    assert "discussions/1" in result[0]


def test_post_findings_skips_duplicate():
    """GIVEN registry.check_local returns 'skip',
    WHEN post_findings is called,
    THEN the finding is not posted.
    """
    from post_insights_to_discussions import post_findings

    finding = _make_finding()
    registry = MagicMock()
    registry.check_local.return_value = "skip"

    with (
        patch(f"{_MODULE}.detect_target_repo", return_value=("o", "r")),
        patch(f"{_MODULE}.resolve_category_id", return_value="CAT_ID"),
        patch(f"{_MODULE}.PostedRecord.load", return_value=MagicMock()),
        patch(f"{_MODULE}.get_repo_node_id", return_value="REPO_ID"),
        patch(f"{_MODULE}.create_discussion") as mock_create,
    ):
        result = post_findings([finding], registry=registry)
    assert result == []
    mock_create.assert_not_called()


def test_post_findings_records_posted_on_success():
    """GIVEN a new finding that passes dedup,
    WHEN post_findings succeeds,
    THEN registry.record_posted is called with the URL.
    """
    from post_insights_to_discussions import post_findings

    finding = _make_finding()
    registry = MagicMock()
    registry.check_local.return_value = "create"
    url = "https://github.com/o/r/discussions/99"

    with (
        patch(f"{_MODULE}.detect_target_repo", return_value=("o", "r")),
        patch(f"{_MODULE}.resolve_category_id", return_value="CAT_ID"),
        patch(f"{_MODULE}.PostedRecord.load", return_value=MagicMock()),
        patch(f"{_MODULE}.get_repo_node_id", return_value="REPO_ID"),
        patch(f"{_MODULE}.create_discussion", return_value=url),
    ):
        result = post_findings([finding], registry=registry)
    assert result == [url]
    registry.record_posted.assert_called_once_with(finding, url)


def test_post_findings_handles_create_discussion_error():
    """GIVEN create_discussion raises RuntimeError,
    WHEN post_findings is called,
    THEN the error is caught and the finding is skipped.
    """
    from post_insights_to_discussions import post_findings

    finding = _make_finding()
    registry = MagicMock()
    registry.check_local.return_value = "create"

    with (
        patch(f"{_MODULE}.detect_target_repo", return_value=("o", "r")),
        patch(f"{_MODULE}.resolve_category_id", return_value="CAT_ID"),
        patch(f"{_MODULE}.PostedRecord.load", return_value=MagicMock()),
        patch(f"{_MODULE}.get_repo_node_id", return_value="REPO_ID"),
        patch(
            f"{_MODULE}.create_discussion",
            side_effect=RuntimeError("API error"),
        ),
    ):
        result = post_findings([finding], registry=registry)
    assert result == []


def test_post_findings_repo_id_error():
    """GIVEN get_repo_node_id raises RuntimeError,
    WHEN post_findings is called,
    THEN it returns empty.
    """
    from post_insights_to_discussions import post_findings

    finding = _make_finding()

    with (
        patch(f"{_MODULE}.detect_target_repo", return_value=("o", "r")),
        patch(f"{_MODULE}.resolve_category_id", return_value="CAT_ID"),
        patch(f"{_MODULE}.PostedRecord.load", return_value=MagicMock()),
        patch(
            f"{_MODULE}.get_repo_node_id",
            side_effect=RuntimeError("no node"),
        ),
    ):
        result = post_findings([finding])
    assert result == []
