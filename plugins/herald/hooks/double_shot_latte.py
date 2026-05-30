#!/usr/bin/env python3
"""Double Shot Latte: a correct, cross-platform Stop-hook continuation judge.

A reimplementation of the ``double-shot-latte`` auto-continue hook that fixes
three defects in the original bash version:

1. **Input keyhole.** The original fed ``tail -n 4`` of the raw transcript
   JSONL to the judge. When a turn ends with several tool-result lines (or one
   large persisted output), the assistant's actual closing message falls
   outside that 4-line window, so a finished turn looks unfinished. This
   version walks the transcript backward and extracts the *last assistant
   text message*, regardless of how many tool lines precede it.

2. **Heavy, non-portable dependencies.** The original required ``jq``, the
   ``claude`` CLI on PATH inside the hook environment, ``/tmp`` (invalid on
   native Windows), and ``date``/``tail``/``tr``. This version is pure Python
   standard library: ``tempfile.gettempdir()`` for state, ``shutil.which`` for
   binary discovery, ``pathlib`` throughout. No external binaries are needed
   for the default path.

3. **Aggressive bias.** The original defaulted to CONTINUE, producing false
   "you're not done" nags on completed work. This version defaults to STOP and
   only continues on an explicit, unambiguous statement of intent to keep
   working.

The judge runs deterministically by default. Set ``DOUBLE_SHOT_LATTE_LLM=1`` to
enable an optional LLM "second shot" via the ``claude`` CLI for ambiguous
cases; it degrades gracefully to the deterministic verdict when ``claude`` or
the network is unavailable, so behavior stays identical across platforms.

Hook contract (Claude Code ``Stop`` event):
  - Reads the event JSON from stdin.
  - Prints ``{"decision": "block", "reason": ...}`` to keep working, or
    ``{"decision": "approve", "reason": ...}`` to allow the stop.
  - Always exits 0; any internal error degrades to "approve" (let it stop).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# --- Tunables (named to satisfy PLR2004 and document intent) ---------------

#: Maximum CONTINUE decisions allowed inside the throttle window before the
#: judge pauses and hands control back to the user. High enough to let a
#: genuine long autonomous run proceed, low enough that a runaway loop is
#: caught and surfaced for a human check-in rather than spinning unbounded.
MAX_CONTINUATIONS = 10

#: Sliding window, in seconds, over which MAX_CONTINUATIONS is counted.
THROTTLE_WINDOW_SECONDS = 300

#: Filename prefix for per-session throttle state in the temp dir. Shared by
#: the path builder and the orphan sweep so they stay in lock-step.
_THROTTLE_PREFIX = "double-shot-latte-"

#: Age, in seconds, after which an orphaned throttle file is reclaimed. Far
#: larger than the throttle window so a live session's file is never swept;
#: only files left by abandoned sessions age out.
THROTTLE_TTL_SECONDS = 3600

#: Only the trailing slice of the assistant message is inspected for await /
#: completion signals, so an early "next" in a long summary cannot flip a
#: finished turn back to CONTINUE.
TAIL_CHARS = 800

#: Cap on transcript bytes read from the end of the file, so a multi-megabyte
#: transcript never blows up memory. 256 KiB comfortably holds the final turn.
TRANSCRIPT_READ_BYTES = 262_144

#: Timeout for the optional LLM second shot. Must stay strictly below the hook
#: timeout registered in ``hooks.json`` (10s): the harness kills the whole hook
#: at that budget, so a larger value here means the hook is killed mid-call and
#: emits no decision at all. 8s leaves margin for interpreter startup, transcript
#: read, and printing the verdict; a guard test keeps it below the hook budget.
LLM_TIMEOUT_SECONDS = 8

#: Recursion guard: when the optional LLM judge spawns ``claude``, this env var
#: is set so the nested instance's own Stop hook short-circuits to "approve".
JUDGE_MODE_ENV = "CLAUDE_HOOK_JUDGE_MODE"

#: Phrases that signal the assistant intends to keep working autonomously.
_CONTINUE_PATTERNS = (
    r"\bnext,? i(?:'ll| will| need to| am going to)\b",
    r"\bnow i(?:'ll| will)\b",
    r"\bnow let me\b",
    r"\blet me now\b",
    r"\bi'?ll now\b",
    r"\bmoving on to\b",
    r"\bproceeding (?:to|with)\b",
    r"\bcontinuing (?:to|with)\b",
    r"\bnext step:",
    r"\bnext up:",
)

#: Phrases that mean the assistant is waiting on the user (handoff/question).
_AWAIT_PATTERNS = (
    r"\blet me know\b",
    r"\bwant me to\b",
    r"\bwould you like\b",
    r"\bshould i\b",
    r"\bdo you want\b",
    r"\byour call\b",
    r"\bwhich (?:option|approach|one)\b",
    r"\bplease confirm\b",
    r"\bwaiting (?:for|on) (?:you|your)\b",
)

#: Phrases that mean the assistant considers the work finished.
_COMPLETE_PATTERNS = (
    r"\b(?:task|work|everything|it)(?:'s| is) (?:done|complete|finished)\b",
    r"\ball (?:set|done)\b",
    r"\bnothing (?:to commit|left to do|further)\b",
    r"\bworking tree is clean\b",
    r"\bcomplete and (?:verified|pushed|committed)\b",
    r"\bverified\b.*\b(?:clean|passing|green)\b",
    r"\bno (?:remaining|outstanding|further) (?:work|steps|items)\b",
)

_CONTINUE_RE = re.compile("|".join(_CONTINUE_PATTERNS), re.IGNORECASE)
_AWAIT_RE = re.compile("|".join(_AWAIT_PATTERNS), re.IGNORECASE)
_COMPLETE_RE = re.compile("|".join(_COMPLETE_PATTERNS), re.IGNORECASE)

#: Verdict reason emitted when no positive signal (question, await, completion,
#: or continuation) matched. This is the only *ambiguous* outcome: every other
#: classify branch is a confident read, so the optional LLM second shot is
#: consulted only when ``classify`` returns this exact reason.
REASON_DEFAULT_STOP = "No explicit continuation intent; defaulting to stop."

#: Verdict reason emitted when the continuation cap is hit. Unlike a hard stop,
#: this hands control back to the user with an explicit invitation to resume:
#: long autonomous runs are legitimate, so the judge pauses for a check-in
#: instead of refusing outright. The throttle is cleared alongside this verdict
#: so a user who continues starts a fresh window rather than re-tripping the cap.
REASON_CONTINUATION_LIMIT = (
    f"Paused after {MAX_CONTINUATIONS} auto-continuation cycles for a check-in. "
    "Reply to continue if there is more work to do."
)


# --- Pure helpers (unit-tested directly) -----------------------------------


def _blocks_to_text(content: object) -> str:
    """Flatten a message ``content`` field to its plain text.

    ``content`` may be a plain string or a list of typed blocks (the Anthropic
    message format), e.g. ``[{"type": "text", "text": "..."},
    {"type": "tool_use", ...}]``. Only text blocks contribute.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


