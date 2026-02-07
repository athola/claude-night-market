#!/usr/bin/env python3
"""
Feature: Consolidate skill descriptions into Claude Code official format

As a plugin developer
I want to consolidate triggers, use_when, and do_not_use_when into a single description
So that Claude Code can read all discovery info from the description field

Format: "[What it does]. Use when [scenarios]. Do not use when [anti-patterns]."
"""

import sys
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

# Add scripts to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from fix_descriptions import consolidate_description, process_skill_file


class TestConsolidateDescription:
    """Test consolidation of frontmatter fields into a single description."""

    @pytest.mark.unit
    def test_simple_description_with_all_fields(self):
        """
        Scenario: Frontmatter has separate description, use_when, and do_not_use_when
        Given a frontmatter dict with all metadata fields
        When I consolidate the description
        Then the result follows "[What]. Use when [X]. Do not use when [Y]." format
        """
        frontmatter = {
            "description": "Analyze and improve code quality.",
            "use_when": "improving code quality, reducing duplication",
            "do_not_use_when": "removing dead code (use bloat-detector)",
        }

        result = consolidate_description(frontmatter)

        assert result.startswith("Analyze and improve code quality")
        assert "Use when improving code quality, reducing duplication" in result
        assert "Do not use when removing dead code (use bloat-detector)" in result
        assert result.endswith(".")

    @pytest.mark.unit
    def test_description_only(self):
        """
        Scenario: Frontmatter has only a description, no metadata fields
        Given a frontmatter dict with only description
        When I consolidate the description
        Then the result is just the description with trailing period
        """
        frontmatter = {
            "description": "Simple skill that does one thing",
        }

        result = consolidate_description(frontmatter)

        assert result == "Simple skill that does one thing."

    @pytest.mark.unit
    def test_triggers_used_when_no_use_when(self):
        """
        Scenario: Frontmatter has triggers but no use_when
        Given triggers field but no use_when field
        When I consolidate the description
        Then triggers are promoted to "Use when:" section
        """
        frontmatter = {
            "description": "Analyze code quality.",
            "triggers": "refine, code quality, clean code",
        }

        result = consolidate_description(frontmatter)

        assert "Use when:" in result
        assert "refine, code quality, clean code" in result

    @pytest.mark.unit
    def test_list_triggers_joined(self):
        """
        Scenario: Triggers field is a YAML list
        Given triggers as a list instead of string
        When I consolidate the description
        Then list items are joined with commas
        """
        frontmatter = {
            "description": "Analyze code.",
            "triggers": ["refine", "code quality", "clean code"],
        }

        result = consolidate_description(frontmatter)

        assert "refine, code quality, clean code" in result

    @pytest.mark.unit
    def test_use_when_preferred_over_triggers(self):
        """
        Scenario: Both use_when and triggers are present
        Given both use_when and triggers fields
        When I consolidate the description
        Then use_when is used (triggers ignored since use_when is more specific)
        """
        frontmatter = {
            "description": "Analyze code.",
            "triggers": "refine, code quality",
            "use_when": "improving code quality, reducing AI slop",
        }

        result = consolidate_description(frontmatter)

        assert "Use when improving code quality" in result
        # Triggers keyword list should NOT appear since use_when supersedes it
        assert "Use when: refine" not in result

    @pytest.mark.unit
    def test_strips_existing_use_when_from_description(self):
        """
        Scenario: Description already has "Use when:" embedded
        Given description text containing "Use when:" inline
        When I consolidate the description
        Then the embedded "Use when:" is removed (replaced by field value)
        """
        frontmatter = {
            "description": "Analyze code. Use when: old embedded triggers",
            "use_when": "new consolidated triggers",
        }

        result = consolidate_description(frontmatter)

        assert "old embedded triggers" not in result
        assert "Use when new consolidated triggers" in result

    @pytest.mark.unit
    def test_strips_existing_triggers_from_description(self):
        """
        Scenario: Description already has "Triggers:" embedded
        Given description text containing "Triggers:" inline
        When I consolidate the description
        Then the embedded "Triggers:" is removed
        """
        frontmatter = {
            "description": "Analyze code. Triggers: old keywords",
            "triggers": "new, clean, keywords",
        }

        result = consolidate_description(frontmatter)

        assert "old keywords" not in result
        assert "new, clean, keywords" in result

    @pytest.mark.unit
    def test_empty_frontmatter_returns_empty(self):
        """
        Scenario: No description or metadata at all
        Given an empty frontmatter dict
        When I consolidate the description
        Then the result is empty
        """
        result = consolidate_description({})

        assert result == ""

    @pytest.mark.unit
    def test_trailing_periods_deduplicated(self):
        """
        Scenario: Fields already end with periods
        Given fields that end with trailing periods
        When I consolidate the description
        Then periods are not doubled
        """
        frontmatter = {
            "description": "Analyze code quality.",
            "use_when": "improving code.",
            "do_not_use_when": "removing dead code.",
        }

        result = consolidate_description(frontmatter)

        # Should not have ".." anywhere
        assert ".." not in result

    @pytest.mark.unit
    def test_real_world_code_refinement(self):
        """
        Scenario: Process actual code-refinement skill frontmatter
        Given frontmatter matching a real skill with all fields
        When I consolidate the description
        Then description is concise and follows official format
        """
        frontmatter = {
            "description": "Analyze and improve living code quality: duplication, algorithmic efficiency.",
            "triggers": "refine, code quality, clean code, refactor",
            "use_when": "improving code quality, reducing AI slop, refactoring for clarity",
            "do_not_use_when": "removing dead/unused code (use conserve:bloat-detector)",
        }

        result = consolidate_description(frontmatter)

        # Should have all three parts
        assert "Analyze and improve living code quality" in result
        assert "Use when improving code quality" in result
        assert "Do not use when removing dead/unused code" in result
        # Should not start with "Triggers:"
        assert not result.startswith("Triggers:")


