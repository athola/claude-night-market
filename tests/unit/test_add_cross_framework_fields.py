"""Tests for cross-framework frontmatter field injection.

Feature: Cross-framework SKILL.md frontmatter fields

As a plugin maintainer
I want version, globs, and alwaysApply fields in SKILL.md frontmatter
So that Copilot and Cursor export pipelines can derive the correct
instruction/rule mode for each target framework.
"""

from __future__ import annotations

import textwrap

import pytest
from scripts.add_cross_framework_fields import (
    derive_always_apply,
    derive_globs,
    discover_skills,
    format_globs_yaml,
    insert_fields,
    parse_frontmatter_raw,
    process_skill,
)


class TestParseAndSplit:
    """Parsing SKILL.md into raw YAML frontmatter and body."""

    @pytest.mark.unit
    def test_splits_frontmatter_from_body(self):
        """
        Scenario: Standard SKILL.md with frontmatter
        Given a SKILL.md with --- delimited frontmatter
        When parsed
        Then raw YAML and body text are returned separately.
        """

        content = textwrap.dedent("""\
            ---
            name: my-skill
            description: A test skill
            ---
            # Body here
        """)
        raw_yaml, body = parse_frontmatter_raw(content)
        assert "name: my-skill" in raw_yaml
        assert "# Body here" in body

    @pytest.mark.unit
    def test_no_frontmatter_returns_empty_yaml(self):
        """
        Scenario: File without frontmatter
        Given a SKILL.md with no --- delimiters
        When parsed
        Then raw YAML is empty and body is the full content.
        """

        content = "# Just a heading\nSome text."
        raw_yaml, body = parse_frontmatter_raw(content)
        assert raw_yaml == ""
        assert "Just a heading" in body


class TestDeriveGlobs:
    """Deriving globs from skill metadata heuristics."""

    @pytest.mark.unit
    def test_plugin_level_override(self):
        """
        Scenario: Python plugin skill
        Given a skill in the parseltongue plugin
        When globs are derived
        Then it returns **/*.py regardless of category.
        """

        result = derive_globs("parseltongue", "python-testing", "testing", [])
        assert result == "**/*.py"

    @pytest.mark.unit
    def test_skill_specific_override(self):
        """
        Scenario: Rust review skill
        Given the pensive:rust-review skill
        When globs are derived
        Then it returns **/*.rs from the skill-level override.
        """

        result = derive_globs("pensive", "rust-review", "code-review", ["rust"])
        assert result == "**/*.rs"

    @pytest.mark.unit
    def test_category_with_globs(self):
        """
        Scenario: Documentation category
        Given a skill with category "documentation"
        When globs are derived
        Then it returns **/*.md.
        """

        result = derive_globs("sanctum", "doc-updates", "documentation", [])
        assert result == "**/*.md"

    @pytest.mark.unit
    def test_generic_workflow_returns_none(self):
        """
        Scenario: Generic workflow skill
        Given a skill with category "workflow" and no language tags
        When globs are derived
        Then it returns None (agent-requested mode).
        """

        result = derive_globs("attune", "project-brainstorming", "workflow", [])
        assert result is None

    @pytest.mark.unit
    def test_tag_fallback(self):
        """
        Scenario: Skill with no plugin/category match but a language tag
        Given a skill with an unmapped category but tag "shell"
        When globs are derived
        Then it falls back to tag-based derivation (**/*.sh).
        """

        result = derive_globs("custom", "shell-thing", "unmapped-category", ["shell"])
        assert result == "**/*.sh"


class TestDeriveAlwaysApply:
    """Determining which skills are always-on behavioral modifiers."""

    @pytest.mark.unit
    def test_token_conservation_is_always_apply(self):
        """
        Scenario: Token conservation skill
        Given the conserve:token-conservation skill
        When alwaysApply is derived
        Then it is true (always-on behavioral modifier).
        """

        assert derive_always_apply("conserve", "token-conservation") is True

    @pytest.mark.unit
    def test_normal_skill_is_not_always_apply(self):
        """
        Scenario: Normal agent-requested skill
        Given the pensive:bug-review skill
        When alwaysApply is derived
        Then it is false (agent-requested).
        """

        assert derive_always_apply("pensive", "bug-review") is False


