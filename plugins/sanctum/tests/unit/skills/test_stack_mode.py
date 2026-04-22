"""Tests for the stack-mode skill structure and contract.

Feature: Shared stack-mode skill consumed by /pr-review and /fix-pr

    As a maintainer of sanctum slash commands
    I want stack-mode to document a stable shared contract
    So that both commands iterate a PR stack the same way
    and consumers can rely on the documented workflow
"""

from __future__ import annotations

from pathlib import Path

import pytest

EXPECTED_MIN_FRONTMATTER_DELIMITERS = 2

SKILL_DIR = Path(__file__).parent.parent.parent.parent / "skills" / "stack-mode"
SKILL_FILE = SKILL_DIR / "SKILL.md"


class TestSkillStructure:
    """Feature: stack-mode skill file structure

    As a plugin maintainer
    I want the stack-mode skill properly structured
    So that it loads correctly via Skill(sanctum:stack-mode)
    """

    @pytest.mark.unit
    def test_skill_file_exists(self) -> None:
        """Scenario: SKILL.md exists

        Given the stack-mode skill directory
        When checking for SKILL.md
        Then the file exists
        """
        assert SKILL_FILE.exists(), f"stack-mode SKILL.md must exist at {SKILL_FILE}"

    @pytest.mark.unit
    def test_skill_has_frontmatter(self) -> None:
        """Scenario: SKILL.md has YAML frontmatter

        Given the stack-mode SKILL.md
        When reading its content
        Then it starts with YAML frontmatter delimiters
        """
        content = SKILL_FILE.read_text()
        assert content.startswith("---")
        assert content.count("---") >= EXPECTED_MIN_FRONTMATTER_DELIMITERS

    @pytest.mark.unit
    def test_skill_name_matches_directory(self) -> None:
        """Scenario: Frontmatter name matches directory

        Given the stack-mode SKILL.md
        When reading the frontmatter
        Then the name field is 'stack-mode'
        """
        content = SKILL_FILE.read_text()
        assert "name: stack-mode" in content

    @pytest.mark.unit
    def test_skill_declares_stacked_diff_siblings(self) -> None:
        """Scenario: Stack-mode depends on sibling stack skills

        Given the stack-mode SKILL.md frontmatter
        When reading dependencies
        Then stack-create, stack-push, stack-rebase are named
        So the loader resolves the full stacked-diff family
        """
        content = SKILL_FILE.read_text()
        for sibling in (
            "sanctum:stack-create",
            "sanctum:stack-push",
            "sanctum:stack-rebase",
        ):
            assert sibling in content, (
                f"stack-mode must declare dependency on {sibling}"
            )


class TestContractSections:
    """Feature: stack-mode documents the shared contract

    As a caller of stack-mode (/pr-review, /fix-pr)
    I want the skill to document the required steps
    So that my command can implement --stack consistently
    """

    @pytest.mark.unit
    def test_contract_section_present(self) -> None:
        """Scenario: Contract section is explicit

        Given the stack-mode SKILL.md
        When reading top-level sections
        Then a `## Contract` section is present
        """
        content = SKILL_FILE.read_text()
        assert "## Contract" in content

    @pytest.mark.unit
    def test_step_1_resolves_stack_membership(self) -> None:
        """Scenario: Step 1 resolves membership

        Given the stack-mode SKILL.md
        When inspecting Step 1
        Then it is named 'Resolve Stack Membership'
        """
        content = SKILL_FILE.read_text()
        assert "Step 1" in content
        assert "Resolve Stack Membership" in content

    @pytest.mark.unit
    def test_three_detection_strategies_documented(self) -> None:
        """Scenario: Three detection strategies documented

        Given the stack-mode SKILL.md
        When reading Step 1
        Then Strategy A, B, and C are each named
        So callers can choose or fall back predictably
        """
        content = SKILL_FILE.read_text()
        for label in (
            "Strategy A",
            "Strategy B",
            "Strategy C",
        ):
            assert label in content, f"stack-mode must document {label}"

    @pytest.mark.unit
    def test_iteration_is_base_to_tip(self) -> None:
        """Scenario: Iteration order is base-to-tip

        Given the stack-mode SKILL.md
        When reading the ordering section
        Then base-to-tip is explicitly specified
        """
        content = SKILL_FILE.read_text()
        assert "base-to-tip" in content

    @pytest.mark.unit
    def test_root_summary_step_present(self) -> None:
        """Scenario: Root summary step is documented

        Given the stack-mode SKILL.md
        When inspecting Step 4
        Then it posts a consolidated summary on the root PR
        """
        content = SKILL_FILE.read_text()
        assert "Step 4" in content
        assert "Post Stack Summary" in content

    @pytest.mark.unit
    def test_per_pr_gates_preserved(self) -> None:
        """Scenario: Per-PR gates are preserved

        Given the stack-mode SKILL.md
        When reading the Notes / Contract sections
        Then Gate 1 and Gate 2 are explicitly per-PR
        So stack mode does not weaken single-PR gates
        """
        content = SKILL_FILE.read_text()
        assert "Gate 1" in content
        assert "Gate 2" in content
        assert "per-PR" in content or "per PR" in content

    @pytest.mark.unit
    def test_single_pr_fallback_documented(self) -> None:
        """Scenario: Size-1 stack falls back gracefully

        Given the stack-mode SKILL.md
        When reading failure modes
        Then size-1 stacks trigger a single-PR fallback
        """
        content = SKILL_FILE.read_text()
        assert (
            "size 1" in content.lower()
            or "size of 1" in content.lower()
            or "only one PR" in content
        )


class TestCallerExpectations:
    """Feature: Callers know how to invoke stack-mode

    As /pr-review or /fix-pr
    I want to know what flags and behaviors to expose
    So that users get a consistent --stack experience
    """

    @pytest.mark.unit
    def test_stack_flag_documented(self) -> None:
        """Scenario: --stack flag is documented

        Given the stack-mode SKILL.md
        When reading the Contract section
        Then `--stack` is named as the caller flag
        """
        content = SKILL_FILE.read_text()
        assert "--stack" in content

    @pytest.mark.unit
    def test_base_override_documented(self) -> None:
        """Scenario: --base override is documented

        Given the stack-mode SKILL.md
        When reading the Contract section
        Then `--base <branch>` override is specified
        """
        content = SKILL_FILE.read_text()
        assert "--base" in content

    @pytest.mark.unit
    def test_both_commands_named_as_consumers(self) -> None:
        """Scenario: Both consumer commands are named

        Given the stack-mode SKILL.md
        When reading the When to Use section
        Then /pr-review and /fix-pr are both named
        So the shared contract is explicitly declared
        """
        content = SKILL_FILE.read_text()
        assert "/pr-review" in content
        assert "/fix-pr" in content
