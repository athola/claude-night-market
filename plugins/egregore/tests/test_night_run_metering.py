"""The on-plan meter charges what the babysitter sends, not what it was given.

Math review finding C5. ``ClaudeBabysitter`` shows the model only the last
``DEFAULT_TAIL_CHARS`` of the diff and of the test output, but the meter
charged the whole of both. A 400000-character test log and a 20000-line
diff were charged as 115000 tokens for a prompt of about 2200, and a
100000 ceiling parked the item on budget it never spent.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import night_run
from claude_babysitter import DEFAULT_TAIL_CHARS, ClaudeBabysitter

TASK = {"id": "T1", "change": "add a function"}
DIFF = "+x\n" * 20000
TEST_OUTPUT = "." * 400000


def _judge(**_: object) -> tuple[str, str, str]:
    return ("PASS", "", "")


def _charge(babysitter: night_run.Babysitter, ceiling: int | None) -> int:
    spend = [0]
    metered = night_run._metered_babysitter(babysitter, spend, None, ceiling)
    metered(task=TASK, diff=DIFF, test_output=TEST_OUTPUT, test_exit=1)
    return spend[0]


def test_a_long_log_is_charged_for_the_tail_that_is_sent() -> None:
    """A ceiling of 100000 holds a prompt that is a few thousand tokens."""
    charged = _charge(_judge, ceiling=100_000)

    shown = 2 * DEFAULT_TAIL_CHARS // night_run.CHARS_PER_TOKEN
    assert shown <= charged < shown + 1000


class _QuietJudge(ClaudeBabysitter):
    """The real prompt rendering, with the CLI call replaced."""

    def __call__(
        self,
        task: Mapping[str, Any],
        diff: str = "",
        test_output: str = "",
        test_exit: int = 0,
        **_: Any,
    ) -> tuple[str, str, str]:
        return ("PASS", "", "")


def test_the_claude_babysitter_is_charged_for_its_exact_prompt() -> None:
    """The judge's rendered prompt, template included, is the charge."""
    sitter = _QuietJudge(tail_chars=500)

    charged = _charge(sitter, ceiling=None)

    assert charged == night_run.estimate_tokens(
        sitter._prompt(TASK, DIFF, TEST_OUTPUT, 1)
    )
