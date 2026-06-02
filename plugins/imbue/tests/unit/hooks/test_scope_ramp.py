# ruff: noqa: D101,D102,D103,D205,D212,E501
"""Tests for the scope-ramp guard logic.

Feature: Couple implementation ambition to demonstrated competence

As the imbue verification spine
I want each code increment bounded to the current ambition rung
So that the agent starts with a small intentional slice and only
ramps a notch after the prior increment's understanding has been
demonstrated and recorded (the magenta hand-fly guard), instead of
one-shotting a large unreviewable change.

The pure logic lives in hooks/shared/scope_ramp.py so it can be
tested without filesystem or hook plumbing. State is passed in and
the new state returned, so these tests never touch disk.

Research: docs/research/3dfdba53-graduated-implementation.md
(Wilson 2019 85% band; Platanios 2019 competence gate; GDL clean
record; children-of-the-magenta hand-fly guard).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture
def sr():
    """Import the scope_ramp shared module via importlib."""
    shared = Path(__file__).resolve().parents[3] / "hooks" / "shared"
    module_path = shared / "scope_ramp.py"
    spec = importlib.util.spec_from_file_location("scope_ramp", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["scope_ramp"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestAddedLines:
    """Feature: measure the size of the increment a tool call would write."""

    @pytest.mark.unit
    def test_write_counts_content_lines(self, sr):
        n = sr.added_lines("Write", {"content": "a\nb\nc\n"})
        assert n == 3

    @pytest.mark.unit
    def test_edit_counts_new_string_lines(self, sr):
        n = sr.added_lines("Edit", {"old_string": "x\n", "new_string": "x\ny\nz\n"})
        assert n == 3

    @pytest.mark.unit
    def test_multiedit_sums_each_edit(self, sr):
        n = sr.added_lines(
            "MultiEdit",
            {"edits": [{"new_string": "a\nb\n"}, {"new_string": "c\n"}]},
        )
        assert n == 3

    @pytest.mark.unit
    def test_empty_content_is_zero(self, sr):
        assert sr.added_lines("Write", {"content": ""}) == 0

    @pytest.mark.unit
    def test_unknown_tool_is_zero(self, sr):
        assert sr.added_lines("Bash", {"command": "ls"}) == 0


class TestHighStakes:
    """Feature: high-blast-radius paths get a tighter rung (hybrid by stakes)."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "path",
        [
            "src/auth/login.py",
            "db/migrations/0007_add.sql",
            "billing/payment_gateway.ts",
            "infra/terraform/main.tf",
            "app/security/crypto.go",
        ],
    )
    def test_flags_high_stakes_paths(self, sr, path):
        assert sr.is_high_stakes(path) is True

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "path",
        ["src/utils/format.py", "README.md", "tests/test_util.py"],
    )
    def test_ordinary_paths_are_low_stakes(self, sr, path):
        assert sr.is_high_stakes(path) is False


