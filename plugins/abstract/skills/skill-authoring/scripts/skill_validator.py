#!/usr/bin/env python3
"""Skill Validator

Validates Claude Code skill structure, frontmatter, and content quality.

Exit codes:
    0 - Success, no issues
    1 - Warnings present (non-critical)
    2 - Errors found (must fix)

Usage:
    python skill_validator.py [--path PATH] [--strict]
    python skill_validator.py --help
"""

import argparse
import re
import sys
from pathlib import Path

# Constants for magic numbers
MAX_ESTIMATED_TOKENS = 5000
MIN_DESCRIPTION_LENGTH = 100
MIN_OPTIMAL_DESCRIPTION = 200
MAX_OPTIMAL_DESCRIPTION = 400
MIN_DESCRIPTION_WORDS = 15

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def add_error(self, message: str) -> None:
        """Add a critical error."""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a non-critical warning."""
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        """Add informational message."""
        self.info.append(message)

    @property
    def has_errors(self) -> bool:
        """Check if any errors exist."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings exist."""
        return len(self.warnings) > 0

    def exit_code(self) -> int:
        """Determine appropriate exit code."""
        if self.has_errors:
            return 2
        if self.has_warnings:
            return 1
        return 0


class SkillValidator:
    """Validates Claude Code skill files."""

    MAX_NAME_LENGTH = 64
    MAX_DESC_LENGTH = 1024
    MAX_SKILL_LINES = 500
    MAX_MODULE_LINES = 400
    MIN_MODULE_LINES = 100

    # Third person indicators (skills should use these)
    THIRD_PERSON_VERBS = {
        "guides",
        "teaches",
        "provides",
        "implements",
        "analyzes",
        "validates",
        "enforces",
        "ensures",
        "prevents",
        "detects",
        "optimizes",
        "automates",
        "generates",
        "manages",
        "coordinates",
    }

    # First person indicators (skills should NOT use these)
    FIRST_PERSON_PATTERNS = [
        r"\bI\s+",
        r"\bwe\s+",
        r"\bour\s+",
        r"\bmy\s+",
        r"\byou\s+",  # Direct address
        r"\byour\s+",
        r"help(s)?\s+you",
        r"let(s)?\s+you",
    ]

    def __init__(self, skill_path: Path, strict: bool = False):
        """Initialize validator.

        Args:
            skill_path: Path to SKILL.md file
            strict: Treat warnings as errors

        """
        self.skill_path = skill_path
        self.skill_dir = skill_path.parent
        self.strict = strict
        self.result = ValidationResult()

    def validate(self) -> ValidationResult:
        """Run all validation checks.

        Returns:
            ValidationResult with errors, warnings, and info

        """
        # Structure checks
        self._check_file_exists()
        if not self.skill_path.exists():
            return self.result

        # Content checks
        content = self._read_file()
        if content is None:
            return self.result

        frontmatter, body = self._extract_frontmatter(content)

        # Frontmatter validation
        if frontmatter:
            self._validate_frontmatter(frontmatter)
        else:
            self.result.add_error("YAML frontmatter missing or invalid")

        # Body validation
        if body:
            self._validate_body(body)
            self._validate_line_count(body)
            self._check_module_references(body)

        # Module validation (if modules exist)
        self._validate_modules()

        return self.result

    def _check_file_exists(self) -> None:
        """Check if SKILL.md exists."""
        if not self.skill_path.exists():
            self.result.add_error(f"SKILL.md not found at {self.skill_path}")
        elif self.skill_path.name != "SKILL.md":
            self.result.add_warning(
                f"File should be named 'SKILL.md', got '{self.skill_path.name}'"
            )

    def _read_file(self) -> str | None:
        """Read skill file content."""
        try:
            return self.skill_path.read_text(encoding="utf-8")
        except Exception as e:
            self.result.add_error(f"Failed to read file: {e}")
            return None

    def _extract_frontmatter(self, content: str) -> tuple[dict | None, str | None]:
        """Extract YAML frontmatter and body.

        Returns:
            (frontmatter_dict, body_content)

        """
        # Match YAML frontmatter: ---\n...\n---
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            self.result.add_error(
                "YAML frontmatter not found (expected ---\\n...\\n---)"
            )
            return None, content

        yaml_text = match.group(1)
        body = match.group(2)

        try:
            frontmatter = yaml.safe_load(yaml_text)
            return frontmatter, body
        except yaml.YAMLError as e:
            self.result.add_error(f"YAML parsing failed: {e}")
            return None, body

    def _validate_frontmatter(self, fm: dict) -> None:
        """Validate YAML frontmatter fields."""
        # Required fields
        required = [
            "name",
            "description",
            "version",
            "category",
            "tags",
            "estimated_tokens",
        ]

        for field in required:
            if field not in fm:
                self.result.add_error(f"Required field missing: {field}")

        # Name validation
        if "name" in fm:
            self._validate_name(fm["name"])

        # Description validation
        if "description" in fm:
            self._validate_description(fm["description"])

        # Version validation
        if "version" in fm:
            self._validate_version(fm["version"])

        # Category validation
        if "category" in fm:
            if not isinstance(fm["category"], str) or not fm["category"].strip():
                self.result.add_error("Category must be non-empty string")

        # Tags validation
        if "tags" in fm:
            if not isinstance(fm["tags"], list):
                self.result.add_error("Tags must be a list")
            elif len(fm["tags"]) == 0:
                self.result.add_warning("No tags specified (affects discoverability)")

        # Estimated tokens validation
        if "estimated_tokens" in fm:
            if not isinstance(fm["estimated_tokens"], int):
                self.result.add_error("estimated_tokens must be an integer")
            elif fm["estimated_tokens"] <= 0:
                self.result.add_error("estimated_tokens must be positive")
            elif fm["estimated_tokens"] > MAX_ESTIMATED_TOKENS:
                self.result.add_warning(
                    f"estimated_tokens very high ({fm['estimated_tokens']}). "
                    "Consider modularization."
                )

        # Dependencies (optional but validate if present)
        if "dependencies" in fm:
            if not isinstance(fm["dependencies"], list):
                self.result.add_error("dependencies must be a list")

    def _validate_name(self, name: str) -> None:
        """Validate skill name."""
        if not isinstance(name, str):
            self.result.add_error("Name must be a string")
            return

        # Length check
        if len(name) > self.MAX_NAME_LENGTH:
            self.result.add_error(
                f"Name too long: {len(name)} chars (max {self.MAX_NAME_LENGTH})"
            )

        # Format check: lowercase, numbers, hyphens only
        if not re.match(r"^[a-z0-9-]+$", name):
            self.result.add_error(
                "Name must be lowercase letters, numbers, and hyphens only"
            )

        # No leading/trailing hyphens
        if name.startswith("-") or name.endswith("-"):
            self.result.add_error("Name cannot start or end with hyphen")

        # No consecutive hyphens
        if "--" in name:
            self.result.add_warning("Name contains consecutive hyphens")

    def _validate_description(self, desc: str) -> None:
        """Validate skill description."""
        if not isinstance(desc, str):
            self.result.add_error("Description must be a string")
            return

        # Length check
        if len(desc) > self.MAX_DESC_LENGTH:
            self.result.add_error(
                f"Description too long: {len(desc)} chars (max {self.MAX_DESC_LENGTH})"
            )

        if len(desc) < MIN_DESCRIPTION_LENGTH:
            msg = (
                f"Description short ({len(desc)} chars). "
                f"Consider {MIN_OPTIMAL_DESCRIPTION}-{MAX_OPTIMAL_DESCRIPTION} "
                "for better discovery."
            )
            self.result.add_warning(msg)
        elif MIN_OPTIMAL_DESCRIPTION <= len(desc) <= MAX_OPTIMAL_DESCRIPTION:
            self.result.add_info("Description length optimal (200-400 chars)")

        # Third person check
        first_sentence = desc.split(".")[0].lower()

        # Check for first person patterns
        has_first_person = any(
            re.search(pattern, first_sentence, re.IGNORECASE)
            for pattern in self.FIRST_PERSON_PATTERNS
        )

        if has_first_person:
            self.result.add_error(
                "Description uses first/second person. Use third person "
                "(e.g., 'Guides...', 'Teaches...', 'Provides...')"
            )

        # Check for third person verbs
        has_third_person = any(
            verb in first_sentence for verb in self.THIRD_PERSON_VERBS
        )

        if not has_third_person and not has_first_person:
            self.result.add_warning(
                "Description doesn't start with common third-person verb "
                f"(e.g., {', '.join(list(self.THIRD_PERSON_VERBS)[:5])})"
            )

        # "Use when" clause check
        if "use when" not in desc.lower():
            self.result.add_warning(
                "Description missing 'Use when...' clause (helps activation)"
            )

        # Discovery terms check
        if len(desc.split()) < MIN_DESCRIPTION_WORDS:
            self.result.add_warning(
                "Description has few words. Include more discovery terms."
            )

    def _validate_version(self, version: str) -> None:
        """Validate version follows semver."""
        if not isinstance(version, str):
            self.result.add_error("Version must be a string")
            return

        # Basic semver check: X.Y.Z
        if not re.match(r"^\d+\.\d+\.\d+(-[a-z0-9.]+)?$", version):
            self.result.add_error(
                f"Version '{version}' invalid. Use semver: X.Y.Z (e.g., 1.0.0)"
            )

    def _validate_body(self, body: str) -> None:
        """Validate skill body content."""
        # Check for essential sections
        required_sections = [
            ("## Overview", "Overview section"),
            ("## When to Use", "When to Use section"),
        ]

        for pattern, name in required_sections:
            if pattern not in body:
                self.result.add_warning(f"Missing recommended section: {name}")

        # Check for at least one example
        if "```" not in body:
            self.result.add_warning("No code examples found (recommended)")

        # Check for broken markdown links
        broken_refs = self._check_broken_references(body)
        for ref in broken_refs:
            self.result.add_error(f"Broken reference: {ref}")

    def _validate_line_count(self, body: str) -> None:
        """Check if SKILL.md is within line count limits."""
        lines = body.count("\n") + 1

        if lines > self.MAX_SKILL_LINES:
            self.result.add_warning(
                f"SKILL.md has {lines} lines (recommend <{self.MAX_SKILL_LINES}). "
                "Consider moving content to modules/"
            )
        else:
            self.result.add_info(f"Line count OK: {lines}/{self.MAX_SKILL_LINES}")

    def _check_broken_references(self, content: str) -> list[str]:
        """Check for broken file references in content."""
        broken = []

        # Find markdown links: [text](path)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        for match in re.finditer(link_pattern, content):
            link_path = match.group(2)

            # Skip URLs
            if link_path.startswith(("http://", "https://", "#")):
                continue

            # Check if file exists
            full_path = self.skill_dir / link_path
            if not full_path.exists():
                broken.append(link_path)

        return broken

    def _check_module_references(self, body: str) -> None:
        """Check that referenced modules exist."""
        # Find references to modules/
        module_pattern = r"`?modules/([a-z0-9-]+\.md)`?"
        referenced_modules = set(re.findall(module_pattern, body))

        modules_dir = self.skill_dir / "modules"
        if not modules_dir.exists() and referenced_modules:
            self.result.add_error(
                f"References {len(referenced_modules)} modules but "
                f"modules/ doesn't exist"
            )
            return

        if modules_dir.exists():
            existing_modules = {f.name for f in modules_dir.glob("*.md")}

            for module in referenced_modules:
                if module not in existing_modules:
                    self.result.add_error(
                        f"Referenced module not found: modules/{module}"
                    )

    def _validate_modules(self) -> None:
        """Validate module files if they exist."""
        modules_dir = self.skill_dir / "modules"
        if not modules_dir.exists():
            return

        module_files = list(modules_dir.glob("*.md"))
        if not module_files:
            self.result.add_warning("modules/ directory exists but is empty")
            return

        self.result.add_info(f"Found {len(module_files)} module(s)")

        for module_path in module_files:
            self._validate_single_module(module_path)

    def _validate_single_module(self, module_path: Path) -> None:
        """Validate a single module file."""
        try:
            content = module_path.read_text(encoding="utf-8")
            lines = content.count("\n") + 1

            # Line count check
            if lines > self.MAX_MODULE_LINES:
                self.result.add_warning(
                    f"{module_path.name}: {lines} lines "
                    f"(recommend <{self.MAX_MODULE_LINES})"
                )
            elif lines < self.MIN_MODULE_LINES:
                self.result.add_warning(
                    f"{module_path.name}: {lines} lines (might be too brief)"
                )

            # Check for broken references
            broken = self._check_broken_references(content)
            for ref in broken:
                self.result.add_error(f"{module_path.name}: Broken reference: {ref}")

        except Exception as e:
            self.result.add_error(f"Failed to read {module_path.name}: {e}")


