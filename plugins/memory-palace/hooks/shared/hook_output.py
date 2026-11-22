"""Hook output construction for research interceptor responses."""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# hooks/shared/ -> the plugin root's src/, as in deduplication: tests and
# hooks import this module before anything else has put src/ on the path.
_SRC = str(Path(__file__).resolve().parents[2] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from memory_palace._vendored_leyline_atomic_file import (  # noqa: E402 - src/ joins sys.path above
    file_lock,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IntakeContext:
    """Per-request identifiers carried into the intake queue entry."""

    query_id: str
    tool_name: str
    query: str
    tool_input: dict[str, Any]


def build_hook_output(
    permission: str | None,
    response_parts: list[str],
    decision: Any,
) -> dict[str, Any]:
    """Build the hookSpecificOutput dict for the Claude hook protocol.

    ``permission`` is None when the hook only adds context: any
    permissionDecision would override the user's own prompt for the
    web call, and "allow" would skip it.
    """
    output: dict[str, Any] = {
        "hookEventName": "PreToolUse",
        "additionalContext": "\n".join(response_parts),
    }
    if permission is not None:
        output["permissionDecision"] = permission
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
        return {"hookSpecificOutput": build_hook_output(None, response_parts, decision)}
    return None


#: A sync holds the queue lock only to read and to rewrite the queue; a
#: hook waits this long and then skips queueing rather than stall the call.
_QUEUE_LOCK_TIMEOUT_SECONDS = 2.0


def queue_for_intake(
    plugin_root: Path,
    decision: Any,
    ctx: IntakeContext,
) -> None:
    """Queue high-novelty queries for knowledge-intake processing."""
    if not (decision.should_flag_for_intake and decision.intake_payload):
        return
    try:
        queue_path = plugin_root / "data" / "intake_queue.jsonl"
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        queue_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_id": ctx.query_id,
            "tool_name": ctx.tool_name,
            "query": ctx.query,
            "intake_payload": decision.intake_payload.to_dict(),
            "tool_input": ctx.tool_input,
        }
        # palace maintenance rewrites the queue under this lock.
        lock = file_lock(queue_path, timeout=_QUEUE_LOCK_TIMEOUT_SECONDS)
        with lock, queue_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(queue_entry) + "\n")
    except TimeoutError:  # an OSError, so caught before the I/O handler
        logger.warning("research_interceptor: intake queue busy; entry not queued")
    except (PermissionError, OSError) as e:
        logger.error(
            "research_interceptor: Failed to queue intake entry (I/O error): %s", e
        )
    except (TypeError, ValueError) as e:
        logger.error(
            "research_interceptor: Failed to queue intake entry (serialization error): %s",
            e,
        )