def _entry_is_assistant(entry: dict[str, object]) -> bool:
    """Return True if a transcript entry represents an assistant message."""
    if entry.get("type") == "assistant":
        return True
    message = entry.get("message")
    if isinstance(message, dict) and message.get("role") == "assistant":
        return True
    return entry.get("role") == "assistant"


def _entry_text(entry: dict[str, object]) -> str:
    """Extract assistant text from a transcript entry (either schema shape)."""
    message = entry.get("message")
    if isinstance(message, dict) and "content" in message:
        return _blocks_to_text(message["content"])
    if "content" in entry:
        return _blocks_to_text(entry["content"])
    return ""


def extract_last_assistant_text(transcript: str) -> str:
    """Return the text of the most recent assistant message in a JSONL transcript.

    Walks lines from the end so the result is the assistant's closing message,
    not whatever tool-result or user line happened to be in the last few rows.
    Malformed lines are skipped. Returns ``""`` when no assistant text exists.
    """
    for raw_line in reversed(transcript.splitlines()):
        line = raw_line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(entry, dict):
            continue
        if _entry_is_assistant(entry):
            text = _entry_text(entry).strip()
            if text:
                return text
    return ""


def classify(text: str) -> tuple[bool, str]:
    """Decide whether the assistant has more autonomous work to do.

    Returns ``(should_continue, reason)``. The bias is to STOP: continue only
    on an explicit statement of intent to keep working that is not overridden
    by a trailing question, handoff, or completion signal.
    """
    stripped = text.strip()
    if not stripped:
        return False, "No assistant text found; defaulting to stop."

    tail = stripped[-TAIL_CHARS:]

    if tail.rstrip().endswith("?"):
        return False, "Assistant ended with a question; waiting on the user."
    if _AWAIT_RE.search(tail):
        return False, "Assistant is offering options / awaiting user input."
    if _COMPLETE_RE.search(tail):
        return False, "Assistant signaled the work is complete."
    if _CONTINUE_RE.search(tail):
        return True, "Assistant stated explicit intent to keep working."
    return False, REASON_DEFAULT_STOP


