"""Extended tests for skill_versioning module.

Feature: Skill version management
    As a developer
    I want skill versions tracked in YAML frontmatter
    So that adaptation history is preserved
"""

from __future__ import annotations

from pathlib import Path

import pytest

from abstract.skill_versioning import SkillVersionManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def skill_file_with_frontmatter(tmp_path: Path) -> Path:
    """Given a skill file with full YAML frontmatter and adaptation block."""
    f = tmp_path / "SKILL.md"
    f.write_text(
        "---\n"
        "name: test-skill\n"
        "adaptation:\n"
        "  current_version: '1.0.0'\n"
        "  rollback_available: false\n"
        "  version_history:\n"
        "    - version: '1.0.0'\n"
        "      timestamp: '2024-01-01T00:00:00+00:00'\n"
        "      baseline_metrics:\n"
        "        success_rate: 0.0\n"
        "        stability_gap: 0.0\n"
        "---\n"
        "\n"
        "# Test Skill\n"
        "\nSkill body content.\n"
    )
    return f


@pytest.fixture
def skill_file_without_adaptation(tmp_path: Path) -> Path:
    """Given a skill file with frontmatter but no adaptation block."""
    f = tmp_path / "SKILL.md"
    f.write_text(
        "---\n"
        "name: test-skill\n"
        "description: A test skill\n"
        "---\n"
        "\n"
        "# Test Skill\n"
        "\nSkill body content.\n"
    )
    return f


@pytest.fixture
def skill_file_no_frontmatter(tmp_path: Path) -> Path:
    """Given a skill file with no frontmatter at all."""
    f = tmp_path / "SKILL.md"
    f.write_text("# Just a Skill\n\nNo frontmatter.\n")
    return f


# ---------------------------------------------------------------------------
# Tests: __init__ and _parse
# ---------------------------------------------------------------------------


class TestSkillVersionManagerInit:
    """Feature: SkillVersionManager initialization."""

    @pytest.mark.unit
    def test_parses_existing_adaptation_block(
        self, skill_file_with_frontmatter: Path
    ) -> None:
        """Scenario: Existing adaptation block is parsed correctly.
        Given a skill file with an adaptation block
        When SkillVersionManager is created
        Then current_version is '1.0.0'
        """
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        assert mgr.current_version == "1.0.0"

    @pytest.mark.unit
    def test_creates_default_adaptation_when_missing(
        self, skill_file_without_adaptation: Path
    ) -> None:
        """Scenario: Missing adaptation block gets default values.
        Given a skill file without an adaptation block
        When SkillVersionManager is created
        Then adaptation is auto-created with version 1.0.0
        """
        mgr = SkillVersionManager(skill_file_without_adaptation)
        assert mgr.current_version == "1.0.0"
        assert not mgr.frontmatter["adaptation"]["rollback_available"]

    @pytest.mark.unit
    def test_parses_body_content(self, skill_file_with_frontmatter: Path) -> None:
        """Scenario: Body content after frontmatter is preserved."""
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        assert "Test Skill" in mgr.body

    @pytest.mark.unit
    def test_no_frontmatter_creates_default_adaptation(
        self, skill_file_no_frontmatter: Path
    ) -> None:
        """Scenario: File without frontmatter gets default adaptation."""
        mgr = SkillVersionManager(skill_file_no_frontmatter)
        assert mgr.current_version == "1.0.0"

    @pytest.mark.unit
    def test_missing_file_does_not_crash(self, tmp_path: Path) -> None:
        """Scenario: Missing skill file produces empty frontmatter without crash."""
        missing = tmp_path / "NONEXISTENT.md"
        mgr = SkillVersionManager(missing)
        assert mgr.frontmatter == {}
        assert mgr.body == ""


# ---------------------------------------------------------------------------
# Tests: current_version property
# ---------------------------------------------------------------------------


