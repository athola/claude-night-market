"""Skill markdown file validator (AR-06)."""

from __future__ import annotations

import re
from pathlib import Path

from ._frontmatter import parse_frontmatter
from ._results import SkillValidationResult


def _extract_skill_refs_from_content(content: str) -> list[str]:
    """Extract skill references from content (shared helper).

    Finds all ``Skill(plugin:skill-name)`` patterns and returns the
    skill name portion (after the colon when present).
    """
    refs: list[str] = []
    matches = re.findall(r"Skill\(([^)]+)\)", content)
    for match in matches:
        if ":" in match:
            refs.append(match.split(":")[1])
        else:
            refs.append(match)
    return refs


class SkillValidator:
    """Validator for skill markdown files."""

    @staticmethod
    def parse_frontmatter(content: str) -> SkillValidationResult:
        """Parse and validate skill frontmatter."""
        errors: list[str] = []
        warnings: list[str] = []
        skill_name = None
        frontmatter = None

        # Check for frontmatter
        has_frontmatter = content.strip().startswith("---")
        if not has_frontmatter:
            errors.append("Missing YAML frontmatter")
            return SkillValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                skill_name=None,
                has_frontmatter=False,
                frontmatter=None,
            )

        # Parse frontmatter
        frontmatter = parse_frontmatter(content)
        if frontmatter is None:
            errors.append("Invalid YAML frontmatter")
            return SkillValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                skill_name=None,
                has_frontmatter=True,
                frontmatter=None,
            )

        # Validate required fields
        skill_name = frontmatter.get("name")
        if not skill_name:
            errors.append("Missing 'name' field in frontmatter")

        if not frontmatter.get("description"):
            errors.append("Missing 'description' field in frontmatter")

        # Validate recommended fields (warnings)
        if not frontmatter.get("category"):
            warnings.append("Missing 'category' field in frontmatter")

        if not frontmatter.get("tags"):
            warnings.append("Missing 'tags' field in frontmatter")

        if not frontmatter.get("tools"):
            warnings.append("Missing 'tools' field in frontmatter")

        # Check for workflow section
        has_workflow = bool(
            re.search(
                r"^##\s+(Workflow|When to Use|Steps)",
                content,
                re.MULTILINE | re.IGNORECASE,
            ),
        )

        return SkillValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            skill_name=skill_name,
            has_frontmatter=True,
            has_workflow=has_workflow,
            frontmatter=frontmatter,
        )

    @staticmethod
    def validate_content(content: str) -> SkillValidationResult:
        """Validate skill markdown content."""
        result = SkillValidator.parse_frontmatter(content)

        # Additional content validation
        warnings = list(result.warnings)

        # Check for main heading
        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if not heading_match:
            warnings.append("Missing main heading in skill body")

        # Check for When to Use section
        if not re.search(r"^##\s+When to Use", content, re.MULTILINE | re.IGNORECASE):
            warnings.append("Missing 'When to Use' section")

        return SkillValidationResult(
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=warnings,
            skill_name=result.skill_name,
            has_frontmatter=result.has_frontmatter,
            has_workflow=result.has_workflow,
            frontmatter=result.frontmatter,
        )

    @staticmethod
    def validate_file(path: Path) -> SkillValidationResult:
        """Validate skill file from disk."""
        path = Path(path)

        if not path.exists():
            return SkillValidationResult(
                is_valid=False,
                errors=["File not found: " + str(path)],
                skill_name=path.stem,
            )

        content = path.read_text()
        result = SkillValidator.validate_content(content)

        if result.skill_name is None:
            result.skill_name = path.stem

        return result

    @staticmethod
    def validate_directory(path: Path) -> SkillValidationResult:
        """Validate a skill directory containing SKILL.md."""
        path = Path(path)

        if not path.is_dir():
            return SkillValidationResult(
                is_valid=False,
                errors=[f"Not a directory: {path}"],
                skill_name=path.name,
            )

        skill_file = path / "SKILL.md"
        if not skill_file.exists():
            return SkillValidationResult(
                is_valid=False,
                errors=["Missing SKILL.md file in skill directory"],
                skill_name=path.name,
            )

        return SkillValidator.validate_file(skill_file)

    @staticmethod
    def validate_references(content: str) -> SkillValidationResult:
        """Validate skill references in content."""
        errors: list[str] = []
        warnings: list[str] = []

        # Find all Skill() references
        refs = re.findall(r"Skill\(([^)]+)\)", content)
        for ref in refs:
            # Valid format: plugin:skill-name or just skill-name
            if not re.match(r"^[\w-]+(:[\w-]+)?$", ref):
                warnings.append(f"Potentially invalid skill reference format: {ref}")

        # Parse frontmatter to get skill name
        frontmatter = parse_frontmatter(content)
        skill_name = frontmatter.get("name") if frontmatter else None

        return SkillValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            skill_name=skill_name,
            has_frontmatter=frontmatter is not None,
            frontmatter=frontmatter,
        )

    @staticmethod
    def extract_skill_references(content: str) -> list[str]:
        """Extract skill references from content.

        Uses the shared regex helper and additionally checks
        frontmatter ``dependencies`` for skill-level refs.
        """
        refs = _extract_skill_refs_from_content(content)

        # Also check frontmatter dependencies
        frontmatter = parse_frontmatter(content)
        if frontmatter and "dependencies" in frontmatter:
            deps = frontmatter["dependencies"]
            if isinstance(deps, list):
                refs.extend(deps)

        return refs

    @staticmethod
    def extract_dependencies(content: str) -> list[str]:
        """Extract skill dependencies from content."""
        deps = []
        deps_match = re.search(
            r"^##\s+Dependencies\s*\n((?:[-*]\s+.+\n?)+)",
            content,
            re.MULTILINE | re.IGNORECASE,
        )
        if deps_match:
            deps_section = deps_match.group(1)
            for line in deps_section.split("\n"):
                match = re.match(r"^[-*]\s+(.+)", line)
                if match:
                    deps.append(match.group(1).strip())
        return deps
