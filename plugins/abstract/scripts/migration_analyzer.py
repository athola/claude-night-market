#!/usr/bin/env python3
"""Migration analyzer for detecting overlapping functionality.

This module analyzes plugin code to identify functionality that might overlap
with existing superpowers, helping with migration decisions.
"""

import os

import yaml

# Constants for magic numbers
OVERLAP_CONFIDENCE_THRESHOLD = 0.5
HIGH_PRIORITY_THRESHOLD = 0.8
MEDIUM_PRIORITY_THRESHOLD = 0.5
try:
    from .compatibility_validator import CompatibilityValidator
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.append(os.path.dirname(__file__))
    from compatibility_validator import CompatibilityValidator


class MigrationAnalyzer:
    """Analyzes plugins for overlapping functionality with superpowers."""

    def __init__(self, plugin_name: str) -> None:
        """Initialize the migration analyzer."""
        self.plugin_name = plugin_name
        # When running from within the plugin directory, use current directory
        self.plugin_path = os.path.abspath(".")
        self.overlap_mappings = self._load_overlap_mappings()
        self.compatibility_validator = CompatibilityValidator()

    def analyze_plugin(self, command_name: str) -> dict:
        """Analyze a plugin command for superpower overlaps."""
        overlaps = {}

        # Load command content
        command_path = os.path.join(self.plugin_path, "commands", f"{command_name}.md")
        if os.path.exists(command_path):
            with open(command_path) as f:
                content = f.read()

            # Check for known patterns
            for superpower, patterns in self.overlap_mappings.items():
                confidence = self._calculate_overlap(content, patterns)
                if confidence > OVERLAP_CONFIDENCE_THRESHOLD:
                    overlaps[superpower] = {
                        "confidence": confidence,
                        "patterns_matched": self._get_matched_patterns(
                            content,
                            patterns,
                        ),
                    }

        return overlaps

    def analyze_migration_path(
        self,
        command_name: str,
        wrapper_path: str | None = None,
    ) -> dict:
        """Analyze migration path for a command to superpowers wrapper.

        Args:
            command_name: Name of the command to migrate
            wrapper_path: Optional path to existing wrapper implementation

        Returns:
            Migration analysis with overlap detection and compatibility validation

        """
        # Analyze overlaps
        overlaps = self.analyze_plugin(command_name)

        migration_path = {
            "command": command_name,
            "overlaps": overlaps,
            "migration_priority": self._calculate_migration_priority(overlaps),
            "suggested_superpower": self._suggest_best_superpower(overlaps),
            "wrapper_status": None,
            "compatibility": None,
        }

        # If wrapper exists, validate compatibility
        if wrapper_path and os.path.exists(wrapper_path):
            original_path = os.path.join(
                self.plugin_path,
                "commands",
                f"{command_name}.md",
            )
            if os.path.exists(original_path):
                compatibility = self.compatibility_validator.validate_wrapper(
                    original_path,
                    wrapper_path,
                )
                migration_path["wrapper_status"] = "exists"
                migration_path["compatibility"] = compatibility

        return migration_path

    def generate_migration_report(self) -> dict:
        """Generate a comprehensive migration report for all commands.

        Returns:
            Report with migration priorities and recommendations

        """
        commands_dir = os.path.join(self.plugin_path, "commands")
        if not os.path.exists(commands_dir):
            return {"error": "No commands directory found"}

        report = {
            "plugin": self.plugin_name,
            "commands": {},
            "summary": {
                "total_commands": 0,
                "high_priority_migrations": 0,
                "medium_priority_migrations": 0,
                "low_priority_migrations": 0,
            },
        }

        # Analyze each command
        for command_file in os.listdir(commands_dir):
            if command_file.endswith(".md"):
                command_name = command_file[:-3]  # Remove .md extension

                command_analysis = self.analyze_migration_path(command_name)
                report["commands"][command_name] = command_analysis

                # Update summary
                report["summary"]["total_commands"] += 1
                priority = command_analysis["migration_priority"]
                if priority >= HIGH_PRIORITY_THRESHOLD:
                    report["summary"]["high_priority_migrations"] += 1
                elif priority >= MEDIUM_PRIORITY_THRESHOLD:
                    report["summary"]["medium_priority_migrations"] += 1
                else:
                    report["summary"]["low_priority_migrations"] += 1

        return report

    def _calculate_migration_priority(self, overlaps: dict) -> float:
        """Calculate migration priority based on overlap confidence."""
        if not overlaps:
            return 0.0

        # Use highest confidence overlap as priority
        max_confidence = max(overlap["confidence"] for overlap in overlaps.values())

        # Boost priority if multiple superpowers overlap
        if len(overlaps) > 1:
            max_confidence = min(1.0, max_confidence + 0.1)

        return round(max_confidence, 2)

    def _suggest_best_superpower(self, overlaps: dict) -> str | None:
        """Suggest the best superpower for migration based on overlap confidence."""
        if not overlaps:
            return None

        # Return superpower with highest confidence
        return max(overlaps.keys(), key=lambda k: overlaps[k]["confidence"])

    def _load_overlap_mappings(self) -> dict:
        """Load predefined overlap patterns."""
        mappings_path = os.path.join(self.plugin_path, "data", "overlap_mappings.yaml")
        if os.path.exists(mappings_path):
            with open(mappings_path) as f:
                return yaml.safe_load(f)

        # Return default mappings if file doesn't exist
        return {
            "test-driven-development": [
                "RED phase",
                "GREEN phase",
                "REFACTOR phase",
                "write failing test",
                "watch it fail",
                "minimal code",
                "test-first",
            ],
            "systematic-debugging": [
                "root cause",
                "investigation",
                "hypothesis",
                "pattern analysis",
                "debug",
            ],
            "requesting-code-review": [
                "code review",
                "pull request",
                "PR",
                "review feedback",
                "quality check",
            ],
            "writing-plans": [
                "implementation plan",
                "design document",
                "break down",
                "tasks",
                "architecture",
            ],
        }

    def _calculate_overlap(self, content: str, patterns: list[str]) -> float:
        """Calculate overlap confidence based on pattern matching."""
        matches = sum(1 for pattern in patterns if pattern.lower() in content.lower())
        return matches / len(patterns) if patterns else 0

    def _get_matched_patterns(self, content: str, patterns: list[str]) -> list[str]:
        """Get list of patterns that matched."""
        return [p for p in patterns if p.lower() in content.lower()]
