"""Counts and bounds in abstract's analysis scripts (math review B2-5 to B2-9).

Each test pins a number a report printed wrong: headings counted inside
code fences, a token count labeled in kilobytes, the "worst" regressions
taken in insertion order, a 0-execution check no input could reach, and
a line range accepted while its end ran past the file.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))

from aggregate_skill_logs import calculate_skill_metrics, load_log_entries
from finding_verifier import FileRef, verify_refs
from insight_types import AnalysisContext
from lenses import health_lens, trend_lens
from skill_analyzer import HIGH_TOKEN_LIMIT, MODERATE_TOKEN_LIMIT, SkillAnalyzer

from abstract.utils import count_sections


def _ctx(metrics=None, improvement_memory=None) -> AnalysisContext:
    return AnalysisContext(
        metrics=metrics or {},
        previous_snapshot=None,
        performance_history=None,
        improvement_memory=improvement_memory,
        trigger="stop",
    )


def test_headings_inside_a_code_fence_are_not_sections() -> None:
    """Shell comments in a bash fence counted as h1 themes (B2-5)."""
    content = (
        "# Title\n\n```bash\n# install deps\n# run tests\n```\n\n~~~\n# lint\n~~~\n"
    )
    assert count_sections(content, level=1) == 1


def test_token_recommendations_name_tokens_not_kilobytes() -> None:
    """2048 tokens is about 8 KB at 4 chars a token, not 2 KB (B2-6)."""
    analyzer = SkillAnalyzer()
    high = analyzer._generate_recommendations(10, 1, 1, HIGH_TOKEN_LIMIT + 1)
    moderate = analyzer._generate_recommendations(10, 1, 1, MODERATE_TOKEN_LIMIT + 1)
    text = " ".join(high + moderate)
    assert "KB" not in text
    assert str(HIGH_TOKEN_LIMIT) in high[-1]
    assert str(HIGH_TOKEN_LIMIT) in moderate[-1]


def test_worst_failures_are_the_largest_regressions() -> None:
    """The summary listed the first three failures, not the worst (B2-7)."""
    improvements = [-0.01, -0.02, -0.03, -0.9, -0.8]

    class Memory:
        @property
        def outcomes(self):
            return {"p:s": self.get_failed_strategies()}

        def get_effective_strategies(self):
            return []

        def get_failed_strategies(self):
            return [
                {"change_summary": f"c{i}", "improvement": imp}
                for i, imp in enumerate(improvements)
            ]

    findings = trend_lens.analyze(_ctx(improvement_memory=Memory()))
    summary = next(f for f in findings if "regression" in f.summary.lower())
    assert "c3 (-0.900)" in summary.evidence
    assert "c4 (-0.800)" in summary.evidence
    assert "c0" not in summary.evidence


def test_a_skill_with_only_old_logs_is_reported_unused(tmp_path: Path) -> None:
    """A skill dir with no in-window entry produced no key, so the
    0-execution branch was unreachable (B2-8).
    """
    skill_dir = tmp_path / "plug" / "stale-skill"
    skill_dir.mkdir(parents=True)
    old = datetime.now(timezone.utc) - timedelta(days=90)
    entry = {"timestamp": old.isoformat(), "outcome": "success"}
    (skill_dir / "log.jsonl").write_text(json.dumps(entry) + "\n")

    entries = load_log_entries(tmp_path, days_back=30)
    metrics = {k: calculate_skill_metrics(k, v) for k, v in entries.items()}
    findings = health_lens.analyze(_ctx(metrics=metrics))
    assert any("plug:stale-skill" in f.evidence for f in findings)


def test_a_naive_timestamp_is_read_as_utc(tmp_path: Path) -> None:
    """A naive timestamp raised TypeError against the aware cutoff and
    aborted the whole aggregation.
    """
    skill_dir = tmp_path / "plug" / "skill"
    skill_dir.mkdir(parents=True)
    naive = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    entry = {"timestamp": naive, "outcome": "success"}
    (skill_dir / "log.jsonl").write_text(json.dumps(entry) + "\n")

    assert len(load_log_entries(tmp_path, days_back=30)["plug:skill"]) == 1


def test_a_range_ending_past_the_file_is_stale(tmp_path: Path) -> None:
    """Only line_start was checked, so 90-500 in a 100-line file passed
    as present (B2-9).
    """
    (tmp_path / "f.py").write_text("x\n" * 100)
    result = verify_refs([FileRef("f.py", 90, 500)], tmp_path)
    assert result.status != "present"
