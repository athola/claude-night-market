"""Tests for rigorous-reasoning skill and anti-sycophancy enforcement.

This module tests the rigorous-reasoning skill's conflict analysis protocols,
red-flag self-monitoring, and priority signal overrides, following TDD/BDD principles.

The Core Principle: Agreement requires validity, accuracy, or truth. Not politeness.
"""

from pathlib import Path

import pytest


class TestRigorousReasoningSkill:
    """Feature: Rigorous-reasoning enforces non-sycophantic analysis.

    As a developer
    I want rigorous-reasoning discipline enforced
    So that conclusions are backed by checklists, not courtesy
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the rigorous-reasoning skill."""
        return Path(__file__).parents[3] / "skills" / "rigorous-reasoning" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the rigorous-reasoning skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_exists(self, skill_path: Path) -> None:
        """Scenario: Rigorous-reasoning skill exists.

        Given the imbue plugin
        When looking for the rigorous-reasoning skill
        Then it should exist at the expected path.
        """
        assert skill_path.exists(), f"Skill not found at {skill_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_priority_signals_section(self, skill_content: str) -> None:
        """Scenario: Rigorous-reasoning skill includes priority signals.

        Given the rigorous-reasoning skill
        When reading the skill content
        Then it should contain priority signals section
        And define the core override principles.
        """
        assert "## Priority Signals" in skill_content
        assert "No courtesy agreement" in skill_content
        assert "Checklist over intuition" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_red_flag_monitoring_table(self, skill_content: str) -> None:
        """Scenario: Rigorous-reasoning skill includes red flag self-monitoring.

        Given the rigorous-reasoning skill
        When reading the skill content
        Then it should contain a red flag monitoring table
        With sycophantic thought patterns to catch.
        """
        assert "Red Flag" in skill_content or "red flag" in skill_content.lower()
        assert "I agree that" in skill_content
        assert "You're right" in skill_content
        assert "VALIDATE" in skill_content or "validate" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_todowrite_items(self, skill_content: str) -> None:
        """Scenario: Rigorous-reasoning skill defines TodoWrite items.

        Given the rigorous-reasoning skill
        When reading the skill content
        Then it should define rigorous-reasoning specific TodoWrite items
        For tracking activation, checklist, conclusion, and retraction.
        """
        assert "rigorous:activation-triggered" in skill_content
        assert "rigorous:checklist-applied" in skill_content
        assert "rigorous:conclusion-committed" in skill_content
        assert "rigorous:retraction-guarded" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_conflict_triggers(self, skill_content: str) -> None:
        """Scenario: Rigorous-reasoning skill defines conflict-based triggers.

        Given the rigorous-reasoning skill
        When reading the skill content
        Then it should define triggers for conflicts, disagreements, debates.
        """
        assert "conflict" in skill_content.lower()
        assert "disagreement" in skill_content.lower()
        assert "debate" in skill_content.lower()
        assert "ethical" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_references_modules(self, skill_content: str) -> None:
        """Scenario: Rigorous-reasoning skill references its modules.

        Given the rigorous-reasoning skill
        When reading the skill content
        Then it should reference all component modules.
        """
        assert "priority-signals.md" in skill_content
        assert "conflict-analysis.md" in skill_content
        assert "engagement-principles.md" in skill_content
        assert "debate-methodology.md" in skill_content
        assert "correction-protocol.md" in skill_content


