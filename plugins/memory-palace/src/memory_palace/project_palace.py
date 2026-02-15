#!/usr/bin/env python3
# mypy: disable-error-code="index,operator,var-annotated,no-any-return"
"""Project Palace Manager for repository-scoped knowledge with PR Review Room support.

Extends the memory palace concept to treat entire projects as palaces with
dedicated rooms for different knowledge types, including a review-chamber
for PR review knowledge capture.

Project Palace Structure:
    project-palace/
    ├── entrance/           # README, getting started
    ├── library/            # Documentation, ADRs
    ├── workshop/           # Development patterns, tooling
    ├── review-chamber/     # PR Reviews (decisions, patterns, standards, lessons)
    │   ├── decisions/      # Architectural choices from PRs
    │   ├── patterns/       # Recurring issues/solutions
    │   ├── standards/      # Quality bar examples
    │   └── lessons/        # Post-mortems, learnings
    └── garden/             # Evolving knowledge, experiments
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .palace_manager import MemoryPalaceManager

# Review chamber room types
REVIEW_CHAMBER_ROOMS = {
    "decisions": {
        "description": "Architectural choices documented in PR discussions",
        "icon": "⚖️",
        "retention": "permanent",
    },
    "patterns": {
        "description": "Recurring issues and their solutions",
        "icon": "🔄",
        "retention": "evergreen",
    },
    "standards": {
        "description": "Quality bar examples and coding standards",
        "icon": "📏",
        "retention": "evergreen",
    },
    "lessons": {
        "description": "Post-mortems and learnings from reviews",
        "icon": "💡",
        "retention": "growing",
    },
}

# Project palace room structure
PROJECT_PALACE_ROOMS = {
    "entrance": {
        "description": "README, getting started, onboarding",
        "icon": "🚪",
    },
    "library": {
        "description": "Documentation, ADRs, specifications",
        "icon": "📚",
    },
    "workshop": {
        "description": "Development patterns, tooling, workflows",
        "icon": "🔧",
    },
    "review-chamber": {
        "description": "PR review knowledge",
        "icon": "🏛️",
        "subrooms": REVIEW_CHAMBER_ROOMS,
    },
    "garden": {
        "description": "Evolving knowledge, experiments",
        "icon": "🌱",
    },
}


class ReviewEntry:
    """Represents a single PR review knowledge entry."""

    def __init__(  # noqa: PLR0913
        self,
        source_pr: str,
        title: str,
        room_type: str,
        content: dict[str, Any],
        participants: list[str] | None = None,
        related_rooms: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Initialize a review entry.

        Args:
            source_pr: Reference to source PR (e.g., "#42 - Add authentication")
            title: Short title for the entry
            room_type: One of decisions, patterns, standards, lessons
            content: Structured content of the entry
            participants: List of PR participants
            related_rooms: Links to related palace rooms
            tags: Searchable tags

        """
        self.id = hashlib.sha256(
            f"{source_pr}{title}{datetime.now()}".encode()
        ).hexdigest()[:12]
        self.source_pr = source_pr
        self.title = title
        self.room_type = room_type
        self.content = content
        self.participants = participants or []
        self.related_rooms = related_rooms or []
        self.tags = tags or []
        self.created = datetime.now().isoformat()
        self.last_accessed = datetime.now().isoformat()
        self.access_count = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "source_pr": self.source_pr,
            "title": self.title,
            "room_type": self.room_type,
            "content": self.content,
            "participants": self.participants,
            "related_rooms": self.related_rooms,
            "tags": self.tags,
            "created": self.created,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewEntry:
        """Deserialize from dictionary."""
        entry = cls(
            source_pr=data["source_pr"],
            title=data["title"],
            room_type=data["room_type"],
            content=data["content"],
            participants=data.get("participants", []),
            related_rooms=data.get("related_rooms", []),
            tags=data.get("tags", []),
        )
        entry.id = data["id"]
        entry.created = data["created"]
        entry.last_accessed = data.get("last_accessed", entry.created)
        entry.access_count = data.get("access_count", 0)
        return entry

    def to_markdown(self) -> str:
        """Generate markdown representation for human readability."""
        lines = [
            "---",
            f'source_pr: "{self.source_pr}"',
            f"date: {self.created[:10]}",
            f"participants: {self.participants}",
            f"palace_location: review-chamber/{self.room_type}",
            f"related_rooms: {self.related_rooms}",
            f"tags: {self.tags}",
            "---",
            "",
            f"## {self.title}",
            "",
        ]

        # Add content sections
        if "decision" in self.content:
            lines.extend(["### Decision", self.content["decision"], ""])

        if "context" in self.content:
            lines.extend(["### Context (from PR discussion)"])
            for ctx in self.content["context"]:
                lines.append(f"- {ctx}")
            lines.append("")

        if "captured_knowledge" in self.content:
            lines.extend(["### Captured Knowledge"])
            for key, value in self.content["captured_knowledge"].items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        if "connected_concepts" in self.content:
            lines.extend(["### Connected Concepts"])
            for concept in self.content["connected_concepts"]:
                lines.append(f"- [[{concept}]]")
            lines.append("")

        return "\n".join(lines)


