#!/usr/bin/env python3
"""Audit and sync plugin.json files with disk contents.

This script scans plugin directories for commands, skills, agents, hooks, and modules,
compares them with plugin.json registrations, and validates module references.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from sanctum.validators import parse_frontmatter as _parse_frontmatter_canonical
except ImportError:
    _parse_frontmatter_canonical = None

# Import Phase 2-4 modules
sys.path.insert(0, str(Path(__file__).parent))
from update_plugins_modules import (
    KnowledgeQueueChecker,
    MetaEvaluator,
    PerformanceAnalyzer,
)
from update_plugins_modules.constants import CACHE_EXCLUDES


class PluginAuditor:
    """Audit and sync plugin.json registrations with disk contents."""

    MODULE_DESCRIPTION_MAX_LEN = 80
    QUEUE_DISPLAY_LIMIT = 10

    def __init__(self, plugins_root: Path, dry_run: bool = True):
        """Initialize auditor with plugins root and dry-run mode."""
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

    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded based on cache/temp patterns."""
        return any(exclude in path.parts for exclude in CACHE_EXCLUDES)

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

        # Collect every cross-skill reference that targets a specific
        # skill via the full path form ``skills/<name>/modules/<file>``.
        cross_skill_refs = self._scan_cross_skill_refs(plugin_path)

        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir() or self._should_exclude(skill_dir):
                continue

            # Scan modules on disk for this skill
            modules_on_disk = self._scan_skill_modules(skill_dir)
            if not modules_on_disk:
                continue  # Skip skills with no modules

            skill_name = skill_dir.name

            # Bare references (``modules/foo.md`` or frontmatter list
            # entries) from this skill's own files belong to this skill.
            # B-10: previously the audit pre-filtered refs by disk
            # presence at this step, so ``missing`` was always empty.
            referenced_modules = self._scan_skill_local_refs(skill_dir)
            referenced_modules.update(cross_skill_refs.get(skill_name, set()))

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

    def _scan_cross_skill_refs(self, plugin_path: Path) -> dict[str, set[str]]:
        """Map ``skill-name`` to cross-skill full-path module references.

        Scans commands, agents, and other skills in the plugin for the
        ``skills/<name>/modules/<file>`` full-path form.
        """
        cross: dict[str, set[str]] = {}
        scanned_dirs = ("skills", "commands", "agents")
        for sub in scanned_dirs:
            sub_dir = plugin_path / sub
            if not sub_dir.exists():
                continue
            for md_file in sub_dir.rglob("*.md"):
                if self._should_exclude(md_file):
                    continue
                text = self._safe_read(md_file)
                for skill_name, module in re.findall(
                    r"skills/([a-zA-Z0-9_-]+)/modules/([a-zA-Z0-9_-]+\.md)",
                    text,
                ):
                    cross.setdefault(skill_name, set()).add(module)
                for skill_name, module in re.findall(
                    r"plugins/[a-zA-Z0-9_-]+/skills/([a-zA-Z0-9_-]+)"
                    r"/modules/([a-zA-Z0-9_-]+\.md)",
                    text,
                ):
                    cross.setdefault(skill_name, set()).add(module)
        return cross

    def _scan_skill_local_refs(self, skill_dir: Path) -> set[str]:
        """Collect a skill's own module references from its .md files.

        Includes bare ``modules/<file>`` content references and
        frontmatter ``modules:`` list entries.
        """
        refs: set[str] = set()
        for md_file in skill_dir.rglob("*.md"):
            if self._should_exclude(md_file):
                continue
            refs.update(self._extract_module_refs_from_file(md_file))
        return refs

    def _safe_read(self, md_file: Path) -> str:
        """Read a markdown file, returning an empty string on errors.

        F3 fix: log to stderr so a silent disk error does not hide
        cross-skill references and produce a falsely-empty
        ``missing`` audit. Mirrors the logging pattern used by
        ``_extract_module_refs_from_file``.
        """
        try:
            return md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(
                f"[update_plugin_registrations] cannot read {md_file}: {exc}",
                file=sys.stderr,
            )
            return ""

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
        - YAML frontmatter modules: list (bare names, converted to filename.md)
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

            # Extract from YAML frontmatter modules: list
            frontmatter_match = re.match(r"^---\n(.*?\n)---", content, re.DOTALL)
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                # Find the modules: block and extract bare names
                modules_match = re.search(
                    r"^modules:\s*\n((?:- .+\n)*)", frontmatter, re.MULTILINE
                )
                if modules_match:
                    for raw_name in re.findall(
                        r"^- (.+)$", modules_match.group(1), re.MULTILINE
                    ):
                        entry = raw_name.strip()
                        if entry and not entry.startswith("{"):
                            # Normalize any path-prefixed entry to its
                            # basename so the set comparison against
                            # on-disk filenames in _scan_skill_modules
                            # (which stores bare names) is apples-to-apples.
                            # Handles: "modules/foo.md", "./modules/foo.md",
                            # "../modules/foo.md", and bare "foo.md".
                            if "/" in entry:
                                entry = entry.rsplit("/", 1)[-1]
                            # Convert bare name to filename: name -> name.md
                            if not entry.endswith(".md"):
                                entry = f"{entry}.md"
                            references.add(entry)

            # Content-level patterns
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
        except (OSError, UnicodeDecodeError) as exc:
            print(
                f"[update_plugin_registrations] cannot read {md_file}: {exc}",
                file=sys.stderr,
            )

        return references

    def scan_disk_files(self, plugin_path: Path) -> dict[str, list[str]]:
        """Scan disk for actual commands, skills, agents, hooks."""
        results: dict[str, list[str]] = {
            "commands": self._scan_commands_dir(plugin_path / "commands"),
            "skills": self._scan_skills_dir(plugin_path / "skills"),
            "agents": self._scan_agents_dir(plugin_path / "agents"),
            "hooks": self._scan_hooks_dir(plugin_path / "hooks"),
        }
        for items in results.values():
            items.sort()
        return results

    def _scan_commands_dir(self, commands_dir: Path) -> list[str]:
        """Find top-level command .md files, excluding module/steps subdirs."""
        if not commands_dir.exists():
            return []
        out: list[str] = []
        for cmd_file in commands_dir.rglob("*.md"):
            if self._should_exclude(cmd_file):
                continue
            # Skip files nested in module subdirs (e.g.
            # commands/fix-pr-modules/steps/1-analyze.md).
            rel = cmd_file.relative_to(commands_dir)
            if any(
                "module" in part.lower() or part == "steps" for part in rel.parts[:-1]
            ):
                continue
            if len(rel.parts) == 1:
                out.append(f"./commands/{cmd_file.name}")
        return out

    def _scan_skills_dir(self, skills_dir: Path) -> list[str]:
        """Find skill directories with SKILL.md or root-level .md files.

        Directories containing only ``modules/`` subdirectories are
        module holders, not skills, and are skipped.
        """
        if not skills_dir.exists():
            return []
        out: list[str] = []
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir() or self._should_exclude(skill_dir):
                continue
            has_skill_md = (skill_dir / "SKILL.md").exists()
            has_root_md = any(
                f.suffix == ".md" for f in skill_dir.iterdir() if f.is_file()
            )
            if has_skill_md or has_root_md:
                out.append(f"./skills/{skill_dir.name}")
        return out

    def _scan_agents_dir(self, agents_dir: Path) -> list[str]:
        """Find top-level agent .md files."""
        if not agents_dir.exists():
            return []
        return [
            f"./agents/{agent_file.name}"
            for agent_file in agents_dir.glob("*.md")
            if not self._should_exclude(agent_file)
        ]

    def _scan_hooks_dir(self, hooks_dir: Path) -> list[str]:
        """Find executable hook files (.sh/.py).

        Excludes test files (``test_*``) and private helpers (``_*``).
        Markdown files in ``hooks/`` are documentation, not executable
        hooks, and are not registered.
        """
        if not hooks_dir.exists():
            return []
        out: list[str] = []
        for hook_file in hooks_dir.iterdir():
            if self._should_exclude(hook_file):
                continue
            if not hook_file.is_file() or hook_file.suffix not in (".sh", ".py"):
                continue
            if hook_file.name.startswith(("test_", "_")):
                continue
            out.append(f"./hooks/{hook_file.name}")
        return out

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
            List of hook script paths in ./hooks/filename format, or None if not found

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

    def _resolve_hooks_set(self, plugin_path: Path, json_value: Any) -> set[str] | None:
        """Resolve registered hooks from plugin.json or auto-loaded hooks.json.

        Returns None if the category should be skipped.
        """
        standard_hooks_json = plugin_path / "hooks" / "hooks.json"

        if isinstance(json_value, str):
            if json_value.endswith(".json"):
                resolved = self.resolve_hooks_json(plugin_path, json_value)
                return set(resolved) if resolved is not None else None
            print(f"[WARN] Unexpected hooks format: {json_value}")
            return None

        if standard_hooks_json.exists():
            resolved = self.resolve_hooks_json(plugin_path, "./hooks/hooks.json")
            return set(resolved) if resolved is not None else set()

        return set(json_value) if json_value else set()

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
        plugin_path = Path(plugin_path)

        discrepancies: dict[str, Any] = {
            "missing": {},  # On disk but not in plugin.json
            "stale": {},  # In plugin.json but not on disk
        }

        for category in ["commands", "skills", "agents", "hooks"]:
            disk_set = set(on_disk[category])
            json_value = in_json.get(category, [])

            if category == "hooks":
                hooks_set = self._resolve_hooks_set(plugin_path, json_value)
                if hooks_set is None:
                    continue
                json_set = hooks_set
            else:
                json_set = set(json_value) if json_value else set()

            missing = disk_set - json_set
            stale = json_set - disk_set

            if missing:
                discrepancies["missing"][category] = sorted(missing)
            if stale:
                discrepancies["stale"][category] = sorted(stale)

        # Claude Code auto-loads hooks/hooks.json if it exists, so
        # plugins should NOT list it in plugin.json (causes duplicate
        # registration). Only flag hook *scripts* that exist on disk
        # but aren't referenced by any hooks.json file.

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

    def _read_module_description(self, module_path: Path) -> str:
        """Return the first prose line from a module file.

        Skips YAML frontmatter (``---`` delimited), blank lines, and
        heading lines (starting with ``#``).  If the resulting line
        exceeds 80 characters it is truncated to 77 chars with an
        ellipsis appended.  Returns an empty string when the file is
        missing, unreadable, or contains no prose.
        """
        try:
            lines = module_path.read_text(encoding="utf-8").splitlines()
            in_frontmatter = False
            for line in lines:
                stripped = line.strip()
                if stripped == "---":
                    in_frontmatter = not in_frontmatter
                    continue
                if in_frontmatter or not stripped:
                    continue
                if stripped.startswith("#"):
                    continue
                if len(stripped) > self.MODULE_DESCRIPTION_MAX_LEN:
                    return stripped[:77] + "..."
                return stripped
        except FileNotFoundError:
            pass  # Expected: orphaned module may not exist on disk
        except OSError as exc:
            print(
                f"[update_plugin_registrations] cannot read {module_path}: {exc}",
                file=sys.stderr,
            )
        return ""

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
                    module_path = (
                        self.plugins_root
                        / plugin_name
                        / "skills"
                        / skill_name
                        / "modules"
                        / module
                    )
                    desc = self._read_module_description(module_path)
                    if desc:
                        print(f"      - modules/{module}")
                        print(f"        {desc}")
                    else:
                        print(f"      - modules/{module}")
            if issues.get("missing"):
                print("    Missing (referenced but not found):")
                for module in issues["missing"]:
                    print(f"      - modules/{module}")

    def _discover_plugin(
        self, plugin_name: str
    ) -> tuple[Path, Path, dict[str, Any]] | None:
        """Load plugin paths and current plugin.json data.

        Returns:
            Tuple of (plugin_path, plugin_json_path, plugin_data), or None if
            there is nothing to fix for this plugin.

        """
        if plugin_name not in self.discrepancies:
            return None

        plugin_path = self.plugins_root / plugin_name
        plugin_json_path = plugin_path / ".claude-plugin" / "plugin.json"

        try:
            with plugin_json_path.open(encoding="utf-8") as f:
                plugin_data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"[ERROR] {plugin_name}: failed to read {plugin_json_path}: {exc}",
                file=sys.stderr,
            )
            return None

        return plugin_path, plugin_json_path, plugin_data

    def _validate_registration(
        self,
        plugin_name: str,
        plugin_path: Path,
        plugin_data: dict[str, Any],
    ) -> tuple[dict[str, Any], bool]:
        """Apply discrepancy rules to plugin_data and report hooks needing manual fixes.

        Mutates plugin_data in place for non-hooks categories.

        Returns:
            Tuple of (updated plugin_data, hooks_need_manual_fix flag).

        """
        disc = self.discrepancies[plugin_name]
        standard_hooks_json = plugin_path / "hooks" / "hooks.json"
        hooks_need_manual_fix = False

        # Fix missing entries (add them)
        for category, items in disc["missing"].items():
            # Hooks require manual update to hooks.json (NOT plugin.json)
            # Claude Code auto-loads hooks/hooks.json; adding to plugin.json
            # causes duplicate registrations
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

        return plugin_data, hooks_need_manual_fix

    def _apply_fixes(
        self,
        plugin_name: str,
        plugin_json_path: Path,
        plugin_data: dict[str, Any],
    ) -> bool:
        """Write the updated plugin.json to disk when non-hooks changes exist.

        Returns:
            True on success (or when no write is needed).

        """
        disc = self.discrepancies[plugin_name]
        non_hooks_changes = any(
            cat != "hooks"
            for cat in list(disc["missing"].keys()) + list(disc["stale"].keys())
        )

        if not non_hooks_changes:
            return True

        if not self.dry_run:
            with plugin_json_path.open("w", encoding="utf-8") as f:
                json.dump(plugin_data, f, indent=2, ensure_ascii=False)
                f.write("\n")  # Trailing newline
            print(f"[FIXED] {plugin_name}: plugin.json updated")
        else:
            print(f"[DRY-RUN] {plugin_name}: would update plugin.json")

        return True

    def fix_plugin(self, plugin_name: str) -> bool:
        """Fix discrepancies by updating plugin.json or hooks.json.

        Note: For hooks, if hooks/hooks.json exists (auto-loaded by Claude Code),
        discrepancies are reported but require manual fixes to hooks.json.
        We do NOT add "hooks" key to plugin.json as that causes duplicates.
        """
        if plugin_name not in self.discrepancies:
            return True  # Nothing to fix
        discovered = self._discover_plugin(plugin_name)
        if discovered is None:
            return False  # I/O error reading plugin.json

        plugin_path, plugin_json_path, plugin_data = discovered

        plugin_data, _hooks_manual = self._validate_registration(
            plugin_name, plugin_path, plugin_data
        )

        return self._apply_fixes(plugin_name, plugin_json_path, plugin_data)

    def analyze_skill_performance(self, plugin_name: str) -> dict[str, Any]:
        """Phase 2: Analyze skill execution metrics for performance issues."""
        return self.performance_analyzer.analyze_plugin(plugin_name)

    def check_meta_evaluation(self, plugin_path: Path) -> dict[str, Any]:
        """Phase 3: Validate recursive quality of evaluation-related skills."""
        return self.meta_evaluator.check_plugin(plugin_path)

    def check_knowledge_queue(self) -> list[dict[str, Any]]:
        """Phase 4: Scan memory-palace queue for pending research items."""
        return self.queue_checker.check_queue()

    def _print_performance_summary(self, report: dict[str, Any]) -> None:
        """Print Phase 2 performance analysis summary."""
        print(f"\n{'=' * 60}")
        print("PHASE 2: PERFORMANCE & IMPROVEMENT ANALYSIS")
        print("=" * 60)
        for plugin, data in report.items():
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

    def _print_meta_eval_summary(self, report: dict[str, Any]) -> None:
        """Print Phase 3 meta-evaluation summary."""
        print(f"\n{'=' * 60}")
        print("PHASE 3: META-EVALUATION CHECK")
        print("=" * 60)
        for plugin, issues in report.items():
            print(f"\n{plugin}:")
            if issues["missing_toc"]:
                print(f"  📋 Missing TOC: {', '.join(issues['missing_toc'])}")
            if issues["missing_verification"]:
                skills = ", ".join(issues["missing_verification"])
                print(f"  🔍 Missing verification: {skills}")
            if issues["missing_tests"]:
                print(f"  🧪 Missing tests: {', '.join(issues['missing_tests'])}")

    def _print_queue_summary(self, queue_items: list[dict[str, Any]]) -> None:
        """Print Phase 4 knowledge queue summary."""
        print(f"\n{'=' * 60}")
        print("PHASE 4: KNOWLEDGE QUEUE PROMOTION CHECK")
        print("=" * 60)
        print(f"\nPending items in memory-palace queue: {len(queue_items)}")
        limit = self.QUEUE_DISPLAY_LIMIT
        for item in queue_items[:limit]:
            age_str = f"{item['age_days']}d ago" if item["age_days"] > 0 else "today"
            print(f"  [{item['priority'].upper()}] {item['file']} ({age_str})")
        if len(queue_items) > limit:
            print(f"  ... and {len(queue_items) - limit} more")

    def audit_all(self, specific_plugin: str | None = None) -> int:
        """Audit all plugins or a specific plugin."""
        if specific_plugin:
            plugins = [specific_plugin]
        else:
            plugins = sorted(
                p.name
                for p in self.plugins_root.iterdir()
                if p.is_dir() and not p.name.startswith(".")
            )

        print(f"Auditing {len(plugins)} plugin(s)...\n")

        plugins_with_issues = 0
        performance_report: dict[str, Any] = {}
        meta_eval_report: dict[str, Any] = {}

        for plugin_name in plugins:
            if self.audit_plugin(plugin_name):
                plugins_with_issues += 1

            perf_data = self.analyze_skill_performance(plugin_name)
            if any(perf_data.values()):
                performance_report[plugin_name] = perf_data

            plugin_path = self.plugins_root / plugin_name
            meta_issues = self.check_meta_evaluation(plugin_path)
            if any(meta_issues.values()):
                meta_eval_report[plugin_name] = meta_issues

        queue_items = self.check_knowledge_queue()

        print(f"\n{'=' * 60}")
        print("AUDIT SUMMARY")
        print("=" * 60)
        print(f"Plugins audited: {len(plugins)}")
        print(f"Plugins with registration issues: {len(self.discrepancies)}")
        print(f"Plugins with module issues: {len(self.module_issues)}")
        print(f"Plugins clean: {len(plugins) - plugins_with_issues}")

        if performance_report:
            self._print_performance_summary(performance_report)
        if meta_eval_report:
            self._print_meta_eval_summary(meta_eval_report)
        if queue_items:
            self._print_queue_summary(queue_items)

        if not self.dry_run and plugins_with_issues > 0:
            print(f"\n{'=' * 60}")
            print("FIXING DISCREPANCIES")
            print("=" * 60)
            for plugin_name in self.discrepancies:
                self.fix_plugin(plugin_name)

        return plugins_with_issues


def main() -> None:
    """Audit and sync plugin.json files with disk contents."""
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
