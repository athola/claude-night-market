"""SessionEnd hooks that need more than the batch deadline must be async.

Claude Code gives SessionEnd hooks max(1500ms, the largest timeout declared
in settings-level hooks). A plugin's own hooks.json timeout does not raise
that cap, so a plugin SessionEnd hook slower than 1.5s prints
"Hook cancelled" on every exit unless it declares `"async": true`, which
lets it outlive the session. Verified on CLI 2.1.251.
"""

from __future__ import annotations

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