class TestPrioritySignalsModule:
    """Feature: Priority signals module defines override principles.

    As a developer
    I want clear override principles
    So that default conversational patterns are corrected
    """

    @pytest.fixture
    def module_path(self) -> Path:
        """Path to the priority-signals module."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "rigorous-reasoning"
            / "modules"
            / "priority-signals.md"
        )

    @pytest.fixture
    def module_content(self, module_path: Path) -> str:
        """Load the priority-signals module content."""
        return module_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_exists(self, module_path: Path) -> None:
        """Scenario: Priority signals module exists.

        Given the rigorous-reasoning skill
        When looking for the priority-signals module
        Then it should exist in the modules directory.
        """
        assert module_path.exists(), f"Module not found at {module_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_no_courtesy_agreement(self, module_content: str) -> None:
        """Scenario: Priority signals module defines no courtesy agreement.

        Given the priority-signals module
        When reading the module content
        Then it should define the no courtesy agreement principle.
        """
        assert "No Courtesy Agreement" in module_content
        assert "validity" in module_content.lower()
        # Accept either "politeness" or "polite" as semantically equivalent
        assert (
            "polite" in module_content.lower()
            or "social comfort" in module_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_checklist_over_intuition(self, module_content: str) -> None:
        """Scenario: Priority signals module defines checklist over intuition.

        Given the priority-signals module
        When reading the module content
        Then it should define the checklist over intuition principle.
        """
        assert "Checklist Over Intuition" in module_content
        assert "initial reaction" in module_content.lower()
        assert "noise" in module_content.lower() or "filter" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_uncomfortable_conclusions(
        self, module_content: str
    ) -> None:
        """Scenario: Priority signals module addresses uncomfortable conclusions.

        Given the priority-signals module
        When reading the module content
        Then it should address maintaining uncomfortable conclusions.
        """
        assert "Uncomfortable" in module_content
        assert (
            "sand down" in module_content.lower() or "palatab" in module_content.lower()
        )


class TestConflictAnalysisModule:
    """Feature: Conflict analysis module provides harm/rights checklist.

    As a developer
    I want a systematic conflict analysis protocol
    So that interpersonal conflicts are analyzed objectively
    """

    @pytest.fixture
    def module_path(self) -> Path:
        """Path to the conflict-analysis module."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "rigorous-reasoning"
            / "modules"
            / "conflict-analysis.md"
        )

    @pytest.fixture
    def module_content(self, module_path: Path) -> str:
        """Load the conflict-analysis module content."""
        return module_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_exists(self, module_path: Path) -> None:
        """Scenario: Conflict analysis module exists.

        Given the rigorous-reasoning skill
        When looking for the conflict-analysis module
        Then it should exist in the modules directory.
        """
        assert module_path.exists(), f"Module not found at {module_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_has_harm_rights_checklist(self, module_content: str) -> None:
        """Scenario: Conflict analysis module has harm/rights checklist.

        Given the conflict-analysis module
        When reading the module content
        Then it should include a harm/rights checklist.
        """
        assert "Harm" in module_content
        assert "Rights" in module_content or "right" in module_content.lower()
        assert "concrete" in module_content.lower()
        assert "measurable" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_has_proportionality_assessment(self, module_content: str) -> None:
        """Scenario: Conflict analysis module includes proportionality.

        Given the conflict-analysis module
        When reading the module content
        Then it should include proportionality assessment.
        """
        assert (
            "Proportionality" in module_content
            or "proportionate" in module_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_has_retraction_bias_protection(self, module_content: str) -> None:
        """Scenario: Conflict analysis module protects against retraction bias.

        Given the conflict-analysis module
        When reading the module content
        Then it should include retraction bias protection.
        """
        assert "Retraction" in module_content or "retract" in module_content.lower()
        assert "substantive" in module_content.lower()
        assert (
            "social pressure" in module_content.lower()
            or "source-based" in module_content.lower()
        )


class TestEngagementPrinciplesModule:
    """Feature: Engagement principles module defines truth-seeking posture.

    As a developer
    I want clear engagement principles
    So that truth-seeking overrides social comfort
    """

    @pytest.fixture
    def module_path(self) -> Path:
        """Path to the engagement-principles module."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "rigorous-reasoning"
            / "modules"
            / "engagement-principles.md"
        )

    @pytest.fixture
    def module_content(self, module_path: Path) -> str:
        """Load the engagement-principles module content."""
        return module_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_exists(self, module_path: Path) -> None:
        """Scenario: Engagement principles module exists.

        Given the rigorous-reasoning skill
        When looking for the engagement-principles module
        Then it should exist in the modules directory.
        """
        assert module_path.exists(), f"Module not found at {module_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_truth_seeking(self, module_content: str) -> None:
        """Scenario: Engagement principles module defines truth-seeking.

        Given the engagement-principles module
        When reading the module content
        Then it should define truth-seeking over social comfort.
        """
        assert "Truth" in module_content or "truth" in module_content.lower()
        assert (
            "social comfort" in module_content.lower()
            or "social" in module_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_pushback_threshold(self, module_content: str) -> None:
        """Scenario: Engagement principles module defines pushback threshold.

        Given the engagement-principles module
        When reading the module content
        Then it should define when to push back vs stay silent.
        """
        assert "Pushback" in module_content or "pushback" in module_content.lower()
        assert "scrutiny" in module_content.lower()
        assert "nitpick" in module_content.lower()


class TestDebateMethodologyModule:
    """Feature: Debate methodology module handles truth claims.

    As a developer
    I want systematic debate methodology
    So that truth claims are properly evaluated
    """

    @pytest.fixture
    def module_path(self) -> Path:
        """Path to the debate-methodology module."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "rigorous-reasoning"
            / "modules"
            / "debate-methodology.md"
        )

    @pytest.fixture
    def module_content(self, module_path: Path) -> str:
        """Load the debate-methodology module content."""
        return module_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_exists(self, module_path: Path) -> None:
        """Scenario: Debate methodology module exists.

        Given the rigorous-reasoning skill
        When looking for the debate-methodology module
        Then it should exist in the modules directory.
        """
        assert module_path.exists(), f"Module not found at {module_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_addresses_definitions(self, module_content: str) -> None:
        """Scenario: Debate methodology addresses standard definitions.

        Given the debate-methodology module
        When reading the module content
        Then it should address operating from standard definitions.
        """
        assert "definition" in module_content.lower()
        assert "standard" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_addresses_resolved_analogues(self, module_content: str) -> None:
        """Scenario: Debate methodology checks for resolved analogues.

        Given the debate-methodology module
        When reading the module content
        Then it should check for resolved analogous cases.
        """
        assert "resolved" in module_content.lower()
        assert "analog" in module_content.lower()


