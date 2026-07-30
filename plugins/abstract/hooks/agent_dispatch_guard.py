#!/usr/bin/env python3
"""PreToolUse hook: block subagent dispatch that names no agent.

Claude Code resolves a subagent's model in this order, first match wins:

1. the ``CLAUDE_CODE_SUBAGENT_MODEL`` environment variable,
2. the per-invocation ``model`` parameter,
3. the agent's ``model:`` frontmatter,
4. the main conversation's model.

An Agent call that omits ``subagent_type`` reaches rung 4 and inherits
the session model. Subagents used to default to Haiku; since v2.1.198
Explore, Plan, and general-purpose all inherit instead. A throwaway
search dispatched from an Opus session is an Opus agent.

This hook denies any dispatch that does not name an agent, and the
denial states which tier fits which task shape. Rationale and the full
per-agent roster live in ``docs/agent-model-matrix.md``.

Zero external dependencies: standard library only.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

# Both names refer to the same dispatch tool. ``Task`` is the legacy
# name still used by older harness versions.
GUARDED_TOOLS = frozenset({"Agent", "Task"})

MATRIX_DOC = "docs/agent-model-matrix.md"


def build_denial_message() -> str:
    """Return the guidance shown when a dispatch names no agent."""
    return (
        "BLOCKED: Agent dispatch without a subagent_type.\n\n"
        "Subagents no longer default to Haiku. With no subagent_type the\n"
        "call falls through to the last rung of model resolution and will\n"
        "inherit the session model, so a throwaway search dispatched from\n"
        "an Opus session runs on Opus.\n\n"
        "Name an agent whose frontmatter pins the tier you want:\n\n"
        "  haiku  - mechanical, single-turn, deterministic output.\n"
        "           Lookups, git state parsing, schema validation,\n"
        "           formatting, recording. Examples:\n"
        "           sanctum:git-workspace-agent, sanctum:commit-agent,\n"
        "           abstract:plugin-validator, tome:code-searcher.\n\n"
        "  sonnet - judgment inside established patterns.\n"
        "           Code review, test generation, docs, implementation,\n"
        "           refactoring. Examples: pensive:code-reviewer,\n"
        "           parseltongue:python-tester, scribe:doc-editor,\n"
        "           attune:project-implementer.\n\n"
        "  opus   - architecture, adversarial reasoning, orchestration.\n"
        "           Design decisions, security audits, multi-agent\n"
        "           coordination. Examples: pensive:architecture-reviewer,\n"
        "           pensive:harden-orchestrator, abstract:meta-architect,\n"
        "           attune:project-architect.\n\n"
        "For a broad read-only sweep with no obvious specialist, use\n"
        "subagent_type: Explore. For open-ended multi-step work, use\n"
        "general-purpose. Both inherit the session model, so pick them\n"
        "deliberately rather than by omission.\n\n"
        f"Full roster and rationale: {MATRIX_DOC}"
    )


def evaluate(tool_name: str, tool_input: Any) -> dict[str, Any]:
    """Judge one PreToolUse call.

    Returns the deny payload when a guarded dispatch names no agent, and
    an empty mapping in every other case. A malformed ``tool_input`` is
    allowed rather than blocked: the guard defends against an omission a
    caller can fix, not against a payload shape it cannot interpret.
    """
    if tool_name not in GUARDED_TOOLS:
        return {}
    if not isinstance(tool_input, dict):
        return {}

    subagent_type = tool_input.get("subagent_type")
    if isinstance(subagent_type, str) and subagent_type.strip():
        return {}

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": build_denial_message(),
        }
    }


def _read_payload() -> dict[str, Any]:
    """Read the PreToolUse payload from stdin, with a legacy env fallback.

    Claude Code delivers the payload as JSON on stdin. The
    ``CLAUDE_TOOL_*`` environment variables are a fallback for the older
    synthetic test harness.
    """
    raw = ""
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()

    if raw:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return payload
        return {}

    legacy_input = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    try:
        parsed = json.loads(legacy_input)
    except json.JSONDecodeError:
        parsed = {}
    return {
        "tool_name": os.environ.get("CLAUDE_TOOL_NAME", ""),
        "tool_input": parsed if isinstance(parsed, dict) else {},
    }


def main() -> None:
    """Emit the hook decision for the incoming dispatch."""
    payload = _read_payload()
    decision = evaluate(payload.get("tool_name", ""), payload.get("tool_input", {}))
    print(json.dumps(decision))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Crash-proof: a broken guard must never wedge every dispatch.
        print(json.dumps({}))
        print(f"agent_dispatch_guard: hook error: {exc}", file=sys.stderr)
