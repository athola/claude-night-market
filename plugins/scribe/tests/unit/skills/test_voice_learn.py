"""
Feature: Voice Learning Loop from Manual Edits

As a writer
I want the system to learn from my manual edits
So that the voice profile improves over time
"""

from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parents[3]
SKILL_DIR = PLUGIN_ROOT / "skills" / "voice-learn"


class TestVoiceLearnSkillStructure:
    """
    Feature: Voice learning skill file structure

    As a plugin developer
    I want the voice-learn skill to have proper structure
    So that it captures and analyzes edit patterns correctly
    """

    @pytest.mark.unit
    def test_skill_file_exists(self):
        """
        Scenario: Skill file exists at expected path
        Given the scribe plugin
        When I look for the voice-learn skill
        Then SKILL.md exists
        """
        assert (SKILL_DIR / "SKILL.md").exists()

    @pytest.mark.unit
    def test_skill_has_required_modules(self):
        """
        Scenario: All declared modules exist on disk
        Given the voice-learn skill declares modules
        When I check the modules directory
        Then each declared module file exists
        """
        modules_dir = SKILL_DIR / "modules"
        assert modules_dir.exists()

        required_modules = [
            "snapshot-management.md",
            "pattern-analysis.md",
        ]
        for module_file in required_modules:
            assert (modules_dir / module_file).exists(), f"Module {module_file} missing"

    @pytest.mark.unit
    def test_skill_uses_opus(self):
        """
        Scenario: Learning analysis uses Opus for nuance
        Given that pattern comparison needs nuanced understanding
        When I check the model hint
        Then it specifies opus
        """
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "model_hint: opus" in content


class TestSnapshotManagement:
    """
    Feature: Three-stage snapshot capture

    As a writer
    I want text captured at three stages
    So that the learning agent can compare what changed
    """

    @pytest.mark.unit
    def test_three_stages_documented(self):
        """
        Scenario: All three snapshot stages are defined
        Given the snapshot-management module
        When I read its content
        Then it defines pre-review, post-review, and post-edit stages
        """
        content = (SKILL_DIR / "modules" / "snapshot-management.md").read_text()
        assert "pre-review" in content
        assert "post-review" in content
        assert "post-edit" in content

    @pytest.mark.unit
    def test_naming_convention_documented(self):
        """
        Scenario: Snapshot file naming is documented
        Given that snapshots need to be matched into sets
        When I read the module
        Then it describes the naming convention
        """
        content = (SKILL_DIR / "modules" / "snapshot-management.md").read_text()
        assert "piece-name" in content or "piece-filename" in content
        assert "timestamp" in content or "YYYYMMDD" in content


class TestPatternAnalysis:
    """
    Feature: Pattern extraction from edit diffs

    As a writer
    I want recurring edit patterns identified
    So that only consistent preferences become rules
    """

    @pytest.mark.unit
    def test_diff_categories_defined(self):
        """
        Scenario: Edit categories are defined for classification
        Given the pattern-analysis module
        When I read its content
        Then it defines categories for different edit types
        """
        content = (SKILL_DIR / "modules" / "pattern-analysis.md").read_text()
        assert "tone_adjustment" in content or "Tone" in content
        assert "voice_insertion" in content or "Voice" in content
        assert "deletion" in content or "Deletion" in content

    @pytest.mark.unit
    def test_evidence_threshold_defined(self):
        """
        Scenario: Evidence threshold prevents premature rule creation
        Given that one-off edits shouldn't become permanent rules
        When I check the threshold requirements
        Then patterns need 3+ instances before becoming rules
        """
        content = (SKILL_DIR / "modules" / "pattern-analysis.md").read_text()
        assert "3+" in content or "3 instance" in content.lower()

    @pytest.mark.unit
    def test_accumulator_matching_documented(self):
        """
        Scenario: New patterns are matched against accumulator
        Given that patterns build up over multiple pieces
        When I check the matching logic
        Then it describes how new patterns are compared to existing ones
        """
        content = (SKILL_DIR / "modules" / "pattern-analysis.md").read_text()
        assert "accumulator" in content.lower()
        assert "match" in content.lower()


class TestLearningRules:
    """
    Feature: Learning rules prevent rule bloat

    As a writer
    I want the system to sharpen rather than add rules
    So that my voice profile stays lean and effective
    """

    @pytest.mark.unit
    def test_sharpen_not_add_rule(self):
        """
        Scenario: Core rule is 'sharpen, don't add'
        Given the voice-learn skill
        When I read its core rules
        Then it emphasizes modifying existing rules over adding new ones
        """
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "Sharpen" in content or "sharpen" in content

    @pytest.mark.unit
    def test_staleness_threshold_defined(self):
        """
        Scenario: Stale patterns are pruned from accumulator
        Given that old patterns may be one-off preferences
        When I check the staleness mechanism
        Then patterns expire after a defined threshold
        """
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "staleness" in content.lower() or "Staleness" in content
        assert "expire" in content.lower() or "prune" in content.lower()

    @pytest.mark.unit
    def test_contradiction_handling(self):
        """
        Scenario: Contradicting patterns are flagged for user
        Given that a writer may be inconsistent across pieces
        When contradicting patterns are detected
        Then the system flags them for user resolution
        """
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "contradiction" in content.lower() or "Contradiction" in content