class TestSessionStartHookIntegration:
    """Feature: Session start hook includes rigorous-reasoning quick reference.

    As a session participant
    I want rigorous-reasoning quick reference at session start
    So that anti-sycophancy patterns are visible
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
    def test_session_hook_includes_rigorous_reasoning_section(
        self, session_hook_content: str
    ) -> None:
        """Scenario: Session start hook includes rigorous-reasoning section.

        Given the imbue session-start.sh hook
        When reading the hook content
        Then it should include rigorous-reasoning quick reference.
        """
        assert "rigorous-reasoning" in session_hook_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_hook_includes_sycophancy_red_flags(
        self, session_hook_content: str
    ) -> None:
        """Scenario: Session start hook includes sycophancy red flags.

        Given the imbue session-start.sh hook
        When reading the hook content
        Then it should mention sycophantic patterns to avoid.
        """
        assert (
            "I agree that" in session_hook_content
            or "sycophantic" in session_hook_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_hook_includes_conflict_analysis_reminder(
        self, session_hook_content: str
    ) -> None:
        """Scenario: Session start hook includes conflict analysis reminder.

        Given the imbue session-start.sh hook
        When reading the hook content
        Then it should mention conflict analysis checklist.
        """
        assert (
            "conflict" in session_hook_content.lower()
            or "checklist" in session_hook_content.lower()
        )


class TestAllModulesExist:
    """Feature: All rigorous-reasoning modules exist.

    As a developer
    I want all documented modules to exist
    So that the skill is complete and functional
    """

    @pytest.fixture
    def modules_dir(self) -> Path:
        """Path to the rigorous-reasoning modules directory."""
        return Path(__file__).parents[3] / "skills" / "rigorous-reasoning" / "modules"

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "module_name",
        [
            "priority-signals.md",
            "conflict-analysis.md",
            "engagement-principles.md",
            "debate-methodology.md",
            "correction-protocol.md",
            "incremental-reasoning.md",
            "pattern-completion.md",
        ],
    )
    def test_module_exists(self, modules_dir: Path, module_name: str) -> None:
        """Scenario: Each documented module exists.

        Given the rigorous-reasoning skill
        When checking for module {module_name}
        Then it should exist in the modules directory.
        """
        module_path = modules_dir / module_name
        assert module_path.exists(), f"Module {module_name} not found at {module_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "module_name",
        [
            "priority-signals.md",
            "conflict-analysis.md",
            "engagement-principles.md",
            "debate-methodology.md",
            "correction-protocol.md",
            "incremental-reasoning.md",
            "pattern-completion.md",
        ],
    )
    def test_module_is_not_empty(self, modules_dir: Path, module_name: str) -> None:
        """Scenario: Each module has substantial content.

        Given the rigorous-reasoning skill
        When reading module {module_name}
        Then it should have at least 50 lines of content.
        """
        module_path = modules_dir / module_name
        content = module_path.read_text()
        lines = content.strip().split("\n")
        assert len(lines) >= 50, (
            f"Module {module_name} has only {len(lines)} lines (expected >= 50)"
        )
