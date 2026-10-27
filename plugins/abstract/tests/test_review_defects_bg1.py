"""Regression tests for defects found in the October 2026 bug review.

Each test names the behavior that was wrong, not the fix.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("scripts", "hooks"):
    _path = str(_PLUGIN_ROOT / _sub)
    if _path not in sys.path:
        sys.path.insert(0, _path)

import aggregate_skill_logs  # noqa: E402 - import after sys.path setup
import context_optimizer  # noqa: E402 - import after sys.path setup
from aggregate_skill_logs import (  # noqa: E402 - import after sys.path setup
    AggregationResult,
    extract_pinned_section,
    generate_learnings_md,
    load_log_entries,
)

from abstract.config import AbstractConfig  # noqa: E402 - import after sys.path setup


def _empty_result() -> AggregationResult:
    return AggregationResult(
        timestamp=datetime(2026, 10, 1, tzinfo=timezone.utc),
        skills_analyzed=0,
        total_executions=0,
        high_impact_issues=[],
        slow_skills=[],
        low_rated_skills=[],
        metrics_by_skill={},
    )


def _load_hook(name: str):
    spec = importlib.util.spec_from_file_location(
        f"bg1_{name}", _PLUGIN_ROOT / "hooks" / f"{name}.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestPinnedLearningsRoundTrip:
    """Regenerating LEARNINGS.md keeps the pinned section the same size."""

    def test_regenerating_twice_does_not_grow_the_pinned_section(self) -> None:
        pinned = "- keep this one"

        first = generate_learnings_md(_empty_result(), existing_pinned=pinned)
        second = generate_learnings_md(
            _empty_result(), existing_pinned=extract_pinned_section(first)
        )
        third = generate_learnings_md(
            _empty_result(), existing_pinned=extract_pinned_section(second)
        )

        assert extract_pinned_section(third) == pinned
        assert third.count("\n---\n") == first.count("\n---\n")


class TestClaudeHomeIsHonored:
    """Logs honor CLAUDE_HOME, so the files that go with them must too."""

    @pytest.fixture
    def claude_home(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        home = tmp_path / "alt-home"
        home.mkdir()
        decoy = tmp_path / "decoy-home"
        decoy.mkdir()
        monkeypatch.setenv("CLAUDE_HOME", str(home))
        monkeypatch.setattr(Path, "home", lambda: decoy)
        return home

    def test_stop_hook_reads_learnings_under_claude_home(
        self, claude_home: Path
    ) -> None:
        skills = claude_home / "skills"
        skills.mkdir()
        (skills / "LEARNINGS.md").write_text("**Skills Analyzed**: 4\n")
        hook = _load_hook("post_learnings_stop")

        assert hook._learnings_have_content() is True

    def test_daily_hook_keeps_its_timestamp_under_claude_home(
        self, claude_home: Path
    ) -> None:
        hook = _load_hook("aggregate_learnings_daily")

        assert hook.get_timestamp_path() == (
            claude_home / "skills" / "logs" / ".last_aggregation"
        )

    def test_hyperagents_section_reads_performance_history_under_claude_home(
        self, claude_home: Path
    ) -> None:
        skills = claude_home / "skills"
        skills.mkdir()
        history = [
            {
                "skill_ref": "abstract:demo",
                "version": "1",
                "score": 0.1 if index < 5 else 0.9,
                "domain": "general",
            }
            for index in range(10)
        ]
        (skills / "performance_history.json").write_text(
            json.dumps({"history": history})
        )

        lines = aggregate_skill_logs._format_hyperagents_section()

        assert any("abstract:demo" in line for line in lines)


class TestLogLoadingSurvivesOddLines:
    """A log line that is valid JSON but not an entry is skipped."""

    def test_valid_json_that_is_not_an_entry_is_skipped_not_fatal(
        self, tmp_path: Path
    ) -> None:
        skill_dir = tmp_path / "abstract" / "demo"
        skill_dir.mkdir(parents=True)
        good = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "outcome": "success",
            "context": {"session_id": "real-1"},
        }
        (skill_dir / "2026-10-01.jsonl").write_text(
            "\n".join(
                [
                    "[1, 2]",
                    "42",
                    "null",
                    json.dumps({"timestamp": None, "outcome": "success"}),
                    json.dumps(good),
                ]
            )
            + "\n"
        )

        entries = load_log_entries(tmp_path, days_back=30)

        assert len(entries["abstract:demo"]) == 1


class TestContextOptimizerReportsUnanalyzableSkill:
    """A skill the optimizer cannot analyze is reported on stderr."""

    def test_failure_reaches_stderr_instead_of_a_silent_debug_call(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        skill = tmp_path / "broken" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: broken\n---\n\nBody.\n", encoding="utf-8")
        optimizer = context_optimizer.ContextOptimizer(AbstractConfig())

        def explode(*args: object, **kwargs: object) -> None:
            raise ValueError("unparseable frontmatter")

        monkeypatch.setattr(optimizer, "analyze_skill_size", explode)

        results = optimizer.analyze_directory(tmp_path)

        assert results == []
        assert "unparseable frontmatter" in capsys.readouterr().err
