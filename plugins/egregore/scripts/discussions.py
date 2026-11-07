"""Settings for publishing egregore output to GitHub Discussions.

Only the configuration lives here; config.py loads it as the
``discussions`` section of the egregore config.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, fields
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
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiscussionsConfig:
        """Deserialize from a plain dictionary, ignoring unknown keys."""
        known = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)
