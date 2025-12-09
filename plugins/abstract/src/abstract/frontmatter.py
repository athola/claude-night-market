#!/usr/bin/env python3
"""Consolidated frontmatter processing for Abstract.

This module provides the single source of truth for all frontmatter operations:
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

    This class consolidates all frontmatter handling logic that was previously
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
