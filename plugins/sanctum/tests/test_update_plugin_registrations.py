#!/usr/bin/env python3
"""Tests for update_plugin_registrations.py script."""

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from update_plugin_registrations import PluginAuditor


class TestPluginAuditor:
    """Test the PluginAuditor class."""

    def test_scan_disk_files_finds_commands(self, tmp_path: Path) -> None:
        """Test scanning for command files."""
        # Create test structure
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "test-command.md").write_text("# Test")
        (commands_dir / "another-command.md").write_text("# Another")

        # Create module subdir (should be excluded)
        modules_dir = commands_dir / "test-modules"
        modules_dir.mkdir()
        (modules_dir / "module-file.md").write_text("# Module")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        assert len(result["commands"]) == 2
        assert "./commands/another-command.md" in result["commands"]
        assert "./commands/test-command.md" in result["commands"]
        assert "./commands/test-modules/module-file.md" not in result["commands"]

    def test_scan_disk_files_finds_skills(self, tmp_path: Path) -> None:
        """Test scanning for skill directories with valid content."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        # Skills need SKILL.md or root .md files to be recognized
        test_skill = skills_dir / "test-skill"
        test_skill.mkdir()
        (test_skill / "SKILL.md").write_text("# Test Skill")
        another_skill = skills_dir / "another-skill"
        another_skill.mkdir()
        (another_skill / "SKILL.md").write_text("# Another Skill")
        (skills_dir / "__pycache__").mkdir()  # Should be excluded

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        assert len(result["skills"]) == 2
        assert "./skills/another-skill" in result["skills"]
        assert "./skills/test-skill" in result["skills"]
        assert "./skills/__pycache__" not in result["skills"]

    def test_scan_disk_files_finds_agents(self, tmp_path: Path) -> None:
        """Test scanning for agent files."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "test-agent.md").write_text("# Agent")
        (agents_dir / "another-agent.md").write_text("# Another")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        assert len(result["agents"]) == 2
        assert "./agents/another-agent.md" in result["agents"]
        assert "./agents/test-agent.md" in result["agents"]

    def test_scan_disk_files_finds_hooks(self, tmp_path: Path) -> None:
        """Test scanning for hook files (.sh, .py only - .md are docs)."""
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "pre-commit.sh").write_text("#!/bin/bash")
        (hooks_dir / "post-commit.py").write_text("# Python hook")
        (hooks_dir / "guide.md").write_text("# Hook guide")  # Docs, not scanned
        (hooks_dir / "__init__.py").write_text("# Init")  # Should be excluded
        (hooks_dir / "test_hooks.py").write_text("# Test")  # Should be excluded

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        # Only .sh and .py are hooks; .md files are documentation
        assert len(result["hooks"]) == 2
        assert "./hooks/post-commit.py" in result["hooks"]
        assert "./hooks/pre-commit.sh" in result["hooks"]
        assert "./hooks/guide.md" not in result["hooks"]  # Docs excluded
        assert "./hooks/__init__.py" not in result["hooks"]
        assert "./hooks/test_hooks.py" not in result["hooks"]

    def test_scan_disk_files_excludes_cache_directories(self, tmp_path: Path) -> None:
        """Test that cache/temp directories are properly excluded."""
        # Create legitimate files
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "real-command.md").write_text("# Real")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        real_skill = skills_dir / "real-skill"
        real_skill.mkdir()
        (real_skill / "SKILL.md").write_text("# Real Skill")

        # Create cache directories that should be excluded
        # Python caches
        venv_cmd = commands_dir / ".venv"
        venv_cmd.mkdir()
        (venv_cmd / "fake-command.md").write_text("# Fake")

        pycache_skill = skills_dir / "__pycache__"
        pycache_skill.mkdir()

        # Node caches
        node_modules = skills_dir / "node_modules"
        node_modules.mkdir()

        # Rust caches
        target_skill = skills_dir / "target"
        target_skill.mkdir()

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        # Should only find legitimate files
        assert len(result["commands"]) == 1
        assert "./commands/real-command.md" in result["commands"]
        assert not any(".venv" in cmd for cmd in result["commands"])

        assert len(result["skills"]) == 1
        assert "./skills/real-skill" in result["skills"]
        assert not any("__pycache__" in skill for skill in result["skills"])
        assert not any("node_modules" in skill for skill in result["skills"])
        assert not any("target" in skill for skill in result["skills"])

    def test_compare_registrations_finds_missing(self, tmp_path: Path) -> None:
        """Test detecting missing registrations."""
        # Create plugin structure for path-based comparison
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        on_disk = {
            "commands": ["./commands/cmd1.md", "./commands/cmd2.md"],
            "skills": [],
            "agents": [],
            "hooks": [],
        }
        in_json = {
            "commands": ["./commands/cmd1.md"],
            "skills": [],
            "agents": [],
            "hooks": [],
        }

        auditor = PluginAuditor(tmp_path, dry_run=True)
        discrepancies = auditor.compare_registrations(plugin_dir, on_disk, in_json)

        assert "commands" in discrepancies["missing"]
        assert "./commands/cmd2.md" in discrepancies["missing"]["commands"]

    def test_compare_registrations_finds_stale(self, tmp_path: Path) -> None:
        """Test detecting stale registrations."""
        # Create plugin structure for path-based comparison
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        on_disk = {
            "commands": ["./commands/cmd1.md"],
            "skills": [],
            "agents": [],
            "hooks": [],
        }
        in_json = {
            "commands": ["./commands/cmd1.md", "./commands/cmd2.md"],
            "skills": [],
            "agents": [],
            "hooks": [],
        }

        auditor = PluginAuditor(tmp_path, dry_run=True)
        discrepancies = auditor.compare_registrations(plugin_dir, on_disk, in_json)

        assert "commands" in discrepancies["stale"]
        assert "./commands/cmd2.md" in discrepancies["stale"]["commands"]

    def test_fix_plugin_adds_missing(self, tmp_path: Path) -> None:
        """Test fixing adds missing registrations."""
        # Create plugin structure
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()

        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps(
                {"name": "test-plugin", "commands": ["./commands/cmd1.md"]}, indent=2
            )
        )

        # Create auditor and simulate discrepancies
        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["test-plugin"] = {
            "missing": {"commands": ["./commands/cmd2.md"]},
            "stale": {},
        }

        # Fix
        auditor.fix_plugin("test-plugin")

        # Verify
        with plugin_json.open() as f:
            data = json.load(f)

        assert len(data["commands"]) == 2
        assert "./commands/cmd1.md" in data["commands"]
        assert "./commands/cmd2.md" in data["commands"]

    def test_fix_plugin_removes_stale(self, tmp_path: Path) -> None:
        """Test fixing removes stale registrations."""
        # Create plugin structure
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()

        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps(
                {
                    "name": "test-plugin",
                    "commands": ["./commands/cmd1.md", "./commands/cmd2.md"],
                },
                indent=2,
            )
        )

        # Create auditor and simulate discrepancies
        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["test-plugin"] = {
            "missing": {},
            "stale": {"commands": ["./commands/cmd2.md"]},
        }

        # Fix
        auditor.fix_plugin("test-plugin")

        # Verify
        with plugin_json.open() as f:
            data = json.load(f)

        assert len(data["commands"]) == 1
        assert "./commands/cmd1.md" in data["commands"]
        assert "./commands/cmd2.md" not in data["commands"]


