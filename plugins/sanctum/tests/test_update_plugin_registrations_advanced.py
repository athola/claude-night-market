#!/usr/bin/env python3
"""Tests for PluginAuditor advanced fix, module scanning, descriptions, and output."""

import json
from pathlib import Path

from update_plugin_registrations import PluginAuditor


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

        assert isinstance(result, dict), "read_plugin_json should return a dict"
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

    def test_truncates_at_81_chars(self, tmp_path: Path) -> None:
        """GIVEN a line of exactly 81 chars (first that triggers truncation)."""
        line_81 = "C" * 81
        module = tmp_path / "test.md"
        module.write_text(f"{line_81}\n")
        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor._read_module_description(module)
        assert len(result) == 80
        assert result == "C" * 77 + "..."

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
        assert "Just a heading" not in captured.out

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

    def test_header_suppressed_when_discrepancies_exist(
        self, tmp_path: Path, capsys
    ) -> None:
        """GIVEN plugin already has discrepancies, THEN header is suppressed."""
        auditor = PluginAuditor(tmp_path, dry_run=True)
        auditor.discrepancies["test-plugin"] = {"commands": {"extra": ["cmd.md"]}}
        module_issues = {"my-skill": {"orphaned": ["orphan.md"], "missing": []}}
        auditor._print_module_issues("test-plugin", module_issues)

        captured = capsys.readouterr()
        assert "PLUGIN: test-plugin" not in captured.out
        assert "[MODULES]" in captured.out

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
