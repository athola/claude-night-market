"""Tests for insight engine core data structures."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from insight_types import (
    INSIGHT_TYPES,
    AnalysisContext,
    Finding,
    finding_hash,
)


def test_finding_creation():
    f = Finding(
        type="Trend",
        severity="medium",
        skill="abstract:skill-auditor",
        summary="success rate dropped from 92% to 71%",
        evidence="- 2026-03-29: 92%\n- 2026-04-12: 71%",
        recommendation="Investigate error pattern",
        source="trend_lens",
    )
    assert f.type == "Trend"
    assert f.severity == "medium"
    assert f.related_files == []


def test_finding_hash_deterministic():
    f = Finding(
        type="Trend",
        severity="medium",
        skill="abstract:skill-auditor",
        summary="success rate dropped from 92% to 71%",
        evidence="different evidence",
        recommendation="different rec",
        source="different_source",
    )
    h1 = finding_hash(f)
    h2 = finding_hash(f)
    assert h1 == h2
    assert len(h1) == 12


def test_finding_hash_differs_by_type():
    base = {
        "severity": "medium",
        "skill": "abstract:skill-auditor",
        "summary": "same summary",
        "evidence": "",
        "recommendation": "",
        "source": "test",
    }
    f1 = Finding(type="Trend", **base)
    f2 = Finding(type="Bug Alert", **base)
    assert finding_hash(f1) != finding_hash(f2)


def test_finding_hash_ignores_evidence():
    """Hash is based on type:skill:summary, not evidence."""
    base = {
        "type": "Trend",
        "severity": "medium",
        "skill": "x:y",
        "summary": "same",
        "recommendation": "",
        "source": "test",
    }
    f1 = Finding(evidence="evidence A", **base)
    f2 = Finding(evidence="evidence B", **base)
    assert finding_hash(f1) == finding_hash(f2)


def test_analysis_context_creation():
    ctx = AnalysisContext(
        metrics={},
        previous_snapshot=None,
        performance_history=None,
        improvement_memory=None,
        code_paths=[],
        pr_diff=None,
        trigger="stop",
    )
    assert ctx.trigger == "stop"
    assert ctx.code_paths == []
    assert ctx.pr_diff is None


def test_finding_title_with_skill():
    f = Finding(
        type="Trend",
        severity="medium",
        skill="abstract:skill-auditor",
        summary="success rate degrading",
        evidence="",
        recommendation="",
        source="test",
    )
    assert f.title() == "[Trend] abstract:skill-auditor: success rate degrading"


def test_finding_title_without_skill():
    f = Finding(
        type="Health Check",
        severity="info",
        skill="",
        summary="12 skills have 0 executions",
        evidence="",
        recommendation="",
        source="test",
    )
    assert f.title() == "[Health Check] 12 skills have 0 executions"


def test_insight_types_has_all_types():
    expected = {
        "Trend",
        "Pattern",
        "Bug Alert",
        "Optimization",
        "Improvement",
        "PR Finding",
        "Health Check",
    }
    assert set(INSIGHT_TYPES.keys()) == expected
