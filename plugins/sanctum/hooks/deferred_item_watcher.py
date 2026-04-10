#!/usr/bin/env python3
"""PostToolUse safety-net hook for deferred-item capture.

PURE LEDGER WRITER -- no gh calls, no network I/O.
Detects deferral signals in watched skill outputs and writes
entries to the session ledger. The Stop hook does the filing.
"""

from __future__ import annotations

import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from _ledger_utils import get_ledger_path as _get_ledger_path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WATCH_LIST = {
    "war-room",
    "brainstorm",
    "scope-guard",
    "feature-review",
    "unified-review",
    "rollback-reviewer",
}

DEFERRAL_PATTERNS = re.compile(
    r"\[Deferred\]"
    r"|out of scope"
    r"|not yet applicable"
    r"|future cycle"
    r"|(?<!\w)rejected(?!\w)"
    r"|(?<!\w)deferred(?!\w)",
    re.IGNORECASE,
)

_DEFERRED_MARKER_RE = re.compile(r"\[Deferred\]\s*(.*)", re.IGNORECASE)
_PREFIX_RE = re.compile(r"^\[Deferred\]\s*", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_title(title: str) -> str:
    """Strip any leading '[Deferred] ' prefix and surrounding whitespace."""
    return _PREFIX_RE.sub("", title).strip()


def get_ledger_path() -> Path:
    """Return the session ledger path, respecting CLAUDE_HOME."""
    return _get_ledger_path()


def read_ledger(path: Path) -> list[dict]:
    """Read existing ledger entries from *path*.

    Returns an empty list if the file does not exist or is corrupt.
    """
    try:
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError) as exc:
        sys.stderr.write(f"deferred_item_watcher: ledger corrupt at {path}: {exc}\n")
        return []


def write_ledger_entry(path: Path, entry: dict) -> None:
    """Append *entry* to the ledger at *path*.

    The entry's title is normalised (any '[Deferred] ' prefix stripped)
    before storage so that dedup logic works consistently.
    """
    # Normalise the title before persisting
    if "title" in entry:
        entry = dict(entry)
        entry["title"] = _normalize_title(entry["title"])

    entries = read_ledger(path)
    entries.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def update_ledger_entry(
    path: Path,
    title: str,
    filed: bool,
    issue_number: int | None = None,
) -> None:
    """Update an existing ledger entry by normalised *title*.

    Sets ``filed`` and optionally ``issue_number``.  If no matching entry
    is found the ledger is left unchanged.
    """
    normalised = _normalize_title(title)
    entries = read_ledger(path)
    changed = False
    for entry in entries:
        if _normalize_title(entry.get("title", "")) == normalised:
            entry["filed"] = filed
            if issue_number is not None:
                entry["issue_number"] = issue_number
            changed = True
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Signal detection
# ---------------------------------------------------------------------------


def scan_for_deferrals(text: str) -> bool:
    """Return True if *text* contains any deferral signal."""
    return bool(DEFERRAL_PATTERNS.search(text))


def extract_deferred_titles(text: str) -> list[str]:
    """Extract titles from ``[Deferred] <title>`` markers in *text*.

    Falls back to ``["Untitled deferred item"]`` when a deferral signal
    is present but no explicit markers exist (including when all markers
    have empty titles after stripping).
    """
    titles: list[str] = []
    for match in _DEFERRED_MARKER_RE.finditer(text):
        raw = match.group(1).strip()
        if raw:
            titles.append(raw)
        else:
            titles.append("Untitled deferred item")
    if not titles and scan_for_deferrals(text):
        return ["Untitled deferred item"]
    return titles


# ---------------------------------------------------------------------------
# Entry-point logic
# ---------------------------------------------------------------------------


_SAFE_SKILL_COMPONENT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")


def _parse_skill_name(tool_input: dict) -> str:
    """Extract the bare skill name from tool input.

    Handles both ``"skill": "name"`` and ``"skill": "plugin:name"`` forms.
    Sanitizes non-empty output to prevent path-traversal (consistent with
    abstract/hooks/shared/skill_utils.py).
    """
    skill_ref = tool_input.get("skill", "")
    # Strip optional plugin prefix (e.g. "sanctum:war-room" -> "war-room")
    if ":" in skill_ref:
        skill_ref = skill_ref.split(":", 1)[1].strip()
    else:
        skill_ref = skill_ref.strip()
    # Empty values are harmless (won't match WATCH_LIST); sanitize non-empty
    if skill_ref and not _SAFE_SKILL_COMPONENT.match(skill_ref):
        return "unknown"
    return skill_ref


def should_process() -> bool:
    """Return True only when the current tool invocation should be examined.

    Checks:
    1. CLAUDE_TOOL_NAME == "Skill"
    2. The skill name (bare, without plugin prefix) is in WATCH_LIST
    """
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    if tool_name != "Skill":
        return False

    tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    try:
        tool_input = json.loads(tool_input_str)
    except json.JSONDecodeError:
        return False

    skill_name = _parse_skill_name(tool_input)
    return skill_name in WATCH_LIST


def main() -> None:
    """PostToolUse hook entry point.

    Orchestration:
    1. Check should_process() -- skip if not a watched skill.
    2. scan_for_deferrals() on CLAUDE_TOOL_OUTPUT.
    3. If signals found, extract titles and write ledger entries.
    """
    if not should_process():
        sys.exit(0)

    tool_output = os.environ.get("CLAUDE_TOOL_OUTPUT", "")
    tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")

    if not scan_for_deferrals(tool_output):
        sys.exit(0)

    try:
        tool_input = json.loads(tool_input_str)
    except json.JSONDecodeError:
        tool_input = {}

    source = _parse_skill_name(tool_input)
    titles = extract_deferred_titles(tool_output)
    ledger_path = get_ledger_path()
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    for title in titles:
        entry = {
            "title": title,
            "source": source,
            "filed": False,
            "timestamp": timestamp,
        }
        write_ledger_entry(ledger_path, entry)


if __name__ == "__main__":
    try:
        main()
    except (
        json.JSONDecodeError,
        OSError,
        KeyError,
        TypeError,
        AttributeError,
        ValueError,
        RuntimeError,
    ):
        sys.stderr.write(f"deferred_item_watcher: {traceback.format_exc()}")
