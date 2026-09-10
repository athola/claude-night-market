"""Hooks must read the payload keys the harness actually sends.

Two hooks read ``hook_input["tool_result"]``. The PostToolUse payload
carries ``tool_response``. The dict was therefore always empty, the
``.get("exitCode", 1)`` beneath it always returned 1, and both hooks
returned ``None`` on every invocation from the day they were written:

- ``plugins/gauntlet/hooks/graph_auto_update.py``
- ``plugins/cartograph/hooks/graph_community_refresh.py``

Nothing caught it, because the tests supplied the same invented payload
the hooks read. A test that builds its own fixture cannot discover that
the fixture does not exist.

``exitCode`` is the second half of the same mistake. The Bash entry of
``tool_response`` carries ``stdout``, ``stderr``, ``interrupted`` and
``isImage``, and no exit status at all. There is nothing to read because
there is nothing to decide: PostToolUse runs only after a tool completes
successfully, and a failed command routes to PostToolUseFailure, where
the exit code arrives as the first line of the ``error`` string.

The check is textual because the alternative is executing every hook
against a live harness. It is scoped to hook files, which is where the
payload contract applies.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS = REPO_ROOT / "plugins"

# Scoped to reading the key off the hook payload, because the same spelling
# is correct one namespace over. ``tool_result`` is a real Anthropic Messages
# API content-block type, and conserve's context_warning and
# tool_output_summarizer both count those blocks out of a session transcript.
# A guard matching the bare token would demand a "fix" that breaks two
# correct files, so it matches the access instead: the payload dict, then the
# key.
_PAYLOAD = r"(?:hook_input|hook_data|payload|event|data)"
_ACCESS = r"""(?:\.get\(\s*|\[\s*)"""
TOOL_RESULT_RE = re.compile(_PAYLOAD + _ACCESS + r"""["']tool_result["']""")

# ``exitCode`` read off any dict. camelCase is unambiguous here: nothing else
# in this repository spells it that way, and the Bash tool_response has no
# such field for a hook to read.
EXIT_CODE_RE = re.compile(_ACCESS + r"""["']exitCode["']""")


def _hook_sources() -> list[Path]:
    """Every plugin hook implementation, excluding caches."""
    found = []
    for path in sorted(PLUGINS.glob("*/hooks/**/*.py")):
        if "__pycache__" in path.parts:
            continue
        found.append(path)
    return found


def test_discovery_finds_hook_sources() -> None:
    """An empty parametrize list would make the guards below vacuous."""
    assert len(_hook_sources()) > 10


@pytest.mark.parametrize(
    "hook", _hook_sources(), ids=lambda p: f"{p.parents[1].name}-{p.stem}"
)
def test_hooks_do_not_read_a_tool_result_key(hook: Path) -> None:
    """``tool_response`` is the PostToolUse key; ``tool_result`` is not."""
    relative = hook.relative_to(REPO_ROOT)
    source = hook.read_text(encoding="utf-8")
    matches = TOOL_RESULT_RE.findall(source)
    assert not matches, (
        f"{relative} reads a 'tool_result' key. The PostToolUse payload "
        f"carries 'tool_response'; 'tool_result' is always absent, so the "
        f"lookup yields an empty dict and every default beneath it wins. "
        f"Two hooks were dead for their whole lifetime this way."
    )


@pytest.mark.parametrize(
    "hook", _hook_sources(), ids=lambda p: f"{p.parents[1].name}-{p.stem}"
)
def test_hooks_do_not_read_an_exit_code_from_a_tool_response(hook: Path) -> None:
    """The Bash tool_response has no exit status to read."""
    relative = hook.relative_to(REPO_ROOT)
    source = hook.read_text(encoding="utf-8")
    assert not EXIT_CODE_RE.findall(source), (
        f"{relative} reads an 'exitCode' field. The Bash entry of "
        f"tool_response has stdout, stderr, interrupted and isImage only. "
        f"PostToolUse fires only on success, so there is no failure to "
        f"detect there; a hook that needs the exit status belongs under "
        f"PostToolUseFailure, where it arrives as the first line of 'error'."
    )