def print_report(validator: SkillValidator, result: ValidationResult) -> None:
    """Print validation report."""
    print("\nSkill Validation Report")
    print("=" * 60)
    print(f"\nSkill: {validator.skill_path.parent.name}")
    print(f"Path: {validator.skill_path}")
    print()

    # Errors
    if result.errors:
        print("ERRORS (must fix)")
        print("-" * 60)
        for error in result.errors:
            print(f"  ✗ {error}")
        print()

    # Warnings
    if result.warnings:
        print("WARNINGS (should fix)")
        print("-" * 60)
        for warning in result.warnings:
            print(f"  ! {warning}")
        print()

    # Info
    if result.info:
        print("INFO")
        print("-" * 60)
        for info in result.info:
            print(f"  ℹ {info}")
        print()

    # Summary
    print("SUMMARY")
    print("-" * 60)
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    print()

    # Result
    exit_code = result.exit_code()
    if exit_code == 0:
        print("✓ PASS - Ready to deploy")
    elif exit_code == 1:
        print("! PASS WITH WARNINGS - Fix warnings before deployment (optional)")
    else:
        print("✗ FAIL - Must fix errors before deployment")

    print()
    print(f"Exit Code: {exit_code}")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Claude Code skill structure and content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit Codes:
  0 - Success, no issues found
  1 - Warnings present (non-critical)
  2 - Errors found (must fix before deployment)

Examples:
  # Validate skill in current directory
  python skill_validator.py

  # Validate specific skill
  python skill_validator.py --path /path/to/skill/SKILL.md

  # Strict mode (treat warnings as errors)
  python skill_validator.py --strict
        """,
    )

    parser.add_argument(
        "--path", type=Path, help="Path to SKILL.md file (default: ./SKILL.md)"
    )

    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )

    args = parser.parse_args()

    # Determine skill path
    if args.path:
        skill_path = args.path
    else:
        skill_path = Path.cwd() / "SKILL.md"

    # Validate
    validator = SkillValidator(skill_path, strict=args.strict)
    result = validator.validate()

    # Print report
    print_report(validator, result)

    # Exit with appropriate code
    exit_code = result.exit_code()
    if args.strict and result.has_warnings:
        exit_code = 2  # Treat warnings as errors in strict mode

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
