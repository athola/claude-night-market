#!/usr/bin/env python3
"""Guard: scope ramp (PreToolUse on Write|Edit|MultiEdit).

Holds each code increment to the current ambition rung. The rung starts
bounded and widens a notch only when a demonstration of the prior
increment has been recorded (a ramp token). This turns "the agent wrote
a 300-line change, ship it" into "the agent earns a bigger slice by
proving the last one was understood", the graduated-practice fix for
blind trust of agent output.

The decision logic is the pure ``shared.scope_ramp`` module; this
wrapper handles stdin, per-session rung state, and the ramp token.

Ramp token (mints a one-notch rung increase, consumed on use):
  - env ``IMBUE_RAMP_OK=1``, or
  - a ``.imbue/ramp-ok`` file in the working directory.
A token should only be created after the prior increment's
understanding is demonstrated and recorded (tradeoff-ledger entry; for
high-stakes paths, the human explaining the diff unaided). See
``Skill(imbue:graduated-implementation)``.

Shadow mode is ON by default (warn only). Set VOW_SHADOW_MODE=0 to
block over-rung increments. The hook never crashes the agent.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared.scope_ramp import (  # noqa: E402 - hook injects sys.path before importing sibling shared/ module
    RUNG_CAP,
    RUNG_START,
    added_lines,
    assess_ramp,
    ledger_entry,
    stakes_for,
)
from shared.vow_utils import (  # noqa: E402 - same path-injection pattern as sibling vow hooks
    OFF_VALUES,
    fd_owned_by_us,
    secure_open,
    secure_state_dir,
    shadow_mode_active,
    vow_output,
)

_CODE_TOOLS = frozenset({"Write", "Edit", "MultiEdit", "StrReplace"})
# The rung measures implementation increments. Prose and data are not
# implementation, and a long README counted as a 500-line code slice.
_UNGATED_SUFFIXES = frozenset(
    {
        ".md",
        ".rst",
        ".txt",
        ".adoc",
        ".json",
        ".jsonl",
        ".yaml",
        ".yml",
        ".toml",
        ".csv",
        ".lock",
        ".svg",
    }
)
_RAMP_OK_FILE = ".imbue/ramp-ok"
_LEDGER_FILE = ".imbue/ramp-ledger.jsonl"


def _state_dir() -> Path:
    """Return the private per-user directory for rung-state files."""
    return secure_state_dir("imbue-state")


def _state_path(session_id: str) -> Path:
    """Return the session-scoped rung-state file path."""
    safe_id = (session_id or "default").replace("/", "_").replace("\\", "_")[:200]
    return _state_dir() / f"scope_ramp_{safe_id}.json"


def _is_int(field: object) -> bool:
    return isinstance(field, int) and not isinstance(field, bool)


def _is_valid_state(state: object) -> bool:
    """Check the shape ``{rung: int, increments: int, env_notch_used?: bool}``.

    A ``null`` or string field raised later inside the hook, whose
    catch-all allowed the write and left the bad state on disk, so the
    gate stayed off for the rest of the session.
    """
    if not isinstance(state, dict):
        return False
    rung = state.get("rung")
    increments = state.get("increments")
    return (
        isinstance(rung, int)
        and _is_int(rung)
        and 1 <= rung <= RUNG_CAP
        and isinstance(increments, int)
        and _is_int(increments)
        and increments >= 0
        and isinstance(state.get("env_notch_used", False), bool)
    )


def _load_state(path: Path) -> dict:
    """Read rung state, returning the bounded default on any error.

    Opens with ``O_NOFOLLOW`` so a symlinked state path is refused rather
    than followed, and distrusts a file not owned by the current user.
    """
    default = {"rung": RUNG_START, "increments": 0}
    try:
        fd = secure_open(path, os.O_RDONLY)
    except OSError:  # missing, or ELOOP on a planted symlink
        return default
    try:
        if not fd_owned_by_us(fd):
            return default
        raw = os.read(fd, 1_000_000).decode("utf-8")
        state = json.loads(raw) if raw else default
        return state if _is_valid_state(state) else default
    except (ValueError, TypeError) as exc:  # corrupt state must not crash the hook
        print(
            f"[guard-scope-ramp] WARN: corrupt state file, using default: {exc}",
            file=sys.stderr,
        )
        return default
    finally:
        os.close(fd)


def _save_state(path: Path, state: dict) -> None:
    """Persist rung state with 0o600 perms; failures are non-fatal.

    ``O_NOFOLLOW`` makes the open fail instead of truncating a symlink's
    target, and the owner check refuses to write through a file planted
    by another user.
    """
    try:
        # No O_TRUNC: truncating at open would empty a foreign file before
        # the owner check below could refuse it.
        fd = secure_open(path, os.O_WRONLY | os.O_CREAT, 0o600)
    except OSError as exc:  # ELOOP on a planted symlink, or other open failure
        print(f"[guard-scope-ramp] WARN: state open refused: {exc}", file=sys.stderr)
        return
    try:
        if not fd_owned_by_us(fd):
            return
        os.ftruncate(fd, 0)
        os.write(fd, json.dumps(state).encode("utf-8"))
    except Exception as exc:  # noqa: S110 - state write is best-effort; hook must not crash
        print(f"[guard-scope-ramp] WARN: state write failed: {exc}", file=sys.stderr)
    finally:
        os.close(fd)


def _explicit_stakes() -> str | None:
    """Read an authoritative risk tier from the environment or a marker.

    `leyline:risk-classification` writes the tier here so the rung is
    driven by the project's risk signal, not path-regex alone. Env
    `IMBUE_STAKES` wins, then a one-line `.imbue/stakes` file.
    """
    env = os.environ.get("IMBUE_STAKES", "").strip()
    if env:
        return env
    try:
        return Path(".imbue/stakes").read_text().strip() or None
    except (FileNotFoundError, OSError):
        return None


def _env_ramp_token() -> bool:
    """Return True when ``IMBUE_RAMP_OK`` grants a notch.

    Case-insensitive, and empty or "off" is off: `IMBUE_RAMP_OK=False`
    handed out a free rung jump because only lowercase spellings matched.
    """
    value = os.environ.get("IMBUE_RAMP_OK", "0").strip().lower()
    return bool(value) and value not in (*OFF_VALUES, "off")


def _ramp_token_present(state: dict | None = None) -> bool:
    """Return True when a recorded-demonstration token is available.

    The env token sits in every call's environment and is never consumed,
    so it counts once per session; the file token is consumed on use.
    """
    if Path(_RAMP_OK_FILE).exists():
        return True
    return _env_ramp_token() and not (state or {}).get("env_notch_used")


def _record_env_notch(state: dict, new_state: dict, token: bool) -> dict:
    """Mark the session's env notch spent once the env token has granted it."""
    spent = state.get("env_notch_used") or (token and not Path(_RAMP_OK_FILE).exists())
    return {**new_state, "env_notch_used": True} if spent else new_state


