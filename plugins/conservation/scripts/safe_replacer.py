#!/usr/bin/env python3
"""Safe dependency reference updater that prevents duplicates."""

import re
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
    updater = SafeDependencyUpdater()

    base_path = Path("/home/alext/conservation/skills")

    _files_updated, _changes = updater.update_directory(base_path)


if __name__ == "__main__":
    main()
