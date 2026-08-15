"""BDD tests for the session-handoff skill.

Feature: Session Handoff
  As a memory-palace user
  I want each session decomposed into typed, dated units
  So that a later session can recognize a topic has history and pick
  up each thread from its actual state rather than a blank slate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILL_DIR = PLUGIN_ROOT / "skills" / "session-handoff"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
PLUGIN_METADATA = PLUGIN_ROOT / ".claude-plugin" / "metadata.json"
PLUGIN_MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestSkillFileExists:
    """Feature: Skill file is present and parseable."""

    @pytest.mark.bdd
    def test_skill_file_exists(self) -> None:
        """Scenario: SKILL.md present."""
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"

    @pytest.mark.bdd
    def test_frontmatter_is_valid_yaml(self) -> None:
        """Scenario: Frontmatter parses and names the skill."""
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        assert fm.get("name") == "session-handoff"
        assert fm.get("description"), "description is required"


class TestTypedUnitSchema:
    """Feature: The four unit types and their fields are specified.

    The types exist so that units with different lifetimes age on
    different schedules; a schema missing a type silently merges two
    lifetimes onto one curve.
    """

    @pytest.mark.bdd
    def test_all_four_unit_types_named(self) -> None:
        """Scenario: finding, decision, open-thread, state all present."""
        content = SKILL_FILE.read_text() + (MODULES_DIR / "unit-schema.md").read_text()
        for unit_type in ("finding", "decision", "open-thread", "state"):
            assert unit_type in content, f"unit type {unit_type!r} not documented"

    @pytest.mark.bdd
    def test_unit_fields_specified(self) -> None:
        """Scenario: Every field of the unit format is named."""
        content = (MODULES_DIR / "unit-schema.md").read_text()
        for field in ("Thread", "Type", "Date", "State", "Why", "Open", "Ref"):
            assert f"{field}:" in content or f"### {field}" in content, (
                f"unit field {field!r} not specified"
            )

    @pytest.mark.bdd
    def test_split_by_aging_rate_rule_present(self) -> None:
        """Scenario: The rule that drives splitting a bundled thread.

        This is the load-bearing rule: a durable finding and the
        transient action that produced it must become separate units
        so each decays on its own schedule.
        """
        content = (MODULES_DIR / "unit-schema.md").read_text()
        assert "ages at the right rate" in content or "age at the right rate" in content

    @pytest.mark.bdd
    def test_open_field_carries_state_of_thinking(self) -> None:
        """Scenario: Open threads record where thinking landed.

        Binary open/closed logging is the failure mode this replaces.
        """
        content = (MODULES_DIR / "unit-schema.md").read_text()
        assert "state of thinking" in content.lower()


class TestTwoPhaseExtraction:
    """Feature: Inventory before judgment."""

    @pytest.mark.bdd
    def test_both_phases_named(self) -> None:
        """Scenario: Phase 1 inventory and Phase 2 render are distinct."""
        content = (MODULES_DIR / "two-phase-extraction.md").read_text()
        assert "PHASE 1" in content and "PHASE 2" in content

    @pytest.mark.bdd
    def test_inventory_is_exhaustive_not_selective(self) -> None:
        """Scenario: Phase 1 forbids filtering."""
        content = (MODULES_DIR / "two-phase-extraction.md").read_text()
        assert "miss nothing" in content.lower()

    @pytest.mark.bdd
    def test_fidelity_rule_present(self) -> None:
        """Scenario: A wrong unit is worse than a missing one."""
        content = (MODULES_DIR / "two-phase-extraction.md").read_text()
        assert "confident-but-wrong" in content or "confident but wrong" in content


class TestTemporalAwareness:
    """Feature: Elapsed time between sessions is narrated, not assumed."""

    @pytest.mark.bdd
    def test_temporal_module_exists(self) -> None:
        """Scenario: The temporal-awareness module is present."""
        assert (MODULES_DIR / "temporal-awareness.md").exists()

    @pytest.mark.bdd
    def test_session_gap_is_computed_not_guessed(self) -> None:
        """Scenario: The gap is derived from stored timestamps.

        Fabricating a timestamp from a stale clock reading is the
        specific failure this guards.
        """
        content = (MODULES_DIR / "temporal-awareness.md").read_text()
        assert "get_recent_sessions" in content, (
            "must name the real API that supplies the previous session time"
        )
        assert "fabricat" in content.lower()


class TestSkillRegistration:
    """Feature: The skill is discoverable by Claude Code."""

    @pytest.mark.bdd
    def test_registered_in_metadata(self) -> None:
        """Scenario: metadata.json lists the skill."""
        skills = json.loads(PLUGIN_METADATA.read_text()).get("skills", [])
        assert "skills/session-handoff" in skills, f"not in metadata: {skills}"

    @pytest.mark.bdd
    def test_registered_in_plugin_manifest(self) -> None:
        """Scenario: plugin.json lists the skill."""
        skills = json.loads(PLUGIN_MANIFEST.read_text()).get("skills", [])
        # plugin.json uses a "./" prefix; metadata.json does not.
        assert any(s.rstrip("/").endswith("skills/session-handoff") for s in skills), (
            f"not in plugin.json: {skills}"
        )


class TestExitCriteria:
    """Feature: The skill states when it is done."""

    @pytest.mark.bdd
    def test_exit_criteria_section_present(self) -> None:
        """Scenario: An Exit Criteria section exists with checkboxes."""
        content = SKILL_FILE.read_text()
        assert "## Exit Criteria" in content
        tail = content.split("## Exit Criteria", 1)[1]
        assert tail.count("- [ ]") >= 3, "need at least 3 exit criteria"


class TestDependencyDocumentation:
    """Feature: the skill documents the dependency declaration.

    A skill that describes a field the code does not have is a
    hallucination; a field the code has that the skill never mentions
    will never be populated. Both directions have to be guarded.
    """

    @pytest.mark.bdd
    def test_files_field_is_in_the_schema(self) -> None:
        """Scenario: the unit schema names the dependency field."""
        content = (MODULES_DIR / "unit-schema.md").read_text()
        assert "Files:" in content

    @pytest.mark.bdd
    def test_capture_shape_includes_files(self) -> None:
        """Scenario: the staged JSON example shows how to declare them."""
        assert '"files"' in SKILL_FILE.read_text()

    @pytest.mark.bdd
    def test_event_signal_beats_elapsed_time(self) -> None:
        """Scenario: the module states which signal wins."""
        content = (MODULES_DIR / "temporal-awareness.md").read_text()
        assert "file_digests" in content, (
            "must name the real field carrying the fingerprint"
        )

    @pytest.mark.bdd
    def test_signal_flags_rather_than_suppresses(self) -> None:
        """Scenario: a moved dependency does not hide the unit."""
        content = (MODULES_DIR / "temporal-awareness.md").read_text()
        assert "STALE SIGNAL" in content
