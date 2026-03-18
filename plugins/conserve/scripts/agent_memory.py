#!/usr/bin/env python3
"""Three-tier agent memory and session routing.

Manages hot/warm/cold memory hierarchy for long-running
agents, and routes work to subagents or dedicated sessions
based on complexity.
"""

from __future__ import annotations

import enum
from pathlib import Path

HOT_TIER_LINE_LIMIT = 200
DEDICATED_SESSION_AREA_THRESHOLD = 4


class RoutingDecision(enum.Enum):
    """Where to route multi-area work."""

    SUBAGENT = "subagent"
    DEDICATED_SESSION = "dedicated_session"
    SEQUENTIAL = "sequential"


class MemoryManager:
    """Manages three-tier memory for an agent.

    - Hot: memory.md (200-line limit, always loaded)
    - Warm: topics/*.md (loaded on demand)
    - Cold: archive/*.md (historical, searchable)
    """

    def __init__(self, agent_dir: Path) -> None:
        """Initialize with the agent's directory path."""
        self.agent_dir = agent_dir
        self.hot_path = agent_dir / "memory.md"
        self.warm_dir = agent_dir / "topics"
        self.cold_dir = agent_dir / "archive"

    def init(self) -> None:
        """Create the memory directory structure.

        Idempotent: safe to call multiple times.
        """
        self.agent_dir.mkdir(parents=True, exist_ok=True)
        self.warm_dir.mkdir(exist_ok=True)
        self.cold_dir.mkdir(exist_ok=True)
        if not self.hot_path.exists():
            self.hot_path.write_text("# Agent Memory (Hot Tier)\n")

    def hot_tier_line_count(self) -> int:
        """Return the number of lines in the hot-tier file."""
        if not self.hot_path.exists():
            return 0
        return len(self.hot_path.read_text().splitlines())

    def is_hot_tier_over_limit(self) -> bool:
        """Check if hot tier exceeds the 200-line limit."""
        return self.hot_tier_line_count() > HOT_TIER_LINE_LIMIT

    def write_warm_topic(self, topic_name: str, content: str) -> None:
        """Write or overwrite a warm-tier topic file.

        Args:
            topic_name: Name for the topic (becomes filename).
            content: Markdown content for the topic.

        """
        topic_path = self.warm_dir / f"{topic_name}.md"
        topic_path.write_text(content)

    def archive_to_cold(self, period: str, content: str) -> None:
        """Archive content to the cold tier.

        Args:
            period: Time period label (e.g., '2026-03').
            content: Markdown content to archive.

        """
        archive_path = self.cold_dir / f"{period}.md"
        archive_path.write_text(content)

    def list_warm_topics(self) -> list[str]:
        """List all warm-tier topic names (without .md extension)."""
        if not self.warm_dir.exists():
            return []
        return sorted(p.stem for p in self.warm_dir.glob("*.md"))


def decide_session_routing(
    files: list[str],
    areas: list[str],
    *,
    codebase_wide: bool = False,
) -> RoutingDecision:
    """Decide whether to use subagents or dedicated sessions.

    Args:
        files: List of file paths involved in the task.
        areas: List of codebase areas involved.
        codebase_wide: Whether this is a codebase-wide operation.

    Returns:
        RoutingDecision indicating the recommended approach.

    """
    if codebase_wide:
        return RoutingDecision.SEQUENTIAL

    if len(areas) >= DEDICATED_SESSION_AREA_THRESHOLD:
        return RoutingDecision.DEDICATED_SESSION

    return RoutingDecision.SUBAGENT
