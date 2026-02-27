#!/usr/bin/env python3
"""Common utilities for Abstract scripts.

Provide utility functions for:
- Project and config discovery
- Frontmatter extraction and validation
- Skill file discovery and loading
- Analysis helpers (scoring, sections, dependencies)

For token-related utilities, use the `tokens` module directly.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from .config import AbstractConfig, SkillValidationConfig
from .frontmatter import FrontmatterProcessor

logger = logging.getLogger(__name__)

__all__ = [
    "check_meta_skill_indicators",
    "count_sections",
    "extract_dependencies",
    # Frontmatter utilities
    "extract_frontmatter",
    "find_dependency_file",
    # Project utilities
    "find_project_root",
    # Path utilities
    "get_config_dir",
    "get_log_directory",
    # Skill file utilities
    "find_skill_files",
    # Analysis utilities
    "format_score",
    "get_skill_name",
    "load_config_with_defaults",
    "load_skill_file",
    "parse_frontmatter_fields",
    "parse_yaml_frontmatter",
    "validate_skill_frontmatter",
]


def find_project_root(start_path: Path) -> Path:
    """Find the project root by walking up until we find config/ directory.

    Args:
        start_path: Path to start searching from.

    Returns:
        Path to project root directory.

    """
    current = start_path.resolve()
    while current.parent != current:
        if (current / "config").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_log_directory(*, create: bool = False) -> Path:
    """Get the skill execution log directory.

    Respects CLAUDE_HOME env var for non-standard installations.

    Args:
        create: If True, create the directory if it doesn't exist.

    Returns:
        Path to ~/.claude/skills/logs/ (or $CLAUDE_HOME/skills/logs/).

    """
    claude_home = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
    log_base = claude_home / "skills" / "logs"
    if create:
        log_base.mkdir(parents=True, exist_ok=True)
    return log_base


def get_config_dir(*, create: bool = False) -> Path:
    """Get the discussions config directory.

    Args:
        create: If True, create the directory if it doesn't exist.

    Returns:
        Path to ~/.claude/skills/discussions/.

    """
    config_dir = Path.home() / ".claude" / "skills" / "discussions"
    if create:
        config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def load_config_with_defaults(project_root: Path | None = None) -> AbstractConfig:
    """Load configuration from YAML with defaults.

    Args:
        project_root: The root directory of the project. If None, auto-detects.

    Returns:
        AbstractConfig instance.

    """
    if project_root is None:
        project_root = find_project_root(Path.cwd())

    config_file = project_root / "config" / "abstract_config.yaml"

    if config_file.exists():
        try:
            return AbstractConfig.from_yaml(config_file)
        except Exception as e:
            logger.debug(f"Failed to load config from {config_file}: {e}")

    return AbstractConfig()


def extract_frontmatter(content: str) -> tuple[str, str]:
    """Extract frontmatter and body from skill content.

    Delegates to FrontmatterProcessor.extract_raw() for consistent behavior.

    Args:
        content: The full skill file content.

    Returns:
        Tuple of (frontmatter, body).

    """
    return FrontmatterProcessor.extract_raw(content)


def parse_frontmatter_fields(frontmatter: str) -> dict[str, str]:
    """Parse YAML frontmatter into a dictionary of fields.

    Note: For full YAML parsing with proper type handling, use
    FrontmatterProcessor.parse() instead. This function does simple
    line-based parsing for backwards compatibility.

    Args:
        frontmatter: The frontmatter string (including --- markers).

    Returns:
        Dictionary of field names to string values.

    """
    fields = {}
    # Remove --- markers
    content = frontmatter.strip().strip("-").strip()

    for line in content.split("\n"):
        if ":" in line and not line.strip().startswith("-"):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()

    return fields


def validate_skill_frontmatter(
    content: str,
    config: SkillValidationConfig,
) -> list[str]:
    """Validate skill frontmatter fields.

    Delegates to FrontmatterProcessor for consistent parsing and validation.

    Args:
        content: The skill file content.
        config: Validation configuration.

    Returns:
        List of validation issues (empty if valid).

    """
    issues = []

    # Use FrontmatterProcessor for parsing
    result = FrontmatterProcessor.parse(
        content,
        required_fields=config.REQUIRED_FRONTMATTER_FIELDS,
    )

    if result.parse_error:
        if "Missing frontmatter" in result.parse_error:
            issues.append("ERROR: Missing frontmatter")
        elif "Incomplete frontmatter" in result.parse_error:
            issues.append("ERROR: Incomplete frontmatter")
        else:
            issues.append(f"ERROR: {result.parse_error}")
        return issues

    # Check required fields
    for field in result.missing_fields:
        issues.append(f"ERROR: Missing required frontmatter field: {field}")

    # Check recommended fields
    missing_recommended = FrontmatterProcessor.check_missing_recommended(
        result.parsed,
        config.RECOMMENDED_FRONTMATTER_FIELDS,
    )
    if missing_recommended:
        issues.append(
            "INFO: Consider adding recommended fields: "
            f"{', '.join(sorted(missing_recommended))}",
        )

    return issues


def check_meta_skill_indicators(
    content: str,
    config: SkillValidationConfig,
    skill_name: str,
) -> str | None:
    """Check if skill has meta-skill indicators.

    Args:
        content: The skill content (without frontmatter).
        config: Validation configuration.
        skill_name: Name of the skill directory.

    Returns:
        Warning message if no indicators found, None otherwise.

    """
    meta_indicators = config.META_INDICATORS or []
    meta_exceptions = config.META_SKILL_EXCEPTIONS or []
    has_meta_indicator = any(
        re.search(rf"\b{indicator}\b", content, re.IGNORECASE)
        for indicator in meta_indicators
    )

    if not has_meta_indicator and skill_name not in meta_exceptions:
        return "WARNING: Should have meta-skill indicators"

    return None


def find_skill_files(directory: Path) -> list[Path]:
    """Find all SKILL.md files in a directory recursively.

    Args:
        directory: Directory to search.

    Returns:
        List of paths to SKILL.md files, sorted by path.

    """
    if not directory.exists():
        return []
    return sorted(directory.rglob("SKILL.md"))


def parse_yaml_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from skill content (full YAML parsing).

    Delegates to FrontmatterProcessor.parse() for consistent behavior.

    Args:
        content: The skill file content.

    Returns:
        Dictionary of frontmatter fields, empty dict if no frontmatter.

    """
    result = FrontmatterProcessor.parse(content, required_fields=[])
    return result.parsed