class TestProcessSkillFile:
    """Test processing of actual SKILL.md files."""

    @pytest.fixture
    def skill_dir(self, tmp_path: Path) -> Path:
        """Create a temporary skill directory."""
        d = tmp_path / "plugins" / "test" / "skills" / "my-skill"
        d.mkdir(parents=True)
        return d

    @pytest.mark.unit
    def test_returns_none_for_clean_file(self, skill_dir: Path):
        """
        Scenario: File has no custom fields and no embedded metadata
        Given a SKILL.md without triggers/use_when/do_not_use_when fields
        And the description has no "Use when:" or "Triggers:" substrings
        When I process the file
        Then it returns None (no changes needed)
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(dedent("""\
            ---
            name: my-skill
            description: "A clean skill that needs no changes"
            version: "1.4.0"
            ---

            # My Skill

            Content here.
        """))

        result = process_skill_file(skill_file, dry_run=True)

        assert result is None

    @pytest.mark.unit
    def test_detects_custom_fields(self, skill_dir: Path):
        """
        Scenario: File has custom metadata fields that need consolidation
        Given a SKILL.md with triggers and use_when fields
        When I process the file
        Then it returns a change dict with old and new descriptions
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(dedent("""\
            ---
            name: my-skill
            description: "Analyze code quality."
            triggers: "refine, code quality"
            use_when: "improving code"
            version: "1.4.0"
            ---

            # My Skill
        """))

        result = process_skill_file(skill_file, dry_run=True)

        assert result is not None
        assert "old_description" in result
        assert "new_description" in result

    @pytest.mark.unit
    def test_dry_run_does_not_modify_file(self, skill_dir: Path):
        """
        Scenario: Dry run mode
        Given a file that needs consolidation
        When I process with dry_run=True
        Then the file content is unchanged
        """
        skill_file = skill_dir / "SKILL.md"
        original = dedent("""\
            ---
            name: my-skill
            description: "Analyze code."
            triggers: "refine, quality"
            version: "1.0.0"
            ---

            # Content
        """)
        skill_file.write_text(original)

        process_skill_file(skill_file, dry_run=True)

        assert skill_file.read_text() == original

    @pytest.mark.unit
    def test_apply_modifies_file(self, skill_dir: Path):
        """
        Scenario: Apply mode writes consolidated description
        Given a file with custom fields
        When I process with dry_run=False
        Then the file is updated with consolidated description
        And custom fields are removed from frontmatter
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(dedent("""\
            ---
            name: my-skill
            description: "Analyze code."
            triggers: "refine, quality"
            use_when: "improving code quality"
            do_not_use_when: "removing dead code"
            version: "1.0.0"
            ---

            # Content
        """))

        process_skill_file(skill_file, dry_run=False)

        updated = skill_file.read_text()
        fm_text = updated.split("---")[1]
        fm = yaml.safe_load(fm_text)

        # Custom fields should be removed
        assert "triggers" not in fm
        assert "use_when" not in fm
        assert "do_not_use_when" not in fm

        # Description should be consolidated
        assert "Use when" in fm["description"]
        assert "Do not use when" in fm["description"]

    @pytest.mark.unit
    def test_returns_none_for_invalid_frontmatter(self, skill_dir: Path):
        """
        Scenario: File has no valid frontmatter
        Given a file without --- delimiters
        When I process the file
        Then it returns None
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# No frontmatter\n\nJust content.")

        result = process_skill_file(skill_file, dry_run=True)

        assert result is None

    @pytest.mark.unit
    def test_detects_embedded_triggers_in_description(self, skill_dir: Path):
        """
        Scenario: File has Triggers: embedded in description text
        Given a SKILL.md where description contains "Triggers:" after real content
        When I process the file
        Then it detects the need for consolidation and strips the triggers
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(dedent("""\
            ---
            name: my-skill
            description: "Analyze code quality. Triggers: refine, code"
            version: "1.0.0"
            ---

            # Content
        """))

        result = process_skill_file(skill_file, dry_run=True)

        # Should detect embedded Triggers: and consolidate
        assert result is not None
        assert "new_description" in result

    @pytest.mark.unit
    def test_embedded_triggers_only_returns_none(self, skill_dir: Path):
        """
        Scenario: Description is ONLY triggers with no real content
        Given a SKILL.md where description starts with "Triggers:" and has no other text
        When I process the file
        Then it returns None (stripping leaves empty, nothing useful to produce)
        """
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(dedent("""\
            ---
            name: my-skill
            description: "Triggers: refine, code"
            version: "1.0.0"
            ---

            # Content
        """))

        result = process_skill_file(skill_file, dry_run=True)

        # Stripping "Triggers:..." leaves empty description → returns None
        assert result is None
