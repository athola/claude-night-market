"""Phase 4: Knowledge Queue Promotion Check module.

Scans memory-palace queue for pending research items that need promotion.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


class KnowledgeQueueChecker:
    """Check memory-palace queue for pending research items."""

    def __init__(self, queue_dir: Path | None = None):
        """Initialize checker with optional custom queue directory."""
        self.queue_dir = (
            queue_dir or Path.home() / ".claude" / "memory-palace" / "queue"
        )

    def check_queue(self) -> list[dict[str, Any]]:
        """Scan queue for pending research items.

        Returns:
            List of pending items sorted by priority and age
        """
        queue_items: list[dict[str, Any]] = []

        if not self.queue_dir.exists():
            return queue_items

        for item_file in self.queue_dir.glob("*.md"):
            try:
                content = item_file.read_text(encoding="utf-8")
                stat = item_file.stat()

                # Extract metadata from frontmatter
                priority_match = re.search(r"priority:\s*(\w+)", content, re.IGNORECASE)
                status_match = re.search(r"status:\s*(\w+)", content, re.IGNORECASE)

                priority = priority_match.group(1) if priority_match else "medium"
                status = status_match.group(1) if status_match else "pending"

                # Skip non-pending items
                if status.lower() != "pending":
                    continue

                # Calculate age
                mtime = datetime.fromtimestamp(stat.st_mtime)
                age_days = (datetime.now() - mtime).days

                queue_items.append(
                    {
                        "file": item_file.name,
                        "priority": priority,
                        "age_days": age_days,
                    }
                )

            except (OSError, json.JSONDecodeError):
                continue

        # Sort by priority and age
        priority_order = {"high": 0, "medium": 1, "low": 2}
        queue_items.sort(
            key=lambda x: (priority_order.get(x["priority"], 1), -x["age_days"])
        )

        return queue_items
