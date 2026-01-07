#!/usr/bin/env python3
"""Consolidated frontmatter processing for Abstract.

Provide the single source of truth for all frontmatter operations:
- Parsing: Extract and parse YAML frontmatter from markdown content
- Validation: Check for required and recommended fields
- Access: Provide clean interfaces for frontmatter data
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class FrontmatterResult:
    """Result of frontmatter parsing operation.

    Attributes:
        raw: The raw frontmatter string including delimiters (--- ... ---).
        parsed: Dictionary of parsed YAML fields. Empty dict if parsing failed.
        body: The content after the frontmatter.
        is_valid: True if frontmatter exists and has valid structure.
        missing_fields: List of required fields that are missing.
        parse_error: Error message if YAML parsing failed, None otherwise.

    """

    raw: str
    parsed: dict
    body: str
    is_valid: bool
    missing_fields: list[str] = field(default_factory=list)
    parse_error: str | None = None


class FrontmatterProcessor:
    """Single source of truth for frontmatter parsing and validation.

    Consolidate all frontmatter handling logic that was previously
    scattered across multiple modules:
    - src/abstract/base.py (check_frontmatter_exists, extract_frontmatter)
    - src/abstract/utils.py (extract_frontmatter, parse_frontmatter_fields,
      validate_skill_frontmatter, parse_yaml_frontmatter)
    - scripts/check_frontmatter.py (has_yaml_frontmatter)
    """

    # Default required fields for skill files
    DEFAULT_REQUIRED_FIELDS = ["name", "description"]

    # Default recommended fields for skill files
    DEFAULT_RECOMMENDED_FIELDS = ["category", "tags", "dependencies", "tools"]

    # Claude Code 2.1.0+ optional fields for skills
    CLAUDE_CODE_210_SKILL_FIELDS = [
        "context",  # "fork" for forked sub-agent context
        "agent",  # Agent type for skill execution
        "user-invocable",  # Boolean: visibility in slash command menu
        "hooks",  # PreToolUse/PostToolUse/Stop lifecycle hooks
        "allowed-tools",  # YAML-style list or comma-separated string
        "model",  # Model override for this skill
    ]

    # Claude Code 2.1.0+ optional fields for agents
    CLAUDE_CODE_210_AGENT_FIELDS = [
        "hooks",  # PreToolUse/PostToolUse/Stop lifecycle hooks
        "skills",  # Skills to auto-load (NOT inherited from parent)
        "escalation",  # Model escalation configuration
        "permissionMode",  # Permission handling mode
    ]

    # Valid hook event types
    VALID_HOOK_EVENTS = [
        "PreToolUse",
        "PostToolUse",
        "UserPromptSubmit",
        "PermissionRequest",
        "Notification",
        "Stop",
        "SubagentStop",
        "PreCompact",
        "SessionStart",
        "SessionEnd",
    ]

    # Valid permission modes
    VALID_PERMISSION_MODES = [
        "default",
        "acceptEdits",
        "dontAsk",
        "bypassPermissions",
        "plan",
        "ignore",
    ]

    @staticmethod
    def has_frontmatter(content: str) -> bool:
        """Check if content has valid frontmatter delimiters.

        Args:
            content: File content to check.

        Returns:
            True if valid frontmatter structure exists, False otherwise.

        """
        if not content.startswith("---\n"):
            return False

        # Find closing delimiter after the opening
        closing_pos = content.find("\n---", 4)
        return closing_pos != -1

    @staticmethod
    def parse(
        content: str,
        required_fields: list[str] | None = None,
    ) -> FrontmatterResult:
        """Parse frontmatter from content.

        This is the primary method for extracting and parsing frontmatter.
        It handles both the structural extraction and YAML parsing in one call.

        Args:
            content: The full file content.
            required_fields: List of fields that must be present.
                Defaults to DEFAULT_REQUIRED_FIELDS if None.

        Returns:
            FrontmatterResult with parsed data and validation info.

        """
        if required_fields is None:
            required_fields = FrontmatterProcessor.DEFAULT_REQUIRED_FIELDS

        # Check for valid frontmatter structure
        if not content.startswith("---\n"):
            return FrontmatterResult(
                raw="",
                parsed={},
                body=content,
                is_valid=False,
                missing_fields=list(required_fields),
                parse_error="Missing frontmatter: content does not start with ---",
            )

        # Find closing delimiter
        closing_pos = content.find("\n---", 4)
        if closing_pos == -1:
            return FrontmatterResult(
                raw=content,
                parsed={},
                body="",
                is_valid=False,
                missing_fields=list(required_fields),
                parse_error="Incomplete frontmatter: missing closing ---",
            )

        # Extract raw frontmatter (with delimiters) and body
        raw_frontmatter = content[: closing_pos + 4]
        body = content[closing_pos + 4 :].lstrip("\n")

        # Extract YAML content (without delimiters)
        yaml_content = content[4:closing_pos].strip()

        # Parse YAML
        try:
            parsed = yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError as e:
            return FrontmatterResult(
                raw=raw_frontmatter,
                parsed={},
                body=body,
                is_valid=False,
                missing_fields=list(required_fields),
                parse_error=f"YAML parsing error: {e}",
            )

        # Validate required fields
        missing = FrontmatterProcessor.validate(parsed, required_fields)

        return FrontmatterResult(
            raw=raw_frontmatter,
            parsed=parsed,
            body=body,
            is_valid=len(missing) == 0,
            missing_fields=missing,
            parse_error=None,
        )

    @staticmethod
    def validate(frontmatter: dict, required_fields: list[str]) -> list[str]:
        """Validate frontmatter against required fields.

        Args:
            frontmatter: Parsed frontmatter dictionary.
            required_fields: List of field names that must be present and non-empty.

        Returns:
            List of missing field names. Empty list if all required fields present.

        """
        missing = []
        for field_name in required_fields:
            if field_name not in frontmatter:
                missing.append(field_name)
            elif not frontmatter[field_name]:
                # Field exists but is empty/None
                missing.append(field_name)
        return missing

    @staticmethod
    def extract_raw(content: str) -> tuple[str, str]:
        """Extract raw frontmatter and body without parsing.

        This is a lightweight method when you just need to separate
        frontmatter from body without YAML parsing overhead.

        Args:
            content: Full file content.

        Returns:
            Tuple of (raw_frontmatter, body).
            Returns ("", content) if no frontmatter found.

        """
        if not FrontmatterProcessor.has_frontmatter(content):
            return "", content

        closing_pos = content.find("\n---", 4)
        raw_frontmatter = content[: closing_pos + 4]
        body = content[closing_pos + 4 :].lstrip("\n")

        return raw_frontmatter, body

    @staticmethod
    def get_field(
        content: str,
        field_name: str,
        default: str | None = None,
    ) -> str | None:
        """Get a single field value from frontmatter.

        Convenience method for when you only need one field.

        Args:
            content: Full file content.
            field_name: Name of the field to retrieve.
            default: Default value if field not found.

        Returns:
            Field value or default.

        """
        result = FrontmatterProcessor.parse(content, required_fields=[])
        return result.parsed.get(field_name, default)

    @staticmethod
    def parse_file(
        file_path: Path,
        required_fields: list[str] | None = None,
    ) -> FrontmatterResult:
        """Parse frontmatter from a file.

        Convenience method that handles file reading.

        Args:
            file_path: Path to the file.
            required_fields: List of required fields for validation.

        Returns:
            FrontmatterResult with parsed data.

        Raises:
            FileNotFoundError: If file doesn't exist.
            UnicodeDecodeError: If file encoding is invalid.

        """
        content = file_path.read_text(encoding="utf-8")
        return FrontmatterProcessor.parse(content, required_fields)

    @staticmethod
    def check_missing_recommended(
        frontmatter: dict,
        recommended_fields: list[str] | None = None,
    ) -> list[str]:
        """Check for missing recommended (non-required) fields.

        Args:
            frontmatter: Parsed frontmatter dictionary.
            recommended_fields: List of recommended field names.
                Defaults to DEFAULT_RECOMMENDED_FIELDS if None.

        Returns:
            List of missing recommended field names.

        """
        if recommended_fields is None:
            recommended_fields = FrontmatterProcessor.DEFAULT_RECOMMENDED_FIELDS

        return [f for f in recommended_fields if f not in frontmatter]

    @staticmethod
    def validate_210_fields(frontmatter: dict) -> list[str]:
        """Validate Claude Code 2.1.0+ specific frontmatter fields.

        Validates:
        - context: Must be "fork" if present
        - user-invocable: Must be boolean if present
        - hooks: Must have valid structure if present
        - permissionMode: Must be valid value if present

        Args:
            frontmatter: Parsed frontmatter dictionary.

        Returns:
            List of validation error messages. Empty if all valid.

        """
        errors: list[str] = []

        # Validate individual fields using helper methods
        errors.extend(FrontmatterProcessor._validate_context(frontmatter))
        errors.extend(FrontmatterProcessor._validate_user_invocable(frontmatter))
        errors.extend(FrontmatterProcessor._validate_hooks(frontmatter))
        errors.extend(FrontmatterProcessor._validate_permission_mode(frontmatter))
        errors.extend(FrontmatterProcessor._validate_allowed_tools(frontmatter))

        return errors

    @staticmethod
    def _validate_context(frontmatter: dict) -> list[str]:
        """Validate context field."""
        errors: list[str] = []
        if "context" in frontmatter:
            if frontmatter["context"] != "fork":
                errors.append(
                    f"Invalid 'context' value: {frontmatter['context']}. "
                    "Only 'fork' is supported."
                )
        return errors

    @staticmethod
    def _validate_user_invocable(frontmatter: dict) -> list[str]:
        """Validate user-invocable field."""
        errors: list[str] = []
        if "user-invocable" in frontmatter:
            if not isinstance(frontmatter["user-invocable"], bool):
                type_name = type(frontmatter["user-invocable"]).__name__
                errors.append(f"'user-invocable' must be boolean, got: {type_name}")
        return errors

    @staticmethod
    def _validate_hooks(frontmatter: dict) -> list[str]:
        """Validate hooks structure."""
        errors: list[str] = []
        if "hooks" not in frontmatter:
            return errors

        hooks = frontmatter["hooks"]
        if not isinstance(hooks, dict):
            type_name = type(hooks).__name__
            errors.append(f"'hooks' must be a dictionary, got: {type_name}")
            return errors

        for event_type in hooks:
            if event_type not in FrontmatterProcessor.VALID_HOOK_EVENTS:
                valid_types = ", ".join(FrontmatterProcessor.VALID_HOOK_EVENTS)
                errors.append(
                    f"Invalid hook event type: {event_type}. Valid types: {valid_types}"
                )
            else:
                errors.extend(
                    FrontmatterProcessor._validate_hook_entries(
                        event_type, hooks[event_type]
                    )
                )

        return errors

    @staticmethod
    def _validate_hook_entries(event_type: str, hook_entries: list) -> list[str]:
        """Validate hook entries for a specific event type."""
        errors: list[str] = []

        if not isinstance(hook_entries, list):
            errors.append(f"Hook entries for '{event_type}' must be a list")
            return errors

        for i, entry in enumerate(hook_entries):
            if not isinstance(entry, dict):
                errors.append(f"Hook entry {i} for '{event_type}' must be a dict")
            elif "command" not in entry:
                errors.append(f"Hook entry {i} for '{event_type}' missing 'command'")

            # Validate 'once' field if present
            if isinstance(entry, dict) and "once" in entry:
                if not isinstance(entry["once"], bool):
                    errors.append(
                        f"Hook entry {i} for '{event_type}': 'once' must be boolean"
                    )

        return errors

    @staticmethod
    def _validate_permission_mode(frontmatter: dict) -> list[str]:
        """Validate permissionMode field."""
        errors: list[str] = []
        if "permissionMode" in frontmatter:
            mode = frontmatter["permissionMode"]
            valid_modes = FrontmatterProcessor.VALID_PERMISSION_MODES
            if mode not in valid_modes:
                modes_str = ", ".join(valid_modes)
                errors.append(
                    f"Invalid 'permissionMode': {mode}. Valid modes: {modes_str}"
                )
        return errors

    @staticmethod
    def _validate_allowed_tools(frontmatter: dict) -> list[str]:
        """Validate allowed-tools field."""
        errors: list[str] = []
        if "allowed-tools" in frontmatter:
            tools = frontmatter["allowed-tools"]
            if not isinstance(tools, list | str):
                type_name = type(tools).__name__
                errors.append(
                    f"'allowed-tools' must be a list or string, got: {type_name}"
                )
        return errors

    @staticmethod
    def has_210_features(frontmatter: dict) -> bool:
        """Check if frontmatter uses any Claude Code 2.1.0+ features.

        Args:
            frontmatter: Parsed frontmatter dictionary.

        Returns:
            True if any 2.1.0+ fields are present.

        """
        all_210_fields = (
            FrontmatterProcessor.CLAUDE_CODE_210_SKILL_FIELDS
            + FrontmatterProcessor.CLAUDE_CODE_210_AGENT_FIELDS
        )
        return any(f in frontmatter for f in all_210_fields)
