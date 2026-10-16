"""estimate_text_tokens must not depend on whether leyline is installed."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

ABSTRACT_SRC = Path(__file__).resolve().parents[2] / "src"

SAMPLE = (
    "---\nname: demo\ndescription: Use when testing\n---\n\n"
    "# Demo\n\nSome prose here, long enough to differ by ratio.\n\n"
    "```python\nprint('hello world')\n```\n" * 6
)

_PROBE = textwrap.dedent(
    """
    import importlib.abc, sys

    BLOCK = {block!r}

    class Blocker(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if BLOCK and (name == "leyline" or name.startswith("leyline.")):
                raise ImportError("leyline blocked for test")
            return None

    sys.meta_path.insert(0, Blocker())
    sys.path.insert(0, {src!r})
    from abstract import tokens

    print(tokens._HAS_LEYLINE)
    print(tokens.estimate_text_tokens({text!r}))
    """
)


def _run(*, block: bool) -> tuple[bool, int]:
    probe = _PROBE.format(block=block, src=str(ABSTRACT_SRC), text=SAMPLE)
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        check=True,
    )
    has_leyline, count = completed.stdout.split()
    return has_leyline == "True", int(count)


def test_token_count_is_same_with_and_without_leyline() -> None:
    leyline_present, with_leyline = _run(block=False)
    leyline_blocked, without_leyline = _run(block=True)

    assert leyline_present is True
    assert leyline_blocked is False
    assert with_leyline == without_leyline
