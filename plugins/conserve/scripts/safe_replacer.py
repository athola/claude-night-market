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
        """Update all skill files in directory."""
        files_updated = 0
        total_changes = 0

        for skill_file in base_path.rglob("SKILL.md"):
            updated, changes = self.update_file(skill_file)
            if updated:
                files_updated += 1
                total_changes += changes

            # Validate results
            issues = self.validate_references(skill_file)
            if issues:
                pass
            else:
                pass

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

        if args.validate_only:
            # Validation mode - just report issues
            issues = []
            for skill_file in base_path.rglob("SKILL.md"):
                file_issues = updater.validate_references(skill_file)
                if file_issues:
                    issues.extend(
                        [
                            {"file": str(skill_file), "issue": issue}
                            for issue in file_issues
                        ]
                    )

            result = {
                "files_scanned": len(list(base_path.rglob("SKILL.md"))),
                "issues_found": issues,
                "validate_only": True,
            }
            output_result(result, args)
        else:
            # Update mode
            files_updated, total_changes = updater.update_directory(base_path)

            # Check for remaining issues
            issues = []
            for skill_file in base_path.rglob("SKILL.md"):
                file_issues = updater.validate_references(skill_file)
                if file_issues:
                    issues.extend(
                        [
                            {"file": str(skill_file), "issue": issue}
                            for issue in file_issues
                        ]
                    )

            result = {
                "files_updated": files_updated,
                "total_changes": total_changes,
                "issues_found": issues,
            }
            output_result(result, args)

    except Exception as e:
        output_error(f"Error updating references: {e}", args)


def output_result(result: dict, args: argparse.Namespace) -> None:
    """Output result in requested format."""
    if args.output_json:
        print(
            json.dumps(
                {
                    "success": True,
                    "data": result,
                },
                indent=2,
            )
        )
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
        print(
            json.dumps(
                {
                    "success": False,
                    "error": message,
                },
                indent=2,
            )
        )
    else:
        print(f"Error: {message}", file=sys.stderr)


if __name__ == "__main__":
    main()
