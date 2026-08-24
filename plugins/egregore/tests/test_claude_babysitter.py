"""Tests for the real babysitter: a structured call to the claude CLI.

The babysitter is the only on-plan cost in a night, and the only place a
model's opinion enters. Both facts shape what is pinned here: it must be
cheap (it sees a diff and a truncated tail, never file contents), and it
must fail closed (an unreadable answer is BLOCKED, never PASS).
"""

from __future__ import annotations

import json
import shlex

import night_run
from claude_babysitter import ClaudeBabysitter


class FakeCli:
    """Stands in for the claude binary."""

    def __init__(self, code: int, output: str) -> None:
        """Reply to every invocation with this exit code and stdout."""
        self.code = code
        self.output = output
        self.calls: list[str] = []
        self.argv: list[list[str]] = []
        self.env: dict[str, str] | None = None

    def run(self, command, cwd=None, timeout=0, env=None):
        del cwd, timeout
        # Runner.run takes argv; joined here so the assertions below can
        # read one string.
        self.calls.append(shlex.join(command))
        self.argv.append(list(command))
        self.env = dict(env) if env is not None else None
        return night_run.Completed(returncode=self.code, output=self.output)


def envelope(verdict: str, reason: str = "ok", nxt: str = "") -> str:
    """Build the shape `claude --output-format json` returns."""
    return json.dumps(
        {
            "result": json.dumps(
                {"verdict": verdict, "reason": reason, "next_instruction": nxt}
            )
        }
    )


class TestVerdictParsing:
    """A structured answer in, a three-tuple out."""

    def test_a_pass_is_read(self) -> None:
        cli = FakeCli(0, envelope("PASS", "diff matches the task"))
        verdict, reason, _ = ClaudeBabysitter(runner=cli)(
            task={"id": "T1", "change": "x"},
            diff="d",
            test_output="1 passed",
            test_exit=0,
        )
        assert verdict == "PASS"
        assert "diff matches" in reason

    def test_a_fail_carries_its_next_instruction(self) -> None:
        cli = FakeCli(0, envelope("FAIL", "wrong file", "edit a/b.py instead"))
        verdict, _, nxt = ClaudeBabysitter(runner=cli)(
            task={"id": "T1", "change": "x"},
            diff="d",
            test_output="1 failed",
            test_exit=1,
        )
        assert verdict == "FAIL"
        assert nxt == "edit a/b.py instead"

    def test_a_bare_json_body_is_also_accepted(self) -> None:
        """Some CLI versions return the object directly, not wrapped."""
        cli = FakeCli(0, json.dumps({"verdict": "PASS", "reason": "fine"}))
        verdict, _, _ = ClaudeBabysitter(runner=cli)(
            task={"id": "T1"}, diff="d", test_output="ok", test_exit=0
        )
        assert verdict == "PASS"


class TestFailsClosed:
    """An unusable answer must never become a PASS."""

    def test_a_nonzero_exit_blocks(self) -> None:
        cli = FakeCli(1, "")
        verdict, reason, _ = ClaudeBabysitter(runner=cli)(
            task={"id": "T1"}, diff="d", test_output="ok", test_exit=0
        )
        assert verdict == "BLOCKED"
        assert "exit" in reason

    def test_unparseable_output_blocks(self) -> None:
        cli = FakeCli(0, "I think it looks good to me!")
        verdict, reason, _ = ClaudeBabysitter(runner=cli)(
            task={"id": "T1"}, diff="d", test_output="ok", test_exit=0
        )
        assert verdict == "BLOCKED"
        assert "parse" in reason.lower()

    def test_an_unknown_verdict_string_blocks(self) -> None:
        cli = FakeCli(0, envelope("LOOKS_FINE"))
        verdict, _, _ = ClaudeBabysitter(runner=cli)(
            task={"id": "T1"}, diff="d", test_output="ok", test_exit=0
        )
        assert verdict == "BLOCKED"


class TestCostControl:
    """The babysitter is the on-plan spend, so what it sees is capped."""

    def test_the_test_output_is_truncated_to_a_tail(self) -> None:
        cli = FakeCli(0, envelope("PASS"))
        ClaudeBabysitter(runner=cli, tail_chars=100)(
            task={"id": "T1"}, diff="d", test_output="x" * 5000, test_exit=0
        )
        assert len(cli.calls[0]) < 2000, "the whole suite output must not be sent"

    def test_the_diff_is_truncated_too(self) -> None:
        cli = FakeCli(0, envelope("PASS"))
        ClaudeBabysitter(runner=cli, tail_chars=100)(
            task={"id": "T1"}, diff="y" * 5000, test_output="ok", test_exit=0
        )
        assert len(cli.calls[0]) < 2000

    def test_the_model_is_the_one_the_item_asked_for(self) -> None:
        cli = FakeCli(0, envelope("PASS"))
        ClaudeBabysitter(runner=cli, model="opus")(
            task={"id": "T1"}, diff="d", test_output="ok", test_exit=0
        )
        assert "opus" in cli.calls[0]

    def test_the_schema_is_sent_so_the_answer_is_structured(self) -> None:
        cli = FakeCli(0, envelope("PASS"))
        ClaudeBabysitter(runner=cli)(
            task={"id": "T1"}, diff="d", test_output="ok", test_exit=0
        )
        assert "--json-schema" in cli.calls[0]
        assert "--output-format" in cli.calls[0]


class TestNoRecursion:
    """A babysitter must not be able to spawn a session that babysits."""

    def test_the_judge_marker_is_set(self) -> None:
        cli = FakeCli(0, envelope("PASS"))
        sitter = ClaudeBabysitter(runner=cli)
        assert sitter.env_marker in sitter.guard_env()
        assert sitter.guard_env()[sitter.env_marker] == "true"


class TestTheJudgeCallCarriesItsGuardAndReportsItsFailure:
    """The recursion marker reaches the child, and a failure says why.

    ``guard_env`` built the marker and nothing passed it, because
    ``Runner.run`` had no env parameter. A judge could therefore spawn a
    judge. Separately, a failed judge call reported only its exit code,
    dropping both the CLI's own error text and the fact that this is the
    one call in the run that spends Anthropic quota.
    """

    @staticmethod
    def _judge(cli: FakeCli) -> tuple[str, str, str]:
        return ClaudeBabysitter(runner=cli)(
            task={"id": "T1", "change": "x"},
            diff="d",
            test_output="out",
            test_exit=0,
        )

    def test_the_recursion_marker_reaches_the_child(self) -> None:
        cli = FakeCli(0, envelope("PASS"))
        sitter = ClaudeBabysitter(runner=cli)

        sitter(task={"id": "T1"}, diff="d", test_output="o", test_exit=0)

        assert cli.env is not None, "the judge child ran with no env at all"
        assert cli.env[sitter.env_marker] == "true"

    def test_a_failed_call_carries_the_error_text(self) -> None:
        verdict, reason, _ = self._judge(FakeCli(1, "claude: no such model"))

        assert verdict == "BLOCKED"
        assert "no such model" in reason

    def test_a_quota_refusal_is_named_as_one(self) -> None:
        _, reason, _ = self._judge(FakeCli(1, "429 rate_limit_error: slow down"))

        assert "rate_limit" in reason, (
            "the one call that spends quota did not classify its own refusal"
        )
