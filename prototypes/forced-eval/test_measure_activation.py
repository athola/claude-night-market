#!/usr/bin/env python3
"""Tests for the forced-eval activation-measurement harness.

Colocated with the prototype (matching test_forced_eval.py) and run via:
    uv run python -m pytest prototypes/forced-eval/test_measure_activation.py

These lock the pure scoring/parsing contract. Live `claude` invocation
(run_trial/run_condition) is not exercised here: it spends tokens and
depends on model behaviour, which is what the harness measures, not what
the unit tests assert.
"""

from __future__ import annotations

import json
from pathlib import Path

import measure_activation as ma
import pytest


# --- extract_fired_skills -------------------------------------------------
class TestExtractFiredSkills:
    """Feature: recover Skill activations from claude stream-json output."""

    def test_nested_tool_use_is_found(self):
        """Given a Skill tool_use nested in an assistant message, it is extracted."""
        line = json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "ok"},
                        {
                            "type": "tool_use",
                            "name": "Skill",
                            "input": {"skill": "superpowers:brainstorming"},
                        },
                    ]
                },
            }
        )
        assert ma.extract_fired_skills([line]) == ["superpowers:brainstorming"]

    def test_command_and_name_input_keys_supported(self):
        """Given alternate input keys, the identifier is still recovered."""
        a = json.dumps(
            {
                "type": "tool_use",
                "name": "Skill",
                "input": {"command": "sanctum:commit-msg"},
            }
        )
        b = json.dumps(
            {"type": "tool_use", "name": "Skill", "input": {"name": "tome:research"}}
        )
        assert ma.extract_fired_skills([a, b]) == [
            "sanctum:commit-msg",
            "tome:research",
        ]

    def test_non_skill_tools_and_garbage_lines_ignored(self):
        """Given non-Skill tools and non-JSON lines, nothing is extracted."""
        lines = [
            "not json",
            json.dumps(
                {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}
            ),
            "",
        ]
        assert ma.extract_fired_skills(lines) == []


# --- score_trial ----------------------------------------------------------
class TestScoreTrial:
    """Feature: judge a trial against its label."""

    def test_positive_substring_match_is_correct(self):
        case = {"id": "p1", "kind": "positive", "expect": ["brainstorming"]}
        out = ma.score_trial(case, ["superpowers:brainstorming"])
        assert out["correct"] and out["activated"]

    def test_positive_no_match_is_incorrect(self):
        case = {"id": "p2", "kind": "positive", "expect": ["brainstorming"]}
        out = ma.score_trial(case, ["sanctum:commit-msg"])
        assert out["correct"] is False and out["activated"] is True

    def test_negative_clean_is_correct(self):
        case = {"id": "n1", "kind": "negative", "expect": []}
        out = ma.score_trial(case, [])
        assert out["correct"] is True and out["activated"] is False

    def test_negative_false_activation_is_incorrect(self):
        case = {"id": "n2", "kind": "negative", "expect": []}
        out = ma.score_trial(case, ["tome:research"])
        assert out["correct"] is False and out["activated"] is True


# --- aggregate ------------------------------------------------------------
class TestAggregate:
    """Feature: roll trial results into per-condition rates."""

    def test_rates_computed_over_kinds(self):
        results = [
            {"id": "p1", "kind": "positive", "activated": True, "correct": True},
            {"id": "p2", "kind": "positive", "activated": True, "correct": False},
            {"id": "n1", "kind": "negative", "activated": False, "correct": True},
            {"id": "n2", "kind": "negative", "activated": True, "correct": False},
        ]
        agg = ma.aggregate(results)
        assert agg["activation_rate"] == 0.5
        assert agg["false_activation_rate"] == 0.5
        assert agg["n_positive"] == 2 and agg["n_negative"] == 2


# --- paired_mcnemar -------------------------------------------------------
class TestPairedMcnemar:
    """Feature: paired discordance between baseline and treatment."""

    def test_treatment_only_wins_counted_as_c(self):
        """Given treatment fixes cases baseline missed, c reflects the lift."""
        baseline = [{"id": f"p{i}", "correct": False} for i in range(6)]
        treatment = [{"id": f"p{i}", "correct": True} for i in range(6)]
        out = ma.paired_mcnemar(baseline, treatment)
        assert out["c_treatment_only"] == 6 and out["b_baseline_only"] == 0
        # chi2cc = (|0-6|-1)^2/6 = 25/6 = 4.17 >= 3.84
        assert out["significant_p05"] is True

    def test_no_discordance_is_not_significant(self):
        baseline = [{"id": "p1", "correct": True}]
        treatment = [{"id": "p1", "correct": True}]
        out = ma.paired_mcnemar(baseline, treatment)
        assert out["n_discordant"] == 0 and out["significant_p05"] is False


# --- build_claude_cmd -----------------------------------------------------
class TestBuildClaudeCmd:
    """Feature: assemble the claude trial command."""

    def test_baseline_omits_settings(self):
        cmd = ma.build_claude_cmd("hi", None)
        assert (
            "--settings" not in cmd
            and "stream-json" in cmd
            and cmd[:2] == ["claude", "-p"]
        )

    def test_treatment_includes_settings(self):
        cmd = ma.build_claude_cmd("hi", Path("/tmp/s.json"))
        assert "--settings" in cmd and "/tmp/s.json" in cmd


# --- load_cases -----------------------------------------------------------
class TestLoadCases:
    """Feature: load and validate the labelled dataset."""

    def test_bad_kind_rejected(self, tmp_path):
        bad = tmp_path / "cases.json"
        bad.write_text(
            json.dumps({"cases": [{"id": "x", "prompt": "y", "kind": "maybe"}]})
        )
        with pytest.raises(ValueError):
            ma.load_cases(bad)

    def test_shipped_dataset_loads_and_has_both_kinds(self):
        cases = ma.load_cases(ma.DEFAULT_CASES)
        kinds = {c["kind"] for c in cases}
        assert kinds == {"positive", "negative"} and len(cases) >= 6
