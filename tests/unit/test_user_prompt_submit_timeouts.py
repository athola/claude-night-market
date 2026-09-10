"""Gate: a UserPromptSubmit hook must be given more time than it needs.

When a ``UserPromptSubmit`` hook exceeds its declared ``timeout``, Claude
Code kills it and discards its output. Nothing fails; the injected context
simply never arrives, and the session runs on without the recall, the URL
capture, or the scope-guard warning the hook existed to provide.

The floor is measured, not guessed. On the reference machine (macOS,
system Python 3.9.6) a bare ``python3 -c pass`` costs 0.8 s, and every
Python hook registered here lands between 1.1 s and 2.3 s once imports and
its own work are counted. ``imbue``'s shell hook shells out to git and
runs 3.2 s warm, 4.8 s cold. Timeouts of 1-3 s left no margin at all and
were killing hooks on ordinary prompts.

Raising a timeout costs nothing on a healthy hook, which exits when it is
done. It costs only when a hook hangs, which is why the floor is a small
multiple of the measurement rather than an open-ended number.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Roughly 2x the slowest measured Python hook (2.3 s).
MIN_TIMEOUT_SECONDS = 5

# Hooks that shell out to git need their own floor: ~2x a 4.8 s cold run.
# Keyed by script basename, because the command carries ${CLAUDE_PLUGIN_ROOT}.
SLOW_HOOK_FLOORS = {"user-prompt-submit.sh": 10}


def _entries() -> list[tuple[str, str, int | None]]:
    """Every registered UserPromptSubmit command, with its declared timeout."""
    found = []
    for manifest in sorted(REPO_ROOT.glob("plugins/*/hooks/hooks.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for group in data.get("hooks", {}).get("UserPromptSubmit", []):
            for hook in group.get("hooks", []):
                found.append(
                    (
                        str(manifest.relative_to(REPO_ROOT)),
                        hook.get("command", ""),
                        hook.get("timeout"),
                    )
                )
    return found


def test_there_is_something_to_check() -> None:
    """A gate that silently matches nothing is not a gate."""
    assert _entries(), "no UserPromptSubmit hook found to check"


def test_every_hook_declares_a_timeout() -> None:
    """An absent timeout inherits a default this gate cannot reason about."""
    missing = [
        f"{path}: {command}" for path, command, timeout in _entries() if timeout is None
    ]
    assert not missing, "UserPromptSubmit hook without a timeout:\n" + "\n".join(
        missing
    )


def test_timeouts_clear_the_measured_floor() -> None:
    """Below the floor the hook is killed and its output is discarded."""
    too_tight = []
    for path, command, timeout in _entries():
        floor = MIN_TIMEOUT_SECONDS
        for basename, slow_floor in SLOW_HOOK_FLOORS.items():
            if basename in command:
                floor = slow_floor
        if timeout is not None and timeout < floor:
            too_tight.append(
                f"{path}: {command} has timeout {timeout}s, needs {floor}s"
            )
    assert not too_tight, (
        "UserPromptSubmit timeout below measured floor:\n" + "\n".join(too_tight)
    )
