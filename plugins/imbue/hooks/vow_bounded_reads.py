#!/usr/bin/env python3
"""Vow: Bounded discovery reads (Hard vow, shadow mode by default).

PreToolUse hook triggered on Read/Grep/Glob.  Tracks consecutive
discovery reads in a session-scoped counter file.  When the counter
exceeds the budget (default 15) a warning is emitted in shadow mode
or the tool call is blocked when VOW_SHADOW_MODE=0.

Counter resets are handled by the companion script
``vow_bounded_reads_reset.py`` which fires on Write/Edit/MultiEdit.

Session ID is taken from the stdin JSON ``session_id`` field, with
``CLAUDE_SESSION_ID`` env var as a fallback, and a fixed filename as
the last resort.

Concurrency: read-modify-write on the counter file is serialised with
``fcntl.flock(LOCK_EX)`` so parallel Read calls (Claude Code 2.1.72+
dispatches them concurrently) cannot lose increments.  On platforms
without ``fcntl`` (Windows) the hook degrades gracefully to unlocked
RMW. The resulting small race window is acceptable because the vow
remains an advisory signal there.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Callable, NamedTuple

# D-06: the shadow_mode helper is in shared/vow_utils, which is also the
# home of the symlink-safe state primitives (CWE-59 defense).
sys.path.insert(0, str(Path(__file__).parent))
from shared.vow_utils import (  # noqa: E402 - hook script must inject sys.path before importing sibling shared/ module
    fd_owned_by_us,
    lock_fd,
    read_counter_path,
    secure_open,
    session_id_from,
    shadow_mode_active,
    unlock_fd,
)

# One definition, shared with the other read-budget hook, so the reset
# truncates exactly the file the increment writes.
_counter_path = read_counter_path
_get_session_id = session_id_from


_READ_TOOLS = frozenset({"Read", "Grep", "Glob"})
_BUDGET = 15

# .claude/rules/bounded-discovery.md prices discovery by what it pulls into
# context: a Glob and a paths-only Grep return paths and are free, a Read
# of fewer than this many lines is half a read.
_SHORT_READ_LINES = 50

# Issue #580: a counter not touched within this many seconds is treated as
# stale and reset to zero on the next increment. Without this, a counter
# left at count>budget by a prior session (especially the missing-session
# fallback path, which several sessions could otherwise share) would make
# every later Read emit advisory output indefinitely. Within an active
# discovery phase reads happen far more often than the TTL, so a live
# counter is never reset by accident.
_COUNTER_TTL_SECONDS = 8 * 60 * 60

# Calls remembered per session for repeat detection. Oldest drop first, so
# the file stays a few KB however long the session runs.
_MAX_REMEMBERED_CALLS = 64


def _read_weight(tool_name: str, tool_input: object) -> float:
    """Return what one call costs against the budget, per bounded-discovery.md.

    Grep defaults to files_with_matches, so only an explicit
    ``output_mode: "content"`` costs a read. ``offset`` without ``limit``
    reads to the end of the file and costs a full read.
    """
    params = tool_input if isinstance(tool_input, dict) else {}
    if tool_name == "Glob":
        return 0.0
    if tool_name == "Grep":
        return 1.0 if params.get("output_mode") == "content" else 0.0
    limit = params.get("limit")
    if isinstance(limit, int) and limit < _SHORT_READ_LINES:
        return 0.5
    return 1.0


def _read_state(fd: int) -> tuple[float, bool, list[str]]:
    """Parse the count, the spent escape and the remembered calls from *fd*.

    One read serves all three. An empty, unparseable, or stale file (mtime
    older than _COUNTER_TTL_SECONDS) reads as a fresh phase.
    """
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        raw = os.read(fd, 65536)
    except OSError:
        raw = b""
    try:
        state = json.loads(raw or b"{}")
        count = float(state.get("count", 0))
        escape_used = state.get("escape_used") is True
        seen = [key for key in state.get("seen", []) if isinstance(key, str)]
    except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
        return 0.0, False, []
    try:
        if (time.time() - os.fstat(fd).st_mtime) > _COUNTER_TTL_SECONDS:
            return 0.0, False, []
    except OSError:
        pass
    return count, escape_used, seen


def _write_with_fd(
    fd: int, count: float, escape_used: bool = False, seen: list[str] | None = None
) -> None:
    """Write the state as JSON to an open file descriptor, replacing prior content."""
    state: dict[str, object] = {"count": count}
    if escape_used:
        state["escape_used"] = True
    if seen:
        state["seen"] = seen
    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)
    os.write(fd, json.dumps(state).encode("utf-8"))


# Given the new count, whether the phase's escape is spent, and the calls
# remembered, return the count, escape flag and calls to store.
_Settle = Callable[[float, bool, "list[str]"], "tuple[float, bool, list[str]]"]


def _atomic_increment(
    path: Path, weight: float = 1.0, settle: _Settle | None = None
) -> float:  # noqa: PLR0912 - POSIX flock requires explicit branch per errno value; cannot reduce without losing error granularity
    """Atomically read-modify-write the counter at *path*.

    Returns the new count, *weight* higher than before. *settle*, when
    given, runs between the one read and the one write and decides what is
    stored, so a call is counted, judged and remembered under one lock.
    Uses an exclusive POSIX
    file lock around the RMW so concurrent hook invocations cannot
    lose increments.  On systems without ``fcntl`` (Windows) the lock
    is skipped and the hook degrades to unlocked RMW.

    Returns 0 on any failure: the hook must never crash the agent.
    """
    fd = -1
    try:
        # O_RDWR|O_CREAT (no O_TRUNC) so we can read the current value
        # before overwriting it.  O_NOFOLLOW (via secure_open) refuses a
        # symlinked counter path.  Mode 0o600 keeps the counter
        # private on shared systems.
        fd = secure_open(path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        if not fd_owned_by_us(fd):
            return 0
        lock_fd(fd)
        # Issue #580: discard a counter left over from a prior session. A
        # file untouched past the TTL cannot belong to the current
        # discovery phase, so its count must not bleed forward.
        current, escape_used, seen = _read_state(fd)
        new_count = current + weight
        # A stale counter reads as 0, and its spent escape goes with it.
        stored = (new_count, current > 0 and escape_used, seen)
        if settle is not None:
            stored = settle(*stored)
        try:
            _write_with_fd(fd, *stored)
        except OSError as exc:
            print(
                f"[vow-bounded-reads] WARN: counter write failed: {exc}",
                file=sys.stderr,
            )
            return 0
        return new_count
    except Exception as exc:  # noqa: BLE001 - hook must not crash agent
        print(
            f"[vow-bounded-reads] WARN: counter increment failed: {exc}",
            file=sys.stderr,
        )
        return 0
    finally:
        if fd >= 0:
            unlock_fd(fd)
            try:
                os.close(fd)
            except OSError:
                pass


def _call_key(tool_name: str, tool_input: object) -> str:
    """Return a short digest of the call, stable across dict key order."""
    canonical = json.dumps([tool_name, tool_input], sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class _Verdict(NamedTuple):
    """How one call is judged, and the state it leaves behind."""

    reads: float
    escape_left: bool
    escape_granted: bool
    denied: bool
    repeated: bool
    stored: tuple[float, bool, list[str]] = (0.0, False, [])


def _judge(
    state: tuple[float, bool, list[str]],
    *,
    weight: float,
    key: str,
    shadow: bool,
) -> _Verdict:
    """Decide one call from the (count, escape spent, seen calls) state.

    A targeted read (under _SHORT_READ_LINES) is allowed up to twice the
    budget: an Edit needs the file read first. It still counts, and past
    twice the budget only one more is allowed per phase, so chunked reads
    cannot walk a tree the budget was meant to bound. A successful Write
    or Edit resets the counter without the spent flag, which returns it.
    """
    count, escape_used, seen = state
    # A free call is judged on 0 and leaves the count where it is.
    judged = count if weight else 0.0
    targeted_spent = judged > 2 * _BUDGET
    escape_left = targeted_spent and not shadow and not escape_used
    escape_granted = escape_left and weight < 1
    denied = (
        judged > _BUDGET
        and not shadow
        and (weight >= 1 or (targeted_spent and not escape_granted))
    )
    repeated = key in seen
    # A denied read read nothing. It is not counted, so a retry does not
    # push the count further from the limit, and not remembered, so its
    # retry is not told to reuse a result that never arrived.
    if not denied and not repeated:
        seen = (seen + [key])[-_MAX_REMEMBERED_CALLS:]
    stored = (count - weight if denied else count, escape_used or escape_granted, seen)
    return _Verdict(judged, escape_left, escape_granted, denied, repeated, stored)


def _is_read_tool(tool_name: str) -> bool:
    """Return True if *tool_name* is a discovery read tool."""
    return tool_name in _READ_TOOLS


def _shadow_mode() -> bool:
    """Return True when shadow (warn-only) mode is active."""
    return shadow_mode_active()


def main() -> None:
    """Entry point for the PreToolUse hook."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    try:
        tool_name = data.get("tool_name", "")
        session_id = _get_session_id(data)
        counter_file = _counter_path(session_id)

        if not _is_read_tool(tool_name):
            sys.exit(0)

        tool_input = data.get("tool_input")
        weight = _read_weight(tool_name, tool_input)
        shadow = _shadow_mode()
        key = _call_key(tool_name, tool_input)
        verdicts: list[_Verdict] = []

        def settle(
            count: float, escape_used: bool, seen: list[str]
        ) -> tuple[float, bool, list[str]]:
            verdicts.append(
                _judge(
                    (count, escape_used, seen), weight=weight, key=key, shadow=shadow
                )
            )
            return verdicts[0].stored

        _atomic_increment(counter_file, weight, settle)
        # A failed read-modify-write never ran settle: allow, say nothing.
        verdict = verdicts[0] if verdicts else _Verdict(0.0, False, False, False, False)
        new_count = verdict.reads
        targeted_spent = new_count > 2 * _BUDGET

        repeat_note = ""
        if verdict.repeated:
            repeat_note = (
                f"This {tool_name} call repeats an earlier identical call in this "
                "discovery phase. Reuse the earlier result. Re-run only if it is "
                "no longer in context or the target changed outside Edit/Write."
            )

        # The budget warning carries the repeat note. With no warning to
        # carry it, the note stands alone, past the budget included.
        reported = verdict.denied or (shadow and new_count > _BUDGET)
        if verdict.escape_granted:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "additionalContext": (
                                "Bounded discovery vow: this short read is the one "
                                "allowed past twice the budget. Edit next. A "
                                "successful Write or Edit resets the count, and "
                                "reads are verdict.denied until then."
                            ),
                        }
                    }
                )
            )
            print("[vow-bounded-reads] WARN: escape read granted", file=sys.stderr)
        elif repeat_note and not reported:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "additionalContext": repeat_note,
                        }
                    }
                )
            )
            print("[vow-bounded-reads] WARN: repeated call", file=sys.stderr)
        elif reported:
            decision = "warn" if shadow else "block"
            short_read = (
                "To read the file you are about to edit, pass offset "
                f"and a limit under {_SHORT_READ_LINES}."
            )
            escape = (
                "Targeted reads are spent too. A successful Write or Edit "
                "resets the count. Until then, work from what is in context. "
                "The user can also set VOW_SHADOW_MODE=1."
                if targeted_spent and not verdict.escape_left
                else (
                    f"One short read is left in this phase. {short_read}"
                    if targeted_spent
                    else short_read
                )
            )
            reason = (
                f"Bounded discovery vow: {new_count:g} reads in this discovery phase. "
                f"Budget is {_BUDGET} for open exploration. "
                f"Consider starting implementation. {escape}"
                + (f" {repeat_note}" if repeat_note else "")
                + (
                    " Shadow mode active — will block once VOW_SHADOW_MODE=0."
                    if shadow
                    else ""
                )
            )
            # Issue #580: Claude Code 2.1.178 rejects top-level
            # additionalContext / decision keys with "(root): Invalid
            # input". The valid PreToolUse output nests under
            # hookSpecificOutput with hookEventName, matching the sibling
            # tdd_bdd_gate and vow_no_emoji_commits hooks. Shadow mode
            # injects advisory text via additionalContext (no permission
            # change). Block mode denies the tool call.
            if shadow:
                output: dict[str, dict[str, str]] = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "additionalContext": reason,
                    }
                }
            else:
                output = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                }
            print(json.dumps(output))
            print(
                f"[vow-bounded-reads] {decision.upper()}: "
                f"{new_count:g} reads (budget {_BUDGET})",
                file=sys.stderr,
            )

        sys.exit(0)

    except Exception as exc:  # hook must not crash the agent under any circumstance
        print(f"[vow-bounded-reads] internal error: {exc}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