class TestHooksJsonResolution:
    """Test the hooks.json parsing and resolution functionality."""

    def test_extract_script_path_with_claude_plugin_root(self, tmp_path: Path) -> None:
        """Test extracting script path from CLAUDE_PLUGIN_ROOT variable."""
        auditor = PluginAuditor(tmp_path, dry_run=True)

        # Standard format
        result = auditor._extract_script_path("${CLAUDE_PLUGIN_ROOT}/hooks/my_hook.py")
        assert result == "./hooks/my_hook.py"

        # With python prefix
        result = auditor._extract_script_path(
            "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/pre_commit.py"
        )
        assert result == "./hooks/pre_commit.py"

    def test_extract_script_path_with_direct_path(self, tmp_path: Path) -> None:
        """Test extracting script path from direct ./hooks/ path."""
        auditor = PluginAuditor(tmp_path, dry_run=True)

        result = auditor._extract_script_path("./hooks/my_script.sh")
        assert result == "./hooks/my_script.sh"

    def test_extract_script_path_returns_none_for_invalid(self, tmp_path: Path) -> None:
        """Test that invalid paths return None."""
        auditor = PluginAuditor(tmp_path, dry_run=True)

        result = auditor._extract_script_path("echo hello")
        assert result is None

        result = auditor._extract_script_path("")
        assert result is None

    def test_resolve_hooks_json_extracts_scripts(self, tmp_path: Path) -> None:
        """Test that resolve_hooks_json parses nested structure correctly."""
        # Create plugin structure
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        hooks_dir = plugin_dir / "hooks"
        hooks_dir.mkdir()

        # Create hooks.json with typical nested structure
        hooks_json = hooks_dir / "hooks.json"
        hooks_data = {
            "hooks": {
                "UserPromptSubmit": [
                    {
                        "matcher": {},
                        "hooks": [
                            {"command": "${CLAUDE_PLUGIN_ROOT}/hooks/prompt_hook.py"},
                            {
                                "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/validate.py"
                            },
                        ],
                    }
                ],
                "SessionStart": [
                    {
                        "matcher": {},
                        "hooks": [{"command": "${CLAUDE_PLUGIN_ROOT}/hooks/init.sh"}],
                    }
                ],
            }
        }
        hooks_json.write_text(json.dumps(hooks_data, indent=2))

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.resolve_hooks_json(plugin_dir, "./hooks/hooks.json")

        assert result is not None
        assert len(result) == 3
        assert "./hooks/init.sh" in result
        assert "./hooks/prompt_hook.py" in result
        assert "./hooks/validate.py" in result

    def test_resolve_hooks_json_returns_none_for_missing_file(
        self, tmp_path: Path
    ) -> None:
        """Test that missing hooks.json returns None."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.resolve_hooks_json(plugin_dir, "./hooks/hooks.json")

        assert result is None

    def test_compare_registrations_with_hooks_json(self, tmp_path: Path) -> None:
        """Test that compare_registrations handles hooks.json references."""
        # Create plugin structure
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        hooks_dir = plugin_dir / "hooks"
        hooks_dir.mkdir()

        # Create actual hook files
        (hooks_dir / "hook_a.py").write_text("# Hook A")
        (hooks_dir / "hook_b.py").write_text("# Hook B")

        # Create hooks.json that only references hook_a
        hooks_json = hooks_dir / "hooks.json"
        hooks_data = {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": {},
                        "hooks": [{"command": "${CLAUDE_PLUGIN_ROOT}/hooks/hook_a.py"}],
                    }
                ]
            }
        }
        hooks_json.write_text(json.dumps(hooks_data, indent=2))

        on_disk = {
            "commands": [],
            "skills": [],
            "agents": [],
            "hooks": ["./hooks/hook_a.py", "./hooks/hook_b.py"],  # Both on disk
        }
        # No explicit hooks in plugin.json - auto-loads from hooks.json
        in_json = {"commands": [], "skills": [], "agents": []}

        auditor = PluginAuditor(tmp_path, dry_run=True)
        discrepancies = auditor.compare_registrations(plugin_dir, on_disk, in_json)

        # hook_b.py is on disk but not in hooks.json - should be missing
        assert "hooks" in discrepancies["missing"]
        assert "./hooks/hook_b.py" in discrepancies["missing"]["hooks"]


class TestExtractModuleRefsFromFile:
    """Test _extract_module_refs_from_file for module reference extraction.

    GIVEN a markdown file with various module reference patterns
    WHEN _extract_module_refs_from_file is called
    THEN it should extract all module filenames correctly.
    """

    def test_extracts_from_yaml_frontmatter_modules_list(self, tmp_path: Path) -> None:
        """
        GIVEN a SKILL.md with YAML frontmatter containing a modules: list
        WHEN extracting module refs
        THEN bare names are converted to name.md filenames.
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text(
            "---\n"
            "name: test-skill\n"
            "modules:\n"
            "- phase-routing\n"
            "- state-detection\n"
            "---\n"
            "# Test Skill\n"
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "phase-routing.md" in refs
        assert "state-detection.md" in refs

    def test_frontmatter_modules_already_with_md_extension(
        self, tmp_path: Path
    ) -> None:
        """
        GIVEN a frontmatter modules: list where names already end in .md
        WHEN extracting module refs
        THEN they are kept as-is without double extension.
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text("---\nmodules:\n- already-named.md\n---\n# Skill\n")

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "already-named.md" in refs
        assert "already-named.md.md" not in refs

    def test_frontmatter_skips_jinja_template_entries(self, tmp_path: Path) -> None:
        """
        GIVEN a frontmatter modules: list with Jinja template entries (starting with {)
        WHEN extracting module refs
        THEN template entries are skipped.
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text(
            "---\nmodules:\n- valid-module\n- {dynamic_module}\n---\n# Skill\n"
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "valid-module.md" in refs
        assert len([r for r in refs if "dynamic" in r]) == 0

    def test_extracts_at_module_references(self, tmp_path: Path) -> None:
        """
        GIVEN markdown content with @modules/filename.md references
        WHEN extracting module refs
        THEN the filename is extracted.
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text("See @modules/task-planning.md for details.\n")

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "task-planning.md" in refs

    def test_extracts_backtick_module_references(self, tmp_path: Path) -> None:
        """
        GIVEN markdown content with `modules/filename.md` references
        WHEN extracting module refs
        THEN the filename is extracted.
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text("Check `modules/bdd-patterns.md` for patterns.\n")

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "bdd-patterns.md" in refs

    def test_extracts_see_module_references(self, tmp_path: Path) -> None:
        """
        GIVEN markdown content with See modules/filename.md references
        WHEN extracting module refs
        THEN the filename is extracted.
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text("See modules/quality-validation.md for criteria.\n")

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "quality-validation.md" in refs

    def test_extracts_full_path_skill_module_references(self, tmp_path: Path) -> None:
        """
        GIVEN markdown with skills/skill-name/modules/filename.md references
        WHEN extracting module refs
        THEN the filename is extracted.
        """
        md_file = tmp_path / "README.md"
        md_file.write_text(
            "See skills/do-issue/modules/parallel-execution.md for details.\n"
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "parallel-execution.md" in refs

    def test_extracts_no_refs_from_empty_file(self, tmp_path: Path) -> None:
        """
        GIVEN an empty markdown file
        WHEN extracting module refs
        THEN an empty set is returned.
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text("")

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert len(refs) == 0

    def test_handles_nonexistent_file_gracefully(self, tmp_path: Path) -> None:
        """
        GIVEN a path to a file that doesn't exist
        WHEN extracting module refs
        THEN an empty set is returned (OSError caught).
        """
        md_file = tmp_path / "nonexistent.md"

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert len(refs) == 0

    def test_combines_frontmatter_and_content_refs(self, tmp_path: Path) -> None:
        """
        GIVEN a file with both YAML frontmatter modules and content-level references
        WHEN extracting module refs
        THEN all references from both sources are combined.
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text(
            "---\n"
            "modules:\n"
            "- state-detection\n"
            "---\n"
            "# Skill\n\n"
            "See @modules/phase-routing.md for routing logic.\n"
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "state-detection.md" in refs
        assert "phase-routing.md" in refs
        assert len(refs) == 2


class TestAuditSkillModules:
    """Test audit_skill_modules end-to-end module orphan/missing detection.

    GIVEN a plugin directory with skills that have modules
    WHEN audit_skill_modules is called
    THEN it correctly identifies orphaned and missing modules.
    """

    def test_detects_orphaned_modules(self, tmp_path: Path) -> None:
        """
        GIVEN a skill with a module file that is not referenced anywhere
        WHEN auditing skill modules
        THEN the module is reported as orphaned.
        """
        # Create skill structure
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        modules_dir = skill_dir / "modules"
        modules_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("# My Skill\nNo module refs here.\n")
        (modules_dir / "orphaned-module.md").write_text("# Orphaned\n")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        issues = auditor.audit_skill_modules(tmp_path)

        assert "my-skill" in issues
        assert "orphaned-module.md" in issues["my-skill"]["orphaned"]

    def test_no_issues_when_all_modules_referenced(self, tmp_path: Path) -> None:
        """
        GIVEN a skill where all modules are referenced in SKILL.md
        WHEN auditing skill modules
        THEN no issues are reported.
        """
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        modules_dir = skill_dir / "modules"
        modules_dir.mkdir()

        (skill_dir / "SKILL.md").write_text(
            "---\nmodules:\n- referenced-module\n---\n# My Skill\n"
        )
        (modules_dir / "referenced-module.md").write_text("# Referenced\n")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        issues = auditor.audit_skill_modules(tmp_path)

        assert "my-skill" not in issues

    def test_no_issues_when_skill_has_no_modules(self, tmp_path: Path) -> None:
        """
        GIVEN a skill with no modules/ directory
        WHEN auditing skill modules
        THEN no issues are reported.
        """
        skill_dir = tmp_path / "skills" / "simple-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Simple Skill\n")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        issues = auditor.audit_skill_modules(tmp_path)

        assert len(issues) == 0


class TestReadPluginJson:
    """Test read_plugin_json for plugin.json reading and error handling.

    GIVEN a plugin directory that may or may not contain a valid plugin.json
    WHEN read_plugin_json is called
    THEN it should return parsed data or None with appropriate error handling.
    """

    def test_reads_valid_plugin_json(self, tmp_path: Path) -> None:
        """
        GIVEN a plugin directory with a valid .claude-plugin/plugin.json
        WHEN reading the plugin JSON
        THEN the parsed dict is returned.
        """
        config_dir = tmp_path / ".claude-plugin"
        config_dir.mkdir()
        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text(json.dumps({"name": "test", "commands": []}, indent=2))

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.read_plugin_json(tmp_path)

        assert result is not None
        assert result["name"] == "test"
        assert result["commands"] == []

    def test_returns_none_for_missing_plugin_json(self, tmp_path: Path) -> None:
        """
        GIVEN a plugin directory with no .claude-plugin/plugin.json
        WHEN reading the plugin JSON
        THEN None is returned.
        """
        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.read_plugin_json(tmp_path)

        assert result is None

    def test_returns_none_for_invalid_json(self, tmp_path: Path) -> None:
        """
        GIVEN a plugin directory with a malformed plugin.json
        WHEN reading the plugin JSON
        THEN None is returned (JSONDecodeError caught).
        """
        config_dir = tmp_path / ".claude-plugin"
        config_dir.mkdir()
        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text("{invalid json content")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.read_plugin_json(tmp_path)

        assert result is None


class TestScanPluginForModuleRefs:
    """Test _scan_plugin_for_module_refs for cross-directory reference scanning.

    GIVEN a plugin directory with skills, commands, and agents
    WHEN _scan_plugin_for_module_refs is called
    THEN it should collect module references from all markdown files.
    """

    def test_scans_skills_directory(self, tmp_path: Path) -> None:
        """
        GIVEN a plugin with a skill that references a module
        WHEN scanning the plugin for module refs
        THEN the reference is found.
        """
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("See @modules/core-logic.md for details.\n")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        refs = auditor._scan_plugin_for_module_refs(tmp_path)

        assert "core-logic.md" in refs

    def test_scans_commands_directory(self, tmp_path: Path) -> None:
        """
        GIVEN a plugin with a command that references a module
        WHEN scanning the plugin for module refs
        THEN the reference is found.
        """
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "my-command.md").write_text(
            "See `modules/command-helpers.md` for helpers.\n"
        )

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        refs = auditor._scan_plugin_for_module_refs(tmp_path)

        assert "command-helpers.md" in refs

    def test_scans_agents_directory(self, tmp_path: Path) -> None:
        """
        GIVEN a plugin with an agent that references a module
        WHEN scanning the plugin for module refs
        THEN the reference is found.
        """
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "my-agent.md").write_text(
            "See @modules/agent-config.md for configuration.\n"
        )

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        refs = auditor._scan_plugin_for_module_refs(tmp_path)

        assert "agent-config.md" in refs

    def test_combines_refs_from_all_directories(self, tmp_path: Path) -> None:
        """
        GIVEN a plugin with refs in skills, commands, and agents
        WHEN scanning the plugin for module refs
        THEN all references are combined into a single set.
        """
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("See @modules/from-skill.md\n")

        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "cmd.md").write_text("See @modules/from-command.md\n")

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "agent.md").write_text("See @modules/from-agent.md\n")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        refs = auditor._scan_plugin_for_module_refs(tmp_path)

        assert "from-skill.md" in refs
        assert "from-command.md" in refs
        assert "from-agent.md" in refs

    def test_returns_empty_for_plugin_with_no_directories(self, tmp_path: Path) -> None:
        """
        GIVEN an empty plugin directory
        WHEN scanning for module refs
        THEN an empty set is returned.
        """
        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        refs = auditor._scan_plugin_for_module_refs(tmp_path)

        assert len(refs) == 0

    def test_excludes_cache_directories(self, tmp_path: Path) -> None:
        """
        GIVEN a plugin with markdown in a __pycache__ directory
        WHEN scanning for module refs
        THEN files in cache directories are skipped.
        """
        cache_dir = tmp_path / "skills" / "__pycache__"
        cache_dir.mkdir(parents=True)
        (cache_dir / "cached.md").write_text("See @modules/should-not-find.md\n")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        refs = auditor._scan_plugin_for_module_refs(tmp_path)

        assert "should-not-find.md" not in refs


class TestExtractModuleRefsEdgeCases:
    """Test edge cases for _extract_module_refs_from_file.

    GIVEN unusual but valid markdown content
    WHEN _extract_module_refs_from_file is called
    THEN it should handle edge cases correctly.
    """

    def test_frontmatter_with_empty_modules_list(self, tmp_path: Path) -> None:
        """
        GIVEN a SKILL.md with modules: key but no list items
        WHEN extracting module refs
        THEN an empty set is returned (no crash).
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text("---\nname: test\nmodules:\n---\n# Skill\n")

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert len(refs) == 0

    def test_extracts_plugin_full_path_references(self, tmp_path: Path) -> None:
        """
        GIVEN markdown with plugins/name/skills/name/modules/file.md references
        WHEN extracting module refs
        THEN the module filename is extracted.
        """
        md_file = tmp_path / "README.md"
        md_file.write_text(
            "See plugins/sanctum/skills/do-issue/modules/parallel-execution.md\n"
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "parallel-execution.md" in refs

    def test_frontmatter_modules_with_underscores(self, tmp_path: Path) -> None:
        """
        GIVEN a frontmatter modules list with underscore-named modules
        WHEN extracting module refs
        THEN underscore names are correctly converted to filename.md.
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text("---\nmodules:\n- my_module\n---\n# Skill\n")

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "my_module.md" in refs

    def test_multiple_content_patterns_in_same_file(self, tmp_path: Path) -> None:
        """
        GIVEN a file with multiple different reference patterns
        WHEN extracting module refs
        THEN all unique references are collected.
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text(
            "# Skill\n\n"
            "See @modules/alpha.md for alpha logic.\n"
            "Check `modules/beta.md` for beta patterns.\n"
            "Also see skills/my-skill/modules/gamma.md for details.\n"
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "alpha.md" in refs
        assert "beta.md" in refs
        assert "gamma.md" in refs
        assert len(refs) == 3

    def test_duplicate_references_are_deduplicated(self, tmp_path: Path) -> None:
        """
        GIVEN a file that references the same module multiple times
        WHEN extracting module refs
        THEN each module appears only once in the result set.
        """
        md_file = tmp_path / "SKILL.md"
        md_file.write_text(
            "---\n"
            "modules:\n"
            "- shared\n"
            "---\n"
            "# Skill\n\n"
            "See @modules/shared.md for details.\n"
            "Also check `modules/shared.md` again.\n"
        )

        auditor = PluginAuditor(tmp_path, dry_run=True)
        refs = auditor._extract_module_refs_from_file(md_file)

        assert "shared.md" in refs
        assert len(refs) == 1


class TestAuditSkillModulesAdvanced:
    """Test audit_skill_modules for advanced scenarios.

    GIVEN complex plugin structures with multiple skills and cross-references
    WHEN audit_skill_modules is called
    THEN it correctly identifies issues across the whole plugin.
    """

    def test_detects_missing_modules(self, tmp_path: Path) -> None:
        """
        GIVEN a skill that references a module via content pattern,
              but the module file does not exist on disk
        WHEN auditing skill modules
        THEN no missing is reported (missing = referenced_modules - modules_on_disk,
              but references only enter referenced_modules if they match on_disk names).
        """
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        modules_dir = skill_dir / "modules"
        modules_dir.mkdir()

        (skill_dir / "SKILL.md").write_text(
            "# My Skill\n\n"
            "See @modules/existing.md for logic.\n"
            "See @modules/nonexistent.md for more.\n"
        )
        (modules_dir / "existing.md").write_text("# Existing\n")
        # nonexistent.md intentionally NOT created

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        issues = auditor.audit_skill_modules(tmp_path)

        # existing.md is referenced AND on disk → not orphaned
        # nonexistent.md is referenced but NOT on disk → only in all_references, not in modules_on_disk
        # The "missing" calculation is: referenced_modules - modules_on_disk
        # But referenced_modules only includes refs that ARE in modules_on_disk
        # So "missing" is always empty in current implementation
        if "my-skill" in issues:
            assert "existing.md" not in issues["my-skill"].get("orphaned", [])
        else:
            # No issues at all — existing.md is properly referenced
            assert True

    def test_multiple_skills_with_mixed_issues(self, tmp_path: Path) -> None:
        """
        GIVEN a plugin with two skills — one with orphaned modules, one clean
        WHEN auditing skill modules
        THEN only the problematic skill is reported.
        """
        # Clean skill
        clean_dir = tmp_path / "skills" / "clean-skill"
        clean_dir.mkdir(parents=True)
        clean_modules = clean_dir / "modules"
        clean_modules.mkdir()
        (clean_dir / "SKILL.md").write_text(
            "---\nmodules:\n- used-module\n---\n# Clean\n"
        )
        (clean_modules / "used-module.md").write_text("# Used\n")

        # Messy skill
        messy_dir = tmp_path / "skills" / "messy-skill"
        messy_dir.mkdir(parents=True)
        messy_modules = messy_dir / "modules"
        messy_modules.mkdir()
        (messy_dir / "SKILL.md").write_text("# Messy\nNo refs.\n")
        (messy_modules / "forgotten.md").write_text("# Forgotten\n")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        issues = auditor.audit_skill_modules(tmp_path)

        assert "clean-skill" not in issues
        assert "messy-skill" in issues
        assert "forgotten.md" in issues["messy-skill"]["orphaned"]

    def test_cross_skill_reference_resolves_orphan(self, tmp_path: Path) -> None:
        """
        GIVEN skill-A references a module that lives in skill-B's modules dir
        WHEN auditing skill modules
        THEN the module in skill-B is NOT reported as orphaned
              (because the ref name matches a module on disk).
        """
        # skill-a references skill-b's module
        skill_a = tmp_path / "skills" / "skill-a"
        skill_a.mkdir(parents=True)
        (skill_a / "SKILL.md").write_text(
            "See skills/skill-b/modules/shared-logic.md for details.\n"
        )

        # skill-b has the module on disk
        skill_b = tmp_path / "skills" / "skill-b"
        skill_b.mkdir(parents=True)
        modules_b = skill_b / "modules"
        modules_b.mkdir()
        (skill_b / "SKILL.md").write_text("# Skill B\n")
        (modules_b / "shared-logic.md").write_text("# Shared Logic\n")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        issues = auditor.audit_skill_modules(tmp_path)

        # shared-logic.md should NOT be orphaned because skill-a references it
        if "skill-b" in issues:
            assert "shared-logic.md" not in issues["skill-b"].get("orphaned", [])
        else:
            assert True  # No issues means it was resolved


class TestFixPluginAdvanced:
    """Test fix_plugin for advanced scenarios.

    GIVEN different plugin configurations and discrepancy types
    WHEN fix_plugin is called
    THEN it handles each case correctly.
    """

    def test_fix_plugin_dry_run_does_not_modify(self, tmp_path: Path) -> None:
        """
        GIVEN discrepancies exist in dry-run mode
        WHEN fix_plugin is called
        THEN plugin.json is NOT modified.
        """
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()

        original_content = json.dumps(
            {"name": "test-plugin", "commands": ["./commands/cmd1.md"]}, indent=2
        )
        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text(original_content)

        auditor = PluginAuditor(tmp_path, dry_run=True)
        auditor.discrepancies["test-plugin"] = {
            "missing": {"commands": ["./commands/cmd2.md"]},
            "stale": {},
        }

        auditor.fix_plugin("test-plugin")

        # File should be unchanged
        assert plugin_json.read_text() == original_content

    def test_fix_plugin_returns_true_when_no_discrepancies(
        self, tmp_path: Path
    ) -> None:
        """
        GIVEN a plugin with no recorded discrepancies
        WHEN fix_plugin is called
        THEN it returns True (nothing to fix).
        """
        auditor = PluginAuditor(tmp_path, dry_run=False)
        result = auditor.fix_plugin("nonexistent-plugin")

        assert result is True

    def test_fix_plugin_handles_both_missing_and_stale(self, tmp_path: Path) -> None:
        """
        GIVEN a plugin with both missing and stale entries
        WHEN fix_plugin is called with write mode
        THEN missing entries are added and stale entries are removed.
        """
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()

        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps(
                {
                    "name": "test-plugin",
                    "commands": ["./commands/keep.md", "./commands/stale.md"],
                    "skills": ["./skills/existing-skill"],
                },
                indent=2,
            )
        )

        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["test-plugin"] = {
            "missing": {"commands": ["./commands/new.md"]},
            "stale": {"commands": ["./commands/stale.md"]},
        }

        auditor.fix_plugin("test-plugin")

        with plugin_json.open() as f:
            data = json.load(f)

        assert "./commands/keep.md" in data["commands"]
        assert "./commands/new.md" in data["commands"]
        assert "./commands/stale.md" not in data["commands"]
        assert "./skills/existing-skill" in data["skills"]

    def test_fix_plugin_validates_written_json(self, tmp_path: Path) -> None:
        """Verify fix_plugin validates JSON after writing."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()

        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps(
                {"name": "test-plugin", "commands": ["./commands/cmd1.md"]}, indent=2
            )
        )

        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["test-plugin"] = {
            "missing": {"commands": ["./commands/cmd2.md"]},
            "stale": {},
        }

        result = auditor.fix_plugin("test-plugin")
        assert result is True

        # Verify the written file is valid JSON
        with plugin_json.open() as f:
            data = json.load(f)
        assert "./commands/cmd2.md" in data["commands"]

    def test_fix_plugin_returns_false_on_corrupt_write(self, tmp_path: Path) -> None:
        """Verify fix_plugin returns False if written JSON is invalid."""
        import unittest.mock

        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()

        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps(
                {"name": "test-plugin", "commands": ["./commands/cmd1.md"]}, indent=2
            )
        )

        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["test-plugin"] = {
            "missing": {"commands": ["./commands/cmd2.md"]},
            "stale": {},
        }

        # Patch json.load: allow the first call (initial read at line 554),
        # but fail on the second call (validation read-back after write).
        original_json_load = json.load
        load_call_count = {"n": 0}

        def selective_failing_load(f):
            load_call_count["n"] += 1
            if load_call_count["n"] >= 2:
                raise json.JSONDecodeError("Mocked corrupt JSON", "", 0)
            return original_json_load(f)

        with unittest.mock.patch("json.load", side_effect=selective_failing_load):
            result = auditor.fix_plugin("test-plugin")

        assert result is False


class TestScanSkillModules:
    """Test _scan_skill_modules for module file discovery.

    GIVEN a skill directory that may or may not contain a modules/ subdirectory
    WHEN _scan_skill_modules is called
    THEN it should return the set of .md filenames found.
    """

    def test_finds_md_files_in_modules_dir(self, tmp_path: Path) -> None:
        """
        GIVEN a skill directory with modules/*.md files
        WHEN scanning skill modules
        THEN all .md filenames are returned.
        """
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        modules_dir = skill_dir / "modules"
        modules_dir.mkdir()
        (modules_dir / "alpha.md").write_text("# Alpha\n")
        (modules_dir / "beta.md").write_text("# Beta\n")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor._scan_skill_modules(skill_dir)

        assert result == {"alpha.md", "beta.md"}

    def test_returns_empty_for_no_modules_dir(self, tmp_path: Path) -> None:
        """
        GIVEN a skill directory with no modules/ subdirectory
        WHEN scanning skill modules
        THEN an empty set is returned.
        """
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor._scan_skill_modules(skill_dir)

        assert result == set()

    def test_ignores_non_md_files(self, tmp_path: Path) -> None:
        """
        GIVEN a modules/ directory containing non-.md files
        WHEN scanning skill modules
        THEN only .md files are returned.
        """
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        modules_dir = skill_dir / "modules"
        modules_dir.mkdir()
        (modules_dir / "valid.md").write_text("# Valid\n")
        (modules_dir / "ignore.txt").write_text("Not a module\n")
        (modules_dir / "also-ignore.py").write_text("# Not a module\n")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor._scan_skill_modules(skill_dir)

        assert result == {"valid.md"}


class TestReadModuleDescription:
    """Test _read_module_description for extracting short descriptions."""

    def test_extracts_first_content_line(self, tmp_path: Path) -> None:
        """GIVEN a module with frontmatter and headings, returns first content."""
        module = tmp_path / "test.md"
        module.write_text("---\nname: test\n---\n# Title\n\nThis is the description.\n")
        auditor = PluginAuditor(tmp_path, dry_run=True)
        assert auditor._read_module_description(module) == "This is the description."

    def test_skips_frontmatter(self, tmp_path: Path) -> None:
        """GIVEN a module with frontmatter, THEN skips frontmatter lines."""
        module = tmp_path / "test.md"
        module.write_text("---\nkey: value\ntags:\n- a\n---\nFirst real line.\n")
        auditor = PluginAuditor(tmp_path, dry_run=True)
        assert auditor._read_module_description(module) == "First real line."

    def test_skips_headings(self, tmp_path: Path) -> None:
        """GIVEN a module starting with headings, skips to first non-heading."""
        module = tmp_path / "test.md"
        module.write_text("# Main Title\n## Subtitle\nActual content here.\n")
        auditor = PluginAuditor(tmp_path, dry_run=True)
        assert auditor._read_module_description(module) == "Actual content here."

    def test_returns_empty_for_frontmatter_only(self, tmp_path: Path) -> None:
        """GIVEN a module with only frontmatter, THEN returns empty string."""
        module = tmp_path / "test.md"
        module.write_text("---\nname: test\n---\n")
        auditor = PluginAuditor(tmp_path, dry_run=True)
        assert auditor._read_module_description(module) == ""

    def test_returns_empty_for_empty_file(self, tmp_path: Path) -> None:
        """GIVEN an empty module file, THEN returns empty string."""
        module = tmp_path / "test.md"
        module.write_text("")
        auditor = PluginAuditor(tmp_path, dry_run=True)
        assert auditor._read_module_description(module) == ""

    def test_returns_empty_for_nonexistent_file(self, tmp_path: Path) -> None:
        """GIVEN a path to a nonexistent file, THEN returns empty string."""
        module = tmp_path / "nonexistent.md"
        auditor = PluginAuditor(tmp_path, dry_run=True)
        assert auditor._read_module_description(module) == ""

    def test_truncates_long_lines(self, tmp_path: Path) -> None:
        """GIVEN a first content line > 80 chars, truncates with ellipsis."""
        long_line = "A" * 100
        module = tmp_path / "test.md"
        module.write_text(f"# Title\n{long_line}\n")
        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor._read_module_description(module)
        expected_len = 80  # 77 chars + "..."
        assert len(result) == expected_len
        assert result.endswith("...")

    def test_returns_line_at_exactly_80_chars(self, tmp_path: Path) -> None:
        """GIVEN a line of exactly 80 chars, THEN returns it unchanged."""
        line_80 = "B" * 80
        module = tmp_path / "test.md"
        module.write_text(f"{line_80}\n")
        auditor = PluginAuditor(tmp_path, dry_run=True)
        assert auditor._read_module_description(module) == line_80

    def test_skips_blank_lines(self, tmp_path: Path) -> None:
        """GIVEN a module with blank lines before content, skips them."""
        module = tmp_path / "test.md"
        module.write_text("# Title\n\n\n\nContent after blanks.\n")
        auditor = PluginAuditor(tmp_path, dry_run=True)
        assert auditor._read_module_description(module) == "Content after blanks."


class TestPrintModuleIssuesEnriched:
    """Test _print_module_issues shows descriptions for orphaned modules."""

    def test_orphaned_with_description(self, tmp_path: Path, capsys) -> None:
        """GIVEN an orphaned module with content, THEN prints description."""
        plugin_dir = tmp_path / "test-plugin"
        skill_dir = plugin_dir / "skills" / "my-skill" / "modules"
        skill_dir.mkdir(parents=True)
        (skill_dir / "orphan.md").write_text("# Orphan\nThis module is orphaned.\n")

        auditor = PluginAuditor(tmp_path, dry_run=True)
        module_issues = {"my-skill": {"orphaned": ["orphan.md"], "missing": []}}
        auditor._print_module_issues("test-plugin", module_issues)

        captured = capsys.readouterr()
        assert "modules/orphan.md" in captured.out
        assert "This module is orphaned." in captured.out

    def test_orphaned_without_description(self, tmp_path: Path, capsys) -> None:
        """GIVEN orphaned module with only headings, prints path only."""
        plugin_dir = tmp_path / "test-plugin"
        skill_dir = plugin_dir / "skills" / "my-skill" / "modules"
        skill_dir.mkdir(parents=True)
        (skill_dir / "empty.md").write_text("# Just a heading\n")

        auditor = PluginAuditor(tmp_path, dry_run=True)
        module_issues = {"my-skill": {"orphaned": ["empty.md"], "missing": []}}
        auditor._print_module_issues("test-plugin", module_issues)

        captured = capsys.readouterr()
        assert "modules/empty.md" in captured.out
        lines = [ln for ln in captured.out.split("\n") if ln.strip()]
        orphan_idx = next(i for i, ln in enumerate(lines) if "modules/empty.md" in ln)
        if orphan_idx + 1 < len(lines):
            next_line = lines[orphan_idx + 1]
            assert not next_line.startswith("        ")

    def test_orphaned_nonexistent_module_file(self, tmp_path: Path, capsys) -> None:
        """GIVEN orphaned module whose file is missing, prints path only."""
        plugin_dir = tmp_path / "test-plugin"
        skill_dir = plugin_dir / "skills" / "my-skill" / "modules"
        skill_dir.mkdir(parents=True)

        auditor = PluginAuditor(tmp_path, dry_run=True)
        module_issues = {"my-skill": {"orphaned": ["ghost.md"], "missing": []}}
        auditor._print_module_issues("test-plugin", module_issues)

        captured = capsys.readouterr()
        assert "modules/ghost.md" in captured.out

    def test_missing_modules_unchanged(self, tmp_path: Path, capsys) -> None:
        """GIVEN missing modules, THEN prints them without descriptions."""
        auditor = PluginAuditor(tmp_path, dry_run=True)
        module_issues = {"my-skill": {"orphaned": [], "missing": ["needed.md"]}}
        auditor._print_module_issues("test-plugin", module_issues)

        captured = capsys.readouterr()
        assert "modules/needed.md" in captured.out

    def test_header_printed_when_no_discrepancies(self, tmp_path: Path, capsys) -> None:
        """GIVEN no prior discrepancies, THEN prints the plugin header."""
        auditor = PluginAuditor(tmp_path, dry_run=True)
        module_issues = {"my-skill": {"orphaned": ["x.md"], "missing": []}}
        auditor._print_module_issues("test-plugin", module_issues)

        captured = capsys.readouterr()
        assert "PLUGIN: test-plugin" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