class TestCurrentVersionProperty:
    """Feature: current_version property access."""

    @pytest.mark.unit
    def test_returns_version_string(self, skill_file_with_frontmatter: Path) -> None:
        """Scenario: current_version returns the version as a string."""
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        assert isinstance(mgr.current_version, str)
        assert mgr.current_version == "1.0.0"


# ---------------------------------------------------------------------------
# Tests: version_history property
# ---------------------------------------------------------------------------


class TestVersionHistoryProperty:
    """Feature: version_history property access."""

    @pytest.mark.unit
    def test_returns_list(self, skill_file_with_frontmatter: Path) -> None:
        """Scenario: version_history returns a list."""
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        history = mgr.version_history
        assert isinstance(history, list)
        assert len(history) >= 1

    @pytest.mark.unit
    def test_initial_version_in_history(
        self, skill_file_with_frontmatter: Path
    ) -> None:
        """Scenario: Initial version 1.0.0 appears in history."""
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        versions = [entry["version"] for entry in mgr.version_history]
        assert "1.0.0" in versions


# ---------------------------------------------------------------------------
# Tests: bump_version
# ---------------------------------------------------------------------------


class TestBumpVersion:
    """Feature: bump_version increments minor version."""

    @pytest.mark.unit
    def test_bumps_minor_version(self, skill_file_with_frontmatter: Path) -> None:
        """Scenario: bump_version increments the minor version number.
        Given a skill at version 1.0.0
        When bump_version is called
        Then the version becomes 1.1.0
        """
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        new_version = mgr.bump_version(
            "Added new section", {"success_rate": 0.85, "stability_gap": 0.1}
        )
        assert new_version == "1.1.0"

    @pytest.mark.unit
    def test_version_history_grows(self, skill_file_with_frontmatter: Path) -> None:
        """Scenario: Each bump adds an entry to version history."""
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        initial_count = len(mgr.version_history)
        mgr.bump_version("First change", {"success_rate": 0.8, "stability_gap": 0.2})
        assert len(mgr.version_history) == initial_count + 1

    @pytest.mark.unit
    def test_rollback_available_after_bump(
        self, skill_file_with_frontmatter: Path
    ) -> None:
        """Scenario: rollback_available is True after first bump."""
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        mgr.bump_version("Change", {"success_rate": 0.9, "stability_gap": 0.05})
        assert mgr.frontmatter["adaptation"]["rollback_available"] is True

    @pytest.mark.unit
    def test_bump_writes_to_file(self, skill_file_with_frontmatter: Path) -> None:
        """Scenario: bump_version writes updated frontmatter to the file."""
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        mgr.bump_version("Updated", {"success_rate": 0.9, "stability_gap": 0.05})

        # Re-read from disk
        mgr2 = SkillVersionManager(skill_file_with_frontmatter)
        assert mgr2.current_version == "1.1.0"

    @pytest.mark.unit
    def test_double_bump_reaches_1_2_0(self, skill_file_with_frontmatter: Path) -> None:
        """Scenario: Two bumps reach version 1.2.0."""
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        mgr.bump_version("First", {"success_rate": 0.8, "stability_gap": 0.2})
        new_version = mgr.bump_version(
            "Second", {"success_rate": 0.9, "stability_gap": 0.1}
        )
        assert new_version == "1.2.0"

    @pytest.mark.unit
    def test_bump_stores_change_summary(
        self, skill_file_with_frontmatter: Path
    ) -> None:
        """Scenario: bump_version stores the change_summary in history."""
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        mgr.bump_version(
            "My important change", {"success_rate": 0.9, "stability_gap": 0.1}
        )
        latest = mgr.version_history[-1]
        assert latest.get("change_summary") == "My important change"

    @pytest.mark.unit
    def test_bump_stores_metrics(self, skill_file_with_frontmatter: Path) -> None:
        """Scenario: bump_version stores the metrics in history."""
        mgr = SkillVersionManager(skill_file_with_frontmatter)
        metrics = {"success_rate": 0.85, "stability_gap": 0.15}
        mgr.bump_version("Change", metrics)
        latest = mgr.version_history[-1]
        assert latest["baseline_metrics"] == metrics
