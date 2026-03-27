#!/usr/bin/env python3
"""PreCompact hook to preserve critical context before compression.

This hook runs before Claude Code's context compression (triggered by /compact
or automatic threshold). It saves critical information to external files so
it can be recovered after compression.

What gets preserved:
- Active file paths and recent edits
- Key decisions made in conversation
- Error patterns encountered and resolved
- Pending work items

Environment variables:
- CLAUDE_HOME: Claude configuration directory
- CLAUDE_SESSION_ID: Current session identifier
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Maximum recent turns to analyze for preservation
_MAX_TURNS_ANALYZED = 50

# Maximum file paths to preserve
_MAX_FILE_PATHS = 20

# Patterns for extracting important information
_FILE_PATH_PATTERN = re.compile(
    r"(?:^|\s|[\"'])([/~][\w/.-]+\.(?:py|md|json|yaml|yml|toml|txt|sh)"
    r"|[\w-]+\.[\w]{1,4})(?:$|\s|[\"'])"
)
_DECISION_PATTERN = re.compile(
    r"(?:decision|decided|chose|selected|will use|going with|settled on)"
    r"[:\s]+(.{10,100})",
    re.IGNORECASE,
)
_ERROR_PATTERN = re.compile(
    r"(?:error|exception|failed|failure)[:\s]+(.{10,150})",
    re.IGNORECASE,
)


def get_archive_dir() -> Path:
    """Get or create the context archive directory."""
    claude_dir = Path(os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")))
    archive_dir = claude_dir / "context-archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


def resolve_session_file() -> Path | None:
    """Find the current session's JSONL file."""
    claude_dir = Path(os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")))
    claude_projects = claude_dir / "projects"

    if not claude_projects.exists():
        return None

    # Try to find project directory from CWD
    cwd = Path.cwd()
    project_dir_name = str(cwd).replace(os.sep, "-")
    if not project_dir_name.startswith("-"):
        project_dir_name = "-" + project_dir_name

    project_dir = claude_projects / project_dir_name
    if not project_dir.exists():
        # Fallback: list all project dirs and use most recent
        project_dirs = sorted(
            claude_projects.iterdir(),
            key=lambda p: p.stat().st_mtime if p.is_dir() else 0,
            reverse=True,
        )
        if project_dirs:
            project_dir = project_dirs[0]
        else:
            return None

    # Find the current session file
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    jsonl_files = list(project_dir.glob("*.jsonl"))

    if not jsonl_files:
        return None

    if session_id:
        for f in jsonl_files:
            if f.stem == session_id:
                return f

    # Fallback to most recent
    return max(jsonl_files, key=lambda f: f.stat().st_mtime)


def extract_recent_content(
    session_file: Path, max_turns: int = _MAX_TURNS_ANALYZED
) -> list[dict]:
    """Extract recent conversation content from session file."""
    try:
        file_size = session_file.stat().st_size
        # Read last ~500KB which should cover recent turns
        read_size = min(file_size, 500_000)

        with open(session_file, encoding="utf-8", errors="replace") as f:
            if file_size > read_size:
                f.seek(file_size - read_size)
                f.readline()  # Skip partial line
            content = f.read()

        entries = []
        for raw_line in content.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
                if entry.get("role") in ("user", "assistant"):
                    entries.append(entry)
            except json.JSONDecodeError:
                continue

        return entries[-max_turns:]

    except (OSError, PermissionError) as e:
        logger.debug("Could not read session file: %s", e)
        return []


def extract_file_paths(entries: list[dict]) -> list[str]:
    """Extract file paths mentioned in conversation."""
    file_paths = set()

    for entry in entries:
        content = entry.get("content", "")
        if isinstance(content, list):
            # Handle content blocks
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "") or block.get("content", "")
                    if text:
                        matches = _FILE_PATH_PATTERN.findall(text)
                        file_paths.update(matches)
                elif isinstance(block, str):
                    matches = _FILE_PATH_PATTERN.findall(block)
                    file_paths.update(matches)
        elif isinstance(content, str):
            matches = _FILE_PATH_PATTERN.findall(content)
            file_paths.update(matches)

    # Filter to existing files and limit
    valid_paths = []
    for path in file_paths:
        try:
            expanded = Path(path).expanduser()
            if expanded.exists() and len(valid_paths) < _MAX_FILE_PATHS:
                valid_paths.append(str(expanded))
        except (OSError, ValueError):
            continue

    return valid_paths


