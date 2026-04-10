"""Hook output construction for research interceptor responses."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def build_hook_output(
    permission: str,
    response_parts: list[str],
    decision: Any,
) -> dict[str, Any]:
    """Build the hookSpecificOutput dict for the Claude hook protocol."""
    output: dict[str, Any] = {
        "hookEventName": "PreToolUse",
        "permissionDecision": permission,
        "additionalContext": "\n".join(response_parts),
    }
    if permission == "deny":
        output["permissionDecisionReason"] = (
            "cache_only mode: local knowledge available"
        )
    if decision.intake_payload:
        output["intakeFlagPayload"] = decision.intake_payload.to_dict()
    if decision.delta_reasoning:
        output["intakeDecisionRationale"] = decision.delta_reasoning
    return output


def build_response_parts(
    decision: Any,
    format_entry_fn: Any,
) -> list[str]:
    """Assemble context strings from a CacheInterceptDecision."""
    parts: list[str] = list(decision.context)
    if decision.cached_entries:
        parts.append("\n--- Relevant Cached Knowledge ---")
        for entry in decision.cached_entries:
            parts.append(format_entry_fn(entry))
    if decision.delta_reasoning:
        parts.append(f"[Memory Palace Intake] {decision.delta_reasoning}")
    return parts


def build_hook_payload(
    decision: Any,
    response_parts: list[str],
) -> dict[str, Any] | None:
    """Wrap decision into the top-level hook JSON payload (or None)."""
    if decision.action == "block":
        return {
            "hookSpecificOutput": build_hook_output("deny", response_parts, decision)
        }
    if (
        decision.action == "augment"
        or decision.should_flag_for_intake
        or response_parts
    ):
        return {
            "hookSpecificOutput": build_hook_output("allow", response_parts, decision)
        }
    return None


def queue_for_intake(
    plugin_root: Path,
    decision: Any,
    query_id: str,
    tool_name: str,
    query: str,
    tool_input: dict[str, Any],
) -> None:
    """Queue high-novelty queries for knowledge-intake processing."""
    if not (decision.should_flag_for_intake and decision.intake_payload):
        return
    try:
        queue_path = plugin_root / "data" / "intake_queue.jsonl"
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        queue_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_id": query_id,
            "tool_name": tool_name,
            "query": query,
            "intake_payload": decision.intake_payload.to_dict(),
            "tool_input": tool_input,
        }
        with queue_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(queue_entry) + "\n")
    except (PermissionError, OSError) as e:
        logger.error(
            "research_interceptor: Failed to queue intake entry (I/O error): %s", e
        )
    except (TypeError, ValueError) as e:
        logger.error(
            "research_interceptor: Failed to queue intake entry (serialization error): %s",
            e,
        )
