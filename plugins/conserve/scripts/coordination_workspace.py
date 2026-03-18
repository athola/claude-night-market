#!/usr/bin/env python3
"""Coordination workspace manager for multi-agent workflows.

Manages the .coordination/ directory lifecycle: creation,
task tracking, findings file parsing, archive, and cleanup.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Pattern to extract YAML frontmatter
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Pattern to extract a specific ## section
SECTION_RE = re.compile(
    r"^##\s+(.+?)\s*\n(.*?)(?=\n##\s|\Z)",
    re.MULTILINE | re.DOTALL,
)


@dataclass
class FindingsFile:
    """Parsed agent findings file."""

    agent: str = "unknown"
    area: str = ""
    tier: int = 0
    evidence_count: int = 0
    validation_status: str = ""
    summary: str = ""
    raw_text: str = ""


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML-like key: value pairs from frontmatter."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def _extract_section(text: str, section_name: str) -> str:
    """Extract the body text of a named ## section."""
    for match in SECTION_RE.finditer(text):
        if match.group(1).strip().lower() == section_name.lower():
            return match.group(2).strip()
    return ""


def parse_findings_file(text: str) -> FindingsFile:
    """Parse a structured findings file into a FindingsFile.

    Extracts YAML frontmatter metadata and the Summary section.

    Args:
        text: Raw Markdown text of the findings file.

    Returns:
        FindingsFile with parsed metadata and summary.

    """
    meta = _parse_frontmatter(text)
    summary = _extract_section(text, "summary")

    tier_str = meta.get("tier", "0")
    evidence_str = meta.get("evidence_count", "0")

    return FindingsFile(
        agent=meta.get("agent", "unknown"),
        area=meta.get("area", ""),
        tier=int(tier_str) if tier_str.isdigit() else 0,
        evidence_count=int(evidence_str) if evidence_str.isdigit() else 0,
        validation_status=meta.get("validation_status", ""),
        summary=summary,
        raw_text=text,
    )


class WorkspaceManager:
    """Manages a .coordination/ workspace directory.

    Handles creation, task tracking, archive, and cleanup.
    """

    def __init__(self, workspace_path: Path) -> None:
        """Initialize with the workspace directory path."""
        self.path = workspace_path
        self.agents_dir = workspace_path / "agents"
        self.handoffs_dir = workspace_path / "handoffs"
        self.tasks_file = workspace_path / "tasks.json"

    def init(self) -> None:
        """Create the workspace directory structure.

        Idempotent: safe to call multiple times. Does not
        overwrite existing tasks.json.
        """
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.handoffs_dir.mkdir(parents=True, exist_ok=True)
        if not self.tasks_file.exists():
            self.tasks_file.write_text("[]")

    def load_tasks(self) -> list[dict[str, str]]:
        """Load the task manifest from tasks.json."""
        if not self.tasks_file.exists():
            return []
        return json.loads(self.tasks_file.read_text())  # type: ignore[no-any-return]

    def _save_tasks(self, tasks: list[dict[str, str]]) -> None:
        """Save the task manifest to tasks.json."""
        self.tasks_file.write_text(json.dumps(tasks, indent=2))

    def add_task(
        self,
        task_id: str,
        agent: str,
        contract_ref: str = "",
    ) -> None:
        """Add a task to the manifest.

        Args:
            task_id: Unique task identifier.
            agent: Agent name assigned to this task.
            contract_ref: Reference to the output contract template.

        """
        tasks = self.load_tasks()
        now = datetime.now(tz=timezone.utc).isoformat()  # noqa: UP017
        tasks.append(
            {
                "id": task_id,
                "agent": agent,
                "status": "pending",
                "contract": contract_ref,
                "findings_path": f"agents/{agent}.findings.md",
                "created_at": now,
                "completed_at": "",
            }
        )
        self._save_tasks(tasks)

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update a task's status.

        Args:
            task_id: The task to update.
            status: New status (pending, active, done, failed).

        """
        tasks = self.load_tasks()
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = status
                if status == "done":
                    task["completed_at"] = datetime.now(
                        tz=timezone.utc  # noqa: UP017
                    ).isoformat()
                break
        self._save_tasks(tasks)

    def pending_tasks(self) -> list[dict[str, str]]:
        """Return tasks with status 'pending'."""
        return [t for t in self.load_tasks() if t["status"] == "pending"]

    def archive(self) -> Path:
        """Archive the workspace to a timestamped directory.

        Moves .coordination/ to .coordination-archive/{timestamp}/.

        Returns:
            Path to the archive directory.

        """
        timestamp = datetime.now(tz=timezone.utc).strftime(  # noqa: UP017
            "%Y%m%d-%H%M%S"
        )
        archive_dir = self.path.parent / ".coordination-archive" / timestamp
        archive_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(self.path), str(archive_dir))
        return archive_dir

    def preserve_on_failure(self, reason: str) -> None:
        """Preserve workspace on failure with a reason file.

        Args:
            reason: Description of why the workflow failed.

        """
        reason_file = self.path / "_failure_reason.md"
        now = datetime.now(tz=timezone.utc).isoformat()  # noqa: UP017
        reason_file.write_text(
            f"# Workflow Failure\n\n**Date**: {now}\n\n**Reason**: {reason}\n"
        )
