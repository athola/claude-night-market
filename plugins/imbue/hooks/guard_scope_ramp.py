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
    RUNG_START,
    added_lines,
    assess_ramp,
    ledger_entry,
    stakes_for,
)
from shared.vow_utils import (  # noqa: E402 - same path-injection pattern as sibling vow hooks
    _OFF_VALUES,
    fd_owned_by_us,
    secure_open,
    secure_state_dir,
    shadow_mode_active,
)

_CODE_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})
_RAMP_OK_FILE = ".imbue/ramp-ok"
_LEDGER_FILE = ".imbue/ramp-ledger.jsonl"


def _state_dir() -> Path:
    """Return the private per-user directory for rung-state files."""
    return secure_state_dir("imbue-state")


def _state_path(session_id: str) -> Path:
    """Return the session-scoped rung-state file path."""
    safe_id = (session_id or "default").replace("/", "_").replace("\\", "_")[:200]
    return _state_dir() / f"scope_ramp_{safe_id}.json"


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
        return json.loads(raw) if raw else default
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
        fd = secure_open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    except OSError as exc:  # ELOOP on a planted symlink, or other open failure
        print(f"[guard-scope-ramp] WARN: state open refused: {exc}", file=sys.stderr)
        return
    try:
        if not fd_owned_by_us(fd):
            return
        os.write(fd, json.dumps(state).encode("utf-8"))
    except Exception as exc:  # noqa: S110 - state write is best-effort; hook must not crash
        print(f"[guard-scope-ramp] WARN: state write failed: {exc}", file=sys.stderr)
    finally:
        os.close(fd)


def _explicit_stakes() -> str | None:
    """Read an authoritative risk tier from the environment or a marker.

    `leyline:risk-classification` writes the tier here so the rung is
    driven by the project's risk signal, not path-regex alone. Env
    `IMBUE_STAKES` wins; otherwise a one-line `.imbue/stakes` file.
    """
    env = os.environ.get("IMBUE_STAKES", "").strip()
    if env:
        return env
    try:
        return Path(".imbue/stakes").read_text().strip() or None
    except (FileNotFoundError, OSError):
        return None


def _ramp_token_present() -> bool:
    """Return True when a recorded-demonstration token is available."""
    if os.environ.get("IMBUE_RAMP_OK", "0").strip() not in _OFF_VALUES:
        return True
    return Path(_RAMP_OK_FILE).exists()


def _consume_ramp_token() -> None:
    """Remove the on-disk token so a demonstration ramps the rung once."""
    try:
        Path(_RAMP_OK_FILE).unlink()
    except (FileNotFoundError, OSError):
        pass  # env-based token is single-turn; nothing to remove


def _append_ledger(entry: dict) -> None:
    """Append a ramp-ledger record as one JSON line; failures are non-fatal."""
    try:
        path = Path(_LEDGER_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception as exc:  # noqa: S110 - ledger is best-effort; hook must not crash
        print(f"[guard-scope-ramp] WARN: ledger write failed: {exc}", file=sys.stderr)


def main() -> None:
    """Entry point for the PreToolUse hook."""
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    try:
        tool_name = data.get("tool_name", "")
        if tool_name not in _CODE_TOOLS:
            sys.exit(0)
        tool_input = data.get("tool_input", {}) or {}
        file_path = tool_input.get("file_path", "")

        added = added_lines(tool_name, tool_input)
        if added <= 0:
            sys.exit(0)

        state_path = _state_path(data.get("session_id", ""))
        state = _load_state(state_path)

        rung_before = int(state.get("rung", RUNG_START))
        token = _ramp_token_present()
        stakes = _explicit_stakes()
        finding, new_state = assess_ramp(
            added, file_path, state, ramp_token=token, stakes=stakes
        )
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
            sys.exit(0)

        shadow = shadow_mode_active()
        decision = "warn" if shadow else "block"
        reason = finding["detail"]
        if shadow:
            reason += (
                " (shadow mode: warns now; set VOW_SHADOW_MODE=0 to block "
                "over-rung increments.)"
            )

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        }
        print(json.dumps(output))
        print(
            f"[guard-scope-ramp] {decision.upper()}: {added} lines "
            f"(rung {new_state['rung']}, high_stakes={finding['high_stakes']})",
            file=sys.stderr,
        )
        sys.exit(0)

    except Exception as exc:  # hook must never crash the agent
        print(f"[guard-scope-ramp] internal error: {exc}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
