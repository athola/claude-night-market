"""Configuration loader for hookify rules.

Loads rules from two sources:
1. Bundled rules (from plugin's skills/rule-catalog/rules/)
2. User rules (from project's .claude/)

User rules override bundled rules with the same name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Condition:
    """A single condition in a rule."""

    field: str
    operator: str
    pattern: str

    def __post_init__(self) -> None:
        """Validate condition fields."""
        valid_operators = {
            "regex_match",
            "contains",
            "equals",
            "not_contains",
            "starts_with",
            "ends_with",
        }
        if self.operator not in valid_operators:
            raise ValueError(
                f"Invalid operator '{self.operator}'. "
                f"Must be one of: {', '.join(sorted(valid_operators))}"
            )


@dataclass
class RuleConfig:
    """Configuration for a hookify rule."""

    name: str
    enabled: bool
    event: str
    action: str = "warn"
    pattern: str | None = None
    conditions: list[Condition] = field(default_factory=list)
    message: str = ""
    file_path: Path | None = None
    source: str = "user"  # "bundled" or "user"

    def __post_init__(self) -> None:
        """Validate rule configuration."""
        valid_events = {"bash", "file", "stop", "prompt", "all"}
        if self.event not in valid_events:
            raise ValueError(
                f"Invalid event '{self.event}'. "
                f"Must be one of: {', '.join(sorted(valid_events))}"
            )

        valid_actions = {"warn", "block"}
        if self.action not in valid_actions:
            raise ValueError(
                f"Invalid action '{self.action}'. "
                f"Must be one of: {', '.join(sorted(valid_actions))}"
            )

        if not self.pattern and not self.conditions:
            raise ValueError("Rule must have either 'pattern' or 'conditions'")


def _get_bundled_rules_dir() -> Path:
    """Get the directory containing bundled rules.

    Uses __file__ to locate relative to this module, ensuring it works
    regardless of where the plugin is installed.

    Returns:
        Path to bundled rules directory.
    """
    # This file is in: plugins/hookify/core/config_loader.py
    # Bundled rules are in: plugins/hookify/skills/rule-catalog/rules/
    core_dir = Path(__file__).parent
    plugin_dir = core_dir.parent
    return plugin_dir / "skills" / "rule-catalog" / "rules"


class ConfigLoader:
    """Loads and parses hookify rule configurations.

    Loads from both bundled rules (shipped with plugin) and user rules
    (in project's .claude/ directory). User rules override bundled rules
    with the same name.
    """

    RULE_PREFIX = "hookify."
    RULE_SUFFIX = ".local.md"

    def __init__(
        self,
        user_rules_dir: Path | None = None,
        include_bundled: bool = True,
    ) -> None:
        """Initialize config loader.

        Args:
            user_rules_dir: Directory for user rules. Defaults to .claude/
            include_bundled: Whether to include bundled rules. Defaults to True.
        """
        if user_rules_dir is None:
            user_rules_dir = Path.cwd() / ".claude"
        self.user_rules_dir = Path(user_rules_dir)
        self.include_bundled = include_bundled
        self.bundled_rules_dir = _get_bundled_rules_dir()

    def load_all_rules(self) -> list[RuleConfig]:
        """Load all hookify rules from bundled and user directories.

        User rules override bundled rules with the same name.

        Returns:
            List of loaded rule configurations.
        """
        rules_by_name: dict[str, RuleConfig] = {}

        # 1. Load bundled rules first (lower priority)
        if self.include_bundled:
            for rule in self._load_bundled_rules():
                rules_by_name[rule.name] = rule

        # 2. Load user rules (higher priority - overrides bundled)
        for rule in self._load_user_rules():
            rules_by_name[rule.name] = rule

        return list(rules_by_name.values())

    def _load_bundled_rules(self) -> list[RuleConfig]:
        """Load rules bundled with the plugin.

        Returns:
            List of bundled rule configurations.
        """
        rules = []

        if not self.bundled_rules_dir.exists():
            return rules

        # Scan all category directories
        for category_dir in self.bundled_rules_dir.iterdir():
            if not category_dir.is_dir():
                continue

            # Load all .md files in category
            for rule_file in category_dir.glob("*.md"):
                try:
                    rule = self.load_rule(rule_file, source="bundled")
                    rules.append(rule)
                except Exception as e:
                    # Log error but continue loading other rules
                    print(f"Error loading bundled rule {rule_file}: {e}")

        return rules

    def _load_user_rules(self) -> list[RuleConfig]:
        """Load user-defined rules from .claude/ directory.

        Returns:
            List of user rule configurations.
        """
        rules = []

        if not self.user_rules_dir.exists():
            return rules

        pattern = f"{self.RULE_PREFIX}*{self.RULE_SUFFIX}"

        for rule_file in self.user_rules_dir.glob(pattern):
            try:
                rule = self.load_rule(rule_file, source="user")
                rules.append(rule)
            except Exception as e:
                print(f"Error loading user rule {rule_file}: {e}")

        return rules

    def load_rule(self, rule_file: Path, source: str = "user") -> RuleConfig:
        """Load a single rule from a file.

        Args:
            rule_file: Path to the rule markdown file
            source: Source of the rule ("bundled" or "user")

        Returns:
            Parsed rule configuration

        Raises:
            ValueError: If rule format is invalid
        """
        content = rule_file.read_text()

        # Parse frontmatter and message body
        frontmatter, message = self._parse_markdown(content)

        # Extract conditions if present
        conditions = []
        if "conditions" in frontmatter:
            conditions = [
                Condition(
                    field=c["field"], operator=c["operator"], pattern=c["pattern"]
                )
                for c in frontmatter["conditions"]
            ]

        return RuleConfig(
            name=frontmatter["name"],
            enabled=frontmatter["enabled"],
            event=frontmatter["event"],
            action=frontmatter.get("action", "warn"),
            pattern=frontmatter.get("pattern"),
            conditions=conditions,
            message=message.strip(),
            file_path=rule_file,
            source=source,
        )

    def _parse_markdown(self, content: str) -> tuple[dict[str, Any], str]:
        """Parse markdown file with YAML frontmatter.

        Args:
            content: Raw markdown content

        Returns:
            Tuple of (frontmatter dict, message body)

        Raises:
            ValueError: If frontmatter is missing or invalid
        """
        # Match YAML frontmatter between --- delimiters
        match = re.match(r"^---\s*\n(.*?\n)---\s*\n(.*)$", content, re.DOTALL)

        if not match:
            raise ValueError("No valid YAML frontmatter found")

        frontmatter_text = match.group(1)
        message = match.group(2)

        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter: {e}") from e

        if not isinstance(frontmatter, dict):
            raise ValueError("Frontmatter must be a YAML mapping")

        # Validate required fields
        required = {"name", "enabled", "event"}
        missing = required - set(frontmatter.keys())
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        return frontmatter, message

    def get_rule_path(self, rule_name: str) -> Path:
        """Get the file path for a user rule name.

        Args:
            rule_name: Name of the rule

        Returns:
            Path where the rule file would be stored
        """
        filename = f"{self.RULE_PREFIX}{rule_name}{self.RULE_SUFFIX}"
        return self.user_rules_dir / filename

    def get_bundled_rule_names(self) -> list[str]:
        """Get names of all bundled rules.

        Returns:
            List of bundled rule names.
        """
        names = []
        if not self.bundled_rules_dir.exists():
            return names

        for category_dir in self.bundled_rules_dir.iterdir():
            if category_dir.is_dir():
                for rule_file in category_dir.glob("*.md"):
                    names.append(rule_file.stem)

        return names

    def get_rule_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all rules (bundled and user).

        Returns:
            Dict mapping rule names to their status info.
        """
        status: dict[str, dict[str, Any]] = {}

        # Get bundled rules
        if self.include_bundled and self.bundled_rules_dir.exists():
            for category_dir in self.bundled_rules_dir.iterdir():
                if category_dir.is_dir():
                    for rule_file in category_dir.glob("*.md"):
                        name = rule_file.stem
                        status[name] = {
                            "source": "bundled",
                            "category": category_dir.name,
                            "path": str(rule_file),
                            "overridden": False,
                        }

        # Check for user overrides
        if self.user_rules_dir.exists():
            pattern = f"{self.RULE_PREFIX}*{self.RULE_SUFFIX}"
            for rule_file in self.user_rules_dir.glob(pattern):
                # Extract rule name from filename
                name = rule_file.stem
                if name.startswith(self.RULE_PREFIX):
                    name = name[len(self.RULE_PREFIX) :]

                if name in status:
                    status[name]["overridden"] = True
                    status[name]["user_path"] = str(rule_file)
                else:
                    status[name] = {
                        "source": "user",
                        "category": "custom",
                        "path": str(rule_file),
                        "overridden": False,
                    }

        return status
