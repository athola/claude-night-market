"""
Feature: Voice Extraction via SICO Comparative Analysis

As a writer
I want to extract my writing voice from samples
So that AI-generated text can match my personal style
"""

from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parents[3]
SKILL_DIR = PLUGIN_ROOT / "skills" / "voice-extract"


class TestVoiceExtractSkillStructure:
    """
    Feature: Voice extraction skill file structure

    As a plugin developer
    I want the voice-extract skill to have proper structure
    So that it loads correctly and follows plugin conventions
    """

    @pytest.mark.unit
    def test_skill_file_exists(self):
        """
        Scenario: Skill file exists at expected path
        Given the scribe plugin
        When I look for the voice-extract skill
        Then SKILL.md exists in the expected directory
        """
        assert (SKILL_DIR / "SKILL.md").exists()

    @pytest.mark.unit
    def test_skill_has_frontmatter(self):
        """
        Scenario: Skill file has valid frontmatter
        Given the voice-extract SKILL.md
        When I read the file
        Then it starts with --- frontmatter delimiters
        And contains required fields
        """
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert content.startswith("---")
        assert "name: voice-extract" in content
        assert "version:" in content
        assert "description:" in content
        assert "tools:" in content
        assert "tags:" in content

    @pytest.mark.unit
    def test_skill_declares_opus_model(self):
        """
        Scenario: Skill recommends Opus for extraction quality
        Given the voice-extract SKILL.md
        When I check the model hint
        Then it specifies opus (research finding: extraction
             needs larger model for nuanced features)
        """
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "model_hint: opus" in content

    @pytest.mark.unit
    def test_skill_has_required_modules(self):
        """
        Scenario: All declared modules exist on disk
        Given the voice-extract skill declares modules
        When I check the modules directory
        Then each declared module file exists
        """
        modules_dir = SKILL_DIR / "modules"
        assert modules_dir.exists()

        required_modules = [
            "sample-intake.md",
            "sico-extraction.md",
            "register-creation.md",
        ]
        for module_file in required_modules:
            assert (modules_dir / module_file).exists(), f"Module {module_file} missing"

    @pytest.mark.unit
    def test_sico_extraction_has_pass_1_and_pass_2(self):
        """
        Scenario: SICO extraction implements two-pass methodology
        Given the sico-extraction module
        When I read its content
        Then it describes Pass 1 (broad comparative) and
             Pass 2 (pressure test for specificity)
        """
        content = (SKILL_DIR / "modules" / "sico-extraction.md").read_text()
        assert "Pass 1" in content
        assert "Pass 2" in content
        assert "Pressure Test" in content

    @pytest.mark.unit
    def test_extraction_includes_strategic_inefficiencies(self):
        """
        Scenario: Extraction captures strategic inefficiencies
        Given research finding that LLMs optimize away deliberate
             detours and variations that make writing human
        When I check the SICO extraction prompt
        Then it explicitly asks for strategic inefficiencies
        """
        content = (SKILL_DIR / "modules" / "sico-extraction.md").read_text()
        assert "STRATEGIC INEFFICIENCIES" in content

    @pytest.mark.unit
    def test_extraction_includes_negation(self):
        """
        Scenario: Extraction captures what writer would NEVER do
        Given research finding that negation-based profiling is
             more revealing than positive preferences
        When I check the SICO extraction prompt
        Then it explicitly asks for negations
        """
        content = (SKILL_DIR / "modules" / "sico-extraction.md").read_text()
        assert "NEGATIONS" in content
        assert "NEVER" in content

    @pytest.mark.unit
    def test_extraction_has_quality_gate(self):
        """
        Scenario: Extraction rejects generic output
        Given the research finding that generic descriptions
             like 'uses varied sentence lengths' are useless
        When I check the SICO extraction module
        Then it has a quality gate rejecting generic phrases
        """
        content = (SKILL_DIR / "modules" / "sico-extraction.md").read_text()
        assert "Quality Gate" in content
        assert "uses varied sentence lengths" in content

    @pytest.mark.unit
    def test_sample_intake_supports_both_modes(self):
        """
        Scenario: Sample intake supports directory and interactive modes
        Given the sample-intake module
        When I check its content
        Then it describes both directory scanning and interactive paste
        """
        content = (SKILL_DIR / "modules" / "sample-intake.md").read_text()
        assert "Directory Mode" in content
        assert "Interactive Mode" in content

    @pytest.mark.unit
    def test_sample_intake_enforces_anonymization(self):
        """
        Scenario: Samples are anonymized before extraction
        Given research finding that context labels cause the
             extractor to anchor on content not voice
        When I check the sample-intake module
        Then it describes anonymization of labels
        """
        content = (SKILL_DIR / "modules" / "sample-intake.md").read_text()
        assert "Anonymiz" in content or "anonymiz" in content


class TestVoiceExtractStorageModel:
    """
    Feature: Voice profile storage structure

    As a user
    I want profiles stored in ~/.claude/voice-profiles/
    So that they persist across sessions and projects
    """

    @pytest.mark.unit
    def test_manifest_schema_documented(self):
        """
        Scenario: Manifest JSON schema is documented
        Given the sample-intake module
        When I look for the manifest format
        Then it documents the expected JSON structure
        """
        content = (SKILL_DIR / "modules" / "sample-intake.md").read_text()
        assert "manifest.json" in content
        assert "profile_name" in content
        assert "samples" in content

    @pytest.mark.unit
    def test_register_creation_documented(self):
        """
        Scenario: Register creation from extraction is documented
        Given the register-creation module
        When I read its content
        Then it describes default register creation
        And mentions inheritance for non-default registers
        """
        content = (SKILL_DIR / "modules" / "register-creation.md").read_text()
        assert "Default Register" in content
        assert "Inherits" in content or "inherit" in content
