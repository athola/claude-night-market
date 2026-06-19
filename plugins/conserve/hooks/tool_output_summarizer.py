#!/usr/bin/env python3
"""PostToolUse hook to monitor and warn about tool output bloat.

This hook tracks cumulative tool output size and warns when approaching
context pressure thresholds. It helps users proactively manage context
before hitting Anthropic's limits.

Environment variables:
- CLAUDE_HOME: Claude configuration directory
- CLAUDE_SESSION_ID: Current session identifier
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# D-05: shared resolver lives at hooks/shared/session_file.py.
sys.path.insert(0, str(Path(__file__).parent))
from shared.session_file import (
    resolve_session_file,  # noqa: E402 - hook script must inject sys.path before importing sibling shared/ module
)

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

# Threshold for warning about accumulated output (bytes)
# ~100KB of text is roughly 25K tokens, which is 2.5% of 1M context
BLOAT_WARNING_THRESHOLD = 100_000

# CCR (reversible compression): a single tool output at or above this many
# characters is archived to an external cache so the original can be fetched
# on demand via context_retrieve.py. ~25K chars is roughly 6K tokens.
# Override with CONSERVE_CCR_THRESHOLD.
CCR_THRESHOLD_DEFAULT = 25_000
CCR_HANDLE_HEX_LEN = 12
DIGEST_HEAD_LINES = 20
DIGEST_TAIL_LINES = 20
ARCHIVE_SUBDIR = Path(".claude") / "context-archive"

# Archives accumulate across sessions and /clears with nothing to prune them.
# A retention sweep deletes handles older than this many days. Override with
# CONSERVE_CCR_RETENTION_DAYS. The sweep runs opportunistically (see below).
CCR_RETENTION_DAYS_DEFAULT = 7
SECONDS_PER_DAY = 86_400
# Probability that an archive write also triggers a retention sweep. Keeps the
# directory scan off the hot path of most hook invocations while still pruning
# regularly over a session's many large outputs.
CCR_CLEANUP_PROBABILITY = 0.1


__all__ = ["resolve_session_file"]


def get_ccr_threshold() -> int:
    """Return the single-output archive threshold in characters.

    Reads ``CONSERVE_CCR_THRESHOLD`` from the environment, falling back to
    ``CCR_THRESHOLD_DEFAULT`` when unset or not a valid integer.
    """
    raw = os.environ.get("CONSERVE_CCR_THRESHOLD")
    if raw is None:
        return CCR_THRESHOLD_DEFAULT
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid CONSERVE_CCR_THRESHOLD=%r; using default", raw)
        return CCR_THRESHOLD_DEFAULT


def get_ccr_retention_days() -> int:
    """Return the archive retention window in days.

    Reads ``CONSERVE_CCR_RETENTION_DAYS`` from the environment, falling back to
    ``CCR_RETENTION_DAYS_DEFAULT`` when unset or not a valid integer.
    """
    raw = os.environ.get("CONSERVE_CCR_RETENTION_DAYS")
    if raw is None:
        return CCR_RETENTION_DAYS_DEFAULT
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid CONSERVE_CCR_RETENTION_DAYS=%r; using default", raw)
        return CCR_RETENTION_DAYS_DEFAULT


def context_archive_cleanup(
    archive_dir: Path | str, max_age_days: int | None = None
) -> int:
    """Delete CCR archives older than *max_age_days* and return the count removed.

    Only files matching the ``ccr-*.txt`` handle pattern are considered, so a
    user's own notes dropped in the archive dir are never touched. A missing
    directory is a no-op (returns 0). Per-file errors are logged and skipped so
    one unreadable archive cannot abort the sweep.
    """
    if max_age_days is None:
        max_age_days = get_ccr_retention_days()
    archive_dir = Path(archive_dir)
    if not archive_dir.is_dir():
        return 0

    cutoff = time.time() - max_age_days * SECONDS_PER_DAY
    removed = 0
    for path in archive_dir.glob("ccr-*.txt"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        except OSError as exc:
            logger.warning("CCR cleanup could not remove %s: %s", path, exc)
    return removed


def should_archive(text: str, threshold: int | None = None) -> bool:
    """Return True when *text* is large enough to archive for retrieval."""
    if threshold is None:
        threshold = get_ccr_threshold()
    return len(text) >= threshold


def extract_tool_response_text(hook_input: dict[str, Any]) -> str:
    """Extract the textual tool output from a PostToolUse payload.

    Handles the shapes Claude Code emits for ``tool_response``: a bare
    string, or a dict (Bash -> stdout/stderr, Read/Grep -> content). Unknown
    dict shapes fall back to a JSON dump so nothing is silently dropped.
    """
    resp = hook_input.get("tool_response")
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        parts = [
            str(resp[key])
            for key in ("stdout", "stderr", "content", "output", "text")
            if resp.get(key)
        ]
        if parts:
            return "\n".join(parts)
        return json.dumps(resp, ensure_ascii=False)
    return str(resp)


def archive_large_output(text: str, archive_dir: Path | str | None = None) -> str:
    """Write *text* to a content-addressed archive file and return its handle.

    The handle is ``ccr-<sha256(text)[:12]>`` so identical content always maps
    to the same file (idempotent, dedupes naturally). This is the cache half
    of reversible compression; ``context_retrieve.py`` reads it back.
    """
    if archive_dir is None:
        archive_dir = Path.cwd() / ARCHIVE_SUBDIR
    archive_dir = Path(archive_dir)
    digest = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()
    handle = f"ccr-{digest[:CCR_HANDLE_HEX_LEN]}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    target = archive_dir / f"{handle}.txt"
    # Atomic write: stage to a temp file in the same directory, then os.replace
    # onto the target. Two concurrent writers of identical content each rename
    # their own complete temp file, so a reader (or the loser of the race) only
    # ever sees a whole file, never a half-written one. errors="replace" mirrors
    # the hash above: a lone surrogate (e.g. from os.fsdecode of a non-UTF-8
    # filename) must not raise UnicodeEncodeError, which is a ValueError and
    # would escape the OSError fail-open guard. It also keeps the file content
    # consistent with its content-addressed handle.
    fd, tmp_name = tempfile.mkstemp(dir=archive_dir, prefix=f"{handle}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", errors="replace") as tmp:
            tmp.write(text)
        os.replace(tmp_name, target)
    except BaseException:
        # Never leave a stray temp file behind on any failure (write or rename).
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return handle


def build_digest(
    text: str,
    handle: str,
    head: int = DIGEST_HEAD_LINES,
    tail: int = DIGEST_TAIL_LINES,
) -> str:
    """Build a compact digest of an archived output plus its retrieval command.

    Shows the first *head* and last *tail* lines, the elided middle count, and
    the exact ``context_retrieve.py`` invocation to fetch the original.
    """
    lines = text.split("\n")
    total_lines = len(lines)
    total_chars = len(text)
    retrieve_cmd = (
        f"python3 ${{CLAUDE_PLUGIN_ROOT}}/scripts/context_retrieve.py {handle}"
    )

    if total_lines <= head + tail:
        body = text
    else:
        elided = total_lines - head - tail
        body = "\n".join(
            [
                *lines[:head],
                f"... [{elided} lines elided] ...",
                *lines[-tail:],
            ]
        )

    # Report characters, not bytes: total_chars is len(text) (a character
    # count), so a "KB" label would overstate precision for multibyte UTF-8.
    return (
        f"Large tool output archived (CCR): {total_lines} lines, "
        f"{total_chars:,} chars, handle {handle}\n"
        f"{body}\n"
        f"Retrieve the full original on demand with:\n  {retrieve_cmd}\n"
        f"  (add --grep PATTERN, --head N, --tail N, or --lines A:B to slice)"
    )


def _count_tool_result_bytes(content: Any) -> int:
    """Count bytes of tool_result content blocks in an entry's content field.

    Handles the three shapes Claude Code emits:
    - list of blocks where a block has type=tool_result with str content,
    - list of blocks where tool_result content is itself a list of items
      (each item a dict with .text or a bare str).
    """
    if not isinstance(content, list):
        return 0

    total = 0
    for block in content:
        if not (isinstance(block, dict) and block.get("type") == "tool_result"):
            continue
        result_content = block.get("content", "")
        if isinstance(result_content, str):
            total += len(result_content)
        elif isinstance(result_content, list):
            for item in result_content:
                if isinstance(item, dict):
                    total += len(item.get("text", ""))
                elif isinstance(item, str):
                    total += len(item)
    return total


def get_session_output_size(session_file: Path, max_bytes: int = 512_000) -> int:
    """Calculate total size of tool outputs in session.

    Reads at most *max_bytes* of the file to stay within the hook
    timeout budget. The result is an approximation for large sessions.
    """
    total_size = 0
    bytes_read = 0

    try:
        with open(session_file, encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                bytes_read += len(raw_line)
                if bytes_read > max_bytes:
                    break
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                total_size += _count_tool_result_bytes(entry.get("content", ""))
    except (OSError, PermissionError) as e:
        logger.warning("Could not read session file: %s", e)

    return total_size


def assess_output_bloat(
    session_file: Path, threshold: int = BLOAT_WARNING_THRESHOLD
) -> dict[str, Any]:
    """Assess tool output bloat and return severity level.

    Args:
        session_file: Path to the session file.
        threshold: Critical threshold in bytes (warning at 80%).

    Returns:
        Dictionary with severity, bytes_accumulated, and recommendations.

    """
    output_size = get_session_output_size(session_file)
    warning_threshold = int(threshold * 0.8)

    if output_size >= threshold:
        return {
            "severity": "critical",
            "bytes_accumulated": output_size,
            "threshold": threshold,
            "recommendations": [
                "Run /clear to reset context immediately",
                "Consider spawning a subagent for remaining work",
                "Archive recent outputs to external files",
            ],
        }
    elif output_size >= warning_threshold:
        return {
            "severity": "warning",
            "bytes_accumulated": output_size,
            "threshold": threshold,
            "recommendations": [
                "Monitor context growth",
                "Consider summarizing recent tool outputs",
                "Use /clear before starting new major task phase",
            ],
        }

    return {
        "severity": "ok",
        "bytes_accumulated": output_size,
        "threshold": threshold,
        "recommendations": [],
    }


def format_hook_output(assessment: dict[str, Any]) -> dict[str, Any]:
    """Format assessment as hook-compatible output.

    Args:
        assessment: The bloat assessment result.

    Returns:
        Dictionary suitable for hook JSON output.

    """
    kb_accumulated = assessment["bytes_accumulated"] / 1024
    kb_threshold = assessment["threshold"] / 1024
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"Tool output bloat: {kb_accumulated:.1f}KB accumulated "
                f"(threshold: {kb_threshold:.1f}KB)\n"
                f"Severity: {assessment['severity'].upper()}\n"
                + "\n".join(f"- {rec}" for rec in assessment["recommendations"])
            ),
        }
    }


def main() -> int:
    """Execute PostToolUse hook entry point."""
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid hook input JSON; treating as empty: %s", exc)
        hook_input = {}

    # Only process Bash, Read, Grep tools (verbose output tools)
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Bash", "Read", "Grep"):
        return 0

    context_blocks: list[str] = []

    # CCR: archive this single oversized output so the original is retrievable
    # on demand (survives /clear and continuation-agent handoffs). The hook
    # cannot redact the result already in context; its value is the durable
    # external cache + retrieval handle.
    output_text = extract_tool_response_text(hook_input)
    if should_archive(output_text):
        try:
            handle = archive_large_output(output_text)
            context_blocks.append(build_digest(output_text, handle))
            # Opportunistic retention sweep so archives do not grow unbounded
            # across sessions and /clears. Probabilistic to keep the directory
            # scan off the hot path; over a session's many large outputs it
            # runs often enough to bound disk use.
            if random.random() < CCR_CLEANUP_PROBABILITY:  # noqa: S311 - sampling gate, not crypto
                context_archive_cleanup(Path.cwd() / ARCHIVE_SUBDIR)
        except (OSError, UnicodeError) as exc:
            # fail-open: never break the host turn on an archive error. The
            # write uses errors="replace" so UnicodeError should not fire, but
            # it is caught here too as a belt-and-suspenders net (it is a
            # ValueError, not an OSError, so the narrow catch missed it).
            logger.warning("CCR archive failed: %s", exc)

    # Cumulative bloat warning across the whole session (unchanged behavior).
    session_file = resolve_session_file()
    if session_file:
        assessment = assess_output_bloat(session_file)
        if assessment["severity"] != "ok":
            context_blocks.append(
                format_hook_output(assessment)["hookSpecificOutput"][
                    "additionalContext"
                ]
            )
    else:
        logger.debug("No session file found")

    if context_blocks:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": "\n\n".join(context_blocks),
                    }
                }
            )
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
