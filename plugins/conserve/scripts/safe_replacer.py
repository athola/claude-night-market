#!/usr/bin/env python3
"""Safe dependency reference updater that prevents duplicates.

Returns (JSON):
    success (bool): Whether update completed successfully
    data.files_updated (int): Number of files modified
    data.total_changes (int): Total number of reference changes made
    data.issues_found (list): List of any remaining issues found
"""

import argparse
import json
import re
import sys
from pathlib import Path

# D-13: pull canonical CLI envelope helpers from leyline.
_LEYLINE_SRC = Path(__file__).resolve().parents[2] / "leyline" / "src"
if str(_LEYLINE_SRC) not in sys.path:
    sys.path.insert(0, str(_LEYLINE_SRC))

from leyline.cli_envelope import (  # noqa: E402 - import after sys.path setup
    error_envelope,
    success_envelope,
)


class SafeDependencyUpdater:
    """Safely updates dependencies in skill files."""

    def __init__(self) -> None:
        """Initialize the safe dependency updater."""
        self.patterns = {
            # Match only standalone references (not already prefixed)
            "standalone_git_review": r"\bgit-workspace-review\b",
            "standalone_review_core": r"\breview-core\b",
            # Match wrong prefixes
            "wrong_workspace_prefix": r"workspace-utils:git-workspace-review",
            "wrong_workflow_prefix": r"workflow-utils:review-core",
            # Match full old plugin paths
            "old_skill_paths": r"~?/\.claude/skills/",
        }

        self.replacements = {
            "standalone_git_review": "sanctum:git-workspace-review",
            "standalone_review_core": "imbue:review-core",
            "wrong_workspace_prefix": "sanctum:git-workspace-review",
            "wrong_workflow_prefix": "imbue:review-core",
            "old_skill_paths": "",
        }

    def update_file(self, file_path: Path) -> tuple[bool, int]:
        """Update a single file safely, preventing duplicates."""
        if not file_path.exists():
            return False, 0

        content = file_path.read_text()
        original_content = content
        changes_made = 0

        for pattern_name, pattern in self.patterns.items():
            replacement = self.replacements[pattern_name]

            # Count existing matches
            matches = re.findall(pattern, content)
            if not matches:
                continue

            # Only replace if the replacement isn't already present
            new_content = re.sub(pattern, replacement, content)

            # Check if we actually made changes
            if new_content != content:
                # Validate that we didn't create duplicates
                if replacement not in original_content or original_content.count(
                    replacement,
                ) < new_content.count(replacement):
                    content = new_content
                    changes_made += len(matches)

        if content != original_content:
            file_path.write_text(content)
            return True, changes_made

        return False, 0

    def validate_references(self, file_path: Path) -> list[str]:
        """Check for any remaining problematic references."""
        content = file_path.read_text()
        issues = []

        # Check for old plugin references
        if "workspace-utils:" in content:
            issues.append("Found workspace-utils: references")
        if "workflow-utils:" in content:
            issues.append("Found workflow-utils: references")
        if "~/.claude/skills/" in content:
            issues.append("Found old skill paths")

        # Check for duplicates
        if "sanctum:sanctum:" in content:
            issues.append("Found duplicate sanctum: prefix")
        if "imbue:imbue:" in content:
            issues.append("Found duplicate imbue: prefix")

        return issues

    def update_directory(self, base_path: Path) -> tuple[int, int]:
        """Update all skill files in directory.

        Walks the tree once. Use ``update_files`` when the caller
        already has a materialised list of paths to avoid a second
        rglob.
        """
        return self.update_files(list(base_path.rglob("SKILL.md")))

    def update_files(self, skill_files: list[Path]) -> tuple[int, int]:
        """Update each ``SKILL.md`` in *skill_files*.

        Validation happens in the caller after all updates complete.
        """
        files_updated = 0
        total_changes = 0
        for skill_file in skill_files:
            updated, changes = self.update_file(skill_file)
            if updated:
                files_updated += 1
                total_changes += changes
        return files_updated, total_changes


def main() -> None:
    """Safe update of dependency references."""
    parser = argparse.ArgumentParser(
        description="Safely update dependency references in skill files"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Base path to search for skill files (default: current directory)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate references without making changes",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output results as JSON for programmatic use",
    )

    args = parser.parse_args()

    try:
        base_path = Path(args.path).resolve()
        if not base_path.exists():
            output_error(f"Path not found: {base_path}", args)
            return

        updater = SafeDependencyUpdater()
        # A-04: walk once, reuse for both update and validation.
        skill_files = list(base_path.rglob("SKILL.md"))

        def _collect_issues() -> list[dict[str, str]]:
            issues: list[dict[str, str]] = []
            for skill_file in skill_files:
                for issue in updater.validate_references(skill_file):
                    issues.append({"file": str(skill_file), "issue": issue})
            return issues

        if args.validate_only:
            output_result(
                {
                    "files_scanned": len(skill_files),
                    "issues_found": _collect_issues(),
                    "validate_only": True,
                },
                args,
            )
        else:
            files_updated, total_changes = updater.update_files(skill_files)
            output_result(
                {
                    "files_updated": files_updated,
                    "total_changes": total_changes,
                    "issues_found": _collect_issues(),
                },
                args,
            )

    except FileNotFoundError as e:
        output_error(f"File not found: {e}", args)
    except PermissionError as e:
        output_error(f"Permission denied: {e}", args)
    except Exception as e:
        output_error(f"Error updating references: {e}", args)


def output_result(result: dict, args: argparse.Namespace) -> None:
    """Output result in requested format."""
    if args.output_json:
        print(json.dumps(success_envelope(result), indent=2))
    else:
        print(f"Files updated: {result.get('files_updated', 0)}")
        print(f"Total changes: {result.get('total_changes', 0)}")
        if result.get("issues_found"):
            print("\nIssues found:")
            for issue in result["issues_found"]:
                print(f"  - {issue}")


def output_error(message: str, args: argparse.Namespace) -> None:
    """Output error in requested format."""
    if args.output_json:
        print(json.dumps(error_envelope(message), indent=2))
    else:
        print(f"Error: {message}", file=sys.stderr)


if __name__ == "__main__":
    main()