def _consume_ramp_token() -> None:
    """Remove the on-disk token so a demonstration ramps the rung once."""
    try:
        Path(_RAMP_OK_FILE).unlink()
    except (FileNotFoundError, OSError):
        pass  # no file token; the env token is spent via env_notch_used


def _append_ledger(entry: dict) -> None:
    """Append a ramp-ledger record as one JSON line; failures are non-fatal."""
    try:
        path = Path(_LEDGER_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception as exc:  # noqa: S110 - ledger is best-effort; hook must not crash
        print(f"[guard-scope-ramp] WARN: ledger write failed: {exc}", file=sys.stderr)


def _is_ungated(file_path: str, stakes: str | None) -> bool:
    """Prose and data skip the rung unless the file is RED or CRITICAL.

    A deploy manifest or CI workflow is data by suffix and high stakes by
    path, and an 800-line one printed nothing while deploy.py was denied.
    """
    if Path(file_path).suffix.lower() not in _UNGATED_SUFFIXES:
        return False
    return stakes_for(file_path, stakes) not in ("RED", "CRITICAL")


def _cursor_response(data: object) -> None:
    """Emit an allow response when Cursor has no additional hook output."""
    if isinstance(data, dict) and "cursor_version" in data:
        print(json.dumps({"permission": "allow"}))


def main() -> None:
    """Entry point for the PreToolUse hook."""
    data: object = None
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    try:
        if not isinstance(data, dict):
            raise TypeError("hook payload is not a JSON object")
        tool_name = data.get("tool_name", "")
        if tool_name not in _CODE_TOOLS:
            _cursor_response(data)
            sys.exit(0)
        tool_input = data.get("tool_input", {}) or {}
        file_path = tool_input.get("file_path", tool_input.get("path", ""))

        added = added_lines(tool_name, tool_input)
        stakes = _explicit_stakes()
        if added <= 0 or _is_ungated(str(file_path), stakes):
            _cursor_response(data)
            sys.exit(0)

        state_path = _state_path(
            data.get("session_id") or data.get("conversation_id", "")
        )
        state = _load_state(state_path)

        rung_before = int(state.get("rung", RUNG_START))
        token = _ramp_token_present(state)
        finding, new_state = assess_ramp(
            added, file_path, state, ramp_token=token, stakes=stakes
        )
        new_state = _record_env_notch(state, new_state, token)
        _save_state(state_path, new_state)
        if token:
            _consume_ramp_token()
            if new_state["rung"] > rung_before:
                _append_ledger(
                    ledger_entry(
                        increment=new_state["increments"],
                        rung_before=rung_before,
                        rung_after=new_state["rung"],
                        tier=stakes_for(file_path, stakes),
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )

        if finding is None:
            _cursor_response(data)
            sys.exit(0)

        shadow = shadow_mode_active()
        decision = "warn" if shadow else "block"
        reason = finding["detail"]
        if shadow:
            reason += (
                " (shadow mode: warns now; set VOW_SHADOW_MODE=0 to block "
                "over-rung increments.)"
            )

        output = vow_output(enforce=decision == "block", reason=reason)
        if "cursor_version" in data:
            output["permission"] = "deny" if decision == "block" else "allow"
        print(json.dumps(output))
        print(
            f"[guard-scope-ramp] {decision.upper()}: {added} lines "
            f"(rung {new_state['rung']}, high_stakes={finding['high_stakes']})",
            file=sys.stderr,
        )
        sys.exit(0)

    except Exception as exc:  # hook must never crash the agent
        print(f"[guard-scope-ramp] internal error: {exc}", file=sys.stderr)
        _cursor_response(data)
        sys.exit(0)


if __name__ == "__main__":
    main()
