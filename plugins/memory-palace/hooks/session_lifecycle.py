#!/usr/bin/env python3
"""Session lifecycle hook for memory-palace.

Records a summary of the current Claude Code session to persistent storage
when the session ends (Stop event).  Designed to stay well under the 2-second
timeout budget: it reads a small JSON payload, constructs a SessionRecord, and
writes one JSON file plus a lightweight index update.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup: add the plugin src/ directory so we can import memory_palace.
# Hooks run as standalone scripts; the package is not installed in sys.path.
# ---------------------------------------------------------------------------
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PLUGIN_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# PLUGIN_ROOT is version scoped: hooks run from cache/<marketplace>/
# <plugin>/<version>/, so user data written under it is invisible to
# the next release (issue #661). DATA_ROOT is the version-independent
# root, and equals PLUGIN_ROOT in a source checkout.
import contextlib

from memory_palace.paths import persistent_root

DATA_ROOT = persistent_root(PLUGIN_ROOT)

_HAS_SESSION_HISTORY = False
try:
    from memory_palace.session_history import (
        SessionHistoryManager,
        SessionRecord,
        SessionUnit,
        merge_handoff_units,
    )

    _HAS_SESSION_HISTORY = True
except (ImportError, ModuleNotFoundError) as _import_err:
    logging.getLogger(__name__).debug(
        "session_lifecycle: memory_palace.session_history not available: %s",
        _import_err,
    )

# ---------------------------------------------------------------------------
# Graph wiring helpers (Issue #393) — never raise
# ---------------------------------------------------------------------------

_CROSS_PALACE_TOOLS = {"WebFetch", "WebSearch", "Read", "Edit"}


def _try_record_journey_completion(
    palaces_dir: Path,
    session_id: str,
    tools_used: list,
) -> None:
    """Record journey completion and run link prediction. Never raises.

    Detects cross-palace navigation by checking whether the session used
    web-intake or read tools, then records a journey via JourneyTracker
    and runs predict_links once.
    """
    try:
        from memory_palace.graph_analyzer import (
            PalaceGraphAnalyzer,  # noqa: PLC0415 - deferred import inside try/except for graceful degradation
        )
        from memory_palace.journey_tracker import (
            JourneyTracker,  # noqa: PLC0415 - deferred import inside try/except for graceful degradation
        )
        from memory_palace.knowledge_graph import (
            KnowledgeGraph,  # noqa: PLC0415 - deferred import inside try/except for graceful degradation
        )

        db_path = palaces_dir / "knowledge_graph.db"
        if not db_path.exists():
            return

        used_set = set(tools_used or [])
        if not used_set.intersection(_CROSS_PALACE_TOOLS):
            return  # No cross-palace navigation detected

        graph = KnowledgeGraph(str(db_path))
        try:
            tracker = JourneyTracker(graph)
            journey_id = tracker.start_journey(
                entity_id=f"session_{session_id[:16]}",
                trigger="session_stop",
            )
            tracker.complete_journey(journey_id, outcome="completed")

            analyzer = PalaceGraphAnalyzer(graph)
            suggestions = analyzer.predict_links(top_n=5)
            if suggestions:
                sys.stderr.write(
                    f"session_lifecycle: link predictions: {suggestions[:3]}\n"
                )
        finally:
            graph.close()
    except Exception as exc:  # noqa: BLE001 - hooks must never crash; log and continue
        logger.debug("session_lifecycle: graph wiring skipped: %s", exc)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _derive_session_id(payload: dict) -> str:
    """Generate a stable, filesystem-safe session ID.

    Combines available environment variables with payload data so that the
    same invocation context always produces the same ID.  The result is a
    date-prefixed hex digest safe to use as a filename.
    """
    seed_parts = [
        os.environ.get("CLAUDE_SESSION_ID", ""),
        os.environ.get("TERM_SESSION_ID", ""),
        os.environ.get("TMUX", ""),
        os.getcwd(),
        str(payload.get("session_id", "")),
    ]
    seed = "|".join(part for part in seed_parts if part)
    if not seed:
        seed = datetime.now(timezone.utc).isoformat()
    digest = hashlib.sha256(seed.encode()).hexdigest()[:12]
    date_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{date_prefix}-{digest}"


def _safe_float(value: object, default: float = 0.0) -> float:
    """Convert value to float, returning default on failure."""
    if not isinstance(value, (int, float, str)):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


_STAGING_PATH = DATA_ROOT / "data" / "state" / "handoff_units.json"


def _read_staged_units(path: Path) -> list[dict] | None:
    """Read the staging file written by session-handoff.

    The Stop payload carries no transcript content and the hook has no
    model, so units cannot be extracted here. The skill stages them; this
    reads them. Returns None when the file cannot be used, which tells the
    caller not to discard it: an unreadable claim stays for a later Stop,
    and one that does not parse is moved to ``*.corrupt`` with a warning
    so the hand-written units can be repaired instead of lost.

    The file is left in place: the caller removes it with
    ``_discard_staged_units`` only after the units are saved, so a failed
    write does not consume them.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        logger.warning("session_lifecycle: cannot read %s: %s", path, exc)
        return None
    except json.JSONDecodeError as exc:
        corrupt = path.with_name(f"{path.name}.corrupt")
        try:
            os.replace(path, corrupt)
        except OSError as move_exc:
            logger.warning(
                "session_lifecycle: %s does not parse (%s) and cannot be moved"
                " aside: %s",
                path,
                exc,
                move_exc,
            )
            return None
        logger.warning(
            "session_lifecycle: %s does not parse (%s); kept as %s",
            path,
            exc,
            corrupt,
        )
        return None
    units = raw.get("units") if isinstance(raw, dict) else raw
    return [u for u in (units or []) if isinstance(u, dict)]


