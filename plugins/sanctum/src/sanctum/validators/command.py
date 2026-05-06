"""Command markdown file validator (AR-06)."""

from __future__ import annotations

import re
from pathlib import Path

from ._frontmatter import parse_frontmatter
from ._results import CommandValidationResult
from ._shared import _extract_skill_refs_from_content  # AR-F3


class CommandValidator:
    """Validator for command markdown files."""

    @staticmethod
    def parse_frontmatter(content: str) -> CommandValidationResult:
        """Parse and validate command frontmatter."""
        errors: list[str] = []
        warnings: list[str] = []
        command_name = None
        description = None

        # Check for frontmatter
        has_frontmatter = content.strip().startswith("---")
        if not has_frontmatter:
            errors.append("Missing YAML frontmatter")
            return CommandValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                command_name=None,
                has_description=False,
                description=None,
            )

        # Parse frontmatter
        frontmatter = parse_frontmatter(content)
        if frontmatter is None:
            errors.append("Invalid YAML frontmatter")
            return CommandValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                command_name=None,
                has_description=False,
                description=None,
            )

        # Extract description (required)
        description = frontmatter.get("description")
        if not description:
            errors.append("Missing 'description' field in frontmatter")

        # Extract command name from heading
        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if heading_match:
            command_name = heading_match.group(1).strip()

        return CommandValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            command_name=command_name,
            has_description=description is not None,
            description=description,
        )

    @staticmethod
    def validate_content(content: str) -> CommandValidationResult:
        """Validate command markdown content."""
        result = CommandValidator.parse_frontmatter(content)
        warnings = list(result.warnings)

        # Check for main heading
        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if not heading_match:
            warnings.append("Missing main heading in command body")

        # Check for usage section
        has_usage = bool(
            re.search(
                r"^##\s+(Usage|Arguments|Options)",
                content,
                re.MULTILINE | re.IGNORECASE,
            ),
        )
        if not has_usage:
            warnings.append("Missing usage section")

        return CommandValidationResult(
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=warnings,
            command_name=result.command_name,
            has_description=result.has_description,
            has_usage=has_usage,
            description=result.description,
        )

    @staticmethod
    def validate_file(path: Path) -> CommandValidationResult:
        """Validate command file from disk."""
        path = Path(path)

        if not path.exists():
            return CommandValidationResult(
                is_valid=False,
                errors=["File not found: " + str(path)],
                command_name=path.stem,
            )

        content = path.read_text()
        result = CommandValidator.validate_content(content)

        if result.command_name is None:
            result.command_name = path.stem

        return result

    @staticmethod
    def extract_skill_references(content: str) -> list[str]:
        """Extract skill references from command content."""
        return _extract_skill_refs_from_content(content)

    @staticmethod
    def validate_skill_references(
        content: str,
        plugin_path: Path,
    ) -> CommandValidationResult:
        """Validate that referenced skills exist in the plugin."""
        errors: list[str] = []
        warnings: list[str] = []

        refs = CommandValidator.extract_skill_references(content)
        skills_dir = plugin_path / "skills"

        for ref in refs:
            skill_dir = skills_dir / ref
            if not skill_dir.exists():
                # It might be a different plugin reference
                if ":" not in ref:
                    warnings.append(f"Referenced skill '{ref}' not found locally")

        # Parse for command name
        frontmatter = parse_frontmatter(content)
        description = frontmatter.get("description") if frontmatter else None

        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        command_name = heading_match.group(1).strip() if heading_match else None

        return CommandValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            command_name=command_name,
            has_description=description is not None,
            description=description,
        )
