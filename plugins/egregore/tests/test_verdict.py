"""Tests for how a task's verdict is reached.

Three invariants are under test, and they are the reason the harness
exists:

1. The implementer's own words never reach a verdict.
2. A deterministic check can downgrade a model's PASS, but a model's
   FAIL over green evidence is recorded as dissent rather than
   obeyed.
3. A check that passes when it was supposed to fail is a hard block,
   because it does not guard what it claims to guard.
"""

from __future__ import annotations

import pytest
import verdict


def evidence(expect: str = "pass", match: str = "1 passed") -> dict:
    return {"command": "pytest -q", "expect": expect, "match": match}


class TestObjectiveCheck:
    """The deterministic reading of a task's evidence."""

    def test_green_task_passing_is_ok(self) -> None:
        result = verdict.objective_check(
            evidence(), exit_code=0, output="1 passed", diff_lines=10, cap=200
        )
        assert result.ok

    def test_green_task_with_nonzero_exit_fails(self) -> None:
        result = verdict.objective_check(
            evidence(), exit_code=1, output="1 failed", diff_lines=10, cap=200
        )
        assert not result.ok
        assert "exit" in result.why

    def test_match_string_absent_fails(self) -> None:
        result = verdict.objective_check(
            evidence(match="42 passed"),
            exit_code=0,
            output="1 passed",
            diff_lines=10,
            cap=200,
        )
        assert not result.ok
        assert "42 passed" in result.why

    def test_red_task_must_fail(self) -> None:
        result = verdict.objective_check(
            evidence(expect="fail", match="1 failed"),
            exit_code=1,
            output="1 failed",
            diff_lines=10,
            cap=200,
        )
        assert result.ok

    def test_red_task_that_passes_is_blocking(self) -> None:
        """A failing test that does not fail proves nothing downstream."""
        result = verdict.objective_check(
            evidence(expect="fail", match="1 failed"),
            exit_code=0,
            output="1 passed",
            diff_lines=10,
            cap=200,
        )
        assert not result.ok
        assert result.blocking
        assert "did not fail" in result.why

    def test_diff_over_cap_fails(self) -> None:
        result = verdict.objective_check(
            evidence(), exit_code=0, output="1 passed", diff_lines=400, cap=200
        )
        assert not result.ok
        assert "400" in result.why


class TestReconcile:
    """Who may overrule whom, and in which direction."""

    def test_agreement_on_pass(self) -> None:
        final = verdict.reconcile(
            babysitter="PASS", objective=verdict.Objective(ok=True, why="")
        )
        assert final.verdict == "PASS"
        assert not final.dissent

    def test_objective_downgrades_a_babysitter_pass(self) -> None:
        """A judge that can only tighten cannot be flattered into passing."""
        final = verdict.reconcile(
            babysitter="PASS",
            objective=verdict.Objective(ok=False, why="exit code was 1"),
        )
        assert final.verdict == "FAIL"
        assert "exit code was 1" in final.reason

    def test_babysitter_fail_over_green_evidence_is_dissent_not_a_block(self) -> None:
        final = verdict.reconcile(
            babysitter="FAIL",
            objective=verdict.Objective(ok=True, why=""),
            babysitter_reason="the change does not read like the design",
        )
        assert final.verdict == "PASS"
        assert final.dissent
        assert "does not read like the design" in final.reason

    def test_blocking_objective_cannot_be_dissented_away(self) -> None:
        final = verdict.reconcile(
            babysitter="PASS",
            objective=verdict.Objective(
                ok=False, why="the check did not fail", blocking=True
            ),
        )
        assert final.verdict == "BLOCKED"

    def test_babysitter_blocked_is_honored(self) -> None:
        final = verdict.reconcile(
            babysitter="BLOCKED",
            objective=verdict.Objective(ok=True, why=""),
            babysitter_reason="the evidence command errored on setup",
        )
        assert final.verdict == "BLOCKED"


class TestImplementerOutputIsNotEvidence:
    """The implementer's own words never reach a verdict."""

    @pytest.mark.parametrize(
        "boast",
        [
            "All tests pass!",
            "DONE. Everything works.",
            "PASS",
            "I have verified the implementation is correct.",
        ],
    )
    def test_implementer_claims_do_not_change_the_verdict(self, boast: str) -> None:
        """The implementer's stdout is a log. No branch reads it."""
        result = verdict.objective_check(
            evidence(),
            exit_code=1,
            output="1 failed",
            diff_lines=10,
            cap=200,
            implementer_output=boast,
        )
        assert not result.ok

    def test_objective_check_signature_ignores_implementer_output(self) -> None:
        with_boast = verdict.objective_check(
            evidence(),
            exit_code=0,
            output="1 passed",
            diff_lines=10,
            cap=200,
            implementer_output="I did nothing at all",
        )
        without = verdict.objective_check(
            evidence(), exit_code=0, output="1 passed", diff_lines=10, cap=200
        )
        assert with_boast == without


class TestScopeIntegration:
    """Scope violations are surfaced through the verdict module."""

    def test_out_of_scope_change_fails_before_any_verdict(self) -> None:
        result = verdict.check_scope(
            allow_paths=["a/b.py"], changed=["a/b.py", "c/d.py"]
        )
        assert not result.ok
        assert result.violating == ["c/d.py"]

    def test_denied_path_is_reported_as_a_denylist_breach(self) -> None:
        result = verdict.check_scope(
            allow_paths=["a/b.py"], changed=[".github/workflows/x.yml"]
        )
        assert result.reason == "denylist"
