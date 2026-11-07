"""The prompt-time state reset must not hold the prompt (#779)."""

from __future__ import annotations

import json
from pathlib import Path

HOOKS_JSON = Path(__file__).resolve().parents[2] / "hooks" / "hooks.json"


def test_clear_state_runs_async_on_user_prompt_submit() -> None:
    """GIVEN the UserPromptSubmit registration that clears notify state.

    THEN it is async: it prints nothing and the next read is the Stop
    hook at turn end, so making the prompt wait on it buys nothing.
    """
    config = json.loads(HOOKS_JSON.read_text())
    entries = [
        hook
        for group in config["hooks"]["UserPromptSubmit"]
        for hook in group["hooks"]
        if "--clear-state" in hook["command"]
    ]
    assert len(entries) == 1
    assert entries[0].get("async") is True