def load_skill_file(skill_path: Path) -> tuple[str, dict]:
    """Load a skill file and parse its frontmatter.

    Delegates to FrontmatterProcessor.parse_file() for file reading.

    Args:
        skill_path: Path to SKILL.md file.

    Returns:
        Tuple of (content, frontmatter_dict).

    Raises:
        FileNotFoundError: If skill file doesn't exist.

    """
    if not skill_path.exists():
        msg = f"Skill not found: {skill_path}"
        raise FileNotFoundError(msg)

    content = skill_path.read_text()
    result = FrontmatterProcessor.parse(content, required_fields=[])

    return content, result.parsed


def get_skill_name(frontmatter: dict, skill_path: Path) -> str:
    """Get skill name from frontmatter or filename.

    Args:
        frontmatter: Parsed frontmatter dictionary.
        skill_path: Path to skill file.

    Returns:
        Skill name string.

    """
    name = frontmatter.get("name", skill_path.stem)
    return str(name)


def format_score(score: float, max_score: float = 100) -> str:
    """Format a score for display.

    Args:
        score: The score value.
        max_score: Maximum possible score.

    Returns:
        Formatted score string (e.g., "85.0/100").

    """
    return f"{score:.1f}/{max_score}"


def count_sections(content: str, level: int = 1) -> int:
    """Count markdown sections at a specific heading level.

    Args:
        content: Markdown content.
        level: Heading level (1 for #, 2 for ##, etc).

    Returns:
        Number of sections found.

    """
    pattern = rf"^{'#' * level}\s+"
    return len(re.findall(pattern, content, re.MULTILINE))


def extract_dependencies(frontmatter: dict) -> list[str]:
    """Extract dependencies from frontmatter.

    Args:
        frontmatter: Parsed frontmatter dictionary.

    Returns:
        List of dependency names.

    """
    deps = frontmatter.get("dependencies", [])
    if isinstance(deps, list):
        return deps
    if isinstance(deps, str):
        return [d.strip() for d in deps.split(",") if d.strip()]
    return []


def find_dependency_file(skill_path: Path, dependency_name: str) -> Path | None:
    """Find the SKILL.md file for a dependency.

    Args:
        skill_path: Path to the skill file that has the dependency.
        dependency_name: Name of the dependency to find.

    Returns:
        Path to dependency SKILL.md if found, None otherwise.

    """
    search_paths = [
        skill_path.parent / f"{dependency_name}.md",
        skill_path.parent / dependency_name / "SKILL.md",
        skill_path.parent.parent / "skills" / dependency_name / "SKILL.md",
        skill_path.parent.parent / dependency_name / "SKILL.md",
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None
