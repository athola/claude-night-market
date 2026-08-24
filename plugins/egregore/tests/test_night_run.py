"""Tests for the night-run driver.

The driver is where the invariants stop being pure functions and start
being an order of operations. What is pinned here is that order: the
diff and the test output are captured by the driver, out-of-scope files
are reverted before any judge sees them, and the loop stops rather than
improvising when it runs out of attempts, budget, or evidence.
"""

from __future__ import annotations

import shlex
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path

import night_run
import pytest
from budget import Budget


class FakeRunner:
    """A scripted command runner. Records every command it was given.

    ``Runner.run`` takes argv, so ``argv`` holds what the driver
    actually built. ``calls`` holds the same commands joined back into
    strings, which is what the substring assertions below read. The
    join happens here, in a test double, and not on the path to
    ``subprocess.run``.
    """

    def __init__(self, script: dict[str, tuple[int, str]]) -> None:
        """Map a command substring to the (exit code, output) it yields."""
        self.script = script
        self.calls: list[str] = []
        self.argv: list[list[str]] = []

    def run(
        self,
        command: Sequence[str],
        cwd: Path | None = None,
        timeout: int = 0,
        env=None,
    ):
        del cwd, timeout
        self.argv.append(list(command))
        joined = shlex.join(command)
        self.calls.append(joined)
        for key, (code, out) in self.script.items():
            if key in joined:
                return night_run.Completed(returncode=code, output=out)
        return night_run.Completed(returncode=0, output="")


def task(expect: str = "pass", match: str = "1 passed") -> dict:
    return {
        "id": "T1",
        "title": "do the thing",
        "change": "change the thing",
        "files": ["a/b.py"],
        "evidence": {"command": "pytest -q", "expect": expect, "match": match},
        "depends_on": [],
    }


HANDOFF = {
    "item": "NS-001",
    "branch": "night/NS-001",
    "base_branch": "main",
    "scope": {"allow_paths": ["a/"], "max_diff_lines": 200},
    "commands": {"setup": "uv sync", "test": "pytest -q", "full_test": "pytest -q"},
    "budget": {
        "max_tasks": 6,
        "max_attempts_per_task": 3,
        "implementer_timeout_s": 900,
    },
    "implementer": {"provider": "auto", "allow_on_plan_fallback": False},
    "babysitter": {"model": "sonnet"},
}


class TestGroundTruthIsCapturedByTheDriver:
    """The driver runs the checks itself."""

    def test_driver_runs_the_evidence_command_itself(self, tmp_path: Path) -> None:
        runner = FakeRunner({"pytest -q": (0, "1 passed")})
        night_run.run_task(
            task(), HANDOFF, tmp_path, runner, babysitter=lambda **_: ("PASS", "", "")
        )
        assert any("pytest -q" in c for c in runner.calls)

    def test_driver_reads_the_diff_itself(self, tmp_path: Path) -> None:
        runner = FakeRunner({"pytest -q": (0, "1 passed")})
        night_run.run_task(
            task(), HANDOFF, tmp_path, runner, babysitter=lambda **_: ("PASS", "", "")
        )
        assert any("diff" in c for c in runner.calls)

    def test_a_lying_implementer_cannot_pass_a_red_task(self, tmp_path: Path) -> None:
        """The implementer says done; the test says failed. The test wins."""
        runner = FakeRunner(
            {
                "delegation_executor": (0, "DONE. All tests pass."),
                "pytest -q": (1, "1 failed"),
            }
        )
        result = night_run.run_task(
            task(), HANDOFF, tmp_path, runner, babysitter=lambda **_: ("PASS", "", "")
        )
        assert result.verdict == "FAIL"


class TestScopeEnforcement:
    """Out-of-scope edits are reverted before judging."""

    def test_out_of_scope_file_is_reverted_before_judging(self, tmp_path: Path) -> None:
        runner = FakeRunner(
            {
                "diff --name-only": (0, "a/b.py\nsecrets/keys.txt\n"),
                "pytest -q": (0, "1 passed"),
            }
        )
        judged: list[bool] = []

        def babysitter(**_):
            judged.append(True)
            return ("PASS", "", "")

        result = night_run.run_task(
            task(), HANDOFF, tmp_path, runner, babysitter=babysitter
        )
        assert result.verdict in {"FAIL", "BLOCKED"}
        assert any("checkout --" in c and "secrets/keys.txt" in c for c in runner.calls)
        assert judged == [], "the babysitter must not see out-of-scope work"


