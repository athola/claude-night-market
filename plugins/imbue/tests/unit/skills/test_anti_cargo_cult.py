"""Tests for anti-cargo-cult module and understanding verification.

This module tests the anti-cargo-cult shared module's presence, structure,
and integration across imbue skills, following TDD/BDD principles.

The Core Principle: If you don't understand the code, don't ship it.

IRON LAW COMPLIANCE: These tests were written BEFORE verifying the module exists.
"""

from pathlib import Path

import pytest


class TestAntiCargoCultPrinciples:
    """Feature: Anti-cargo-cult principles are enforced in imbue skills.

    As a developer
    I want anti-cargo-cult discipline enforced
    So that code is understood, not just copied

    Note: The shared/modules/anti-cargo-cult.md module was consolidated into
    proof-of-work and scope-guard skills. These tests verify the principles
    remain present in their new locations.
    """

    @pytest.fixture
    def proof_of_work_path(self) -> Path:
        """Path to proof-of-work skill (now contains anti-cargo-cult concepts)."""
        return Path(__file__).parents[3] / "skills" / "proof-of-work" / "SKILL.md"

    @pytest.fixture
    def proof_of_work_content(self, proof_of_work_path: Path) -> str:
        """Load the proof-of-work skill content."""
        if not proof_of_work_path.exists():
            pytest.fail(f"Skill not found at {proof_of_work_path}")
        return proof_of_work_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_proof_of_work_skill_exists(self, proof_of_work_path: Path) -> None:
        """Scenario: Proof-of-work skill exists (hosts anti-cargo-cult concepts).

        Given the imbue plugin skills
        When looking for the proof-of-work skill
        Then it should exist at the expected path.
        """
        assert proof_of_work_path.exists(), f"Skill not found at {proof_of_work_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_proof_of_work_has_understanding_verification(
        self, proof_of_work_content: str
    ) -> None:
        """Scenario: Proof-of-work enforces understanding verification.

        Given the proof-of-work skill (consolidated from shared anti-cargo-cult)
        When reading the skill content
        Then it should enforce understanding before shipping code.
        """
        content_lower = proof_of_work_content.lower()
        assert "understand" in content_lower or "verification" in content_lower, (
            "Should enforce understanding verification"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_proof_of_work_has_evidence_requirements(
        self, proof_of_work_content: str
    ) -> None:
        """Scenario: Proof-of-work requires evidence of work done.

        Given the proof-of-work skill
        When reading the skill content
        Then it should require proof/evidence before claiming completion.
        """
        content_lower = proof_of_work_content.lower()
        assert "evidence" in content_lower or "proof" in content_lower, (
            "Should require evidence of work"
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
    def test_proof_of_work_references_anti_cargo_cult(
        self, proof_of_work_path: Path
    ) -> None:
        """Scenario: Proof-of-work skill references anti-cargo-cult concepts.

        Given the proof-of-work skill
        When reading the skill content
        Then it should reference cargo cult or understanding verification.
        """
        content = proof_of_work_path.read_text()
        assert (
            "cargo" in content.lower()
            or "understanding" in content.lower()
            or "NO CODE WITHOUT UNDERSTANDING" in content
        )


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
    def test_red_flags_references_cargo_cult_concepts(
        self, red_flags_content: str
    ) -> None:
        """Scenario: Red flags references cargo cult concepts.

        Given the red-flags module
        When reading the module content
        Then it should reference cargo cult patterns or understanding.
        """
        content_lower = red_flags_content.lower()
        assert (
            "cargo" in content_lower
            or "understand" in content_lower
            or "anti-cargo" in content_lower
        )