class TestInsertFields:
    """Inserting version/globs/alwaysApply into raw YAML frontmatter."""

    @pytest.mark.unit
    def test_inserts_all_three_fields(self):
        """
        Scenario: Skill with no cross-framework fields
        Given raw YAML with name and description only
        When fields are inserted
        Then version, globs, and alwaysApply appear in the output.
        """

        raw = textwrap.dedent("""\
            name: my-skill
            description: A test skill
            category: testing""")
        result = insert_fields(raw, "1.7.1", "**/*.py", False)
        assert "version: 1.7.1" in result
        assert 'globs: "**/*.py"' in result
        assert "alwaysApply: false" in result

    @pytest.mark.unit
    def test_inserts_without_globs_when_none(self):
        """
        Scenario: Agent-requested skill with no globs
        Given a skill where globs derivation returns None
        When fields are inserted
        Then version and alwaysApply are present but globs is omitted.
        """

        raw = "name: my-skill\ndescription: A test skill"
        result = insert_fields(raw, "1.7.1", None, False)
        assert "version: 1.7.1" in result
        assert "alwaysApply: false" in result
        assert "globs" not in result

    @pytest.mark.unit
    def test_updates_existing_version(self):
        """
        Scenario: Skill that already has a version field
        Given raw YAML with version: 1.0.0
        When fields are inserted with version 1.7.1
        Then the version is updated in-place (not duplicated).
        """

        raw = "name: my-skill\ndescription: A test skill\nversion: 1.0.0"
        result = insert_fields(raw, "1.7.1", None, False)
        assert result.count("version:") == 1
        assert "version: 1.7.1" in result

    @pytest.mark.unit
    def test_handles_multiline_quoted_description(self):
        """
        Scenario: Skill with single-quoted multiline description
        Given a SKILL.md where description spans multiple lines in quotes
        When fields are inserted
        Then they appear after the description block, not mid-quote.
        """

        raw = textwrap.dedent("""\
            name: my-skill
            description: 'A long description that
              spans multiple lines and ends here'
            category: testing""")
        result = insert_fields(raw, "1.7.1", "**/*.py", False)
        assert "version: 1.7.1" in result
        # Fields should not be inside the quoted string
        lines = result.split("\n")
        desc_end = next(i for i, ln in enumerate(lines) if ln.rstrip().endswith("'"))
        version_line = next(
            i for i, ln in enumerate(lines) if ln.startswith("version:")
        )
        assert version_line > desc_end

    @pytest.mark.unit
    def test_handles_list_globs(self):
        """
        Scenario: Skill needing multiple glob patterns
        Given a globs value that is a list of patterns
        When fields are inserted
        Then globs is formatted as inline YAML list.
        """

        raw = "name: my-skill\ndescription: test"
        globs = ["**/conftest.py", "**/pytest.ini"]
        result = insert_fields(raw, "1.7.1", globs, False)
        assert 'globs: ["**/conftest.py", "**/pytest.ini"]' in result


class TestFormatGlobsYaml:
    """YAML formatting of globs values."""

    @pytest.mark.unit
    def test_string_globs(self):
        assert format_globs_yaml("**/*.py") == 'globs: "**/*.py"'

    @pytest.mark.unit
    def test_list_globs(self):
        result = format_globs_yaml(["**/*.py", "**/*.pyi"])
        assert result == 'globs: ["**/*.py", "**/*.pyi"]'

    @pytest.mark.unit
    def test_none_globs(self):
        assert format_globs_yaml(None) == ""


class TestProcessSkill:
    """End-to-end processing of a single SKILL.md file."""

    @pytest.mark.unit
    def test_dry_run_does_not_write(self, tmp_path):
        """
        Scenario: Dry-run mode
        Given a SKILL.md file on disk
        When process_skill runs with write=False
        Then the file is unchanged on disk.
        """

        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        original = "---\nname: my-skill\ndescription: test\n---\n# Body\n"
        skill_md.write_text(original)

        info = process_skill(skill_md, "pensive", "1.7.1", write=False)
        assert info["changed"] is True
        assert info["status"] == "dry-run"
        assert skill_md.read_text() == original

    @pytest.mark.unit
    def test_write_mode_modifies_file(self, tmp_path):
        """
        Scenario: Write mode
        Given a SKILL.md file missing cross-framework fields
        When process_skill runs with write=True
        Then the file contains version and alwaysApply fields.
        """

        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("---\nname: my-skill\ndescription: test\n---\n# Body\n")

        info = process_skill(skill_md, "pensive", "1.7.1", write=True)
        assert info["status"] == "updated"
        content = skill_md.read_text()
        assert "version: 1.7.1" in content
        assert "alwaysApply: false" in content
        assert "# Body" in content

    @pytest.mark.unit
    def test_idempotent_rerun(self, tmp_path):
        """
        Scenario: Running twice produces no change on second run
        Given a SKILL.md already processed by the script
        When process_skill runs again
        Then it reports unchanged (idempotent).
        """

        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("---\nname: my-skill\ndescription: test\n---\n# Body\n")

        # First run
        process_skill(skill_md, "pensive", "1.7.1", write=True)
        # Second run
        info = process_skill(skill_md, "pensive", "1.7.1", write=True)
        assert info["changed"] is False
        assert info["status"] == "unchanged"


class TestDiscoverSkills:
    """Discovering SKILL.md files across plugin directories."""

    @pytest.mark.unit
    def test_finds_skills_in_standard_layout(self, tmp_path):
        """
        Scenario: Standard plugin layout
        Given plugins/foo/skills/bar/SKILL.md exists
        When discover_skills runs
        Then it returns (foo, path_to_SKILL.md).
        """

        (tmp_path / "foo" / "skills" / "bar").mkdir(parents=True)
        (tmp_path / "foo" / "skills" / "bar" / "SKILL.md").write_text(
            "---\nname: bar\n---\n"
        )

        results = discover_skills(tmp_path)
        assert len(results) == 1
        assert results[0][0] == "foo"
        assert results[0][1].name == "SKILL.md"

    @pytest.mark.unit
    def test_skips_non_skill_directories(self, tmp_path):
        """
        Scenario: Plugin without skills directory
        Given a plugin with only hooks (no skills/)
        When discover_skills runs
        Then it returns nothing for that plugin.
        """

        (tmp_path / "foo" / "hooks").mkdir(parents=True)
        results = discover_skills(tmp_path)
        assert len(results) == 0
