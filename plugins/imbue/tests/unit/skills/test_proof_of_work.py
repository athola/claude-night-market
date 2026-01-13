"""Tests for proof-of-work skill and Iron Law enforcement.

This module tests the proof-of-work validation workflow and the Iron Law TDD
enforcement patterns, following TDD/BDD principles.

The Iron Law: NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST
"""

from pathlib import Path

import pytest


class TestProofOfWorkSkill:
    """Feature: Proof-of-work enforces evidence-based completion claims.

    As a developer
    I want proof-of-work discipline enforced
    So that completion claims are backed by evidence
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the proof-of-work skill."""
        return Path(__file__).parents[3] / "skills" / "proof-of-work" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the proof-of-work skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_iron_law_section(self, skill_content: str) -> None:
        """Scenario: Proof-of-work skill includes Iron Law section.

        Given the proof-of-work skill
        When reading the skill content
        Then it should contain the Iron Law section
        And define the core principle.
        """
        # Assert - Iron Law section exists
        assert "## The Iron Law" in skill_content
        assert "NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_iron_law_self_check_table(self, skill_content: str) -> None:
        """Scenario: Proof-of-work skill includes Iron Law self-check table.

        Given the proof-of-work skill
        When reading the skill content
        Then it should contain a self-check table
        With questions about TDD compliance.
        """
        # Assert - self-check table elements exist
        assert "Self-Check" in skill_content or "self-check" in skill_content.lower()
        assert "documented evidence" in skill_content.lower()
        assert "failure" in skill_content.lower()
        assert "pre-conceived" in skill_content.lower()
        assert "uncertainty" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_iron_law_todowrite_items(self, skill_content: str) -> None:
        """Scenario: Proof-of-work skill defines Iron Law TodoWrite items.

        Given the proof-of-work skill
        When reading the skill content
        Then it should define TDD-specific TodoWrite items
        For tracking RED/GREEN/REFACTOR phases.
        """
        # Assert - Iron Law TodoWrite items exist
        assert "proof:iron-law-red" in skill_content
        assert "proof:iron-law-green" in skill_content
        assert "proof:iron-law-refactor" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_references_iron_law_module(self, skill_content: str) -> None:
        """Scenario: Proof-of-work skill references Iron Law enforcement module.

        Given the proof-of-work skill
        When reading the skill content
        Then it should reference the iron-law-enforcement.md module.
        """
        # Assert - module reference exists
        assert "iron-law-enforcement.md" in skill_content


