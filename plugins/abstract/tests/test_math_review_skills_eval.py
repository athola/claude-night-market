"""Token and audit scoring in skills_eval (math review B2-1 to B2-4)."""

from __future__ import annotations

import argparse
from pathlib import Path

from abstract.cli import AuditCLI, TokenCLI
from abstract.skills_eval.auditor import SkillsAuditor
from abstract.skills_eval.token_tracker import TokenUsageTracker


def _skill(root: Path, rel: str, words: int) -> Path:
    path = root / rel / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(["token"] * words)
    path.write_text(f"---\nname: {Path(rel).name}\ndescription: d\n---\n\n{body}\n")
    return path


def test_token_score_never_rises_as_tokens_grow(tmp_path: Path) -> None:
    """2500 tokens scored 80 and 2501 scored 99.98 (B2-1)."""
    auditor = SkillsAuditor(tmp_path)
    acceptable = int(auditor.audit_metrics["token_acceptable"])
    at, past = (
        auditor._calculate_token_score(acceptable),
        auditor._calculate_token_score(acceptable + 1),
    )
    assert past <= at


def test_a_skill_past_the_maximum_gets_the_critical_message(tmp_path: Path) -> None:
    """The optimal check ran first, so CRITICAL was unreachable (B2-2)."""
    tracker = TokenUsageTracker(tmp_path, optimal_limit=100, max_limit=200)
    _skill(tmp_path, "big", 2000)
    suggestions = tracker.optimize_suggestions("big")
    assert any(s.startswith("CRITICAL") for s in suggestions)


def test_nested_skills_are_measured_at_their_own_path(tmp_path: Path) -> None:
    """Nested skills were looked up as skills_dir/<leaf>/SKILL.md and read
    as 0 tokens (B2-3).
    """
    _skill(tmp_path, "group/inner", 300)
    data = TokenUsageTracker(tmp_path).analyze_all_skills()
    assert data["summary"]["total_tokens"] > 0


def test_tokens_command_reports_the_analysis_it_ran(tmp_path: Path) -> None:
    """It printed "Total tokens: 0, Files analyzed: 0" for any tree (B2-4)."""
    _skill(tmp_path, "one", 300)
    cli = TokenCLI()
    result = cli.execute(argparse.Namespace(path=tmp_path, output=None, threshold=50))
    text = cli.format_text(result.data)
    assert "Total tokens: 0" not in text
    assert "Files analyzed: 1" in text
    assert "OVER" in text


def test_audit_command_lists_each_skill(tmp_path: Path) -> None:
    """audit_skills returns skill_metrics; the formatter read 'skills' (B2-4)."""
    _skill(tmp_path, "one", 50)
    cli = AuditCLI()
    data = SkillsAuditor(tmp_path).audit_skills()
    assert "one:" in cli.format_text(data)
