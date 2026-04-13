"""
Feature: Voice Generation with Source Material Framing

As a writer
I want to generate text in my extracted voice
So that I get a usable first draft without blank page syndrome
"""

from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parents[3]
SKILL_DIR = PLUGIN_ROOT / "skills" / "voice-generate"


class TestVoiceGenerateSkillStructure:
    """
    Feature: Voice generation skill file structure

    As a plugin developer
    I want the voice-generate skill to have proper structure
    So that it loads correctly and follows plugin conventions
    """

    @pytest.mark.unit
    def test_skill_file_exists(self):
        """
        Scenario: Skill file exists at expected path
        Given the scribe plugin
        When I look for the voice-generate skill
        Then SKILL.md exists in the expected directory
        """
        assert (SKILL_DIR / "SKILL.md").exists()

    @pytest.mark.unit
    def test_skill_has_frontmatter(self):
        """
        Scenario: Skill file has valid frontmatter
        Given the voice-generate SKILL.md
        When I read the file
        Then it contains required frontmatter fields
        """
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert content.startswith("---")
        assert "name: voice-generate" in content
        assert "version:" in content
        assert "model_hint: opus" in content

    @pytest.mark.unit
    def test_skill_has_required_modules(self):
        """
        Scenario: All declared modules exist on disk
        Given the voice-generate skill declares modules
        When I check the modules directory
        Then each declared module file exists
        """
        modules_dir = SKILL_DIR / "modules"
        assert modules_dir.exists()

        required_modules = [
            "source-framing.md",
            "register-selection.md",
            "generation-pipeline.md",
        ]
        for module_file in required_modules:
            assert (modules_dir / module_file).exists(), f"Module {module_file} missing"


class TestSourceFraming:
    """
    Feature: Source material framing as raw notes

    As a writer
    I want my source material framed as raw notes
    So that generated text feels like thinking not reporting
    (Research: source framing is the largest single variable
     in output quality - larger than voice rules or model choice)
    """

    @pytest.mark.unit
    def test_default_framing_is_raw_notes(self):
        """
        Scenario: Default framing uses raw notes approach
        Given the source-framing module
        When I check the default framing
        Then it frames material as notes being thought through
        """
        content = (SKILL_DIR / "modules" / "source-framing.md").read_text()
        assert "rough notes" in content or "raw notes" in content
        assert "still thinking" in content or "still working" in content

    @pytest.mark.unit
    def test_alternative_framings_available(self):
        """
        Scenario: Alternative framings exist for explicit override
        Given the source-framing module
        When I check for override options
        Then it provides alternatives for when user requests them
        """
        content = (SKILL_DIR / "modules" / "source-framing.md").read_text()
        assert "Override" in content or "override" in content

    @pytest.mark.unit
    def test_framing_lever_documented(self):
        """
        Scenario: The framing lever effect is documented
        Given that framing is the largest quality variable
        When I read the source-framing module
        Then it explains why framing matters
        """
        content = (SKILL_DIR / "modules" / "source-framing.md").read_text()
        assert "framing" in content.lower()
        assert "quality" in content.lower() or "better" in content.lower()


class TestGenerationPipeline:
    """
    Feature: End-to-end generation pipeline

    As a writer
    I want a clear pipeline from source to reviewed text
    So that generation follows a consistent quality process
    """

    @pytest.mark.unit
    def test_pipeline_includes_auto_fix(self):
        """
        Scenario: Pipeline auto-fixes hard failures
        Given the generation pipeline
        When I check its stages
        Then it includes auto-fix for banned phrases and em dashes
        """
        content = (SKILL_DIR / "modules" / "generation-pipeline.md").read_text()
        assert "Auto-Fix" in content or "auto-fix" in content
        assert "banned phrase" in content.lower()
        assert "em dash" in content.lower()

    @pytest.mark.unit
    def test_pipeline_routes_models_correctly(self):
        """
        Scenario: Pipeline routes to correct models
        Given that Opus is needed for generation but Sonnet
             suffices for review
        When I check the model routing table
        Then generation uses Opus and review uses Sonnet
        """
        content = (SKILL_DIR / "modules" / "generation-pipeline.md").read_text()
        assert "Opus" in content
        assert "Sonnet" in content

    @pytest.mark.unit
    def test_pipeline_includes_snapshot_stage(self):
        """
        Scenario: Pipeline captures snapshots for learning
        Given that the learning loop needs pre/post snapshots
        When I check the pipeline stages
        Then it includes snapshot capture points
        """
        content = (SKILL_DIR / "modules" / "generation-pipeline.md").read_text()
        assert "snapshot" in content.lower() or "Snapshot" in content
