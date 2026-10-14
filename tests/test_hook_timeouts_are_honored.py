"""SessionEnd hooks that need more than the batch deadline must be async.

Claude Code gives SessionEnd hooks max(1500ms, the largest timeout declared
in settings-level hooks). A plugin's own hooks.json timeout does not raise
that cap, so a plugin SessionEnd hook slower than 1.5s prints
"Hook cancelled" on every exit unless it declares `"async": true`, which
lets it outlive the session. Verified on CLI 2.1.251.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

PLUGINS = Path(__file__).resolve().parent.parent / "plugins"
BATCH_DEADLINE_SECONDS = 1.5


def _session_end_entries() -> list[tuple[Path, dict]]:
    found = []
    for manifest in sorted(PLUGINS.glob("*/hooks/hooks.json")):
        groups = json.loads(manifest.read_text()).get("hooks", {}).get("SessionEnd", [])
        for group in groups:
            for entry in group.get("hooks", []):
                found.append((manifest, entry))
    return found


def test_discovery_finds_session_end_hooks() -> None:
    """An empty parametrize list would make the gate below vacuously green."""
    assert _session_end_entries()


@pytest.mark.parametrize(
    "manifest,entry",
    _session_end_entries(),
    ids=lambda v: (
        v.parent.parent.name if isinstance(v, Path) else v.get("command", "")[-30:]
    ),
)
def test_slow_session_end_hooks_are_async(manifest: Path, entry: dict) -> None:
    """A declared timeout above the batch deadline means nothing unless async."""
    timeout = entry.get("timeout", 0)
    if timeout <= BATCH_DEADLINE_SECONDS:
        return
    assert entry.get("async") is True, (
        f"{manifest.parent.parent.name}: SessionEnd hook {entry.get('command')} "
        f"declares timeout {timeout}s but is not async, so it is cancelled at "
        f"{BATCH_DEADLINE_SECONDS}s on every session exit."
    )


def test_daily_learnings_aggregation_does_not_block_the_prompt() -> None:
    """The once-a-day aggregation may run for seconds and returns no context.

    It runs on UserPromptSubmit with a 15s timeout. Run in the foreground,
    the prompt waits for it on the first submit of each day, for output
    that is an empty additionalContext. Async lets the prompt go ahead.
    The second assertion keeps that reason true: an async hook's context
    arrives a turn late, so a hook that starts emitting context needs
    this decision revisited.
    """
    manifest = PLUGINS / "abstract" / "hooks" / "hooks.json"
    groups = json.loads(manifest.read_text())["hooks"]["UserPromptSubmit"]
    entries = [
        entry
        for group in groups
        for entry in group.get("hooks", [])
        if entry.get("command", "").endswith('aggregate_learnings_daily.py"')
    ]
    assert len(entries) == 1
    assert entries[0].get("async") is True

    spec = importlib.util.spec_from_file_location(
        "aggregate_learnings_daily", manifest.parent / "aggregate_learnings_daily.py"
    )
    assert spec is not None and spec.loader is not None
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    output = json.loads(hook.format_hook_output())
    assert output["hookSpecificOutput"]["additionalContext"] == ""
