"""Structure and content tests for the code-refinement skill.

Validates that all skill artifacts exist with proper frontmatter,
cross-references are consistent, and fallback patterns are present.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).parent.parent
SKILL_DIR = PLUGIN_ROOT / "skills" / "code-refinement"
MODULES_DIR = SKILL_DIR / "modules"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
AGENTS_DIR = PLUGIN_ROOT / "agents"

EXPECTED_MODULES = [
    "duplication-analysis.md",
    "algorithm-efficiency.md",
    "clean-code-checks.md",
    "architectural-fit.md",
]


def _parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    end = text.index("---", 3)
    return yaml.safe_load(text[3:end]) or {}


class TestCodeRefinementSkillStructure:
    """
    Feature: Code refinement skill has valid structure

    As a plugin developer
    I want all skill artifacts to exist with proper metadata
    So that the skill loads correctly in Claude Code
    """

    @pytest.mark.unit
    def test_skill_file_exists(self):
        """Given the code-refinement skill, SKILL.md must exist."""
        assert (SKILL_DIR / "SKILL.md").exists()

    @pytest.mark.unit
    def test_skill_has_valid_frontmatter(self):
        """Given SKILL.md, it must have required frontmatter fields."""
        fm = _parse_frontmatter(SKILL_DIR / "SKILL.md")
        assert fm.get("name") == "code-refinement"
        assert "description" in fm
        assert fm.get("category") == "code-quality"
        assert "version" in fm
        assert "modules" in fm
        assert "dependencies" in fm

    @pytest.mark.unit
    @pytest.mark.parametrize("module_file", EXPECTED_MODULES)
    def test_module_exists(self, module_file):
        """Given expected modules, each file must exist."""
        assert (MODULES_DIR / module_file).exists(), f"Missing module: {module_file}"

    @pytest.mark.unit
    @pytest.mark.parametrize("module_file", EXPECTED_MODULES)
    def test_module_has_frontmatter(self, module_file):
        """Given a module file, it must have parent_skill reference."""
        fm = _parse_frontmatter(MODULES_DIR / module_file)
        assert fm.get("parent_skill") == "pensive:code-refinement"
        assert "estimated_tokens" in fm

    @pytest.mark.unit
    def test_skill_modules_list_matches_files(self):
        """Given SKILL.md modules list, all referenced files must exist."""
        fm = _parse_frontmatter(SKILL_DIR / "SKILL.md")
        for module_ref in fm.get("modules", []):
            path = SKILL_DIR / module_ref
            assert path.exists(), f"SKILL.md references missing module: {module_ref}"


class TestCodeRefinerAgent:
    """
    Feature: Code refiner agent has valid structure

    As a plugin developer
    I want the agent to have proper metadata and escalation config
    So that it orchestrates refinement correctly
    """

    @pytest.mark.unit
    def test_agent_exists(self):
        """Given the code-refiner agent, the file must exist."""
        assert (AGENTS_DIR / "code-refiner.md").exists()

    @pytest.mark.unit
    def test_agent_has_valid_frontmatter(self):
        """Given code-refiner.md, it must have model and escalation."""
        fm = _parse_frontmatter(AGENTS_DIR / "code-refiner.md")
        assert fm.get("name") == "code-refiner"
        assert fm.get("model") == "sonnet"
        assert "escalation" in fm
        assert fm["escalation"].get("to") == "opus"

    @pytest.mark.unit
    def test_agent_references_skill(self):
        """Given code-refiner agent, it must reference the skill."""
        text = (AGENTS_DIR / "code-refiner.md").read_text()
        assert "pensive:code-refinement" in text


class TestRefineCodeCommand:
    """
    Feature: Refine-code command has valid structure

    As a user
    I want /refine-code to have proper options and documentation
    So that I can use it effectively
    """

    @pytest.mark.unit
    def test_command_exists(self):
        """Given the refine-code command, the file must exist."""
        assert (COMMANDS_DIR / "refine-code.md").exists()

    @pytest.mark.unit
    def test_command_has_valid_frontmatter(self):
        """Given refine-code.md, it must have name and usage."""
        fm = _parse_frontmatter(COMMANDS_DIR / "refine-code.md")
        assert fm.get("name") == "refine-code"
        assert "usage" in fm

    @pytest.mark.unit
    def test_command_documents_fallbacks(self):
        """Given refine-code.md, it must document plugin fallbacks."""
        text = (COMMANDS_DIR / "refine-code.md").read_text()
        assert "Optional" in text or "optional" in text
        assert "Fallback" in text or "fallback" in text


class TestCleanupCommand:
    """
    Feature: Cleanup command has valid structure in conserve plugin

    As a user
    I want /cleanup to orchestrate multiple cleanup commands
    So that I get comprehensive codebase maintenance
    """

    CONSERVE_ROOT = PLUGIN_ROOT.parent / "conserve"

    @pytest.mark.unit
    def test_command_exists(self):
        """Given the cleanup command, the file must exist."""
        assert (self.CONSERVE_ROOT / "commands" / "cleanup.md").exists()

    @pytest.mark.unit
    def test_command_has_valid_frontmatter(self):
        """Given cleanup.md, it must have name and usage."""
        fm = _parse_frontmatter(self.CONSERVE_ROOT / "commands" / "cleanup.md")
        assert fm.get("name") == "cleanup"
        assert "usage" in fm

    @pytest.mark.unit
    def test_command_documents_graceful_degradation(self):
        """Given cleanup.md, it must document behavior when plugins missing."""
        text = (self.CONSERVE_ROOT / "commands" / "cleanup.md").read_text()
        assert "pensive" in text.lower()
        assert "Graceful" in text or "graceful" in text or "fallback" in text.lower()

    @pytest.mark.unit
    def test_command_references_sub_commands(self):
        """Given cleanup.md, it must reference bloat-scan, unbloat, and refine-code."""
        text = (self.CONSERVE_ROOT / "commands" / "cleanup.md").read_text()
        assert "/bloat-scan" in text
        assert "/unbloat" in text
        assert "/refine-code" in text
        assert "/ai-hygiene-audit" in text


class TestCrossPluginFallbacks:
    """
    Feature: Cross-plugin references have proper fallbacks

    As a user with partial plugin installation
    I want skills to degrade gracefully
    So that I can use what's available without errors
    """

    @pytest.mark.unit
    def test_skill_documents_optional_dependencies(self):
        """Given SKILL.md, optional deps must have documented fallbacks."""
        text = (SKILL_DIR / "SKILL.md").read_text()
        # Must mention each optional plugin with fallback behavior
        assert "imbue" in text
        assert "conserve" in text
        assert "archetypes" in text
        # Must have fallback table or section
        assert "Fallback" in text or "fallback" in text

    @pytest.mark.unit
    def test_architectural_fit_has_two_modes(self):
        """Given architectural-fit module, it must support paradigm-aware and principle-based modes."""
        text = (MODULES_DIR / "architectural-fit.md").read_text()
        assert "Mode 1" in text or "Paradigm-Aware" in text
        assert "Mode 2" in text or "Principle-Based" in text
        assert "fallback" in text.lower()

    @pytest.mark.unit
    def test_clean_code_checks_has_conserve_fallback(self):
        """Given clean-code-checks module, it must work without conserve plugin."""
        text = (MODULES_DIR / "clean-code-checks.md").read_text()
        assert "conserve" in text.lower()
        assert "Fallback" in text or "fallback" in text
