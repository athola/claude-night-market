#!/usr/bin/env python3
"""Evaluate hookify rules against the event Claude Code is about to run.

This is the runtime the rule catalog exists for. ``install_rule.py``
writes ``.claude/hookify.<name>.local.md``; ``ConfigLoader`` reads those
and the bundled catalog; ``RuleEngine`` decides. Without this hook the
first two happen and the third never does.

Registered for PreToolUse (Bash, Write, Edit, MultiEdit),
UserPromptSubmit and Stop. Each maps onto one hookify event and the
context fields ``skills/writing-rules/SKILL.md`` documents:

    bash   -> command
    file   -> file_path, new_text, old_text, content
    prompt -> user_prompt
    stop   -> transcript (the tail of the transcript file)

A ``block`` rule denies the tool call, blocks the prompt, or keeps the
session going. A ``warn`` rule attaches its message as a system message.
Any failure inside the hook is reported on stderr and the event passes:
a guard that crashes must not take the session with it, and stderr is
the one channel that distinguishes a crash from a quiet pass.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from core.config_loader import (
    ConfigLoader,  # noqa: E402 - plugin root goes on sys.path first
)
from core.rule_engine import (  # noqa: E402 - plugin root goes on sys.path first
    RuleEngine,
    RuleResult,
)

# How much of the transcript a stop rule sees. The whole file can run to
# megabytes; the rules in the catalog look for what the session just did.
_TRANSCRIPT_TAIL_BYTES = 65_536

_FILE_TOOLS = {"Write", "Edit", "MultiEdit"}


def _read_payload() -> dict[str, Any] | None:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not raw.strip():
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"rule_guard: ignoring malformed stdin JSON: {exc}\n")
        return None
    return payload if isinstance(payload, dict) else None


def _file_context(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "Write":
        new_text = str(tool_input.get("content", ""))
        old_text = ""
    elif tool_name == "Edit":
        new_text = str(tool_input.get("new_string", ""))
        old_text = str(tool_input.get("old_string", ""))
    else:  # MultiEdit
        edits = tool_input.get("edits") or []
        new_text = "\n".join(str(e.get("new_string", "")) for e in edits)
        old_text = "\n".join(str(e.get("old_string", "")) for e in edits)
    return {
        "file_path": str(tool_input.get("file_path", "")),
        "new_text": new_text,
        "old_text": old_text,
        "content": new_text,
    }


def _transcript_tail(path: str) -> str:
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - _TRANSCRIPT_TAIL_BYTES))
            return handle.read().decode("utf-8", errors="replace")
    except OSError as exc:
        sys.stderr.write(f"rule_guard: cannot read transcript {path}: {exc}\n")
        return ""


def classify(payload: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    """Map a hook payload onto (hookify event, context), or None to pass."""
    event = payload.get("hook_event_name", "")
    if event == "UserPromptSubmit":
        return "prompt", {"user_prompt": str(payload.get("prompt", ""))}
    if event == "Stop":
        if payload.get("stop_hook_active"):
            # Already continued once on our say-so; a second block loops.
            return None
        return "stop", {
            "transcript": _transcript_tail(str(payload.get("transcript_path", "")))
        }
    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    if tool_name == "Bash":
        return "bash", {"command": str(tool_input.get("command", ""))}
    if tool_name in _FILE_TOOLS:
        return "file", _file_context(tool_name, tool_input)
    return None


def decide(event: str, results: list[RuleResult], engine: RuleEngine) -> dict[str, Any]:
    """Turn matched rules into the JSON Claude Code expects for this event."""
    if not results:
        return {}
    message = engine.format_messages(results)
    if engine.has_blocking_results(results):
        if event in ("prompt", "stop"):
            return {"decision": "block", "reason": message}
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": message,
            }
        }
    return {"systemMessage": message}


def main() -> None:
    payload = _read_payload()
    if payload is None:
        print(json.dumps({}))
        return
    classified = classify(payload)
    if classified is None:
        print(json.dumps({}))
        return
    event, context = classified

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    loader = ConfigLoader(user_rules_dir=Path(project_dir) / ".claude")
    engine = RuleEngine(loader.load_all_rules())
    results = engine.evaluate_event(event, context)
    print(json.dumps(decide(event, results, engine)))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - a crashed guard must not end the session
        sys.stderr.write(f"rule_guard: hook error: {exc}\n")
        print(json.dumps({}))
        sys.exit(0)