class TestAttempts:
    """Retry budget, and when retrying is pointless."""

    def test_retries_up_to_the_budget_then_blocks(self, tmp_path: Path) -> None:
        runner = FakeRunner({"pytest -q": (1, "1 failed")})
        result = night_run.run_task(
            task(), HANDOFF, tmp_path, runner, babysitter=lambda **_: ("FAIL", "no", "")
        )
        assert result.verdict in {"FAIL", "BLOCKED"}
        assert result.attempts == 3

    def test_stops_at_the_first_pass(self, tmp_path: Path) -> None:
        runner = FakeRunner({"pytest -q": (0, "1 passed")})
        result = night_run.run_task(
            task(), HANDOFF, tmp_path, runner, babysitter=lambda **_: ("PASS", "", "")
        )
        assert result.verdict == "PASS"
        assert result.attempts == 1

    def test_a_blocking_objective_does_not_retry(self, tmp_path: Path) -> None:
        """A test that should fail but passes is not fixable by retrying."""
        runner = FakeRunner({"pytest -q": (0, "1 passed")})
        result = night_run.run_task(
            task(expect="fail", match="1 failed"),
            HANDOFF,
            tmp_path,
            runner,
            babysitter=lambda **_: ("PASS", "", ""),
        )
        assert result.verdict == "BLOCKED"
        assert result.attempts == 1


class TestImplementerDispatch:
    """Implementation goes off-plan, with no silent fallback."""

    def test_implementer_is_dispatched_off_plan(self, tmp_path: Path) -> None:
        runner = FakeRunner({"pytest -q": (0, "1 passed")})
        night_run.run_task(
            task(), HANDOFF, tmp_path, runner, babysitter=lambda **_: ("PASS", "", "")
        )
        dispatch = [c for c in runner.calls if "delegation_executor" in c]
        assert dispatch, "implementation must go through conjure's delegation executor"
        assert "auto" in dispatch[0]

    def test_no_claude_fallback_unless_the_item_allows_it(self, tmp_path: Path) -> None:
        runner = FakeRunner(
            {
                "delegation_executor": (1, "providers_exhausted"),
                "pytest -q": (1, "1 failed"),
            }
        )
        result = night_run.run_task(
            task(), HANDOFF, tmp_path, runner, babysitter=lambda **_: ("FAIL", "", "")
        )
        assert result.verdict == "BLOCKED"
        assert "providers_exhausted" in result.reason
        assert not any("claude --print" in c for c in runner.calls)


class TestProofLedger:
    """Every attempt leaves a row a human can read."""

    def test_every_attempt_is_recorded(self, tmp_path: Path) -> None:
        runner = FakeRunner({"pytest -q": (1, "1 failed")})
        result = night_run.run_task(
            task(), HANDOFF, tmp_path, runner, babysitter=lambda **_: ("FAIL", "no", "")
        )
        assert len(result.ledger) == result.attempts
        for row in result.ledger:
            assert row["command"] == "pytest -q"
            assert "exit" in row

    def test_ledger_rows_carry_the_raw_output(self, tmp_path: Path) -> None:
        runner = FakeRunner({"pytest -q": (0, "1 passed")})
        result = night_run.run_task(
            task(), HANDOFF, tmp_path, runner, babysitter=lambda **_: ("PASS", "", "")
        )
        assert result.ledger[0]["output"] == "1 passed"


def test_render_proof_table_is_readable(tmp_path: Path) -> None:
    runner = FakeRunner({"pytest -q": (0, "1 passed")})
    result = night_run.run_task(
        task(), HANDOFF, tmp_path, runner, babysitter=lambda **_: ("PASS", "", "")
    )
    table = night_run.render_proof(result)
    assert "| T1 |" in table
    assert "pytest -q" in table
    assert "PASS" in table


@pytest.mark.parametrize("provider", ["auto", "minimax", "qwen"])
def test_provider_is_passed_through(tmp_path: Path, provider: str) -> None:
    handoff = {**HANDOFF, "implementer": {"provider": provider}}
    runner = FakeRunner({"pytest -q": (0, "1 passed")})
    night_run.run_task(
        task(), handoff, tmp_path, runner, babysitter=lambda **_: ("PASS", "", "")
    )
    assert any(provider in c for c in runner.calls if "delegation_executor" in c)