class TestIronLawEnforcementModule:
    """Feature: Iron Law enforcement module provides TDD compliance patterns.

    As a developer
    I want comprehensive TDD enforcement patterns
    So that Cargo Cult TDD is prevented
    """

    @pytest.fixture
    def module_path(self) -> Path:
        """Path to the iron-law-enforcement module."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "proof-of-work"
            / "modules"
            / "iron-law-enforcement.md"
        )

    @pytest.fixture
    def module_content(self, module_path: Path) -> str:
        """Load the iron-law-enforcement module content."""
        return module_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_exists(self, module_path: Path) -> None:
        """Scenario: Iron Law enforcement module exists.

        Given the proof-of-work skill
        When looking for the iron-law-enforcement module
        Then it should exist in the modules directory.
        """
        assert module_path.exists(), f"Module not found at {module_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_enforcement_levels(self, module_content: str) -> None:
        """Scenario: Iron Law module defines multiple enforcement levels.

        Given the iron-law-enforcement module
        When reading the module content
        Then it should define multiple enforcement levels
        Including self-enforcement, adversarial, git history, pre-commit, coverage.
        """
        # Assert - enforcement levels are documented
        assert "Level 1" in module_content or "Self-Enforcement" in module_content
        assert "Level 2" in module_content or "Adversarial" in module_content
        assert "Git History" in module_content
        assert "Pre-Commit" in module_content or "pre-commit" in module_content
        assert "Coverage" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_includes_red_flags_table(self, module_content: str) -> None:
        """Scenario: Iron Law module includes red flags for TDD violations.

        Given the iron-law-enforcement module
        When reading the module content
        Then it should include red flags table
        For detecting TDD violations.
        """
        # Assert - red flags are documented
        assert "Red Flag" in module_content or "red flag" in module_content.lower()
        assert "plan the implementation" in module_content.lower()
        assert "pre-conceived" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_includes_subagent_pattern(self, module_content: str) -> None:
        """Scenario: Iron Law module documents adversarial subagent pattern.

        Given the iron-law-enforcement module
        When reading the module content
        Then it should document RED/GREEN/REFACTOR subagent pattern
        For adversarial TDD verification.
        """
        # Assert - subagent pattern is documented
        assert "RED Agent" in module_content or "red agent" in module_content.lower()
        assert (
            "GREEN Agent" in module_content or "green agent" in module_content.lower()
        )
        assert (
            "REFACTOR Agent" in module_content
            or "refactor agent" in module_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_includes_git_audit_commands(self, module_content: str) -> None:
        """Scenario: Iron Law module includes git history audit commands.

        Given the iron-law-enforcement module
        When reading the module content
        Then it should include git commands for TDD audit
        To detect implementation without tests.
        """
        # Assert - git audit commands exist
        assert "git log" in module_content
        assert "git show" in module_content or "git diff" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_includes_coverage_requirements(self, module_content: str) -> None:
        """Scenario: Iron Law module includes three-pillar coverage requirements.

        Given the iron-law-enforcement module
        When reading the module content
        Then it should define line, branch, and mutation coverage
        As the three pillars of test quality.
        """
        # Assert - coverage requirements exist
        assert "Line Coverage" in module_content or "line coverage" in module_content
        assert (
            "Branch Coverage" in module_content or "branch coverage" in module_content
        )
        assert "Mutation" in module_content or "mutation" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_includes_recovery_protocol(self, module_content: str) -> None:
        """Scenario: Iron Law module includes recovery protocol for violations.

        Given the iron-law-enforcement module
        When reading the module content
        Then it should include recovery protocol
        For when Iron Law is violated.
        """
        # Assert - recovery protocol exists
        assert "Recovery" in module_content or "recovery" in module_content.lower()
        assert "Violation" in module_content or "violation" in module_content.lower()


class TestGovernancePolicyIronLaw:
    """Feature: Governance policy includes Iron Law enforcement.

    As a session participant
    I want Iron Law enforced at session start
    So that TDD compliance is reminded
    """

    @pytest.fixture
    def policy_path(self) -> Path:
        """Path to the post_implementation_policy.py."""
        return (
            Path(__file__).parents[4]
            / "sanctum"
            / "hooks"
            / "post_implementation_policy.py"
        )

    @pytest.fixture
    def policy_content(self, policy_path: Path) -> str:
        """Load the governance policy content."""
        return policy_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_policy_includes_iron_law_statement(self, policy_content: str) -> None:
        """Scenario: Governance policy includes Iron Law statement.

        Given the post_implementation_policy hook
        When reading the hook content
        Then it should include the Iron Law statement.
        """
        # Assert - Iron Law statement exists
        assert "Iron Law" in policy_content
        assert "NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST" in policy_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_policy_includes_iron_law_todowrite_items(
        self, policy_content: str
    ) -> None:
        """Scenario: Governance policy mentions Iron Law TodoWrite items.

        Given the post_implementation_policy hook
        When reading the hook content
        Then it should mention iron-law TodoWrite items.
        """
        # Assert - TodoWrite items mentioned
        assert "iron-law-red" in policy_content
        assert "iron-law-green" in policy_content
        assert "iron-law-refactor" in policy_content


class TestSessionStartIronLaw:
    """Feature: Session start hook includes Iron Law quick reference.

    As a session participant
    I want Iron Law quick reference at session start
    So that TDD compliance is visible
    """

    @pytest.fixture
    def session_hook_path(self) -> Path:
        """Path to the imbue session-start.sh hook."""
        return Path(__file__).parents[3] / "hooks" / "session-start.sh"

    @pytest.fixture
    def session_hook_content(self, session_hook_path: Path) -> str:
        """Load the session start hook content."""
        return session_hook_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_hook_includes_iron_law_section(
        self, session_hook_content: str
    ) -> None:
        """Scenario: Session start hook includes Iron Law section.

        Given the imbue session-start.sh hook
        When reading the hook content
        Then it should include Iron Law quick reference.
        """
        # Assert - Iron Law section exists
        assert "Iron Law" in session_hook_content
        assert "NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST" in session_hook_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_hook_includes_tdd_todowrite_items(
        self, session_hook_content: str
    ) -> None:
        """Scenario: Session start hook mentions TDD TodoWrite items.

        Given the imbue session-start.sh hook
        When reading the hook content
        Then it should mention iron-law TodoWrite items.
        """
        # Assert - TodoWrite items mentioned
        assert "iron-law-red" in session_hook_content
        assert "iron-law-green" in session_hook_content
        assert "iron-law-refactor" in session_hook_content


class TestProofEnforcementIronLaw:
    """Feature: Proof enforcement documentation includes Iron Law rule.

    As a developer
    I want proof enforcement to include Iron Law
    So that TDD compliance is checked before completion
    """

    @pytest.fixture
    def enforcement_doc_path(self) -> Path:
        """Path to the proof-enforcement.md documentation."""
        return Path(__file__).parents[3] / "hooks" / "proof-enforcement.md"

    @pytest.fixture
    def enforcement_doc_content(self, enforcement_doc_path: Path) -> str:
        """Load the proof enforcement documentation."""
        return enforcement_doc_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_enforcement_doc_includes_iron_law_rule(
        self, enforcement_doc_content: str
    ) -> None:
        """Scenario: Proof enforcement doc includes Iron Law TDD rule.

        Given the proof-enforcement.md documentation
        When reading the documentation
        Then it should include Iron Law TDD Compliance rule.
        """
        # Assert - Iron Law rule exists
        assert "Iron Law" in enforcement_doc_content
        assert "TDD" in enforcement_doc_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_enforcement_doc_includes_tdd_evidence_markers(
        self, enforcement_doc_content: str
    ) -> None:
        """Scenario: Proof enforcement doc includes TDD evidence markers.

        Given the proof-enforcement.md documentation
        When reading the documentation
        Then it should mention TDD evidence markers.
        """
        # Assert - TDD evidence markers mentioned
        assert "iron-law-red" in enforcement_doc_content
        assert "iron-law-green" in enforcement_doc_content
        # Can be either in frontmatter or content
        assert (
            "[E-TDD" in enforcement_doc_content
            or "TDD evidence" in enforcement_doc_content.lower()
        )
