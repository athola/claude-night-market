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