class TestBudgetReuse:
    """The driver honors egregore's existing cooldown, not a second one.

    Folding the night-shift driver into egregore means it shares the
    cooldown that ``watchdog.sh`` and ``budget.py`` already agree on. A
    parallel cooldown file would be a second source of truth and the two
    would drift.
    """

    def test_cooldown_stops_the_task_before_any_dispatch(self, tmp_path: Path) -> None:

        future = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        cooling = Budget(cooldown_until=future)
        runner = FakeRunner({"pytest -q": (0, "1 passed")})

        result = night_run.run_task(
            task(),
            HANDOFF,
            tmp_path,
            runner,
            babysitter=lambda **_: ("PASS", "", ""),
            budget=cooling,
        )
        assert result.verdict == "BLOCKED"
        assert "cooldown" in result.reason
        assert runner.calls == [], "nothing may run during a cooldown"

    def test_an_expired_cooldown_does_not_stop_the_task(self, tmp_path: Path) -> None:

        past = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        runner = FakeRunner({"pytest -q": (0, "1 passed")})
        result = night_run.run_task(
            task(),
            HANDOFF,
            tmp_path,
            runner,
            babysitter=lambda **_: ("PASS", "", ""),
            budget=Budget(cooldown_until=past),
        )
        assert result.verdict == "PASS"

    def test_no_budget_means_no_cooldown_check(self, tmp_path: Path) -> None:
        runner = FakeRunner({"pytest -q": (0, "1 passed")})
        result = night_run.run_task(
            task(), HANDOFF, tmp_path, runner, babysitter=lambda **_: ("PASS", "", "")
        )
        assert result.verdict == "PASS"


class TestSubprocessRunner:
    """The real runner. This is the argv path the security review shaped."""

    def test_runs_a_command_and_captures_stdout(self, tmp_path: Path) -> None:
        result = night_run.SubprocessRunner().run(["echo", "hello"], cwd=tmp_path)
        assert result.returncode == 0
        assert "hello" in result.output

    def test_captures_stderr_too(self, tmp_path: Path) -> None:
        """A crash is evidence. A runner that drops stderr is silent on it."""
        script = tmp_path / "boom.py"
        script.write_text("import sys\nsys.stderr.write('boom')\nsys.exit(3)\n")
        result = night_run.SubprocessRunner().run(
            ["python3", str(script)], cwd=tmp_path
        )
        assert result.returncode == 3
        assert "boom" in result.output

    def test_no_shell_means_metacharacters_are_literal(self, tmp_path: Path) -> None:
        """`;` reaches echo as an argument; it does not start a new command."""
        marker = tmp_path / "pwned"
        result = night_run.SubprocessRunner().run(
            ["echo", "a", ";", "touch", str(marker)], cwd=tmp_path
        )
        assert result.returncode == 0
        assert ";" in result.output
        assert not marker.exists(), "a shell would have created this file"

    def test_a_command_line_passed_as_one_word_is_not_re_split(
        self, tmp_path: Path
    ) -> None:
        """The runner takes argv, so it never parses a string into words.

        This is what the protocol change bought. The runner used to
        ``shlex.split`` whatever it was handed, so a caller who built the
        string by hand had its quoting honoured and its words separated.
        Handing the same text as one argv element now looks for a binary
        by that literal name and fails at 127, which is loud, rather than
        running ``touch`` as a second word, which is not.
        """
        marker = tmp_path / "pwned"
        result = night_run.SubprocessRunner().run(
            [f"echo a ; touch {marker}"], cwd=tmp_path
        )
        assert result.returncode == 127
        assert not marker.exists()

    def test_a_missing_binary_is_reported_not_raised(self, tmp_path: Path) -> None:
        result = night_run.SubprocessRunner().run(
            ["definitely-not-a-binary"], cwd=tmp_path
        )
        assert result.returncode == 127
        assert "definitely-not-a-binary" in result.output

    def test_an_empty_command_is_reported(self, tmp_path: Path) -> None:
        """An empty argv still reaches the runner from the text boundary.

        ``_argv_from_text`` returns ``[]`` for a handoff that declares a
        blank command, so this guard defends a real boundary rather than
        an internal invariant.
        """
        assert night_run._argv_from_text("   ") == []
        result = night_run.SubprocessRunner().run([], cwd=tmp_path)
        assert result.returncode == 1
        assert "empty" in result.output

    def test_a_timeout_is_reported_with_the_conventional_code(
        self, tmp_path: Path
    ) -> None:
        script = tmp_path / "slow.py"
        script.write_text("import time\ntime.sleep(5)\n")
        result = night_run.SubprocessRunner().run(
            ["python3", str(script)], cwd=tmp_path, timeout=1
        )
        assert result.returncode == night_run.TIMEOUT_EXIT
        assert "timed out" in result.output
