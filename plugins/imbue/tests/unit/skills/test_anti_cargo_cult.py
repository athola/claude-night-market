"""Tests for anti-cargo-cult module and understanding verification.

This module tests the anti-cargo-cult shared module's presence, structure,
and integration across imbue skills, following TDD/BDD principles.

The Core Principle: If you don't understand the code, don't ship it.

IRON LAW COMPLIANCE: These tests were written BEFORE verifying the module exists.
"""

from pathlib import Path

import pytest


class TestAntiCargoCultModule:
    """Feature: Anti-cargo-cult module enforces understanding verification.

    As a developer
    I want anti-cargo-cult discipline enforced
    So that code is understood, not just copied
    """

    @pytest.fixture
    def module_path(self) -> Path:
        """Path to the anti-cargo-cult module."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "shared"
            / "modules"
            / "anti-cargo-cult.md"
        )

    @pytest.fixture
    def module_content(self, module_path: Path) -> str:
        """Load the anti-cargo-cult module content."""
        if not module_path.exists():
            pytest.fail(f"Module not found at {module_path} - Iron Law RED phase")
        return module_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_exists(self, module_path: Path) -> None:
        """Scenario: Anti-cargo-cult module exists.

        Given the imbue plugin shared modules
        When looking for the anti-cargo-cult module
        Then it should exist at the expected path.
        """
        assert module_path.exists(), f"Module not found at {module_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_has_five_whys_section(self, module_content: str) -> None:
        """Scenario: Anti-cargo-cult module includes Five Whys protocol.

        Given the anti-cargo-cult module
        When reading the module content
        Then it should contain the Five Whys of Understanding
        And explain each question's purpose.
        """
        assert "Five Whys" in module_content or "five whys" in module_content.lower()
        assert "WHY does this approach work" in module_content
        assert "WHY this pattern over alternatives" in module_content
        assert "WHAT breaks if we change" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_has_red_flags_table(self, module_content: str) -> None:
        """Scenario: Anti-cargo-cult module includes red flags.

        Given the anti-cargo-cult module
        When reading the module content
        Then it should contain red flags for cargo cult patterns
        Both code-level and thought-level.
        """
        assert "Red Flag" in module_content or "red flag" in module_content.lower()
        assert "Copy" in module_content or "copy" in module_content.lower()
        assert (
            "AI suggested" in module_content or "ai suggested" in module_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_has_understanding_checklist(self, module_content: str) -> None:
        """Scenario: Anti-cargo-cult module has understanding checklist.

        Given the anti-cargo-cult module
        When reading the module content
        Then it should contain a checklist for verifying understanding.
        """
        assert (
            "Understanding Checklist" in module_content
            or "checklist" in module_content.lower()
        )
        assert "[ ]" in module_content  # Checklist items

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_has_recovery_protocol(self, module_content: str) -> None:
        """Scenario: Anti-cargo-cult module includes recovery protocol.

        Given the anti-cargo-cult module
        When reading the module content
        Then it should explain how to recover from cargo cult code.
        """
        assert "Recovery" in module_content or "recovery" in module_content.lower()
        assert "Gap" in module_content or "gap" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_has_fundamental_rule(self, module_content: str) -> None:
        """Scenario: Anti-cargo-cult module states the fundamental rule.

        Given the anti-cargo-cult module
        When reading the module content
        Then it should state: "If you don't understand the code, don't ship it."
        """
        assert "don't understand" in module_content.lower()
        assert (
            "don't ship" in module_content.lower()
            or "ship it" in module_content.lower()
        )


class TestAntiCargoCultIntegration:
    """Feature: Anti-cargo-cult integrates with other imbue skills.

    As a developer
    I want anti-cargo-cult patterns integrated across skills
    So that understanding verification is consistent
    """

    @pytest.fixture
    def proof_of_work_path(self) -> Path:
        """Path to proof-of-work skill."""
        return Path(__file__).parents[3] / "skills" / "proof-of-work" / "SKILL.md"

    @pytest.fixture
    def rigorous_reasoning_path(self) -> Path:
        """Path to rigorous-reasoning skill."""
        return Path(__file__).parents[3] / "skills" / "rigorous-reasoning" / "SKILL.md"

    @pytest.fixture
    def anti_overengineering_path(self) -> Path:
        """Path to anti-overengineering module."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "scope-guard"
            / "modules"
            / "anti-overengineering.md"
        )

    @pytest.fixture
    def iron_law_path(self) -> Path:
        """Path to iron-law-enforcement module."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "proof-of-work"
            / "modules"
            / "iron-law-enforcement.md"
        )

    @pytest.fixture
    def shared_skill_path(self) -> Path:
        """Path to shared skill."""
        return Path(__file__).parents[3] / "skills" / "shared" / "SKILL.md"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_proof_of_work_has_understanding_verification(
        self, proof_of_work_path: Path
    ) -> None:
        """Scenario: Proof-of-work skill includes understanding verification.

        Given the proof-of-work skill
        When reading the skill content
        Then it should reference cargo cult or understanding verification.
        """
        content = proof_of_work_path.read_text()
        assert "cargo cult" in content.lower() or "understanding" in content.lower()
        assert (
            "NO CODE WITHOUT UNDERSTANDING" in content
            or "understand" in content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_rigorous_reasoning_has_cargo_cult_patterns(
        self, rigorous_reasoning_path: Path
    ) -> None:
        """Scenario: Rigorous-reasoning skill includes cargo cult reasoning patterns.

        Given the rigorous-reasoning skill
        When reading the skill content
        Then it should include cargo cult reasoning patterns to catch.
        """
        content = rigorous_reasoning_path.read_text()
        assert "Cargo Cult" in content or "cargo cult" in content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_anti_overengineering_has_cargo_cult_section(
        self, anti_overengineering_path: Path
    ) -> None:
        """Scenario: Anti-overengineering module includes cargo cult patterns.

        Given the anti-overengineering module
        When reading the module content
        Then it should include cargo cult overengineering patterns.
        """
        content = anti_overengineering_path.read_text()
        assert "Cargo Cult" in content or "cargo cult" in content.lower()
        assert "Enterprise" in content or "enterprise" in content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_iron_law_has_fourth_law(self, iron_law_path: Path) -> None:
        """Scenario: Iron Law enforcement includes understanding requirement.

        Given the iron-law-enforcement module
        When reading the module content
        Then it should include the fourth law about understanding.
        """
        content = iron_law_path.read_text()
        assert "NO CODE WITHOUT UNDERSTANDING" in content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shared_skill_references_anti_cargo_cult(
        self, shared_skill_path: Path
    ) -> None:
        """Scenario: Shared skill references anti-cargo-cult module.

        Given the shared skill
        When reading the skill content
        Then it should reference the anti-cargo-cult module.
        """
        content = shared_skill_path.read_text()
        assert "anti-cargo-cult" in content.lower()


class TestProofOfWorkRedFlags:
    """Feature: Proof-of-work red flags include cargo cult patterns.

    As a developer
    I want cargo cult red flags in proof-of-work
    So that AI-generated code is properly scrutinized
    """

    @pytest.fixture
    def red_flags_path(self) -> Path:
        """Path to red-flags module."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "proof-of-work"
            / "modules"
            / "red-flags.md"
        )

    @pytest.fixture
    def red_flags_content(self, red_flags_path: Path) -> str:
        """Load the red-flags module content."""
        return red_flags_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_red_flags_has_cargo_cult_family(self, red_flags_content: str) -> None:
        """Scenario: Red flags module has cargo cult family section.

        Given the red-flags module
        When reading the module content
        Then it should have a "Cargo Cult" Family section.
        """
        assert "Cargo Cult" in red_flags_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_red_flags_has_ai_suggested_pattern(self, red_flags_content: str) -> None:
        """Scenario: Red flags includes AI suggestion pattern.

        Given the red-flags module
        When reading the module content
        Then it should warn about blindly accepting AI suggestions.
        """
        assert (
            "AI suggested" in red_flags_content
            or "ai suggested" in red_flags_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_red_flags_has_best_practice_pattern(self, red_flags_content: str) -> None:
        """Scenario: Red flags includes best practice pattern.

        Given the red-flags module
        When reading the module content
        Then it should warn about undefined "best practices".
        """
        assert "best practice" in red_flags_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_red_flags_has_copy_snippet_pattern(self, red_flags_content: str) -> None:
        """Scenario: Red flags includes copy-paste pattern.

        Given the red-flags module
        When reading the module content
        Then it should warn about copying without understanding.
        """
        assert "copy" in red_flags_content.lower()
        assert (
            "snippet" in red_flags_content.lower()
            or "Stack Overflow" in red_flags_content
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_red_flags_references_anti_cargo_cult_module(
        self, red_flags_content: str
    ) -> None:
        """Scenario: Red flags references anti-cargo-cult module.

        Given the red-flags module
        When reading the module content
        Then it should link to the anti-cargo-cult module.
        """
        assert "anti-cargo-cult.md" in red_flags_content
