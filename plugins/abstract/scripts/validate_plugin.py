#!/usr/bin/env python3
"""Validate Claude Code plugin structure.

Validate plugin structure against official Claude Code documentation.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

# Constants
FRONTMATTER_PARTS_MIN = 3
MIN_ARGS = 2  # Script name + plugin directory


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class PluginValidator:
    """Validate Claude Code plugin structure."""

    def __init__(self, plugin_path: Path) -> None:
        """Initialize validator with plugin path."""
        self.plugin_path = plugin_path.resolve()
        self.config: dict[str, Any] | None = None
        self.issues: dict[str, list[str]] = {
            "critical": [],
            "warnings": [],
            "recommendations": [],
            "info": [],
        }

    def validate(self) -> int:
        """Run all validation checks.

        Returns:
            Exit code (0 for success, 1 for failures)

        """
        self._validate_plugin_json_exists()

        if self.config is not None:
            self._validate_plugin_name()
            self._validate_recommended_fields()
            self._validate_paths()
            self._validate_dependencies()
            self._validate_directory_structure()
            self._validate_skills()
            self._validate_claude_config()

        self._print_report()
        return 1 if self.issues["critical"] else 0

    def _validate_plugin_json_exists(self) -> None:
        """Validate that .claude-plugin/plugin.json exists."""
        json_path = self.plugin_path / ".claude-plugin" / "plugin.json"

        if not json_path.exists():
            # Check if it's in the wrong location
            wrong_path = self.plugin_path / "plugin.json"
            if wrong_path.exists():
                self.issues["critical"].append(
                    "plugin.json found at root but should be at "
                    ".claude-plugin/plugin.json",
                )
                self.issues["info"].append(
                    "Run: mkdir -p .claude-plugin && mv plugin.json .claude-plugin/",
                )
            else:
                self.issues["critical"].append(".claude-plugin/plugin.json not found")
            return

        try:
            with open(json_path) as f:
                data = json.load(f)
            if not isinstance(data, dict):
                self.issues["critical"].append(
                    "plugin.json must contain a JSON object at the top level",
                )
                return
            self.config = data
            self.issues["info"].append(
                "[OK] .claude-plugin/plugin.json exists and is valid JSON",
            )
        except json.JSONDecodeError as e:
            self.issues["critical"].append(f"plugin.json is not valid JSON: {e}")

    def _require_config(self) -> dict[str, Any]:
        """Return loaded config or raise if missing."""
        if self.config is None:
            msg = "plugin.json not loaded"
            raise RuntimeError(msg)
        return self.config

    def _validate_plugin_name(self) -> None:
        """Validate plugin name follows kebab-case convention."""
        config = self._require_config()

        if "name" not in config:
            self.issues["critical"].append("Missing required field: name")
            return

        name = config["name"]
        if not isinstance(name, str):
            self.issues["critical"].append(
                "Plugin name must be a string (kebab-case)",
            )
            return

        # Check kebab-case format
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            self.issues["critical"].append(
                f"Invalid plugin name: '{name}' "
                "(must be kebab-case: lowercase with hyphens)",
            )
            self.issues["info"].append(
                "Example valid names: 'my-plugin', 'ai-assistant', 'code-helper'",
            )
        else:
            self.issues["info"].append(
                f"[OK] Plugin name '{name}' follows kebab-case convention",
            )

    def _validate_recommended_fields(self) -> None:
        """Check for recommended metadata fields."""
        config = self._require_config()
        recommended = {
            "version": "Semantic version (e.g., '1.0.0')",
            "description": "Clear description of plugin functionality",
            "author": "Author name or object with name/email",
            "license": "License identifier (e.g., 'MIT')",
        }

        for field, description in recommended.items():
            if field not in config:
                self.issues["recommendations"].append(
                    f"Missing recommended field: {field} - {description}",
                )

        # Validate version format if present
        if "version" in config:
            version = config["version"]
            if not isinstance(version, str):
                self.issues["warnings"].append(
                    "Version should be a string following semantic versioning",
                )
                return
            if not re.match(r"^\d+\.\d+\.\d+", version):
                self.issues["warnings"].append(
                    f"Version '{version}' should follow semantic versioning "
                    "(e.g., '1.0.0')",
                )

    def _validate_paths(self) -> None:
        """Validate path references in plugin.json."""
        config = self._require_config()
        path_fields = ["skills", "commands", "agents"]

        for field in path_fields:
            if field not in config:
                continue

            value = config[field]

            # Handle both string and list formats
            if isinstance(value, str):
                paths = [value]
            elif isinstance(value, list):
                paths = [p for p in value if isinstance(p, str)]
            else:
                paths = []

            for path in paths:
                # Check relative path format
                if not path.startswith("./") and not path.startswith(field + "/"):
                    self.issues["warnings"].append(
                        f"{field} path should use relative format: {path}",
                    )

                # Check if referenced path exists
                # Try both as-is and with .md extension
                clean_path = path.lstrip("./")
                check_paths = [
                    self.plugin_path / clean_path,
                    self.plugin_path / f"{clean_path}.md",
                    self.plugin_path / clean_path / "SKILL.md",
                ]

                if not any(p.exists() for p in check_paths):
                    self.issues["critical"].append(
                        f"Referenced {field} path not found: {path}",
                    )

    def _validate_dependencies(self) -> None:
        """Validate dependencies format and versioning."""
        config = self._require_config()
        if "dependencies" not in config:
            return

        deps = config["dependencies"]

        # Check if it's a list (old format)
        if isinstance(deps, list):
            self.issues["recommendations"].append(
                "Dependencies should be an object with versions, not an array. "
                'Example: {"abstract": ">=2.0.0"}',
            )
            return

        # Validate each dependency
        if isinstance(deps, dict):
            for dep_name, version in deps.items():
                if not isinstance(version, str):
                    self.issues["warnings"].append(
                        f"Dependency '{dep_name}' version should be a string",
                    )
                    continue

                # Check for semantic versioning
                if not re.match(r"^[><=\^~]*\d+\.\d+\.\d+", version):
                    self.issues["warnings"].append(
                        f"Dependency '{dep_name}' should use semantic "
                        f"versioning (found: '{version}')",
                    )

    def _validate_directory_structure(self) -> None:
        """Validate plugin directory structure."""
        config = self._require_config()
        # Check that component directories exist if referenced
        if config.get("skills"):
            if not (self.plugin_path / "skills").exists():
                self.issues["warnings"].append(
                    "Plugin references skills but skills/ directory is missing",
                )

        if config.get("commands"):
            if not (self.plugin_path / "commands").exists():
                self.issues["warnings"].append(
                    "Plugin references commands but commands/ directory is missing",
                )

        if "agents" in config and config.get("agents"):
            if not (self.plugin_path / "agents").exists():
                self.issues["warnings"].append(
                    "Plugin references agents but agents/ directory is missing",
                )

        # Check that component directories are at plugin root, not in .claude-plugin
        for dirname in ["skills", "commands", "agents", "hooks"]:
            wrong_location = self.plugin_path / ".claude-plugin" / dirname
            if wrong_location.exists():
                self.issues["critical"].append(
                    f"{dirname}/ should be at plugin root, not inside .claude-plugin/",
                )
                self.issues["info"].append(f"Run: mv .claude-plugin/{dirname} ./")

    def _validate_skills(self) -> None:
        """Validate skill files and structure."""
        config = self._require_config()
        if "skills" not in config:
            return

        skills_list = config["skills"]
        if not isinstance(skills_list, list):
            return

        for skill_path in skills_list:
            if not isinstance(skill_path, str):
                continue
            clean_path = skill_path.lstrip("./")

            # Check for YAML frontmatter
            possible_paths = [
                self.plugin_path / f"{clean_path}.md",
                self.plugin_path / clean_path / "SKILL.md",
            ]

            skill_file = next((p for p in possible_paths if p.exists()), None)

            if skill_file:
                self._validate_skill_file(skill_file, skill_path)

    def _validate_skill_file(self, skill_file: Path, skill_path: str) -> None:
        """Validate individual skill file."""
        try:
            with open(skill_file) as f:
                content = f.read()

            # Check for YAML frontmatter
            if not content.startswith("---"):
                self.issues["warnings"].append(
                    f"Skill {skill_path} should start with YAML frontmatter (---)",
                )
                return

            # Extract frontmatter
            parts = content.split("---", 2)
            if len(parts) < FRONTMATTER_PARTS_MIN:
                self.issues["warnings"].append(
                    f"Skill {skill_path} has incomplete YAML frontmatter",
                )
                return

            # Check for required frontmatter fields
            frontmatter = parts[1]
            if "name:" not in frontmatter:
                self.issues["warnings"].append(
                    f"Skill {skill_path} missing 'name' in frontmatter",
                )
            if "description:" not in frontmatter:
                self.issues["recommendations"].append(
                    f"Skill {skill_path} missing 'description' in frontmatter",
                )

        except Exception as e:
            self.issues["warnings"].append(f"Error validating skill {skill_path}: {e}")

    def _validate_claude_config(self) -> None:
        """Validate Claude-specific configuration."""
        config = self._require_config()
        if "claude" not in config:
            self.issues["recommendations"].append(
                "Consider adding 'claude' configuration object for enhanced metadata",
            )
            return

        claude_config = config["claude"]
        if not isinstance(claude_config, dict):
            self.issues["warnings"].append(
                "claude configuration should be a JSON object",
            )
            return

        # Check for useful Claude config fields
        recommended_claude_fields = {
            "skill_prefix": "Prefix for skill names",
            "auto_load": "Whether to auto-load plugin",
            "categories": "Plugin categorization",
        }

        for field, description in recommended_claude_fields.items():
            if field not in claude_config:
                self.issues["recommendations"].append(
                    f"Consider adding claude.{field} - {description}",
                )

    def _print_report(self) -> None:
        """Print validation report."""
        name = self.config.get("name", "unknown") if self.config else "unknown"
        print(f"\n{Colors.BOLD}Plugin Validation Report: {name}{Colors.END}\n")

        # Critical issues
        if self.issues["critical"]:
            print(f"{Colors.RED}{Colors.BOLD}Critical Issues:{Colors.END}")
            for issue in self.issues["critical"]:
                print(f"  {Colors.RED}FAIL{Colors.END} {issue}")
            print()

        # Warnings
        if self.issues["warnings"]:
            print(f"{Colors.YELLOW}{Colors.BOLD}Warnings:{Colors.END}")
            for issue in self.issues["warnings"]:
                print(f"  {Colors.YELLOW}[WARN]{Colors.END} {issue}")
            print()

        # Recommendations
        if self.issues["recommendations"]:
            print(f"{Colors.BLUE}{Colors.BOLD}Recommendations:{Colors.END}")
            for issue in self.issues["recommendations"]:
                print(f"  {Colors.BLUE}→{Colors.END} {issue}")
            print()

        # Info messages
        if self.issues["info"]:
            print(f"{Colors.GREEN}{Colors.BOLD}Info:{Colors.END}")
            for info in self.issues["info"]:
                print(f"  {Colors.GREEN}OK{Colors.END} {info}")
            print()

        # Summary
        if not self.issues["critical"] and not self.issues["warnings"]:
            print(f"{Colors.GREEN}{Colors.BOLD}OK Plugin validation passed{Colors.END}")
        elif self.issues["critical"]:
            print(f"{Colors.RED}{Colors.BOLD}FAIL Plugin validation failed{Colors.END}")
        else:
            print(f"{Colors.YELLOW}{Colors.BOLD}[WARN] Plugin has warnings{Colors.END}")


def main() -> int:
    """Run the plugin validator CLI."""
    if len(sys.argv) < MIN_ARGS:
        print(f"Usage: {sys.argv[0]} <plugin-directory>", file=sys.stderr)
        return 1

    plugin_path = Path(sys.argv[1]).expanduser()

    if not plugin_path.exists():
        print(f"Error: Path does not exist: {plugin_path}", file=sys.stderr)
        return 1

    if not plugin_path.is_dir():
        print(f"Error: Path is not a directory: {plugin_path}", file=sys.stderr)
        return 1

    validator = PluginValidator(plugin_path)
    return validator.validate()


if __name__ == "__main__":
    sys.exit(main())
