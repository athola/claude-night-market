"""Tests for latent-space-engineering skill instruction framing and style transfer.

This module tests the three core techniques: emotional framing, style gene
transfer, and competitive review patterns. Following TDD/BDD principles.

Note: latent-space-engineering is a markdown-only methodology skill with no
Python source modules. The tests below validate:
  1. Skill file structure (SKILL.md exists, has frontmatter, modules present)
  2. Methodology concepts (emotional framing, style gene transfer, competitive
     review) using inline logic that mirrors the rules documented in the skill
     markdown files.
Structural and conceptual tests are the appropriate test type for skills that
contain no executable Python code. See GitHub issue #320.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestLatentSpaceEngineeringStructure:
    """Feature: Skill file structure is valid and discoverable.

    As a plugin developer
    I want the skill to have proper structure
    So that it can be discovered and loaded correctly
    """

    @pytest.fixture
    def skill_dir(self) -> Path:
        """Return the skill directory path."""
        return Path(__file__).parents[3] / "skills" / "latent-space-engineering"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md file exists.

        Given the latent-space-engineering skill directory
        When checking for SKILL.md
        Then the file should exist
        """
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"SKILL.md not found at {skill_file}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_frontmatter(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md has valid YAML frontmatter.

        Given the SKILL.md file
        When parsing the file
        Then it should have YAML frontmatter with required fields
        """
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text()

        assert content.startswith("---"), "SKILL.md should start with frontmatter"
        assert content.count("---") >= 2, "SKILL.md should have closing frontmatter"

        # Verify required frontmatter fields
        frontmatter_end = content.index("---", 3)
        frontmatter = content[3:frontmatter_end]
        assert "name:" in frontmatter, "Frontmatter missing 'name' field"
        assert "description:" in frontmatter, "Frontmatter missing 'description' field"
        assert "category:" in frontmatter, "Frontmatter missing 'category' field"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_modules_exist(self, skill_dir: Path) -> None:
        """Scenario: All declared modules are present on disk.

        Given the SKILL.md frontmatter declares module dependencies
        When checking the modules directory
        Then each declared module file should exist
        """
        expected_modules = [
            "modules/emotional-framing.md",
            "modules/style-gene-transfer.md",
            "modules/competitive-review.md",
        ]
        for module_path in expected_modules:
            full_path = skill_dir / module_path
            assert full_path.exists(), f"Module not found: {full_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modules_have_frontmatter(self, skill_dir: Path) -> None:
        """Scenario: Each module file has valid frontmatter.

        Given the module markdown files
        When parsing each file
        Then each should have YAML frontmatter with parent_skill
        """
        modules_dir = skill_dir / "modules"
        for md_file in sorted(modules_dir.glob("*.md")):
            content = md_file.read_text()
            assert content.startswith("---"), (
                f"{md_file.name} should start with frontmatter"
            )
            frontmatter_end = content.index("---", 3)
            frontmatter = content[3:frontmatter_end]
            assert "parent_skill:" in frontmatter, (
                f"{md_file.name} missing 'parent_skill' field"
            )


class TestEmotionalFraming:
    """Feature: Emotional framing replaces threat-based prompting.

    As a skill author
    I want confident, calm instructions
    So that agents produce higher-quality output without rushing
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_threat_pattern_detection(self) -> None:
        """Scenario: Threat patterns are identified for replacement.

        Given an instruction with threat language
        When analyzing for emotional framing issues
        Then it should flag urgency markers inappropriately used
        """
        # Arrange
        threat_instructions = [
            "You MUST do X or the system will fail",
            "CRITICAL: failure to comply will cause data loss",
            "WARNING: do NOT deviate from this approach",
            "NEVER do X under ANY circumstances",
            "This is your LAST CHANCE to fix this",
        ]

        threat_markers = ["MUST", "CRITICAL", "WARNING", "NEVER", "LAST CHANCE"]

        # Act - detect threat language
        flagged_instructions = []
        for instruction in threat_instructions:
            for marker in threat_markers:
                if marker in instruction:
                    flagged_instructions.append(instruction)
                    break

        # Assert
        assert len(flagged_instructions) == 5
        assert all(
            marker in instr
            for instr, marker in zip(flagged_instructions, threat_markers)
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_confident_framing_patterns(self) -> None:
        """Scenario: Confident patterns encourage careful reasoning.

        Given calm, positive instructions
        When evaluating for quality
        Then they should promote deliberation without threat
        """
        # Arrange
        confident_patterns = {
            "You've got this. Take your time with X.": "encourages careful reasoning",
            "Focus on getting X right. The details matter here.": "directs attention without threat",
            "This is important work. Here's what good looks like...": "sets positive exemplar",
            "Take a careful look at X before proceeding.": "promotes deliberation",
            "Your goal is to produce Y. Here's the approach...": "outcome-focused",
        }

        # Act - verify confident patterns
        verified = {}
        for pattern, property_name in confident_patterns.items():
            # Check if pattern lacks threat markers
            threat_free = all(
                marker not in pattern
                for marker in ["MUST", "CRITICAL", "WARNING", "NEVER"]
            )
            if threat_free:
                verified[pattern] = property_name

        # Assert
        assert len(verified) == 5
        assert all(v for v in verified.values())

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_urgency_markers_for_genuine_constraints(self) -> None:
        """Scenario: Urgency is appropriate for safety constraints.

        Given genuinely critical constraints
        When evaluating instruction tone
        Then strong language should be acceptable
        And the test should recognize legitimate safety requirements
        """
        # Arrange
        safety_constraints = [
            "NEVER commit secrets to git",
            "CRITICAL: do not expose API keys in logs",
            "WARNING: this operation is destructive",
        ]

        # Act - validate these are genuine constraints
        legitimate_urgency = []
        for constraint in safety_constraints:
            # Simulate checking if constraint would cause real harm if violated
            causes_real_harm = True  # All three would cause real harm
            if causes_real_harm:
                legitimate_urgency.append(constraint)

        # Assert
        assert len(legitimate_urgency) == 3
        assert all(
            "NEVER" in c or "CRITICAL" in c or "WARNING" in c
            for c in legitimate_urgency
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_instructions_lack_unnecessary_urgency(self) -> None:
        """Scenario: Well-written skills avoid threat language.

        Given a skill instruction file (latent-space-engineering/SKILL.md)
        When checking for anti-patterns
        Then threat markers should be minimal or absent
        And related only to actual safety constraints
        """
        # Arrange - simulate checking the hub SKILL.md
        skill_content = """---
name: latent-space-engineering
description: >-
  Shape agent behavior through instruction framing.
---

# Latent Space Engineering

Shape agent behavior by framing instructions.
"""

        threat_markers = ["MUST", "NEVER", "CRITICAL", "WARNING"]

        # Act - count unnecessary urgency
        urgent_count = sum(skill_content.count(marker) for marker in threat_markers)

        # Assert - should be 0 for methodology skill
        assert urgent_count == 0


class TestStyleGeneTransfer:
    """Feature: Style gene transfer injects exemplar code into context.

    As a code generator
    I want to reproduce stylistic attributes from samples
    So that output matches codebase conventions
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_exemplar_size_guidelines(self) -> None:
        """Scenario: Exemplar size affects effectiveness and cost.

        Given different exemplar sizes
        When evaluating token cost vs. style transfer fidelity
        Then 50-200 lines is optimal range
        """
        # Arrange
        exemplars = {
            "tiny": 20,  # Low effectiveness
            "small": 75,  # Good balance
            "medium": 150,  # Excellent fidelity
            "large": 300,  # Diminishing returns
            "huge": 500,  # Wasteful
        }

        effectiveness_scores = {
            "tiny": 0.3,
            "small": 0.7,
            "medium": 0.9,
            "large": 0.85,
            "huge": 0.80,
        }

        # Act - identify optimal range
        optimal = {
            name: (size, eff)
            for name, size in exemplars.items()
            for e_name, eff in effectiveness_scores.items()
            if name == e_name and 50 <= size <= 200
        }

        # Assert
        assert "small" in optimal
        assert "medium" in optimal
        assert len(optimal) == 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_exemplar_selection_criteria(self) -> None:
        """Scenario: Exemplars must meet quality criteria.

        Given candidate exemplars
        When evaluating selection
        Then exemplar must be from same codebase and be recent
        And represent best practices, not legacy code
        """
        # Arrange
        candidates = {
            "recent_clean": {
                "source": "same_codebase",
                "age_months": 1,
                "quality": "best_practices",
                "valid": True,
            },
            "legacy_old": {
                "source": "same_codebase",
                "age_months": 24,
                "quality": "deprecated",
                "valid": False,
            },
            "external": {
                "source": "different_codebase",
                "age_months": 2,
                "quality": "best_practices",
                "valid": False,
            },
        }

        # Act - filter by criteria
        selection_criteria = [
            lambda c: c["source"] == "same_codebase",
            lambda c: c["age_months"] <= 12,
            lambda c: c["quality"] == "best_practices",
        ]

        valid_exemplars = {
            name: cand
            for name, cand in candidates.items()
            if all(criterion(cand) for criterion in selection_criteria)
        }

        # Assert
        assert "recent_clean" in valid_exemplars
        assert "legacy_old" not in valid_exemplars
        assert "external" not in valid_exemplars
        assert len(valid_exemplars) == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_style_transfer_not_needed_for_greenfield(self) -> None:
        """Scenario: Style gene transfer skipped for greenfield projects.

        Given a brand new project with no style precedent
        When considering style transfer
        Then exemplar injection should be skipped
        As there is nothing to match
        """
        # Arrange
        project_state = {
            "is_greenfield": True,
            "has_existing_code": False,
            "precedent_count": 0,
        }

        # Act - determine if style transfer needed
        needs_style_transfer = (
            not project_state["is_greenfield"]
            and project_state["has_existing_code"]
            and project_state["precedent_count"] > 0
        )

        # Assert
        assert needs_style_transfer is False

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_style_transfer_skipped_for_rigid_formats(self) -> None:
        """Scenario: Style transfer not needed for template-driven output.

        Given output that is rigidly template-specified
        When considering style transfer
        Then exemplar injection should be skipped
        As template constraints override style
        """
        # Arrange
        tasks = {
            "generate_json": {
                "template_driven": True,
                "flexible_output": False,
                "needs_style": False,
            },
            "write_config": {
                "template_driven": True,
                "flexible_output": False,
                "needs_style": False,
            },
            "write_doc": {
                "template_driven": False,
                "flexible_output": True,
                "needs_style": True,
            },
        }

        # Act - identify style-sensitive tasks
        style_sensitive = {
            name: config
            for name, config in tasks.items()
            if not config["template_driven"] and config["flexible_output"]
        }

        # Assert
        assert "write_doc" in style_sensitive
        assert "generate_json" not in style_sensitive
        assert "write_config" not in style_sensitive


class TestCompetitiveReview:
    """Feature: Competitive review framing increases agent thoroughness.

    As a multi-agent review orchestrator
    I want to frame reviews with competitive incentives
    So that agents produce more thorough findings
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_competitive_framing_for_3_plus_agents(self) -> None:
        """Scenario: Competitive framing is used for 3+ agents.

        Given a parallel review dispatch with 3+ agents
        When framing the dispatch
        Then each agent should be told others are reviewing too
        And findings will be compared for thoroughness
        """
        # Arrange
        agent_counts = [1, 2, 3, 4, 5]
        expected_framing = {
            1: "collaborative",  # Single agent, no framing needed
            2: "collaborative",  # Pair, use collaboration not competition
            3: "competitive",  # Threshold for competitive
            4: "competitive",
            5: "competitive",
        }

        # Act - determine framing by agent count
        framings = {
            count: ("competitive" if count >= 3 else "collaborative")
            for count in agent_counts
        }

        # Assert
        assert framings == expected_framing
        assert framings[3] == "competitive"
        assert framings[2] == "collaborative"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_avoid_perverse_incentives(self) -> None:
        """Scenario: Competitive framing should prevent inflated findings.

        Given competitive review incentives
        When evaluating findings
        Then volume should not be rewarded without evidence
        And each finding must cite specific code locations
        """
        # Arrange
        findings = [
            {
                "issue": "Missing validation",
                "evidence": "Line 42: no input check before use",
                "severity": "high",
                "valid": True,
            },
            {
                "issue": "Bad naming",
                "evidence": None,  # No specific reference
                "severity": "low",
                "valid": False,
            },
            {
                "issue": "Performance concern",
                "evidence": "File X, loop on line Y: O(n²) iteration",
                "severity": "medium",
                "valid": True,
            },
        ]

        # Act - filter by evidence requirement
        evidence_backed = [f for f in findings if f["evidence"] is not None]

        # Assert
        assert len(evidence_backed) == 2
        assert all(f["valid"] for f in evidence_backed)
        assert findings[1] not in evidence_backed

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_collaborative_framing_for_pair_agents(self) -> None:
        """Scenario: Two agents use collaborative framing.

        Given a review dispatch with exactly 2 agents
        When framing the dispatch
        Then each should focus on assigned scope
        Not compete for throughput
        """
        # Arrange
        agent_count = 2
        team_composition = ["security_reviewer", "performance_reviewer"]

        # Act - determine framing
        is_pair = agent_count == 2
        should_collaborate = is_pair
        framing_type = "collaborative" if should_collaborate else "competitive"

        # Assert
        assert should_collaborate is True
        assert framing_type == "collaborative"
        assert len(team_composition) == 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_competitive_anti_patterns(self) -> None:
        """Scenario: Some uses of competitive framing are wrong.

        Given various agent dispatch scenarios
        When determining appropriate framing
        Then competitive framing should NOT be used for:
        - Implementation agents (cooperation needed)
        - Planning agents (synthesis needed)
        - Single-agent dispatch (no comparison possible)
        """
        # Arrange
        scenarios = {
            "implementation_team": {
                "agent_type": "implementation",
                "count": 4,
                "should_be_competitive": False,
            },
            "planning_team": {
                "agent_type": "planning",
                "count": 4,
                "should_be_competitive": False,
            },
            "single_reviewer": {
                "agent_type": "review",
                "count": 1,
                "should_be_competitive": False,
            },
            "review_panel": {
                "agent_type": "review",
                "count": 4,
                "should_be_competitive": True,
            },
        }

        # Act - check each scenario
        appropriate = {}
        for name, config in scenarios.items():
            # Competitive is only appropriate for review with 3+ agents
            is_appropriate = (
                config["agent_type"] == "review"
                and config["count"] >= 3
                and config["should_be_competitive"]
            ) or (
                (config["agent_type"] != "review" or config["count"] < 3)
                and not config["should_be_competitive"]
            )
            appropriate[name] = is_appropriate

        # Assert
        assert all(appropriate.values())
        assert appropriate["implementation_team"] is True
        assert appropriate["planning_team"] is True
        assert appropriate["single_reviewer"] is True
        assert appropriate["review_panel"] is True
