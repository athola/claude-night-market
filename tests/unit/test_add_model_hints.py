"""Tests for add_model_hints script."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from add_model_hints import get_model_hint, process_skill


class TestModelHintMapping:
    """
    Feature: Model hint derivation from skill complexity

    As a plugin developer
    I want skills routed to appropriate models by complexity
    So that simple tasks don't waste tokens on expensive models
    """

    @pytest.mark.unit
    def test_low_complexity_maps_to_fast(self):
        """
        Scenario: Low complexity skill gets fast hint
        Given a skill with complexity "low"
        When model_hint is derived
        Then it should be "fast"
        """
        assert get_model_hint("some-skill", "low") == "fast"

    @pytest.mark.unit
    def test_basic_complexity_maps_to_fast(self):
        assert get_model_hint("some-skill", "basic") == "fast"

    @pytest.mark.unit
    def test_intermediate_maps_to_standard(self):
        assert get_model_hint("some-skill", "intermediate") == "standard"

    @pytest.mark.unit
    def test_advanced_maps_to_deep(self):
        assert get_model_hint("some-skill", "advanced") == "deep"

    @pytest.mark.unit
    def test_unknown_complexity_defaults_to_standard(self):
        assert get_model_hint("some-skill", "unknown-value") == "standard"

    @pytest.mark.unit
    def test_force_fast_overrides_complexity(self):
        """
        Scenario: commit-messages skill forced to fast
        Given a skill named "commit-messages" with complexity "intermediate"
        When model_hint is derived
        Then it should be "fast" (overridden)
        """
        assert get_model_hint("commit-messages", "intermediate") == "fast"

    @pytest.mark.unit
    def test_force_deep_overrides_complexity(self):
        assert get_model_hint("war-room", "intermediate") == "deep"


class TestProcessSkill:
    """
    Feature: Process individual SKILL.md files to add model_hint

    As a plugin developer
    I want to add model_hint frontmatter to skill files
    So that downstream tools can route to appropriate models
    """

    @pytest.mark.unit
    def test_skips_file_without_frontmatter(self, tmp_path: Path):
        """
        Given a SKILL.md with no frontmatter
        When processed
        Then it returns "unknown" with "skip" and no change
        """
        skill = tmp_path / "SKILL.md"
        skill.write_text("# No frontmatter here\n\nJust content.\n")
        name, hint, changed = process_skill(skill, write=False)
        assert name == "unknown"
        assert hint == "skip"
        assert changed is False

    @pytest.mark.unit
    def test_skips_file_with_existing_model_hint(self, tmp_path: Path):
        """
        Given a SKILL.md that already has model_hint
        When processed
        Then it reports the existing hint and no change
        """
        skill = tmp_path / "SKILL.md"
        skill.write_text(
            "---\nname: my-skill\ncomplexity: low\nmodel_hint: fast\n---\n\n# Body\n"
        )
        name, hint, changed = process_skill(skill, write=False)
        assert name == "my-skill"
        assert hint == "fast"
        assert changed is False

    @pytest.mark.unit
    def test_inserts_hint_after_complexity(self, tmp_path: Path):
        """
        Given a SKILL.md with complexity but no model_hint
        When processed in dry-run mode
        Then it reports the derived hint and changed=True
        And the file is not modified
        """
        content = "---\nname: my-skill\ncomplexity: advanced\n---\n\n# Body\n"
        skill = tmp_path / "SKILL.md"
        skill.write_text(content)
        name, hint, changed = process_skill(skill, write=False)
        assert name == "my-skill"
        assert hint == "deep"
        assert changed is True
        # Dry run: file unchanged
        assert skill.read_text() == content

    @pytest.mark.unit
    def test_writes_hint_when_write_enabled(self, tmp_path: Path):
        """
        Given a SKILL.md with complexity "low"
        When processed with write=True
        Then model_hint is inserted into the file after complexity
        """
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: my-skill\ncomplexity: low\n---\n\n# Body\n")
        name, hint, changed = process_skill(skill, write=True)
        assert changed is True
        assert hint == "fast"
        updated = skill.read_text()
        assert "model_hint: fast" in updated
        assert updated.index("complexity: low") < updated.index("model_hint: fast")

    @pytest.mark.unit
    def test_inserts_before_closing_fence_when_no_complexity(self, tmp_path: Path):
        """
        Given a SKILL.md without a complexity field
        When processed with write=True
        Then model_hint is inserted before the closing ---
        And defaults to "standard"
        """
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: simple-skill\n---\n\n# Body\n")
        name, hint, changed = process_skill(skill, write=True)
        assert changed is True
        assert hint == "standard"
        updated = skill.read_text()
        assert "model_hint: standard" in updated

    @pytest.mark.unit
    def test_falls_back_to_parent_dir_for_name(self, tmp_path: Path):
        """
        Given a SKILL.md with frontmatter but no name field
        When processed
        Then it uses the parent directory name as skill name
        """
        skill_dir = tmp_path / "my-dir-skill"
        skill_dir.mkdir()
        skill = skill_dir / "SKILL.md"
        skill.write_text("---\ncomplexity: low\n---\n\n# Body\n")
        name, hint, changed = process_skill(skill, write=False)
        assert name == "my-dir-skill"
        assert hint == "fast"