# Far past the 2s Stop timeout in hooks.json: a claim this old belongs to a
# Stop that was killed, even if its pid has since been reused.
_STALE_CLAIM_NS = 10 * 60 * 10**9

# Claims pile up while record writes keep failing, and every later Stop
# re-read all of them inside its 2s budget. Oldest first, a batch per Stop.
_MAX_CLAIMS_PER_STOP = 8


def _pid_is_running(pid: int) -> bool:
    """Probe with signal 0, which checks existence without delivering."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _claim_is_ours(claim: Path, now_ns: int) -> bool:
    """Whether this Stop may record a claim file.

    A claim made by this process is ours. So is one whose Stop can no
    longer record it: its process has exited, or it is older than any Stop
    runs. A fresh claim from another live pid belongs to a concurrent Stop
    that has not recorded it yet.
    """
    parts = claim.name.split(".")
    try:
        made_ns, pid = int(parts[-3]), int(parts[-2])
    except (IndexError, ValueError):
        return False
    if pid == os.getpid():
        return True
    if now_ns - made_ns > _STALE_CLAIM_NS:
        return True
    return pid > 0 and not _pid_is_running(pid)


def _claim_staged_units(path: Path) -> list[Path]:
    """Move the staging file aside and return the claims this Stop records.

    The skill may stage more units while this Stop runs. Renaming first
    sends those writes to a fresh staging file instead of one this hook is
    about to delete. Claims left by an earlier Stop whose record write
    failed are returned too, so their units are not stranded.
    """
    now_ns = time.time_ns()
    claim = path.with_name(f"{path.name}.{now_ns}.{os.getpid()}.claim")
    try:
        os.rename(path, claim)
    except FileNotFoundError:
        pass  # nothing staged since the last Stop
    except OSError as exc:
        # The session record matters more than this turn's staged units,
        # which stay in place for a later Stop.
        logger.warning("session_lifecycle: cannot claim %s: %s", path, exc)
    ours = sorted(
        c for c in path.parent.glob(f"{path.name}.*.claim") if _claim_is_ours(c, now_ns)
    )
    return ours[:_MAX_CLAIMS_PER_STOP]


def _discard_staged_units(path: Path) -> None:
    """Remove the staging file once its units are recorded."""
    with contextlib.suppress(OSError):
        path.unlink()


def _coerce_units(raw: list[dict]) -> list[SessionUnit]:
    """Validate staged dicts into units, dropping any the schema rejects.

    This is the single ingress boundary for the type vocabulary; every
    downstream reader may assume the type is valid.
    """
    units: list[SessionUnit] = []
    for item in raw:
        try:
            units.append(SessionUnit.from_dict(item))
        except TypeError as exc:
            logger.warning("session_lifecycle: dropping invalid unit: %s", exc)
    _fingerprint_dependencies(units)
    return units


def _fingerprint_dependencies(units: list[SessionUnit]) -> None:
    """Record a content digest for each declared dependency.

    The writer names the files a claim rests on; the machine records
    what they contained. Splitting it this way keeps the model out of
    hashing and keeps the hook out of judging relevance.
    """
    try:
        from memory_palace.corpus.staleness_signals import capture_digests
    except ImportError:
        return
    root = Path.cwd()
    for unit in units:
        if unit.files and not unit.file_digests:
            unit.file_digests = capture_digests(unit.files, root=root)


def _derive_topics(units: list[SessionUnit]) -> list[str]:
    """Thread labels, deduplicated, in first-seen order."""
    return list(dict.fromkeys(u.thread for u in units))


def _derive_key_decisions(units: list[SessionUnit]) -> list[str]:
    """Return the state text of every unit typed as a decision."""
    return [u.state for u in units if u.type == "decision"]


def _build_record(payload: dict) -> SessionRecord:
    """Construct a SessionRecord from a Stop hook payload.

    The Stop event payload may contain:
    - session_id (str, optional)
    - stop_reason (str): "end_turn", "max_tokens", "stop_sequence"
    - stats (dict, optional): tool_uses, duration_ms, context_tokens_used, etc.
    - tools_used (list[str], optional)
    - files_modified (list[str], optional)
    - transcript_summary (str, optional)

    Fields absent from the payload receive sensible defaults.
    """
    stats: dict = payload.get("stats") or {}

    session_id: str = str(payload.get("session_id") or _derive_session_id(payload))
    started_at: str = str(
        payload.get("started_at") or datetime.now(timezone.utc).isoformat()
    )
    ended_at: str = datetime.now(timezone.utc).isoformat()

    duration_ms = _safe_float(stats.get("duration_ms", 0))
    duration_seconds = duration_ms / 1000.0

    # Derive outcome from stop_reason
    stop_reason: str = str(payload.get("stop_reason", "") or "")
    if stop_reason == "max_tokens":
        outcome = "interrupted"
    elif stop_reason in ("end_turn", "stop_sequence"):
        outcome = "completed"
    else:
        outcome = stop_reason or "completed"

    # Context usage as a fraction 0.0–1.0
    context_tokens = _safe_float(stats.get("context_tokens_used", 0))
    context_limit = _safe_float(stats.get("context_window_size", 0))
    context_peak = (
        min(context_tokens / context_limit, 1.0) if context_limit > 0 else 0.0
    )

    tools_used: list[str] = list(payload.get("tools_used") or [])
    files_modified: list[str] = list(payload.get("files_modified") or [])
    summary: str = str(payload.get("transcript_summary") or "")

    return SessionRecord(
        session_id=session_id,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration_seconds,
        summary=summary,
        topics=[],
        skills_used=[],
        tools_used=tools_used,
        files_modified=files_modified,
        key_decisions=[],
        outcome=outcome,
        context_usage_peak=context_peak,
        continuation_count=0,
        parent_session_id=None,
        tags=[],
        metadata={
            "stop_reason": stop_reason,
            "tool_use_count": int(_safe_float(stats.get("tool_uses", 0))),
        },
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Record session summary on Stop event."""
    if not _HAS_SESSION_HISTORY:
        sys.exit(0)

    try:
        payload: dict = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        logger.warning("session_lifecycle: Failed to parse Stop payload: %s", exc)
        sys.exit(0)

    # Only process Stop events (empty hook_event_name means Claude Code
    # invoked the hook directly for the Stop event without setting the field)
    hook_event = str(
        payload.get("hook_event_name") or payload.get("hookEventName") or ""
    )
    if hook_event and hook_event != "Stop":
        sys.exit(0)

    try:
        record = _build_record(payload)
        mgr = SessionHistoryManager(data_dir=DATA_ROOT / "data")
        # Stop fires repeatedly and record_session overwrites by session_id,
        # so units must be merged forward or the next turn erases them.
        previous = mgr.get_session(record.session_id)
        if previous is not None and not payload.get("started_at"):
            # The Stop payload has no start time, so a later turn would
            # otherwise restamp the session as starting now.
            record.started_at = previous.started_at
        claims = _claim_staged_units(_STAGING_PATH)
        readable: list[Path] = []
        raw_units: list[dict] = []
        for claim in claims:
            claim_units = _read_staged_units(claim)
            if claim_units is not None:
                readable.append(claim)
                raw_units.extend(claim_units)
        staged = _coerce_units(raw_units)
        record.handoff_units = merge_handoff_units(
            list(previous.handoff_units) if previous else [], staged
        )
        if record.handoff_units:
            record.topics = _derive_topics(record.handoff_units)
            record.key_decisions = _derive_key_decisions(record.handoff_units)
        mgr.record_session(record)
        for claim in readable:
            _discard_staged_units(claim)
    except Exception as exc:
        # Non-critical: never block the session from ending
        logger.warning("session_lifecycle: Failed to record session: %s", exc)

    # Graph wiring: record journey completion if cross-palace navigation occurred
    _try_record_journey_completion(
        palaces_dir=DATA_ROOT / "data" / "palaces",
        session_id=str(payload.get("session_id", "")),
        tools_used=list(payload.get("tools_used") or []),
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
