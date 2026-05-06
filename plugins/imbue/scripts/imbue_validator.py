#!/usr/bin/env python3
"""Validate Imbue plugin review workflow and evidence management skills."""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import TypedDict

# Bootstrap leyline so we can use its add_plugin_src_to_path helper
# to discover the sibling 'abstract' plugin (AR-15).
_LEYLINE_SRC = Path(__file__).resolve().parents[2] / "leyline" / "src"
if str(_LEYLINE_SRC) not in sys.path:
    sys.path.insert(0, str(_LEYLINE_SRC))

try:
    from leyline.bootstrap import add_plugin_src_to_path  # type: ignore[import-not-found]

    add_plugin_src_to_path("abstract", caller=__file__)
    from abstract.report_formatter import (  # type: ignore[import-not-found]  # cross-plugin import via sys.path
        format_validator_report,
    )
except (ImportError, FileNotFoundError):

    def format_validator_report(results: dict, plugin_name: str = "") -> str:  # type: ignore[misc]  # redefinition needed for import fallback
        """Fallback when leyline.bootstrap or abstract is not available."""
        return str(results)


# Configure logging for the validator
logger = logging.getLogger(__name__)

# Constants
FRONTMATTER_PARTS_COUNT = 3  # Expected parts when splitting by '---'


class ImbueValidationResult(TypedDict):
    """Result of imbue plugin validation."""

    skills_found: set[str]
    review_workflow_skills: set[str]
    evidence_logging_patterns: set[str]
    issues: list[str]


