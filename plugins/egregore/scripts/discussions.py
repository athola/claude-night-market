"""Publish egregore discoveries and insights to GitHub Discussions.

Provides a discussion entry model, content type categorization,
rate limiting per work item, and publish tracking for the egregore
autonomous agent orchestrator.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DiscussionsConfig:
    """Configuration for Discussions publishing."""

    enabled: bool = True
    publish_discoveries: bool = True
    publish_insights: bool = True
    publish_contention: bool = True
    publish_retrospectives: bool = True
    max_per_work_item: int = 10

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "enabled": self.enabled,
            "publish_discoveries": self.publish_discoveries,
            "publish_insights": self.publish_insights,
            "publish_contention": self.publish_contention,
            "publish_retrospectives": self.publish_retrospectives,
            "max_per_work_item": self.max_per_work_item,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiscussionsConfig:
        """Deserialize from a plain dictionary, ignoring unknown keys."""
        known = {
            "enabled",
            "publish_discoveries",
            "publish_insights",
            "publish_contention",
            "publish_retrospectives",
            "max_per_work_item",
        }
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


class DiscussionCategory:
    """Maps egregore content types to GitHub Discussion categories."""

    RESEARCH = "Research"
    WAR_ROOM = "War Room"

    @classmethod
    def for_content_type(cls, content_type: str) -> str:
        """Return the Discussion category for a given content type."""
        mapping = {
            "discovery": cls.RESEARCH,
            "insight": cls.WAR_ROOM,
            "contention": cls.WAR_ROOM,
            "improvement": cls.RESEARCH,
            "tangential_idea": cls.RESEARCH,
            "retrospective": cls.WAR_ROOM,
        }
        return mapping.get(content_type, cls.RESEARCH)


@dataclass
class DiscussionEntry:
    """A discussion entry to be published."""

    title: str
    body: str
    content_type: str  # discovery, insight, contention, etc.
    work_item_id: str = ""
    pipeline_step: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def category(self) -> str:
        """Return the GitHub Discussion category for this entry."""
        return DiscussionCategory.for_content_type(self.content_type)


@dataclass
class PublishTracker:
    """Tracks discussions published per work item for rate limiting."""

    counts: dict[str, int] = field(default_factory=dict)

    def can_publish(self, item_id: str, max_per_item: int) -> bool:
        """Return True if the work item has not hit its publish limit."""
        return self.counts.get(item_id, 0) < max_per_item

    def record_publish(self, item_id: str) -> None:
        """Increment the publish count for a work item."""
        self.counts[item_id] = self.counts.get(item_id, 0) + 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {"counts": dict(self.counts)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PublishTracker:
        """Deserialize from a plain dictionary."""
        return cls(counts=data.get("counts", {}))


def build_discussion_body(entry: DiscussionEntry) -> str:
    """Build markdown body for a GitHub Discussion.

    Args:
        entry: The discussion entry to format.

    Returns:
        Markdown-formatted discussion body string.

    """
    heading = entry.content_type.replace("_", " ").title()
    lines = [
        f"## {heading}",
        "",
    ]

    if entry.work_item_id:
        lines.append(f"**Work Item:** {entry.work_item_id}")
    if entry.pipeline_step:
        lines.append(f"**Pipeline Step:** {entry.pipeline_step}")
    lines.append(f"**Timestamp:** {entry.created_at}")
    lines.append("")
    lines.append(entry.body)

    if entry.tags:
        lines.extend(["", "---", f"Tags: {', '.join(entry.tags)}"])

    return "\n".join(lines)


def publish_discussion(
    entry: DiscussionEntry,
    config: DiscussionsConfig,
    tracker: PublishTracker,
) -> bool:
    """Publish a discussion entry to GitHub Discussions.

    Checks whether the content type is enabled and whether the work
    item has hit its rate limit before publishing. The actual GraphQL
    mutation requires runtime repo/category IDs, so for now this
    logs the intent and tracks the publish count.

    Args:
        entry: The discussion entry to publish.
        config: Discussions configuration.
        tracker: Publish tracker for rate limiting.

    Returns:
        True if published (or recorded) successfully,
        False if skipped or disabled.

    """
    if not config.enabled:
        logger.info("Discussions publishing disabled")
        return False

    # Check whether the content type is enabled
    type_enabled: dict[str, bool] = {
        "discovery": config.publish_discoveries,
        "insight": config.publish_insights,
        "contention": config.publish_contention,
        "retrospective": config.publish_retrospectives,
        "improvement": config.publish_discoveries,
        "tangential_idea": config.publish_discoveries,
    }
    if not type_enabled.get(entry.content_type, False):
        logger.info("Content type %s disabled", entry.content_type)
        return False

    # Rate limit check
    if entry.work_item_id and not tracker.can_publish(
        entry.work_item_id, config.max_per_work_item
    ):
        logger.warning(
            "Rate limit reached for work item %s (max %d)",
            entry.work_item_id,
            config.max_per_work_item,
        )
        return False

    category = entry.category
    logger.info(
        "Would publish discussion: [%s] %s (category: %s)",
        entry.content_type,
        entry.title,
        category,
    )

    if entry.work_item_id:
        tracker.record_publish(entry.work_item_id)

    return True


def save_tracker(tracker: PublishTracker, path: Path) -> None:
    """Save publish tracker to JSON.

    Args:
        tracker: The tracker to persist.
        path: File path to write JSON to.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tracker.to_dict(), indent=2) + "\n")


def load_tracker(path: Path) -> PublishTracker:
    """Load publish tracker from JSON.

    If the file does not exist or is corrupt, returns an empty tracker.

    Args:
        path: File path to read JSON from.

    Returns:
        A PublishTracker instance.

    """
    if not path.exists():
        return PublishTracker()
    try:
        data = json.loads(path.read_text())
        return PublishTracker.from_dict(data)
    except (json.JSONDecodeError, OSError):
        return PublishTracker()
