"""Versioned skill definitions with YAML frontmatter management.

Manages adaptation version history in skill YAML frontmatter,
supporting version bumps, rollback tracking, and metric baselines.

Part of the self-adapting system. See: docs/adr/0006-self-adapting-skill-health.md
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class SkillVersionManager:
    """Manages version history in a skill's YAML frontmatter."""

    def __init__(self, skill_file: Path) -> None:
        self.skill_file = skill_file
        self.frontmatter: dict[str, Any] = {}
        self.body: str = ""
        self._raw_frontmatter: str = ""
        self._parse()

    def _parse(self) -> None:
        """Parse YAML frontmatter and body from skill file."""
        # An unreadable file must raise: empty state would let a later
        # bump_version overwrite the real skill file with an empty body.
        content = self.skill_file.read_text()
        match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
        if match:
            self._raw_frontmatter = match.group(1)
            self.frontmatter = yaml.safe_load(self._raw_frontmatter) or {}
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
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        # Nothing was measured before the first bump; zeros
                        # here would read as a skill that never worked.
                        "baseline_metrics": {},
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "change_summary": change_summary,
                "baseline_metrics": metrics,
            }
        )
        adaptation["current_version"] = new_version
        adaptation["rollback_available"] = True

        self._write()
        return new_version

    def _write(self) -> None:
        """Write the adaptation block back, leaving other frontmatter lines as-is.

        Dumping the whole frontmatter folded long descriptions, dropped
        quoting and comments, and turned every improvement of a checked-in
        SKILL.md into a frontmatter-wide diff. Only the adaptation block
        changes, so only it is re-serialized.
        """
        kept = re.sub(
            r"^adaptation:[^\n]*\n?(?:[ \t-][^\n]*\n?)*",
            "",
            self._raw_frontmatter,
            flags=re.MULTILINE,
        ).rstrip("\n")
        block = yaml.dump(
            {"adaptation": self.frontmatter["adaptation"]},
            default_flow_style=False,
            sort_keys=False,
        )
        fm_str = f"{kept}\n{block}" if kept else block
        self.skill_file.write_text(f"---\n{fm_str}---\n{self.body}")
        self._raw_frontmatter = fm_str.rstrip("\n")