class ImbueValidator:
    """Validate imbue plugin review workflow and evidence management skills."""

    def __init__(self, plugin_root: Path) -> None:
        """Initialize the imbue validator.

        Args:
            plugin_root: Root directory of the imbue plugin.

        Log warnings when:
            - Plugin root directory does not exist
            - Plugin root directory exists but is empty
            - Plugin root directory lacks expected structure (skills/ or plugin.json)

        """
        self.plugin_root = plugin_root

        # Check root status and log appropriate warnings (addresses issue #34)
        self.root_exists = plugin_root.exists()
        self.root_empty = False
        self.has_valid_structure = False

        if not self.root_exists:
            logger.warning(
                "Plugin root directory does not exist: %s",
                plugin_root,
            )
            self.skill_files: list[Path] = []
            self.plugin_config = plugin_root / "plugin.json"
            return

        # Check if directory is empty
        try:
            contents = list(plugin_root.iterdir())
            self.root_empty = len(contents) == 0
        except OSError as e:
            logger.warning("Unable to read directory %s: %s", plugin_root, e)
            self.root_empty = True

        if self.root_empty:
            logger.warning(
                "Plugin root directory is empty: %s",
                plugin_root,
            )
            self.skill_files = []
            self.plugin_config = plugin_root / "plugin.json"
            return

        # Check for expected plugin structure
        skills_dir = plugin_root / "skills"
        plugin_json = plugin_root / "plugin.json"
        has_skills = skills_dir.exists() and skills_dir.is_dir()
        has_plugin_json = plugin_json.exists() and plugin_json.is_file()

        self.has_valid_structure = has_skills or has_plugin_json

        if not self.has_valid_structure:
            logger.warning(
                "Plugin root lacks expected structure "
                "(no skills/ directory or plugin.json): %s",
                plugin_root,
            )

        self.skill_files = list(plugin_root.rglob("SKILL.md"))
        self.plugin_config = plugin_json

    def scan_and_validate(self) -> tuple[ImbueValidationResult, list[str]]:
        """Scan for review workflow skills and validate in a single pass.

        Results are cached so that callers like scan_review_workflows
        and validate_review_workflows do not trigger redundant scans.
        """
        if hasattr(self, "_cached_scan_result"):
            return self._cached_scan_result
        result = self._scan_and_validate_impl()
        self._cached_scan_result: tuple[ImbueValidationResult, list[str]] = result
        return result

    def _scan_and_validate_impl(
        self,
    ) -> tuple[ImbueValidationResult, list[str]]:
        """Run the actual scan and validation pass."""
        skills_found: set[str] = set()
        review_workflow_skills: set[str] = set()
        evidence_logging_patterns: set[str] = set()
        scan_issues: list[str] = []
        validation_issues: list[str] = []

        # Load plugin configuration
        if self.plugin_config.exists():
            try:
                plugin_config_content = self.plugin_config.read_text()
                json.loads(plugin_config_content)
            except (OSError, UnicodeDecodeError) as e:
                scan_issues.append(
                    f"Unable to read plugin.json at {self.plugin_config}: {e}"
                )
            except json.JSONDecodeError as e:
                scan_issues.append(f"Invalid plugin.json at line {e.lineno}: {e.msg}")
            else:
                evidence_logging_patterns.add("review-workflows")
                evidence_logging_patterns.add("evidence-logging")
                evidence_logging_patterns.add("structured-output")
                evidence_logging_patterns.add("workflow-orchestration")

        for skill_file in self.skill_files:
            skill_name = skill_file.parent.name
            skills_found.add(skill_name)

            try:
                content = skill_file.read_text()
            except (OSError, UnicodeDecodeError) as e:
                scan_issues.append(f"{skill_name}: Unable to read {skill_file}: {e}")
                continue

            # --- Scan phase: classify skill ---
            frontmatter = None
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= FRONTMATTER_PARTS_COUNT:
                    frontmatter = parts[1]

            is_review_skill = False
            if frontmatter:
                has_review_category = re.search(
                    r"^\s*category:\s*review-patterns\b",
                    frontmatter,
                    re.MULTILINE,
                )
                has_review_usage = re.search(
                    r"^\s*-\s*review-workflow\b",
                    frontmatter,
                    re.MULTILINE,
                )
                if has_review_category or has_review_usage:
                    review_workflow_skills.add(skill_name)
                    is_review_skill = True

            if not is_review_skill:
                review_pattern = re.compile(
                    r"workflow|evidence|structured|output|orchestrat|checklist|deliverable",
                    re.IGNORECASE,
                )
                if review_pattern.search(content):
                    review_workflow_skills.add(skill_name)

            # --- Validate phase: check review workflow compliance ---
            if skill_name == "review-core":
                review_components = [
                    r"checklist",
                    r"deliverable",
                    r"evidence",
                    r"structured",
                    r"workflow",
                ]
                missing_components = [
                    component
                    for component in review_components
                    if not re.search(component, content, re.IGNORECASE)
                ]
                if missing_components:
                    missing_str = ", ".join(missing_components)
                    validation_issues.append(
                        f"{skill_name}: Missing review components: {missing_str}"
                    )

            evidence_patterns = [
                r"log",
                r"track",
                r"record",
                r"document",
                r"capture",
                r"evidence",
            ]
            has_evidence = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in evidence_patterns
            )
            if not has_evidence and skill_name not in ["review-core"]:
                validation_issues.append(
                    f"{skill_name}: Should have evidence logging patterns"
                )

        scan_result = ImbueValidationResult(
            skills_found=skills_found,
            review_workflow_skills=review_workflow_skills,
            evidence_logging_patterns=evidence_logging_patterns,
            issues=scan_issues,
        )
        return scan_result, validation_issues

    def scan_review_workflows(self) -> ImbueValidationResult:
        """Scan for review workflow skills and evidence patterns."""
        result, _ = self.scan_and_validate()
        return result

    def validate_review_workflows(self) -> list[str]:
        """Validate that skills follow review workflow patterns."""
        _, validation_issues = self.scan_and_validate()
        return validation_issues

    def generate_report(self) -> str:
        """Generate detailed validation report."""
        result, validation_issues = self.scan_and_validate()
        issues = list(dict.fromkeys(result["issues"] + validation_issues))

        return format_validator_report(  # type: ignore[no-any-return]  # cross-plugin import typed as Any
            title="Imbue Plugin Review Workflow Report",
            plugin_root=self.plugin_root,
            skill_file_count=len(self.skill_files),
            metadata=[
                ("Review Workflow Skills", sorted(result["review_workflow_skills"])),
                (
                    "Evidence Logging Patterns",
                    sorted(result["evidence_logging_patterns"]),
                ),
            ],
            issues=issues,
            success_message="All review workflow skills validated successfully!",
        )


def main() -> None:
    """Run CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate imbue plugin review workflow skills",
    )
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent.parent),
        help="Imbue plugin root directory",
    )
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan for review workflow patterns",
    )

    args = parser.parse_args()

    validator = ImbueValidator(Path(args.root))

    if args.report:
        print(validator.generate_report())
        return
    elif args.scan:
        scan_result = validator.scan_review_workflows()
        issues = validator.validate_review_workflows()
        fields: dict[str, set[str]] = {
            "skills_found": scan_result["skills_found"],
            "review_workflow_skills": scan_result["review_workflow_skills"],
            "evidence_logging_patterns": scan_result["evidence_logging_patterns"],
        }
        for key, values in fields.items():
            print(f"{key}: {sorted(values)}")
        if issues:
            print("\nIssues:")
            for issue in issues:
                print(f"- {issue}")
            sys.exit(1)
        print("\nNo issues found.")
        return

    # Default action: print help
    parser.print_help()


if __name__ == "__main__":
    main()