# --- Throttle state (cross-platform temp dir) ------------------------------


def _throttle_path(session_id: str) -> Path:
    """Return the throttle state file path for a session, OS-portable."""
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
    return Path(tempfile.gettempdir()) / f"{_THROTTLE_PREFIX}{safe}.json"


def _sweep_stale_throttles(now: float) -> None:
    """Best-effort removal of throttle files left by abandoned sessions.

    A session that keeps continuing and is then closed without a final stop
    leaves its throttle file behind. Files whose mtime predates the TTL (far
    longer than the throttle window) are unlinked so the temp dir does not
    accumulate orphans. Every error is swallowed: this is housekeeping and must
    never affect the stop decision.
    """
    try:
        tmp = Path(tempfile.gettempdir())
        for path in tmp.glob(f"{_THROTTLE_PREFIX}*.json"):
            try:
                if now - path.stat().st_mtime > THROTTLE_TTL_SECONDS:
                    path.unlink()
            except OSError:
                continue
    except OSError:
        pass


def _read_throttle(path: Path) -> tuple[int, float]:
    """Read ``(count, last_time)`` from the throttle file, tolerating absence."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data.get("count", 0)), float(data.get("last", 0.0))
    except (OSError, ValueError, json.JSONDecodeError):
        return 0, 0.0


def _write_throttle(path: Path, count: int, when: float) -> None:
    """Persist throttle state, ignoring write failures (best-effort)."""
    try:
        path.write_text(json.dumps({"count": count, "last": when}), encoding="utf-8")
    except OSError:
        pass


def _clear_throttle(path: Path) -> None:
    """Remove the throttle file, ignoring absence."""
    try:
        path.unlink()
    except OSError:
        pass


# --- Optional LLM second shot ----------------------------------------------


def _llm_second_shot(text: str) -> tuple[bool, str] | None:
    """Consult the ``claude`` CLI as a second opinion, or None if unavailable.

    Returns ``(should_continue, reason)`` on success. Returns ``None`` when the
    feature is disabled, ``claude`` is not installed, or the call fails -- the
    caller then keeps the deterministic verdict. This keeps every platform's
    default behavior identical and side-effect free.
    """
    if os.environ.get("DOUBLE_SHOT_LATTE_LLM") != "1":
        return None
    if os.environ.get(JUDGE_MODE_ENV) == "true":
        return None
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return None

    model = os.environ.get("DOUBLE_SHOT_LATTE_MODEL", "haiku")
    schema = (
        '{"type":"object","properties":'
        '{"should_continue":{"type":"boolean"},'
        '"reasoning":{"type":"string"}},'
        '"required":["should_continue","reasoning"]}'
    )
    prompt = (
        "You are a conversation-state classifier. Given the assistant's final "
        "message, does it have more autonomous work to do RIGHT NOW? Continue "
        "only if it explicitly states a next action it will take itself. If it "
        "is waiting on the user, asking a question, or reporting completion, "
        "the answer is no. Default to no when uncertain.\n\n"
        f"Final assistant message:\n{text[-TAIL_CHARS:]}"
    )
    env = dict(os.environ)
    env[JUDGE_MODE_ENV] = "true"
    try:
        result = subprocess.run(
            [
                claude_bin,
                "--print",
                "--model",
                model,
                "--output-format",
                "json",
                "--json-schema",
                schema,
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=LLM_TIMEOUT_SECONDS,
            env=env,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout)
        if isinstance(payload.get("result"), str):
            payload = json.loads(payload["result"])
        should = bool(payload["should_continue"])
        reason = str(payload.get("reasoning", "LLM second shot"))
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None
    return should, f"LLM second shot: {reason}"


# --- Decision orchestration ------------------------------------------------


def decide(event: dict[str, object], now: float) -> dict[str, str]:
    """Produce the hook decision dict for a Stop event.

    Encapsulates recursion guard, throttling, transcript extraction,
    deterministic classification, and the optional LLM second shot.
    """
    if os.environ.get(JUDGE_MODE_ENV) == "true":
        return _approve("Running in judge mode; allowing stop.")

    _sweep_stale_throttles(now)

    session_id = str(event.get("session_id", "unknown"))
    throttle = _throttle_path(session_id)
    stop_active = bool(event.get("stop_hook_active", False))

    if stop_active:
        count, last = _read_throttle(throttle)
        within_window = (now - last) <= THROTTLE_WINDOW_SECONDS
        if within_window and count >= MAX_CONTINUATIONS:
            _clear_throttle(throttle)
            return _approve(REASON_CONTINUATION_LIMIT)

    transcript_path = str(event.get("transcript_path", ""))
    if not transcript_path or not Path(transcript_path).is_file():
        return _approve("No transcript available; allowing stop.")

    text = extract_last_assistant_text(_read_tail(Path(transcript_path)))
    should_continue, reason = classify(text)

    # The LLM "second shot" is a tiebreaker for ambiguous turns only. A confident
    # deterministic verdict (question, await, completion, or explicit intent) is
    # trusted as-is, so the LLM cannot undo the STOP-by-default guarantee.
    if reason == REASON_DEFAULT_STOP:
        second = _llm_second_shot(text)
        if second is not None:
            should_continue, reason = second

    if should_continue:
        count, last = _read_throttle(throttle)
        if (now - last) > THROTTLE_WINDOW_SECONDS:
            count = 0
        _write_throttle(throttle, count + 1, now)
        return _block(reason)

    _clear_throttle(throttle)
    return _approve(reason)


def _read_tail(path: Path) -> str:
    """Read up to the final TRANSCRIPT_READ_BYTES of a file as UTF-8 text."""
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size > TRANSCRIPT_READ_BYTES:
                handle.seek(size - TRANSCRIPT_READ_BYTES)
            raw = handle.read()
        return raw.decode("utf-8", errors="replace")
    except OSError:
        return ""


def _approve(reason: str) -> dict[str, str]:
    """Build an 'allow the stop' decision."""
    return {"decision": "approve", "reason": f"Double Shot Latte: {reason}"}


def _block(reason: str) -> dict[str, str]:
    """Build a 'keep working' decision."""
    return {"decision": "block", "reason": f"Double Shot Latte: {reason}"}


def main() -> None:
    """Entry point: read the Stop event from stdin and emit a decision."""
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            event = {}
    except (json.JSONDecodeError, ValueError):
        event = {}

    try:
        decision = decide(event, time.time())
    except Exception as exc:  # noqa: BLE001 - never let the hook crash a stop
        decision = _approve(f"Internal error, allowing stop: {exc}")

    print(json.dumps(decision))
    sys.exit(0)


if __name__ == "__main__":
    main()