class ProjectPalaceManager(MemoryPalaceManager):
    """Manages project-scoped palaces with PR review room support.

    Extends MemoryPalaceManager to support project-as-palace metaphor
    where each repository becomes a palace with dedicated rooms for
    different knowledge types.
    """

    def __init__(
        self,
        config_path: str | None = None,
        palaces_dir_override: str | None = None,
    ) -> None:
        """Initialize ProjectPalaceManager.

        Args:
            config_path: Path to configuration file
            palaces_dir_override: Override directory for palace storage

        """
        super().__init__(config_path, palaces_dir_override)
        self.project_palaces_dir = os.path.join(self.palaces_dir, "projects")
        os.makedirs(self.project_palaces_dir, exist_ok=True)

    def create_project_palace(
        self,
        repo_name: str,
        repo_url: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new project palace for a repository.

        Args:
            repo_name: Repository name (e.g., "owner/repo")
            repo_url: Optional GitHub URL
            description: Optional project description

        Returns:
            Dictionary representing the new project palace

        """
        palace_id = hashlib.sha256(f"{repo_name}{datetime.now()}".encode()).hexdigest()[
            :8
        ]

        # Create room structure
        rooms = {}
        for room_name, room_config in PROJECT_PALACE_ROOMS.items():
            room_data: dict[str, Any] = {
                "description": room_config["description"],
                "icon": room_config["icon"],
                "entries": [],
                "created": datetime.now().isoformat(),
            }

            # Add subrooms for review-chamber
            if "subrooms" in room_config:
                room_data["subrooms"] = {}
                for subroom_name, subroom_config in room_config["subrooms"].items():
                    room_data["subrooms"][subroom_name] = {
                        "description": subroom_config["description"],
                        "icon": subroom_config["icon"],
                        "retention": subroom_config["retention"],
                        "entries": [],
                    }

            rooms[room_name] = room_data

        project_palace = {
            "id": palace_id,
            "type": "project",
            "name": repo_name,
            "repo_url": repo_url,
            "description": description,
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "rooms": rooms,
            "metadata": {
                "total_entries": 0,
                "review_entries": 0,
                "pr_count": 0,
                "contributors": [],
            },
            "connections": [],  # Links to other project palaces
        }

        # Save to project palaces directory
        palace_file = os.path.join(self.project_palaces_dir, f"{palace_id}.json")
        with open(palace_file, "w") as f:
            json.dump(project_palace, f, indent=2)

        self._update_project_index()
        return project_palace

    def load_project_palace(self, palace_id: str) -> dict[str, Any] | None:
        """Load a project palace by ID.

        Args:
            palace_id: The palace ID to load

        Returns:
            Project palace dictionary or None if not found

        """
        palace_file = os.path.join(self.project_palaces_dir, f"{palace_id}.json")
        if os.path.exists(palace_file):
            with open(palace_file) as f:
                return json.load(f)
        return None

    def find_project_palace(self, repo_name: str) -> dict[str, Any] | None:
        """Find a project palace by repository name.

        Args:
            repo_name: Repository name to search for

        Returns:
            Project palace dictionary or None if not found

        """
        for file_path in Path(self.project_palaces_dir).glob("*.json"):
            if file_path.name == "project_index.json":
                continue
            with open(file_path) as f:
                palace = json.load(f)
                if palace.get("name") == repo_name:
                    return palace
        return None

    def get_or_create_project_palace(
        self,
        repo_name: str,
        repo_url: str | None = None,
    ) -> dict[str, Any]:
        """Get existing project palace or create new one.

        Args:
            repo_name: Repository name
            repo_url: Optional GitHub URL

        Returns:
            Project palace dictionary

        """
        palace = self.find_project_palace(repo_name)
        if palace:
            return palace
        return self.create_project_palace(repo_name, repo_url)

    def save_project_palace(self, palace: dict[str, Any]) -> None:
        """Save a project palace.

        Args:
            palace: Project palace dictionary to save

        """
        palace["last_modified"] = datetime.now().isoformat()
        palace_file = os.path.join(self.project_palaces_dir, f"{palace['id']}.json")

        # Create backup
        self._create_project_backup(palace["id"])

        with open(palace_file, "w") as f:
            json.dump(palace, f, indent=2)

        self._update_project_index()

    def add_review_entry(
        self,
        palace_id: str,
        entry: ReviewEntry,
    ) -> bool:
        """Add a review entry to a project palace's review chamber.

        Args:
            palace_id: Project palace ID
            entry: ReviewEntry to add

        Returns:
            True if successfully added

        """
        palace = self.load_project_palace(palace_id)
        if not palace:
            return False

        # Validate room type
        if entry.room_type not in REVIEW_CHAMBER_ROOMS:
            return False

        # Add to appropriate subroom
        review_chamber = palace["rooms"]["review-chamber"]
        subroom = review_chamber["subrooms"][entry.room_type]
        subroom["entries"].append(entry.to_dict())

        # Update metadata
        palace["metadata"]["total_entries"] += 1
        palace["metadata"]["review_entries"] += 1

        # Track contributors
        for participant in entry.participants:
            if participant not in palace["metadata"]["contributors"]:
                palace["metadata"]["contributors"].append(participant)

        self.save_project_palace(palace)
        return True

    def search_review_chamber(
        self,
        palace_id: str,
        query: str,
        room_type: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search the review chamber of a project palace.

        Args:
            palace_id: Project palace ID
            query: Search query
            room_type: Optional filter by room type
            tags: Optional filter by tags

        Returns:
            List of matching review entries

        """
        palace = self.load_project_palace(palace_id)
        if not palace:
            return []

        results = []
        query_lower = query.lower()

        review_chamber = palace["rooms"]["review-chamber"]
        for subroom_name, subroom in review_chamber.get("subrooms", {}).items():
            # Filter by room type if specified
            if room_type and subroom_name != room_type:
                continue

            for entry_data in subroom.get("entries", []):
                # Check query match
                entry_text = json.dumps(entry_data).lower()
                if query_lower not in entry_text:
                    continue

                # Filter by tags if specified
                if tags:
                    entry_tags = entry_data.get("tags", [])
                    if not any(tag in entry_tags for tag in tags):
                        continue

                results.append(
                    {
                        "room": f"review-chamber/{subroom_name}",
                        "entry": entry_data,
                        "palace_id": palace_id,
                        "palace_name": palace["name"],
                    }
                )

        return results

    def get_review_chamber_stats(self, palace_id: str) -> dict[str, Any]:
        """Get statistics for a project palace's review chamber.

        Args:
            palace_id: Project palace ID

        Returns:
            Statistics dictionary

        """
        palace = self.load_project_palace(palace_id)
        if not palace:
            return {}

        stats: dict[str, Any] = {
            "total_entries": 0,
            "by_room": {},
            "recent_entries": [],
            "top_tags": {},
            "contributors": palace["metadata"].get("contributors", []),
        }

        review_chamber = palace["rooms"]["review-chamber"]
        all_entries = []

        for subroom_name, subroom in review_chamber.get("subrooms", {}).items():
            entries = subroom.get("entries", [])
            stats["by_room"][subroom_name] = len(entries)
            stats["total_entries"] += len(entries)

            for entry in entries:
                all_entries.append(entry)
                for tag in entry.get("tags", []):
                    stats["top_tags"][tag] = stats["top_tags"].get(tag, 0) + 1

        # Sort entries by creation date and get recent
        all_entries.sort(key=lambda x: x.get("created", ""), reverse=True)
        stats["recent_entries"] = all_entries[:5]

        # Sort tags by frequency
        stats["top_tags"] = dict(
            sorted(stats["top_tags"].items(), key=lambda x: x[1], reverse=True)[:10]
        )

        return stats

    def list_project_palaces(self) -> list[dict[str, Any]]:
        """List all project palaces.

        Returns:
            List of project palace summaries

        """
        palaces = []
        for file_path in Path(self.project_palaces_dir).glob("*.json"):
            if file_path.name == "project_index.json":
                continue
            with open(file_path) as f:
                palace = json.load(f)
                palaces.append(
                    {
                        "id": palace["id"],
                        "name": palace["name"],
                        "repo_url": palace.get("repo_url"),
                        "created": palace["created"],
                        "last_modified": palace["last_modified"],
                        "total_entries": palace["metadata"]["total_entries"],
                        "review_entries": palace["metadata"]["review_entries"],
                    }
                )
        return palaces

    def _create_project_backup(self, palace_id: str) -> None:
        """Create backup of a project palace."""
        palace_file = os.path.join(self.project_palaces_dir, f"{palace_id}.json")
        if os.path.exists(palace_file):
            backup_dir = os.path.join(self.project_palaces_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"{palace_id}_{timestamp}.json")
            with open(palace_file) as src, open(backup_file, "w") as dst:
                dst.write(src.read())

    def _update_project_index(self) -> None:
        """Update the project palaces index."""
        index: dict[str, Any] = {
            "last_updated": datetime.now().isoformat(),
            "projects": [],
            "stats": {
                "total_projects": 0,
                "total_review_entries": 0,
            },
        }

        for file_path in Path(self.project_palaces_dir).glob("*.json"):
            if file_path.name == "project_index.json":
                continue
            try:
                with open(file_path) as f:
                    palace = json.load(f)
                    index["projects"].append(
                        {
                            "id": palace["id"],
                            "name": palace["name"],
                            "last_modified": palace["last_modified"],
                        }
                    )
                    index["stats"]["total_projects"] += 1
                    index["stats"]["total_review_entries"] += palace["metadata"].get(
                        "review_entries", 0
                    )
            except (json.JSONDecodeError, KeyError):
                pass

        index_file = os.path.join(self.project_palaces_dir, "project_index.json")
        with open(index_file, "w") as f:
            json.dump(index, f, indent=2)


def capture_pr_review_knowledge(  # noqa: PLR0913
    repo_name: str,
    pr_number: int,
    pr_title: str,
    findings: list[dict[str, Any]],
    participants: list[str],
    config_path: str | None = None,
) -> list[str]:
    """Capture knowledge from PR review findings.

    This is the main integration point for sanctum:pr-review.
    It evaluates findings and creates appropriate review entries.

    Args:
        repo_name: Repository name (e.g., "owner/repo")
        pr_number: PR number
        pr_title: PR title
        findings: List of review findings with severity and content
        participants: List of PR participants
        config_path: Optional path to configuration file

    Returns:
        List of created entry IDs

    """
    manager = ProjectPalaceManager(config_path)
    palace = manager.get_or_create_project_palace(repo_name)

    created_ids = []
    source_pr = f"#{pr_number} - {pr_title}"

    for finding in findings:
        # Classify finding into room type
        room_type = _classify_finding(finding)
        if not room_type:
            continue

        # Create review entry
        entry = ReviewEntry(
            source_pr=source_pr,
            title=finding.get("title", "Untitled Finding"),
            room_type=room_type,
            content={
                "decision": finding.get("description", ""),
                "context": finding.get("context", []),
                "captured_knowledge": {
                    "severity": finding.get("severity", "SUGGESTION"),
                    "category": finding.get("category", "general"),
                    "file": finding.get("file", ""),
                    "line": finding.get("line", ""),
                },
                "connected_concepts": finding.get("related", []),
            },
            participants=participants,
            tags=finding.get("tags", []),
        )

        if manager.add_review_entry(palace["id"], entry):
            created_ids.append(entry.id)

    return created_ids


def _classify_finding(finding: dict[str, Any]) -> str | None:
    """Classify a finding into a review chamber room type.

    Args:
        finding: Finding dictionary with severity and content

    Returns:
        Room type string or None if not worth capturing

    """
    severity = finding.get("severity", "").upper()
    category = finding.get("category", "").lower()

    # Architectural decisions (BLOCKING with architectural context)
    if severity == "BLOCKING" and any(
        kw in category for kw in ["architecture", "design", "pattern", "security"]
    ):
        return "decisions"

    # Recurring patterns (IN-SCOPE issues that represent patterns)
    if severity in ["BLOCKING", "IN-SCOPE"] and any(
        kw in category for kw in ["pattern", "recurring", "common", "best-practice"]
    ):
        return "patterns"

    # Quality standards (code quality findings)
    if severity in ["BLOCKING", "IN-SCOPE"] and any(
        kw in category for kw in ["quality", "style", "convention", "standard"]
    ):
        return "standards"

    # Lessons learned (post-mortems, retrospective insights)
    if any(kw in category for kw in ["lesson", "learning", "retrospective", "insight"]):
        return "lessons"

    # High-severity findings are worth capturing as patterns
    if severity == "BLOCKING":
        return "patterns"

    return None
