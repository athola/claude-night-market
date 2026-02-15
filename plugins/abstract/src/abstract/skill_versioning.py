"""Versioned skill definitions with YAML frontmatter management.

Manages adaptation version history in skill YAML frontmatter,
supporting version bumps, rollback tracking, and metric baselines.

Part of the self-adapting system. See:
docs/plans/2026-02-15-self-adapting-systems-design.md
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


class SkillVersionManager:
    """Manages version history in a skill's YAML frontmatter."""

    def __init__(self, skill_file: Path) -> None:
        self.skill_file = skill_file
        self.frontmatter: dict[str, Any] = {}
        self.body: str = ""
        self._parse()

    def _parse(self) -> None:
        """Parse YAML frontmatter and body from skill file."""
        content = self.skill_file.read_text()
        match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
        if match:
            self.frontmatter = yaml.safe_load(match.group(1)) or {}
            self.body = match.group(2)
        else:
            self.frontmatter = {}
            self.body = content

        # Ensure adaptation block exists
        if "adaptation" not in self.frontmatter:
            self.frontmatter["adaptation"] = {
                "current_version": "1.0.0",
                "rollback_available": False,
                "version_history": [
                    {
                        "version": "1.0.0",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "baseline_metrics": {
                            "success_rate": 0.0,
                            "stability_gap": 0.0,
                        },
                    }
                ],
            }

    @property
    def current_version(self) -> str:
        """Get current version string."""
        return str(self.frontmatter["adaptation"]["current_version"])

    @property
    def version_history(self) -> list[dict[str, Any]]:
        """Get full version history."""
        return list(self.frontmatter["adaptation"]["version_history"])

    def bump_version(self, change_summary: str, metrics: dict[str, float]) -> str:
        """Bump minor version and record in history.

        Returns the new version string.
        """
        parts = self.current_version.split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        new_version = f"{major}.{minor + 1}.{patch}"

        adaptation = self.frontmatter["adaptation"]
        adaptation["version_history"].append(
            {
                "version": new_version,
                "timestamp": datetime.now(UTC).isoformat(),
                "change_summary": change_summary,
                "baseline_metrics": metrics,
            }
        )
        adaptation["current_version"] = new_version
        adaptation["rollback_available"] = True

        self._write()
        return new_version

    def _write(self) -> None:
        """Write frontmatter + body back to file."""
        fm_str = yaml.dump(self.frontmatter, default_flow_style=False, sort_keys=False)
        self.skill_file.write_text(f"---\n{fm_str}---\n{self.body}")
