"""Tests for versioned skill definitions."""

from pathlib import Path

from abstract.skill_versioning import SkillVersionManager


class TestVersionParsing:
    """Test reading and writing version info in YAML frontmatter."""

    def test_should_read_current_version(self, tmp_path: Path) -> None:
        """Given a skill with adaptation block, when read, then version returned."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: test-skill\ndescription: A test skill\n"
            'adaptation:\n  current_version: "1.0.0"\n'
            "  rollback_available: false\n  version_history:\n"
            '    - version: "1.0.0"\n'
            '      timestamp: "2026-02-15T04:00:00Z"\n'
            "      baseline_metrics:\n"
            "        success_rate: 0.85\n"
            "        stability_gap: 0.15\n"
            "---\n\n# Test Skill\n"
        )
        mgr = SkillVersionManager(skill_file)
        assert mgr.current_version == "1.0.0"

    def test_should_default_to_1_0_0_without_adaptation(self, tmp_path: Path) -> None:
        """Given a skill without adaptation block, when read, then default 1.0.0."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: test-skill\ndescription: A test skill\n---\n\n# Test Skill\n"
        )
        mgr = SkillVersionManager(skill_file)
        assert mgr.current_version == "1.0.0"


class TestVersionBump:
    """Test version incrementing."""

    def test_should_bump_minor_version(self, tmp_path: Path) -> None:
        """Given version 1.0.0, when bumped, then 1.1.0."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: test-skill\ndescription: A test skill\n---\n\n# Test Skill\n"
        )
        mgr = SkillVersionManager(skill_file)
        mgr.bump_version(
            change_summary="Added error handling",
            metrics={"success_rate": 0.92, "stability_gap": 0.08},
        )
        assert mgr.current_version == "1.1.0"

    def test_should_preserve_history(self, tmp_path: Path) -> None:
        """Given version bumps, when read, then full history present."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: test-skill\ndescription: A test skill\n---\n\n# Test Skill\n"
        )
        mgr = SkillVersionManager(skill_file)
        mgr.bump_version(
            change_summary="First improvement",
            metrics={"success_rate": 0.90, "stability_gap": 0.10},
        )
        mgr.bump_version(
            change_summary="Second improvement",
            metrics={"success_rate": 0.95, "stability_gap": 0.05},
        )
        assert mgr.current_version == "1.2.0"
        assert len(mgr.version_history) == 3  # 1.0.0 + 1.1.0 + 1.2.0

    def test_should_write_back_to_file(self, tmp_path: Path) -> None:
        """Given a version bump, when file re-read, then changes persisted."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: test-skill\ndescription: A test skill\n"
            "---\n\n# Test Skill\n\nContent here.\n"
        )
        mgr = SkillVersionManager(skill_file)
        mgr.bump_version(
            change_summary="Added feature",
            metrics={"success_rate": 0.90, "stability_gap": 0.10},
        )
        # Re-read from disk
        mgr2 = SkillVersionManager(skill_file)
        assert mgr2.current_version == "1.1.0"
        # Body should be preserved
        assert "Content here." in skill_file.read_text()