class TestAssessRamp:
    """Feature: gate the increment against the current rung."""

    @pytest.mark.unit
    def test_within_rung_is_allowed(self, sr):
        state = {"rung": sr.RUNG_START, "increments": 0}
        finding, new_state = sr.assess_ramp(
            sr.RUNG_START - 1, "src/util.py", state, ramp_token=False
        )
        assert finding is None
        assert new_state["increments"] == 1

    @pytest.mark.unit
    def test_over_rung_is_flagged(self, sr):
        state = {"rung": sr.RUNG_START, "increments": 0}
        finding, _ = sr.assess_ramp(
            sr.RUNG_START + 50, "src/util.py", state, ramp_token=False
        )
        assert finding is not None
        assert finding["kind"] == "over-rung"
        assert str(sr.RUNG_START) in finding["detail"]

    @pytest.mark.unit
    def test_ramp_token_widens_the_rung(self, sr):
        """A recorded demonstration mints a token that ramps the rung a notch.

        An increment that was over-rung becomes within-rung once the token
        widens the rung. This is the 'ramp up a notch as you progress' rule:
        the bigger slice is only earned after understanding was demonstrated.
        """
        state = {"rung": sr.RUNG_START, "increments": 3}
        widened = int(round(sr.RUNG_START * sr.RAMP_FACTOR))
        # An increment just above the start rung but at/below the widened rung.
        increment = sr.RUNG_START + 5
        assert increment <= widened  # guard the fixture's own assumption
        finding, new_state = sr.assess_ramp(
            increment, "src/util.py", state, ramp_token=True
        )
        assert finding is None
        assert new_state["rung"] == widened

    @pytest.mark.unit
    def test_rung_never_exceeds_cap(self, sr):
        state = {"rung": sr.RUNG_CAP, "increments": 9}
        _, new_state = sr.assess_ramp(1, "src/util.py", state, ramp_token=True)
        assert new_state["rung"] == sr.RUNG_CAP

    @pytest.mark.unit
    def test_high_stakes_halves_effective_rung(self, sr):
        """A high-stakes increment within the raw rung but over its half is flagged."""
        state = {"rung": sr.RUNG_START, "increments": 2}
        increment = (sr.RUNG_START // 2) + 5  # within raw rung, over the half
        finding, _ = sr.assess_ramp(
            increment, "src/auth/login.py", state, ramp_token=False
        )
        assert finding is not None
        assert finding["kind"] == "over-rung"
        assert finding["high_stakes"] is True

    @pytest.mark.unit
    def test_high_stakes_reason_demands_explanation(self, sr):
        state = {"rung": sr.RUNG_START, "increments": 2}
        finding, _ = sr.assess_ramp(
            sr.RUNG_START * 3, "db/migrations/9.sql", state, ramp_token=False
        )
        assert "explain" in finding["detail"].lower()

    @pytest.mark.unit
    def test_low_stakes_reason_points_to_evidence(self, sr):
        state = {"rung": sr.RUNG_START, "increments": 2}
        finding, _ = sr.assess_ramp(
            sr.RUNG_START * 3, "src/util.py", state, ramp_token=False
        )
        assert "ramp-ok" in finding["detail"] or "evidence" in finding["detail"].lower()

    @pytest.mark.unit
    def test_corrupt_state_defaults_to_start_rung(self, sr):
        """Missing rung key falls back to the bounded start, never crashes."""
        finding, new_state = sr.assess_ramp(1, "src/util.py", {}, ramp_token=False)
        assert finding is None
        assert new_state["rung"] == sr.RUNG_START


class TestStakesTier:
    """Feature: drive the rung from leyline risk tiers, not a binary flag."""

    @pytest.mark.unit
    def test_high_stakes_path_resolves_to_red(self, sr):
        assert sr.stakes_for("src/auth/login.py") == "RED"

    @pytest.mark.unit
    def test_ordinary_path_resolves_to_green(self, sr):
        assert sr.stakes_for("src/util.py") == "GREEN"

    @pytest.mark.unit
    def test_explicit_tier_overrides_path(self, sr):
        """An authoritative risk-classification tier wins over the path guess."""
        assert sr.stakes_for("src/util.py", explicit="CRITICAL") == "CRITICAL"
        assert sr.stakes_for("src/auth/login.py", explicit="GREEN") == "GREEN"

    @pytest.mark.unit
    def test_unknown_explicit_tier_falls_back_to_path(self, sr):
        assert sr.stakes_for("src/util.py", explicit="banana") == "GREEN"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "tier,divisor",
        [("GREEN", 1), ("YELLOW", 1), ("RED", 2), ("CRITICAL", 4)],
    )
    def test_effective_rung_scales_by_tier(self, sr, tier, divisor):
        assert sr._effective_rung(80, tier) == max(1, 80 // divisor)

    @pytest.mark.unit
    def test_critical_quarters_the_rung_and_demands_explanation(self, sr):
        state = {"rung": sr.RUNG_START, "increments": 1}
        # A 12-line slice is within GREEN's 40 but over CRITICAL's 10.
        finding, _ = sr.assess_ramp(
            12, "src/util.py", state, ramp_token=False, stakes="CRITICAL"
        )
        assert finding is not None
        assert finding["stakes"] == "CRITICAL"
        assert finding["high_stakes"] is True
        assert "explain" in finding["detail"].lower()

    @pytest.mark.unit
    def test_yellow_keeps_full_rung_and_points_to_evidence(self, sr):
        state = {"rung": sr.RUNG_START, "increments": 1}
        finding, _ = sr.assess_ramp(
            sr.RUNG_START * 2,
            "src/routes/view.py",
            state,
            ramp_token=False,
            stakes="YELLOW",
        )
        assert finding["stakes"] == "YELLOW"
        assert finding["high_stakes"] is False
        assert "evidence" in finding["detail"].lower() or "ramp-ok" in finding["detail"]


class TestLedgerEntry:
    """Feature: record each rung climbed so the ramp can be audited."""

    @pytest.mark.unit
    def test_entry_captures_the_notch(self, sr):
        entry = sr.ledger_entry(
            increment=3,
            rung_before=40,
            rung_after=60,
            tier="GREEN",
            timestamp="2026-06-02T00:00:00",
        )
        assert entry == {
            "increment": 3,
            "rung_before": 40,
            "rung_after": 60,
            "stakes": "GREEN",
            "gate": "evidence",
            "timestamp": "2026-06-02T00:00:00",
        }

    @pytest.mark.unit
    def test_high_stakes_entry_records_explanation_gate(self, sr):
        entry = sr.ledger_entry(
            increment=1,
            rung_before=40,
            rung_after=60,
            tier="RED",
            timestamp="2026-06-02T00:00:00",
        )
        assert entry["gate"] == "explanation"

    @pytest.mark.unit
    def test_critical_entry_records_explanation_gate(self, sr):
        entry = sr.ledger_entry(
            increment=1,
            rung_before=40,
            rung_after=60,
            tier="CRITICAL",
            timestamp="2026-06-02T00:00:00",
        )
        assert entry["gate"] == "explanation"
