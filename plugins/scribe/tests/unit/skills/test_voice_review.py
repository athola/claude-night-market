"""
Feature: Dual-Gate Voice Review with Prose + Craft Agents

As a writer
I want generated text reviewed by specialized agents
So that AI patterns are caught and craft quality is assessed
"""

from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parents[3]
SKILL_DIR = PLUGIN_ROOT / "skills" / "voice-review"
AGENTS_DIR = PLUGIN_ROOT / "agents"


class TestVoiceReviewSkillStructure:
    """
    Feature: Voice review skill file structure

    As a plugin developer
    I want the voice-review skill to have proper structure
    So that it orchestrates both review agents correctly
    """

    @pytest.mark.unit
    def test_skill_file_exists(self):
        """
        Scenario: Skill file exists at expected path
        Given the scribe plugin
        When I look for the voice-review skill
        Then SKILL.md exists
        """
        assert (SKILL_DIR / "SKILL.md").exists()

    @pytest.mark.unit
    def test_skill_mentions_parallel_dispatch(self):
        """
        Scenario: Skill dispatches both agents in parallel
        Given the voice-review skill
        When I read its methodology
        Then it describes parallel dispatch of prose + craft reviewers
        """
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "parallel" in content.lower()
        assert "prose" in content.lower()
        assert "craft" in content.lower()

    @pytest.mark.unit
    def test_skill_separates_hard_and_soft_failures(self):
        """
        Scenario: Skill distinguishes hard failures from advisories
        Given that some issues should auto-fix and others need approval
        When I read the skill
        Then it separates hard failures (auto-fix) from advisories
        """
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "Hard" in content or "hard fail" in content.lower()
        assert "Advisory" in content or "advisory" in content.lower()


class TestProseReviewerAgent:
    """
    Feature: Prose reviewer agent for AI pattern detection

    As a writer
    I want AI patterns and voice drift detected
    So that generated text doesn't read as obviously synthetic
    """

    @pytest.mark.unit
    def test_prose_reviewer_exists(self):
        """
        Scenario: Prose reviewer agent file exists
        Given the scribe plugin
        When I look for the prose-reviewer agent
        Then the agent file exists
        """
        assert (AGENTS_DIR / "prose-reviewer.md").exists()

    @pytest.mark.unit
    def test_prose_reviewer_has_hard_failures(self):
        """
        Scenario: Prose reviewer defines hard failure patterns
        Given the prose-reviewer agent
        When I read its detection rules
        Then it lists patterns that are auto-fixed without asking
        """
        content = (AGENTS_DIR / "prose-reviewer.md").read_text()
        assert "Hard Failure" in content or "hard fail" in content.lower()
        assert "em dash" in content.lower() or "Em dash" in content

    @pytest.mark.unit
    def test_prose_reviewer_detects_voice_drift(self):
        """
        Scenario: Prose reviewer checks voice drift against register
        Given that each user has a unique extracted voice
        When the reviewer analyzes text
        Then it compares against the register features
        """
        content = (AGENTS_DIR / "prose-reviewer.md").read_text()
        assert "Voice Drift" in content or "voice drift" in content.lower()
        assert "register" in content.lower()

    @pytest.mark.unit
    def test_prose_reviewer_outputs_advisory_table(self):
        """
        Scenario: Prose reviewer outputs structured advisory table
        Given that soft issues need user decision
        When the reviewer reports findings
        Then it uses a table format with line/pattern/current/proposed
        """
        content = (AGENTS_DIR / "prose-reviewer.md").read_text()
        assert "Advisory Table" in content or "advisory table" in content.lower()
        assert "Proposed fix" in content or "proposed" in content.lower()


class TestCraftReviewerAgent:
    """
    Feature: Craft reviewer agent for writing quality assessment

    As a writer
    I want my text evaluated on craft dimensions
    So that it's memorable and structurally interesting
    """

    @pytest.mark.unit
    def test_craft_reviewer_exists(self):
        """
        Scenario: Craft reviewer agent file exists
        Given the scribe plugin
        When I look for the craft-reviewer agent
        Then the agent file exists
        """
        assert (AGENTS_DIR / "craft-reviewer.md").exists()

    @pytest.mark.unit
    def test_craft_reviewer_evaluates_five_dimensions(self):
        """
        Scenario: Craft reviewer evaluates all five dimensions
        Given the five craft dimensions from prose-craft
        When I read the craft reviewer
        Then it evaluates naming, aphoristic destinations,
             dwelling, structural devices, and anchoring
        """
        content = (AGENTS_DIR / "craft-reviewer.md").read_text()
        assert "Naming" in content
        assert "Aphoristic" in content or "aphoristic" in content
        assert "Dwelling" in content or "dwelling" in content
        assert "Structural" in content
        assert "Anchoring" in content or "anchoring" in content

    @pytest.mark.unit
    def test_craft_reviewer_uses_rating_system(self):
        """
        Scenario: Craft reviewer rates each dimension
        Given the three-level rating system
        When I check the output format
        Then it uses Strong/Adequate/Opportunity ratings
        """
        content = (AGENTS_DIR / "craft-reviewer.md").read_text()
        assert "Strong" in content
        assert "Adequate" in content
        assert "Opportunity" in content
