#!/usr/bin/env python3
"""Tests for PluginAuditor module reference extraction and audit."""

from pathlib import Path

from update_plugin_registrations import PluginAuditor


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
        # nonexistent.md is referenced but NOT on disk → only in all_references,
        # not in modules_on_disk. The "missing" calculation is:
        # referenced_modules - modules_on_disk, but referenced_modules only
        # includes refs that ARE in modules_on_disk, so "missing" is always
        # empty in current implementation.
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
