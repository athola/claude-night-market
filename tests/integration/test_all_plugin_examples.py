#!/usr/bin/env python3
"""Verify all plugins have proper examples in their documentation.

This script checks that each plugin has:
- A README.md with usage examples
- Code blocks demonstrating plugin usage
- Skill invocation examples where applicable
"""

import argparse
import re
import sys
from pathlib import Path


class PluginExampleChecker:
    """Check plugins for proper example documentation."""

    def __init__(self, plugins_root: Path):
        self.plugins_root = plugins_root
        self.results: dict[str, dict] = {}

    def find_plugins(self) -> list[Path]:
        """Find all plugin directories."""
        plugins = []
        for item in self.plugins_root.iterdir():
            if item.is_dir() and (item / ".claude-plugin" / "plugin.json").exists():
                plugins.append(item)
        return sorted(plugins)

    def check_readme_exists(self, plugin_path: Path) -> bool:
        """Check if plugin has a README.md."""
        return (plugin_path / "README.md").exists()

    def check_has_code_examples(self, content: str) -> tuple[bool, int]:
        """Check if content has code block examples."""
        code_blocks = re.findall(r"```[\w]*\n[^`]+```", content, re.MULTILINE)
        return len(code_blocks) > 0, len(code_blocks)

    def check_has_skill_examples(self, content: str) -> bool:
        """Check if content has Skill() invocation examples."""
        return "Skill(" in content or "/plugin" in content

    def check_has_command_examples(self, content: str) -> bool:
        """Check if content has command examples (slash commands)."""
        return bool(re.search(r"/[a-z]+-?[a-z]+", content))

    def check_plugin(self, plugin_path: Path) -> dict:
        """Check a single plugin for examples."""
        plugin_name = plugin_path.name
        result = {
            "name": plugin_name,
            "readme_exists": False,
            "has_code_examples": False,
            "code_block_count": 0,
            "has_skill_examples": False,
            "has_command_examples": False,
            "issues": [],
        }

        # Check README
        readme_path = plugin_path / "README.md"
        if not readme_path.exists():
            result["issues"].append("Missing README.md")
            return result

        result["readme_exists"] = True

        # Read content
        try:
            content = readme_path.read_text(encoding="utf-8")
        except Exception as e:
            result["issues"].append(f"Failed to read README: {e}")
            return result

        # Check for code examples
        has_code, count = self.check_has_code_examples(content)
        result["has_code_examples"] = has_code
        result["code_block_count"] = count

        if not has_code:
            result["issues"].append("No code block examples in README")

        # Check for skill examples
        result["has_skill_examples"] = self.check_has_skill_examples(content)

        # Check for command examples
        result["has_command_examples"] = self.check_has_command_examples(content)

        # Warn if no usage examples at all
        if not has_code and not result["has_skill_examples"]:
            result["issues"].append("No usage examples (code blocks or Skill() calls)")

        return result

    def check_all(self) -> dict:
        """Check all plugins."""
        plugins = self.find_plugins()

        summary = {
            "total": len(plugins),
            "passed": 0,
            "with_issues": 0,
            "plugins": [],
        }

        for plugin_path in plugins:
            result = self.check_plugin(plugin_path)
            self.results[result["name"]] = result
            summary["plugins"].append(result)

            if not result["issues"]:
                summary["passed"] += 1
            else:
                summary["with_issues"] += 1

        return summary

    def print_report(self, summary: dict) -> None:
        """Print a summary report."""
        print(f"\nPlugins Checked: {summary['total']}")
        print(f"Passed: {summary['passed']}")
        print(f"With Issues: {summary['with_issues']}")
        print()

        # Show passing plugins
        passing = [p for p in summary["plugins"] if not p["issues"]]
        if passing:
            print("Passing Plugins:")
            for p in passing:
                extras = []
                if p["has_skill_examples"]:
                    extras.append("skills")
                if p["has_command_examples"]:
                    extras.append("commands")
                extra_str = f" ({', '.join(extras)})" if extras else ""
                print(
                    f"  [OK] {p['name']}: {p['code_block_count']} code blocks{extra_str}"
                )
            print()

        # Show plugins with issues
        with_issues = [p for p in summary["plugins"] if p["issues"]]
        if with_issues:
            print("Plugins With Issues:")
            for p in with_issues:
                print(f"  [!] {p['name']}:")
                for issue in p["issues"]:
                    print(f"      - {issue}")
            print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify all plugins have proper examples"
    )
    parser.add_argument(
        "--plugins-root",
        type=Path,
        default=Path(__file__).parents[2] / "plugins",
        help="Root directory containing plugins",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print detailed report",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if any plugin has issues",
    )

    args = parser.parse_args()

    # Validate path
    if not args.plugins_root.exists():
        print(f"[ERROR] Plugins root not found: {args.plugins_root}")
        return 1

    # Run checks
    checker = PluginExampleChecker(args.plugins_root)
    summary = checker.check_all()

    # Print report
    if args.report:
        checker.print_report(summary)
    else:
        # Brief output
        print(
            f"Checked {summary['total']} plugins: {summary['passed']} passed, {summary['with_issues']} with issues"
        )

    # Exit code
    if args.strict and summary["with_issues"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