def extract_decisions(entries: list[dict]) -> list[str]:
    """Extract key decisions from conversation."""
    decisions = []

    for entry in entries:
        content = entry.get("content", "")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "")
                    if text:
                        matches = _DECISION_PATTERN.findall(text)
                        decisions.extend(matches[:2])  # Limit per entry
        elif isinstance(content, str):
            matches = _DECISION_PATTERN.findall(content)
            decisions.extend(matches[:2])

    return decisions[:10]  # Total limit


def extract_errors(entries: list[dict]) -> list[str]:
    """Extract error patterns from conversation."""
    errors = []

    for entry in entries:
        content = entry.get("content", "")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "")
                    if text:
                        matches = _ERROR_PATTERN.findall(text)
                        errors.extend(matches[:2])
        elif isinstance(content, str):
            matches = _ERROR_PATTERN.findall(content)
            errors.extend(matches[:2])

    return errors[:10]


def save_preserved_context(
    file_paths: list[str],
    decisions: list[str],
    errors: list[str],
    trigger: str,
) -> Path:
    """Save preserved context to archive file."""
    archive_dir = get_archive_dir()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")[:8]
    archive_file = archive_dir / f"pre-compact-{timestamp}-{session_id}.md"

    content_lines = [
        "# Context Preservation Archive",
        "",
        f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}",
        f"**Trigger:** {trigger}",
        f"**Session:** {session_id}",
        "",
        "## Active Files",
        "",
    ]

    if file_paths:
        for path in file_paths:
            content_lines.append(f"- `{path}`")
    else:
        content_lines.append("_No files tracked_")

    content_lines.extend(
        [
            "",
            "## Key Decisions",
            "",
        ]
    )

    if decisions:
        for decision in decisions:
            content_lines.append(f"- {decision.strip()}")
    else:
        content_lines.append("_No decisions tracked_")

    content_lines.extend(
        [
            "",
            "## Errors Encountered",
            "",
        ]
    )

    if errors:
        for error in errors:
            content_lines.append(f"- {error.strip()}")
    else:
        content_lines.append("_No errors tracked_")

    content_lines.extend(
        [
            "",
            "---",
            "",
            "To restore context, read this file and the files listed above.",
        ]
    )

    archive_file.write_text("\n".join(content_lines), encoding="utf-8")
    return archive_file


def cleanup_old_archives(keep_count: int = 10) -> None:
    """Remove old archive files, keeping only the most recent."""
    archive_dir = get_archive_dir()
    archives = sorted(
        archive_dir.glob("pre-compact-*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for old_archive in archives[keep_count:]:
        try:
            old_archive.unlink()
            logger.debug("Removed old archive: %s", old_archive)
        except OSError as e:
            logger.warning("Could not remove old archive %s: %s", old_archive, e)


def main() -> int:
    """Execute PreCompact hook."""
    # Read hook input
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    trigger = hook_input.get("trigger", "manual")

    # Find and analyze session
    session_file = resolve_session_file()
    if not session_file:
        logger.debug("No session file found, skipping preservation")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreCompact"}}))
        return 0

    entries = extract_recent_content(session_file)
    if not entries:
        logger.debug("No content to preserve")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreCompact"}}))
        return 0

    # Extract information
    file_paths = extract_file_paths(entries)
    decisions = extract_decisions(entries)
    errors = extract_errors(entries)

    # Save archive
    archive_file = save_preserved_context(file_paths, decisions, errors, trigger)

    # Cleanup old archives
    cleanup_old_archives()

    # Output with summary
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreCompact",
            "additionalContext": (
                f"Context preserved to {archive_file}\n"
                f"- {len(file_paths)} files tracked\n"
                f"- {len(decisions)} decisions saved\n"
                f"- {len(errors)} errors logged\n"
                f"Archive location: .claude/context-archive/"
            ),
            "archivePath": str(archive_file),
        }
    }

    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
