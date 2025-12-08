#!/usr/bin/env python3
"""Tool for managing dependencies in Claude Code plugins."""

import argparse
import json
import re
from pathlib import Path


class DependencyManager:
    """Manages dependencies for Claude Code plugins."""

    def __init__(self, plugin_root: Path):
        """Initialize the dependency manager.

        Args:
            plugin_root: Root directory of the plugin

        """
        self.plugin_root = plugin_root
        self.skill_files = list(plugin_root.rglob("SKILL.md"))
        self.plugin_config = plugin_root / "plugin.json"

    def scan_dependencies(self) -> dict[str, set[str] | list[str]]:
        """Scan all files for dependency references."""
        dependencies: dict[str, set[str] | list[str]] = {
            "found": set(),
            "expected": set(),
            "issues": [],
        }

        # Load expected dependencies from plugin.json
        if self.plugin_config.exists():
            try:
                config = json.loads(self.plugin_config.read_text())
                deps = config.get("dependencies", [])
                if isinstance(deps, list):
                    dependencies["expected"] = set(deps)
                else:
                    dependencies["expected"] = set(deps.keys())
            except json.JSONDecodeError:
                issues_list = dependencies["issues"]
                if isinstance(issues_list, list):
                    issues_list.append("Invalid plugin.json")

        # Scan skill files for references
        plugin_patterns = {
            "imbue": r"\bimbue:",
            "sanctum": r"\bsanctum:",
        }

        for skill_file in self.skill_files:
            content = skill_file.read_text()

            for plugin, pattern in plugin_patterns.items():
                if re.search(pattern, content):
                    found_set = dependencies["found"]
                    if isinstance(found_set, set):
                        found_set.add(plugin)

        return dependencies

    def detect_issues(self) -> list[str]:
        """Detect dependency-related issues."""
        deps = self.scan_dependencies()
        issues = []

        # Check for missing expected dependencies
        found_deps = deps["found"]
        if not isinstance(found_deps, set):
            found_deps = set(found_deps)

        expected_deps = deps["expected"]
        if not isinstance(expected_deps, set):
            expected_deps = set(expected_deps)

        missing = expected_deps - found_deps
        if missing:
            issues.append(f"Expected dependencies not found in skills: {missing}")

        # Check for unexpected dependencies
        unexpected = found_deps - expected_deps
        if unexpected:
            issues.append(f"Found dependencies not in plugin.json: {unexpected}")

        # Check for old reference patterns
        old_patterns = {
            "workspace-utils:": r"\bworkspace-utils:",
            "workflow-utils:": r"\bworkflow-utils:",
        }

        for skill_file in self.skill_files:
            content = skill_file.read_text()
            for pattern_name, pattern in old_patterns.items():
                if re.search(pattern, content):
                    issues.append(
                        f"Found old reference pattern '{pattern_name}' "
                        f"in {skill_file.name}"
                    )

        return issues

    def fix_dependencies(self, dry_run: bool = True) -> list[str]:
        """Fix dependency issues automatically."""
        issues_fixed = []

        # Read plugin.json to get expected dependencies
        if not self.plugin_config.exists():
            return ["plugin.json not found"]

        try:
            config = json.loads(self.plugin_config.read_text())
            expected_deps = set(config.get("dependencies", {}).keys())
        except json.JSONDecodeError:
            return ["Invalid plugin.json"]

        # Define corrections based on expected dependencies
        corrections = []

        if "sanctum" in expected_deps:
            corrections.extend(
                [
                    (
                        r"\bworkspace-utils:git-workspace-review\b",
                        "sanctum:git-workspace-review",
                    ),
                    (r"\bgit-workspace-review\b", "sanctum:git-workspace-review"),
                ]
            )

        if "imbue" in expected_deps:
            corrections.extend(
                [
                    (r"\bworkflow-utils:review-core\b", "imbue:review-core"),
                    (r"\breview-core\b", "imbue:review-core"),
                ]
            )

        # Add general cleanup
        corrections.extend(
            [
                (r"~?/\.claude/skills/", ""),
                (r"sanctum:sanctum:", "sanctum:"),
                (r"imbue:imbue:", "imbue:"),
            ]
        )

        # Apply corrections to all skill files
        for skill_file in self.skill_files:
            content = skill_file.read_text()
            original_content = content
            file_changes = 0

            for pattern, replacement in corrections:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    file_changes += len(re.findall(pattern, original_content))
                    content = new_content

            if content != original_content:
                if not dry_run:
                    skill_file.write_text(content)
                prefix = "[DRY RUN] " if dry_run else ""
                issues_fixed.append(
                    f"{prefix}Updated {skill_file.name}: {file_changes} changes"
                )

        return issues_fixed if issues_fixed else ["No changes needed"]

    def generate_report(self) -> str:
        """Generate a dependency report."""
        deps = self.scan_dependencies()
        issues = self.detect_issues()

        report = ["Dependency Management Report", "=" * 40]
        report.append(f"\nPlugin Root: {self.plugin_root}")
        report.append(f"Skill Files: {len(self.skill_files)}")

        report.append(f"\nExpected Dependencies: {sorted(deps['expected'])}")
        report.append(f"Found Dependencies: {sorted(deps['found'])}")

        if issues:
            report.append(f"\nIssues Found ({len(issues)}):")
            for i, issue in enumerate(issues, 1):
                report.append(f"  {i}. {issue}")
        else:
            report.append("\nNo issues found!")

        return "\n".join(report)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Manage plugin dependencies")
    parser.add_argument(
        "--root", default="/home/alext/conservation", help="Plugin root directory"
    )
    parser.add_argument("--scan", action="store_true", help="Scan for dependencies")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--fix", action="store_true", help="Fix dependency issues")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run for fix operations"
    )

    args = parser.parse_args()

    manager = DependencyManager(Path(args.root))

    if args.report:
        print(manager.generate_report())
    elif args.scan:
        issues = manager.detect_issues()
        if issues:
            print(f"Found {len(issues)} issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("No issues found!")
    elif args.fix:
        fixes = manager.fix_dependencies(dry_run=args.dry_run)
        for fix in fixes:
            print(fix)
    else:
        print("Use --report, --scan, or --fix. Use --help for details.")


if __name__ == "__main__":
    main()
