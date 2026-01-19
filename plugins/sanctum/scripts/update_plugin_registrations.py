#!/usr/bin/env python3
"""Audit and sync plugin.json files with disk contents.

This script scans plugin directories for commands, skills, agents, and hooks,
compares them with plugin.json registrations, and optionally fixes discrepancies.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class PluginAuditor:
    """Audit and sync plugin.json registrations with disk contents."""

    def __init__(self, plugins_root: Path, dry_run: bool = True):
        self.plugins_root = plugins_root
        self.dry_run = dry_run
        self.discrepancies: dict[str, Any] = {}

    # Cache/temp directories to exclude from scans (consistent with update_versions.py)
    CACHE_EXCLUDES = {
        ".venv",
        "venv",
        ".virtualenv",
        "virtualenv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        "node_modules",
        ".npm",
        ".yarn",
        ".cache",
        "target",
        ".cargo",
        ".rustup",
        "dist",
        "build",
        "_build",
        "out",
    }

    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded based on cache/temp patterns."""
        return any(exclude in path.parts for exclude in self.CACHE_EXCLUDES)

    def scan_disk_files(self, plugin_path: Path) -> dict[str, list[str]]:
        """Scan disk for actual commands, skills, agents, hooks."""
        results: dict[str, list[str]] = {
            "commands": [],
            "skills": [],
            "agents": [],
            "hooks": [],
        }

        # Commands: *.md files in commands/ (excluding module subdirectories and cache dirs)
        commands_dir = plugin_path / "commands"
        if commands_dir.exists():
            for cmd_file in commands_dir.rglob("*.md"):
                # Skip cache directories
                if self._should_exclude(cmd_file):
                    continue
                # Skip files in module subdirectories (check all ancestors, not just parent)
                # This handles paths like commands/fix-pr-modules/steps/1-analyze.md
                rel_to_commands = cmd_file.relative_to(commands_dir)
                if any(
                    "module" in part.lower() or part == "steps"
                    for part in rel_to_commands.parts[:-1]
                ):
                    continue
                # Only register top-level commands (direct children of commands/)
                if len(rel_to_commands.parts) == 1:
                    rel_path = f"./commands/{cmd_file.name}"
                    results["commands"].append(rel_path)

        # Skills: directories in skills/ (excluding cache directories)
        skills_dir = plugin_path / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and not self._should_exclude(skill_dir):
                    rel_path = f"./skills/{skill_dir.name}"
                    results["skills"].append(rel_path)

        # Agents: *.md files in agents/ (excluding cache directories)
        agents_dir = plugin_path / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                if not self._should_exclude(agent_file):
                    rel_path = f"./agents/{agent_file.name}"
                    results["agents"].append(rel_path)

        # Hooks: *.md, *.sh, *.py files in hooks/ (excluding test files, __init__.py, and cache dirs)
        hooks_dir = plugin_path / "hooks"
        if hooks_dir.exists():
            for hook_file in hooks_dir.iterdir():
                if self._should_exclude(hook_file):
                    continue
                if hook_file.is_file() and hook_file.suffix in [".md", ".sh", ".py"]:
                    # Skip test files and __init__.py
                    if (
                        not hook_file.name.startswith("test_")
                        and hook_file.name != "__init__.py"
                    ):
                        rel_path = f"./hooks/{hook_file.name}"
                        results["hooks"].append(rel_path)

        # Sort all lists for consistent comparison
        for key in results:
            results[key].sort()

        return results

    def read_plugin_json(self, plugin_path: Path) -> dict[str, Any] | None:
        """Read plugin.json file."""
        plugin_json = plugin_path / ".claude-plugin" / "plugin.json"
        if not plugin_json.exists():
            return None

        try:
            with plugin_json.open(encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[ERROR] Failed to read {plugin_json}: {e}")
            return None

    def compare_registrations(
        self, _plugin_name: str, on_disk: dict[str, list[str]], in_json: dict[str, Any]
    ) -> dict[str, Any]:
        """Compare disk files with plugin.json registrations."""
        discrepancies: dict[str, Any] = {
            "missing": {},  # On disk but not in plugin.json
            "stale": {},  # In plugin.json but not on disk
        }

        for category in ["commands", "skills", "agents", "hooks"]:
            disk_set = set(on_disk[category])
            json_list = in_json.get(category, [])
            json_set = set(json_list) if json_list else set()

            missing = disk_set - json_set
            stale = json_set - disk_set

            if missing:
                discrepancies["missing"][category] = sorted(missing)
            if stale:
                discrepancies["stale"][category] = sorted(stale)

        return discrepancies

    def audit_plugin(self, plugin_name: str) -> bool:
        """Audit a single plugin and return True if discrepancies found."""
        plugin_path = self.plugins_root / plugin_name

        if not plugin_path.exists() or not plugin_path.is_dir():
            print(f"[SKIP] {plugin_name}: not a directory")
            return False

        # Read plugin.json
        plugin_json_data = self.read_plugin_json(plugin_path)
        if plugin_json_data is None:
            print(f"[SKIP] {plugin_name}: no valid plugin.json")
            return False

        # Scan disk
        on_disk = self.scan_disk_files(plugin_path)

        # Compare
        discrepancies = self.compare_registrations(
            plugin_name, on_disk, plugin_json_data
        )

        # Report
        has_discrepancies = bool(discrepancies["missing"] or discrepancies["stale"])

        if has_discrepancies:
            self.discrepancies[plugin_name] = discrepancies
            self._print_discrepancies(plugin_name, discrepancies)

        return has_discrepancies

    def _print_discrepancies(
        self, plugin_name: str, discrepancies: dict[str, Any]
    ) -> None:
        """Print discrepancies for a plugin."""
        print(f"\n{'=' * 60}")
        print(f"PLUGIN: {plugin_name}")
        print("=" * 60)

        if discrepancies["missing"]:
            print("\n[MISSING] Files on disk but not in plugin.json:")
            for category, items in discrepancies["missing"].items():
                print(f"  {category}:")
                for item in items:
                    print(f"    - {item}")

        if discrepancies["stale"]:
            print("\n[STALE] Registered in plugin.json but not on disk:")
            for category, items in discrepancies["stale"].items():
                print(f"  {category}:")
                for item in items:
                    print(f"    - {item}")

    def fix_plugin(self, plugin_name: str) -> bool:
        """Fix discrepancies by updating plugin.json."""
        if plugin_name not in self.discrepancies:
            return True  # Nothing to fix

        plugin_path = self.plugins_root / plugin_name
        plugin_json_path = plugin_path / ".claude-plugin" / "plugin.json"

        # Read current plugin.json
        with plugin_json_path.open(encoding="utf-8") as f:
            plugin_data = json.load(f)

        # Get discrepancies
        disc = self.discrepancies[plugin_name]

        # Fix missing entries (add them)
        for category, items in disc["missing"].items():
            if category not in plugin_data:
                plugin_data[category] = []
            plugin_data[category].extend(items)
            plugin_data[category].sort()

        # Fix stale entries (remove them)
        for category, items in disc["stale"].items():
            if category in plugin_data:
                plugin_data[category] = [
                    item for item in plugin_data[category] if item not in items
                ]

        # Write updated plugin.json
        if not self.dry_run:
            with plugin_json_path.open("w", encoding="utf-8") as f:
                json.dump(plugin_data, f, indent=2, ensure_ascii=False)
                f.write("\n")  # Trailing newline
            print(f"[FIXED] {plugin_name}: plugin.json updated")
        else:
            print(f"[DRY-RUN] {plugin_name}: would update plugin.json")

        return True

    def audit_all(self, specific_plugin: str | None = None) -> int:
        """Audit all plugins or a specific plugin."""
        if specific_plugin:
            plugins = [specific_plugin]
        else:
            # Get all plugin directories
            plugins = [
                p.name
                for p in self.plugins_root.iterdir()
                if p.is_dir() and not p.name.startswith(".")
            ]
            plugins.sort()

        print(f"Auditing {len(plugins)} plugin(s)...\n")

        plugins_with_issues = 0
        for plugin_name in plugins:
            if self.audit_plugin(plugin_name):
                plugins_with_issues += 1

        # Summary
        print(f"\n{'=' * 60}")
        print("AUDIT SUMMARY")
        print("=" * 60)
        print(f"Plugins audited: {len(plugins)}")
        print(f"Plugins with discrepancies: {plugins_with_issues}")
        print(f"Plugins clean: {len(plugins) - plugins_with_issues}")

        # Fix if requested
        if not self.dry_run and plugins_with_issues > 0:
            print(f"\n{'=' * 60}")
            print("FIXING DISCREPANCIES")
            print("=" * 60)
            for plugin_name in self.discrepancies:
                self.fix_plugin(plugin_name)

        return plugins_with_issues


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Audit and sync plugin.json files with disk contents"
    )
    parser.add_argument(
        "plugin", nargs="?", help="Specific plugin to audit (default: all plugins)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix discrepancies by updating plugin.json files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show discrepancies without making changes (default)",
    )
    parser.add_argument(
        "--plugins-root",
        type=Path,
        default=Path.cwd() / "plugins",
        help="Root directory containing plugins (default: ./plugins)",
    )

    args = parser.parse_args()

    # If --fix is specified, disable dry-run
    if args.fix:
        args.dry_run = False

    # Validate plugins root
    if not args.plugins_root.exists():
        print(f"[ERROR] Plugins root not found: {args.plugins_root}")
        sys.exit(1)

    # Create auditor
    auditor = PluginAuditor(args.plugins_root, dry_run=args.dry_run)

    # Run audit
    issues_found = auditor.audit_all(args.plugin)

    # Exit code
    if issues_found > 0 and args.dry_run:
        print("\n[HINT] Run with --fix to automatically update plugin.json files")
        sys.exit(1)
    elif issues_found > 0:
        sys.exit(1)
    else:
        print("\n[SUCCESS] All plugins have consistent registrations!")
        sys.exit(0)


if __name__ == "__main__":
    main()
