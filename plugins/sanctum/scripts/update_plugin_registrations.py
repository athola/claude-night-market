#!/usr/bin/env python3
"""Audit and sync plugin.json files with disk contents.

This script scans plugin directories for commands, skills, agents, hooks, and modules,
compares them with plugin.json registrations, and validates module references.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Import Phase 2-4 modules
sys.path.insert(0, str(Path(__file__).parent))
from update_plugins_modules import (
    KnowledgeQueueChecker,
    MetaEvaluator,
    PerformanceAnalyzer,
)


class PluginAuditor:
    """Audit and sync plugin.json registrations with disk contents."""

    def __init__(self, plugins_root: Path, dry_run: bool = True):
        self.plugins_root = plugins_root
        self.dry_run = dry_run
        self.discrepancies: dict[str, Any] = {}
        self.module_issues: dict[
            str, dict[str, Any]
        ] = {}  # Track module issues separately

        # Initialize Phase 2-4 analyzers
        self.performance_analyzer = PerformanceAnalyzer()
        self.meta_evaluator = MetaEvaluator()
        self.queue_checker = KnowledgeQueueChecker()

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

    def audit_skill_modules(self, plugin_path: Path) -> dict[str, Any]:
        """Audit modules within each skill directory.

        Scans the ENTIRE plugin for module references, including:
        - Skill files (SKILL.md and root .md files)
        - Commands (commands/*.md and commands/*/modules/*.md)
        - Agents (agents/*.md)

        For each skill with modules, reports:
        - Orphaned modules (exist but not referenced anywhere in plugin)
        - Missing modules (referenced but don't exist)

        Returns:
            Dict mapping skill names to their module issues
        """
        skill_module_issues: dict[str, Any] = {}
        skills_dir = plugin_path / "skills"

        if not skills_dir.exists():
            return skill_module_issues

        # First, collect ALL module references from the entire plugin
        all_references = self._scan_plugin_for_module_refs(plugin_path)

        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir() or self._should_exclude(skill_dir):
                continue

            # Scan modules on disk for this skill
            modules_on_disk = self._scan_skill_modules(skill_dir)
            if not modules_on_disk:
                continue  # Skip skills with no modules

            skill_name = skill_dir.name

            # Find references to THIS skill's modules
            # References can be: modules/file.md, skills/skill-name/modules/file.md
            referenced_modules: set[str] = set()
            for ref in all_references:
                # Direct module reference (from within the skill or relative)
                if ref in modules_on_disk:
                    referenced_modules.add(ref)
                # Full path reference: skills/skill-name/modules/file.md
                elif f"skills/{skill_name}/modules/" in ref:
                    module_name = ref.split("/")[-1]
                    if module_name in modules_on_disk:
                        referenced_modules.add(module_name)

            # Calculate discrepancies
            orphaned = modules_on_disk - referenced_modules
            missing = referenced_modules - modules_on_disk

            if orphaned or missing:
                skill_module_issues[skill_name] = {
                    "orphaned": sorted(orphaned),
                    "missing": sorted(missing),
                }

        return skill_module_issues

    def _scan_plugin_for_module_refs(self, plugin_path: Path) -> set[str]:
        """Scan entire plugin for module references.

        Searches in:
        - skills/**/*.md (skill definitions)
        - commands/**/*.md (command files and their modules)
        - agents/*.md (agent definitions)
        """
        all_refs: set[str] = set()

        # Scan skills
        skills_dir = plugin_path / "skills"
        if skills_dir.exists():
            for md_file in skills_dir.rglob("*.md"):
                if not self._should_exclude(md_file):
                    all_refs.update(self._extract_module_refs_from_file(md_file))

        # Scan commands
        commands_dir = plugin_path / "commands"
        if commands_dir.exists():
            for md_file in commands_dir.rglob("*.md"):
                if not self._should_exclude(md_file):
                    all_refs.update(self._extract_module_refs_from_file(md_file))

        # Scan agents
        agents_dir = plugin_path / "agents"
        if agents_dir.exists():
            for md_file in agents_dir.rglob("*.md"):
                if not self._should_exclude(md_file):
                    all_refs.update(self._extract_module_refs_from_file(md_file))

        return all_refs

    def _scan_skill_modules(self, skill_dir: Path) -> set[str]:
        """Scan for .md files in a skill's modules/ subdirectory."""
        modules: set[str] = set()
        modules_dir = skill_dir / "modules"

        if modules_dir.exists():
            for module_file in modules_dir.glob("*.md"):
                if not self._should_exclude(module_file):
                    modules.add(module_file.name)

        return modules

    def _extract_module_refs_from_file(self, md_file: Path) -> set[str]:
        """Extract module references from a single markdown file.

        Patterns matched:
        - @modules/filename.md
        - modules/filename.md
        - `modules/filename.md`
        - See `modules/filename.md`
        - skills/skill-name/modules/filename.md (full path)
        - plugins/plugin-name/skills/skill-name/modules/filename.md
        """
        references: set[str] = set()

        try:
            content = md_file.read_text(encoding="utf-8")
            patterns = [
                # Direct module references
                r"@modules/([a-zA-Z0-9_-]+\.md)",
                r"[`\s\(]modules/([a-zA-Z0-9_-]+\.md)",
                r"See\s+`?modules/([a-zA-Z0-9_-]+\.md)",
                # Full path references (captures entire path)
                r"skills/[a-zA-Z0-9_-]+/modules/([a-zA-Z0-9_-]+\.md)",
                r"plugins/[a-zA-Z0-9_-]+/skills/[a-zA-Z0-9_-]+/modules/([a-zA-Z0-9_-]+\.md)",
            ]
            for pattern in patterns:
                matches = re.findall(pattern, content)
                references.update(matches)
        except OSError:
            pass

        return references

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

        # Skills: directories in skills/ that contain skill content
        # A valid skill directory must have SKILL.md OR *.md files at root level
        # Directories with only modules/ subdirectories are module holders, not skills
        skills_dir = plugin_path / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and not self._should_exclude(skill_dir):
                    # Check if directory has actual skill content
                    has_skill_md = (skill_dir / "SKILL.md").exists()
                    has_root_md_files = any(
                        f.suffix == ".md" for f in skill_dir.iterdir() if f.is_file()
                    )
                    # Only register if it has skill content
                    if has_skill_md or has_root_md_files:
                        rel_path = f"./skills/{skill_dir.name}"
                        results["skills"].append(rel_path)

        # Agents: *.md files in agents/ (excluding cache directories)
        agents_dir = plugin_path / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                if not self._should_exclude(agent_file):
                    rel_path = f"./agents/{agent_file.name}"
                    results["agents"].append(rel_path)

        # Hooks: *.sh, *.py files in hooks/ (excluding test files, __init__.py, and cache dirs)
        # Note: *.md files in hooks/ are documentation, not executable hooks
        hooks_dir = plugin_path / "hooks"
        if hooks_dir.exists():
            for hook_file in hooks_dir.iterdir():
                if self._should_exclude(hook_file):
                    continue
                if hook_file.is_file() and hook_file.suffix in [".sh", ".py"]:
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

    def resolve_hooks_json(
        self, plugin_path: Path, hooks_json_ref: str
    ) -> list[str] | None:
        """Parse a hooks.json file and extract registered hook script paths.

        Args:
            plugin_path: Path to the plugin directory
            hooks_json_ref: Relative path like "./hooks/hooks.json"

        Returns:
            List of hook script paths in ./hooks/filename format, or None if file not found
        """
        # Resolve the hooks.json path
        hooks_json_path = plugin_path / hooks_json_ref.lstrip("./")
        if not hooks_json_path.exists():
            print(f"[WARN] hooks.json reference not found: {hooks_json_path}")
            return None

        try:
            with hooks_json_path.open(encoding="utf-8") as f:
                hooks_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[ERROR] Failed to read {hooks_json_path}: {e}")
            return None

        # Extract all command paths from the nested structure
        # Structure: { "hooks": { "EventType": [{ "hooks": [{ "command": "..." }] }] } }
        hook_scripts: set[str] = set()
        hooks_obj = hooks_data.get("hooks", {})

        for _event_type, matcher_configs in hooks_obj.items():
            if not isinstance(matcher_configs, list):
                continue
            for matcher_config in matcher_configs:
                if not isinstance(matcher_config, dict):
                    continue
                hook_defs = matcher_config.get("hooks", [])
                if not isinstance(hook_defs, list):
                    continue
                for hook_def in hook_defs:
                    if not isinstance(hook_def, dict):
                        continue
                    command = hook_def.get("command", "")
                    if command:
                        # Extract script path from command
                        # Handles: "${CLAUDE_PLUGIN_ROOT}/hooks/file.py"
                        # Handles: "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/file.py"
                        script_path = self._extract_script_path(command)
                        if script_path:
                            hook_scripts.add(script_path)

        return sorted(hook_scripts)

    def _extract_script_path(self, command: str) -> str | None:
        """Extract the script path from a hook command string.

        Converts "${CLAUDE_PLUGIN_ROOT}/hooks/file.py" to "./hooks/file.py"
        Also handles "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/file.py" format.
        """
        # Pattern to match ${CLAUDE_PLUGIN_ROOT}/path or similar
        match = re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}/(.+?)(?:\s|$)", command)
        if match:
            rel_path = match.group(1).strip()
            return f"./{rel_path}"

        # Fallback: try to find ./hooks/ pattern directly
        match = re.search(r"(\./hooks/[^\s]+)", command)
        if match:
            return match.group(1)

        return None

    def compare_registrations(
        self,
        plugin_path: Path,
        on_disk: dict[str, list[str]],
        in_json: dict[str, Any],
    ) -> dict[str, Any]:
        """Compare disk files with plugin.json registrations.

        Note: Claude Code auto-loads hooks/hooks.json if it exists, so plugins
        should NOT add "hooks": "./hooks/hooks.json" to plugin.json (causes duplicate).
        """
        # Ensure plugin_path is a Path object
        plugin_path = Path(plugin_path)

        discrepancies: dict[str, Any] = {
            "missing": {},  # On disk but not in plugin.json
            "stale": {},  # In plugin.json but not on disk
        }

        for category in ["commands", "skills", "agents", "hooks"]:
            disk_set = set(on_disk[category])
            json_value = in_json.get(category, [])

            # Special handling for hooks - Claude Code auto-loads hooks/hooks.json
            if category == "hooks":
                # Check if standard hooks.json exists (auto-loaded by Claude Code)
                standard_hooks_json = plugin_path / "hooks" / "hooks.json"

                if isinstance(json_value, str):
                    # plugin.json has explicit hooks reference
                    if json_value.endswith(".json"):
                        resolved_hooks = self.resolve_hooks_json(
                            plugin_path, json_value
                        )
                        if resolved_hooks is not None:
                            json_set = set(resolved_hooks)
                        else:
                            continue
                    else:
                        print(f"[WARN] Unexpected hooks format: {json_value}")
                        continue
                elif standard_hooks_json.exists():
                    # No hooks key in plugin.json but hooks.json exists
                    # Claude Code auto-loads this, so compare against it
                    resolved_hooks = self.resolve_hooks_json(
                        plugin_path, "./hooks/hooks.json"
                    )
                    if resolved_hooks is not None:
                        json_set = set(resolved_hooks)
                    else:
                        json_set = set()
                else:
                    # No hooks.json, use array from plugin.json (if any)
                    json_set = set(json_value) if json_value else set()
            else:
                json_set = set(json_value) if json_value else set()

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

        # Compare registrations
        discrepancies = self.compare_registrations(
            plugin_path, on_disk, plugin_json_data
        )

        # Audit modules within skills
        module_issues = self.audit_skill_modules(plugin_path)

        # Report
        has_discrepancies = bool(discrepancies["missing"] or discrepancies["stale"])
        has_module_issues = bool(module_issues)

        if has_discrepancies:
            self.discrepancies[plugin_name] = discrepancies
            self._print_discrepancies(plugin_name, discrepancies)

        if has_module_issues:
            self.module_issues[plugin_name] = module_issues
            self._print_module_issues(plugin_name, module_issues)

        return has_discrepancies or has_module_issues

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

    def _print_module_issues(
        self, plugin_name: str, module_issues: dict[str, Any]
    ) -> None:
        """Print module issues for a plugin's skills."""
        # Only print header if we haven't already printed discrepancies
        if plugin_name not in self.discrepancies:
            print(f"\n{'=' * 60}")
            print(f"PLUGIN: {plugin_name}")
            print("=" * 60)

        print("\n[MODULES] Skill module issues:")
        for skill_name, issues in sorted(module_issues.items()):
            print(f"  {skill_name}/:")
            if issues.get("orphaned"):
                print("    Orphaned (exist but not referenced):")
                for module in issues["orphaned"]:
                    print(f"      - modules/{module}")
            if issues.get("missing"):
                print("    Missing (referenced but not found):")
                for module in issues["missing"]:
                    print(f"      - modules/{module}")

    def fix_plugin(self, plugin_name: str) -> bool:
        """Fix discrepancies by updating plugin.json or hooks.json.

        Note: For hooks, if hooks/hooks.json exists (auto-loaded by Claude Code),
        discrepancies are reported but require manual fixes to hooks.json.
        We do NOT add "hooks" key to plugin.json as that causes duplicates.
        """
        if plugin_name not in self.discrepancies:
            return True  # Nothing to fix

        plugin_path = self.plugins_root / plugin_name
        plugin_json_path = plugin_path / ".claude-plugin" / "plugin.json"
        standard_hooks_json = plugin_path / "hooks" / "hooks.json"

        # Read current plugin.json
        with plugin_json_path.open(encoding="utf-8") as f:
            plugin_data = json.load(f)

        # Get discrepancies
        disc = self.discrepancies[plugin_name]

        # Track if we have hooks that need manual fixing
        hooks_need_manual_fix = False

        # Fix missing entries (add them)
        for category, items in disc["missing"].items():
            # Hooks require manual update to hooks.json (NOT plugin.json)
            # Claude Code auto-loads hooks/hooks.json, adding to plugin.json causes duplicates
            if category == "hooks":
                if standard_hooks_json.exists() or isinstance(
                    plugin_data.get("hooks"), str
                ):
                    hooks_ref = plugin_data.get("hooks", "./hooks/hooks.json")
                    print(
                        f"[MANUAL] {plugin_name}: hooks are auto-loaded from hooks.json"
                    )
                    print(f"         Update {hooks_ref} to add missing hooks:")
                    for item in items:
                        print(f"           - {item}")
                    hooks_need_manual_fix = True
                    continue
                # No hooks.json exists, would need to create one or use array
                # For now, skip and report
                print(f"[MANUAL] {plugin_name}: no hooks.json found, create one with:")
                for item in items:
                    print(f"           - {item}")
                hooks_need_manual_fix = True
                continue

            if category not in plugin_data:
                plugin_data[category] = []
            plugin_data[category].extend(items)
            plugin_data[category].sort()

        # Fix stale entries (remove them)
        for category, items in disc["stale"].items():
            # Hooks require manual update
            if category == "hooks":
                if not hooks_need_manual_fix:
                    hooks_ref = plugin_data.get("hooks", "./hooks/hooks.json")
                    print(
                        f"[MANUAL] {plugin_name}: hooks are auto-loaded from hooks.json"
                    )
                    print(f"         Update {hooks_ref} to remove stale hooks:")
                for item in items:
                    print(f"           - {item}")
                continue

            if category in plugin_data:
                plugin_data[category] = [
                    item for item in plugin_data[category] if item not in items
                ]

        # Write updated plugin.json (only if there are non-hooks changes)
        non_hooks_changes = any(
            cat != "hooks"
            for cat in list(disc["missing"].keys()) + list(disc["stale"].keys())
        )

        if non_hooks_changes:
            if not self.dry_run:
                with plugin_json_path.open("w", encoding="utf-8") as f:
                    json.dump(plugin_data, f, indent=2, ensure_ascii=False)
                    f.write("\n")  # Trailing newline
                print(f"[FIXED] {plugin_name}: plugin.json updated")
            else:
                print(f"[DRY-RUN] {plugin_name}: would update plugin.json")

        return True

    def analyze_skill_performance(self, plugin_name: str) -> dict[str, Any]:
        """Phase 2: Analyze skill execution metrics for performance issues."""
        return self.performance_analyzer.analyze_plugin(plugin_name)

    def check_meta_evaluation(
        self, plugin_name: str, plugin_path: Path
    ) -> dict[str, Any]:
        """Phase 3: Validate recursive quality of evaluation-related skills."""
        return self.meta_evaluator.check_plugin(plugin_name, plugin_path)

    def check_knowledge_queue(self) -> list[dict[str, Any]]:
        """Phase 4: Scan memory-palace queue for pending research items."""
        return self.queue_checker.check_queue()

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
        performance_report: dict[str, Any] = {}
        meta_eval_report: dict[str, Any] = {}

        # Phase 1: Registration Audit
        for plugin_name in plugins:
            if self.audit_plugin(plugin_name):
                plugins_with_issues += 1

            # Phase 2: Performance Analysis
            perf_data = self.analyze_skill_performance(plugin_name)
            if any(perf_data.values()):
                performance_report[plugin_name] = perf_data

            # Phase 3: Meta-Evaluation Check
            plugin_path = self.plugins_root / plugin_name
            meta_issues = self.check_meta_evaluation(plugin_name, plugin_path)
            if any(meta_issues.values()):
                meta_eval_report[plugin_name] = meta_issues

        # Phase 4: Knowledge Queue Check (once for all plugins)
        queue_items = self.check_knowledge_queue()

        # Summary
        print(f"\n{'=' * 60}")
        print("AUDIT SUMMARY")
        print("=" * 60)
        print(f"Plugins audited: {len(plugins)}")
        print(f"Plugins with registration issues: {len(self.discrepancies)}")
        print(f"Plugins with module issues: {len(self.module_issues)}")
        print(f"Plugins clean: {len(plugins) - plugins_with_issues}")

        # Phase 2 Summary
        if performance_report:
            print(f"\n{'=' * 60}")
            print("PHASE 2: PERFORMANCE & IMPROVEMENT ANALYSIS")
            print("=" * 60)
            for plugin, data in performance_report.items():
                print(f"\n{plugin}:")
                if data["unstable_skills"]:
                    print("  ⚠ Unstable skills (stability_gap > 0.3):")
                    for item in data["unstable_skills"]:
                        print(f"    - {item['skill']}: {item['stability_gap']}")
                if data["recent_failures"]:
                    print("  ❌ Recent failures (last 7 days):")
                    for item in data["recent_failures"]:
                        print(f"    - {item['skill']}: {item['failures']} failures")
                if data["low_success_rate"]:
                    print("  📉 Low success rate (< 80%):")
                    for item in data["low_success_rate"]:
                        print(f"    - {item['skill']}: {item['success_rate']:.0%}")

        # Phase 3 Summary
        if meta_eval_report:
            print(f"\n{'=' * 60}")
            print("PHASE 3: META-EVALUATION CHECK")
            print("=" * 60)
            for plugin, issues in meta_eval_report.items():
                print(f"\n{plugin}:")
                if issues["missing_toc"]:
                    print(f"  📋 Missing TOC: {', '.join(issues['missing_toc'])}")
                if issues["missing_verification"]:
                    print(
                        f"  🔍 Missing verification: {', '.join(issues['missing_verification'])}"
                    )
                if issues["missing_tests"]:
                    print(f"  🧪 Missing tests: {', '.join(issues['missing_tests'])}")

        # Phase 4 Summary
        if queue_items:
            print(f"\n{'=' * 60}")
            print("PHASE 4: KNOWLEDGE QUEUE PROMOTION CHECK")
            print("=" * 60)
            print(f"\nPending items in memory-palace queue: {len(queue_items)}")
            for item in queue_items[:10]:  # Show top 10
                age_str = (
                    f"{item['age_days']}d ago" if item["age_days"] > 0 else "today"
                )
                print(f"  [{item['priority'].upper()}] {item['file']} ({age_str})")
            if len(queue_items) > 10:
                print(f"  ... and {len(queue_items) - 10} more")

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
