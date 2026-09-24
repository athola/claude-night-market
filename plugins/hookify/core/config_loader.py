"""Configuration loader for hookify rules.

Load rules from two sources:
1. Bundled rules (from plugin's skills/rule-catalog/rules/)
2. User rules (from project's .claude/)

User rules override bundled rules with the same name.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    # Hooks run under the operator's python3, which rarely has PyYAML.
    # Rule frontmatter is then read by _parse_frontmatter_subset below.
    yaml = None  # type: ignore[assignment]  # None sentinel; the loader branches on `yaml is None`

logger = logging.getLogger(__name__)

VALID_EVENT_TYPES: frozenset[str] = frozenset({"bash", "file", "stop", "prompt", "all"})


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
        if self.operator == "regex_match":
            _compile_or_raise(self.pattern, f"condition on '{self.field}'")


def _compile_or_raise(pattern: str, where: str) -> None:
    """Reject a rule whose regex cannot compile.

    A rule that fails to compile at evaluation time is a rule that
    never fires, and for a ``block`` rule that is a silent hole in the
    guard. Failing here surfaces the typo in the loader's warning.
    """
    try:
        re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern in {where}: {exc}") from exc


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
        if self.event not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid event '{self.event}'. Must be one of: {', '.join(sorted(VALID_EVENT_TYPES))}"
            )

        valid_actions = {"warn", "block"}
        if self.action not in valid_actions:
            raise ValueError(
                f"Invalid action '{self.action}'. "
                f"Must be one of: {', '.join(sorted(valid_actions))}"
            )

        if not self.pattern and not self.conditions:
            raise ValueError("Rule must have either 'pattern' or 'conditions'")
        if self.pattern:
            _compile_or_raise(self.pattern, f"rule '{self.name}'")


# PyYAML 1.1 booleans, so the stdlib parser reads ``enabled`` as it does.
_YAML_BOOLS = {
    form: value
    for word, value in (
        ("true", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("no", False),
        ("off", False),
    )
    for form in (word, word.title(), word.upper())
}
_UNSUPPORTED_VALUE_STARTS = ("|", ">", "[", "{", "&", "*", "!")


def _parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if raw.startswith("'"):
        if len(raw) < 2 or not raw.endswith("'"):  # noqa: PLR2004 - two quotes
            raise ValueError(f"Unterminated quote in frontmatter value: {raw}")
        return raw[1:-1].replace("''", "'")
    if raw.startswith('"'):
        # A JSON string is a YAML double-quoted scalar for every escape a
        # rule pattern uses.
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid double-quoted frontmatter value: {raw}") from exc
    if raw.startswith(_UNSUPPORTED_VALUE_STARTS):
        raise ValueError(
            f"Unsupported frontmatter value without PyYAML: {raw}. "
            "Use a plain or quoted scalar."
        )
    raw = "" if raw.startswith("#") else re.split(r"\s#", raw, maxsplit=1)[0].rstrip()
    if not raw:
        return None
    if ": " in raw:
        raise ValueError(f"Unquoted ': ' in frontmatter value: {raw}. Quote it.")
    return _YAML_BOOLS.get(raw, raw)


def _parse_frontmatter_subset(text: str) -> dict[str, Any]:
    """Read rule frontmatter with the standard library alone.

    Covers the shape every rule uses: top-level scalars plus one list of
    flat maps (``conditions``). Anything else raises, because a block
    rule parsed wrong is a guard that silently stops guarding.
    """
    frontmatter: dict[str, Any] = {}
    current_key = ""
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        is_item = stripped.startswith("- ")
        if not line[0].isspace() and not is_item:
            key, sep, rest = line.partition(":")
            if not sep:
                raise ValueError(f"Invalid frontmatter line {number}: {line}")
            current_key = key.strip()
            frontmatter[current_key] = _parse_scalar(rest)
            continue
        items = frontmatter.get(current_key)
        if items is None and current_key:
            items = frontmatter[current_key] = []
        if not isinstance(items, list):
            raise ValueError(f"Invalid frontmatter line {number}: {line}")
        if is_item:
            items.append({})
            stripped = stripped[2:]
        elif not items:
            raise ValueError(f"Invalid frontmatter line {number}: {line}")
        key, sep, rest = stripped.partition(":")
        if not sep:
            raise ValueError(f"Invalid frontmatter line {number}: {line}")
        items[-1][key.strip()] = _parse_scalar(rest)
    return frontmatter


def get_bundled_rules_dir() -> Path:
    """Return the directory containing bundled rules.

    Uses __file__ to locate relative to this module, so this works
    regardless of where the plugin is installed.

    Returns:
        Path to the bundled rules directory.
    """
    # This file is in: plugins/hookify/core/config_loader.py
    # Bundled rules are in: plugins/hookify/skills/rule-catalog/rules/
    core_dir = Path(__file__).parent
    plugin_dir = core_dir.parent
    return plugin_dir / "skills" / "rule-catalog" / "rules"


# Back-compat alias; callers should prefer get_bundled_rules_dir.
_get_bundled_rules_dir = get_bundled_rules_dir


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
        # Rules skipped as unreadable, so a caller can say which guards
        # are not running instead of leaving that in a log.
        self.load_errors: list[str] = []
        self.bundled_rules_dir = _get_bundled_rules_dir()

    def _iter_bundled_rule_files(self) -> list[Path]:
        """Return all bundled rule markdown files."""
        rule_files: list[Path] = []
        if not self.bundled_rules_dir.exists():
            return rule_files
        for category_dir in self.bundled_rules_dir.iterdir():
            if category_dir.is_dir():
                rule_files.extend(category_dir.glob("*.md"))
        return rule_files

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
        rules: list[RuleConfig] = []

        for rule_file in self._iter_bundled_rule_files():
            try:
                rule = self.load_rule(rule_file, source="bundled")
                rules.append(rule)
            except (OSError, ValueError) as e:
                logger.warning("Error loading bundled rule %s: %s", rule_file, e)
                self.load_errors.append(f"{rule_file.name}: {e}")

        return rules

    def _load_user_rules(self) -> list[RuleConfig]:
        """Load user-defined rules from .claude/ directory.

        Returns:
            List of user rule configurations.
        """
        rules: list[RuleConfig] = []

        if not self.user_rules_dir.exists():
            return rules

        pattern = f"{self.RULE_PREFIX}*{self.RULE_SUFFIX}"

        for rule_file in self.user_rules_dir.glob(pattern):
            try:
                rule = self.load_rule(rule_file, source="user")
                rules.append(rule)
            except (OSError, ValueError) as e:
                logger.warning("Error loading user rule %s: %s", rule_file, e)
                self.load_errors.append(f"{rule_file.name}: {e}")

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

        if yaml is None:
            frontmatter = _parse_frontmatter_subset(frontmatter_text)
        else:
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
        return [f.stem for f in self._iter_bundled_rule_files()]

    def get_rule_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all rules (bundled and user).

        Returns:
            Dict mapping rule names to their status info.
        """
        status: dict[str, dict[str, Any]] = {}

        # Get bundled rules
        if self.include_bundled:
            for rule_file in self._iter_bundled_rule_files():
                name = rule_file.stem
                status[name] = {
                    "source": "bundled",
                    "category": rule_file.parent.name,
                    "path": str(rule_file),
                    "overridden": False,
                }

        # Check for user overrides
        if self.user_rules_dir.exists():
            pattern = f"{self.RULE_PREFIX}*{self.RULE_SUFFIX}"
            for rule_file in self.user_rules_dir.glob(pattern):
                # hookify.<name>.local.md: strip both ends, not just the
                # prefix, or the ".local" tail keeps the name from ever
                # matching its bundled entry.
                name = rule_file.name[len(self.RULE_PREFIX) : -len(self.RULE_SUFFIX)]

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
