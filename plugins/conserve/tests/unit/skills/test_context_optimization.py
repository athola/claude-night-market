"""Tests for context-optimization skill business logic.

This module tests the MECW principles, context analysis, and optimization
functionality following TDD/BDD principles.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Constants for PLR2004 magic values
THREE = 3
FOUR = 4  # Also used for path traversal in TestSubagentCoordinationModuleContent
THIRTY_POINT_ZERO = 30.0
SIXTY = 60
EIGHTY = 80
NINETY_POINT_ZERO = 90.0
FIVE_HUNDRED_THOUSAND = 500000
FIVE_HUNDRED_FORTY_THOUSAND = 540000
ONE_MILLION = 1000000


class TestContextOptimizationSkill:
    """Feature: Context optimization implements MECW principles for efficient usage.

    As a context optimization workflow
    I want to analyze context usage and apply MECW principles
    So that resource utilization stays within optimal thresholds
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_mecw_assessment_analyzes_context_usage(self, mock_mecw_analyzer) -> None:
        """Scenario: MECW assessment analyzes context usage accurately.

        Given different context usage scenarios
        When performing MECW assessment
        Then it should classify context status correctly
        And provide appropriate recommendations.
        """
        # Arrange - values aligned with mock thresholds (30%, 50%, 70%) of 1M window
        test_scenarios = [
            {"context_tokens": 10000, "expected_status": "LOW"},  # 1% < 30%
            {"context_tokens": 400000, "expected_status": "OPTIMAL"},  # 40% (30-50%)
            {"context_tokens": 600000, "expected_status": "HIGH"},  # 60% (50-70%)
            {"context_tokens": 800000, "expected_status": "CRITICAL"},  # 80% >= 70%
        ]

        # Act & Assert
        for scenario in test_scenarios:
            analysis = mock_mecw_analyzer.analyze_context_usage(
                scenario["context_tokens"],
            )

            assert (
                analysis["utilization_percentage"]
                == (scenario["context_tokens"] / ONE_MILLION) * 100
            )
            assert analysis["status"] == scenario["expected_status"]

            # Check MECW compliance (50% rule)
            is_compliant = (
                scenario["context_tokens"] <= FIVE_HUNDRED_THOUSAND
            )  # 50% of 1M
            assert analysis["mecw_compliant"] == is_compliant

            # Verify recommendations exist
            assert len(analysis["recommended_actions"]) > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_validation_confirms_optimization_effectiveness(
        self, mock_mecw_analyzer
    ) -> None:
        """Scenario: Validation confirms optimization effectiveness.

        Given context optimization applied
        When validating results
        Then it should confirm improved context utilization
        And validate MECW compliance.
        """
        # Arrange
        before_optimization = mock_mecw_analyzer.analyze_context_usage(
            600000,
        )  # 60% utilization of 1M window
        after_optimization = mock_mecw_analyzer.analyze_context_usage(
            400000,
        )  # 40% utilization of 1M window

        # Act - calculate improvements
        improvement_percentage = (
            (
                before_optimization["utilization_percentage"]
                - after_optimization["utilization_percentage"]
            )
            / before_optimization["utilization_percentage"]
        ) * 100

        # Assert
        assert before_optimization["status"] == "HIGH"
        assert before_optimization["mecw_compliant"] is False

        assert after_optimization["status"] == "OPTIMAL"
        assert after_optimization["mecw_compliant"] is True

        assert improvement_percentage > THIRTY_POINT_ZERO  # Significant improvement

    @pytest.mark.unit
    def test_context_optimization_handles_large_contexts_efficiently(
        self,
        mock_claude_tools,
    ) -> None:
        """Scenario: Context optimization handles large contexts efficiently.

        Given very large context windows approaching limits
        When applying optimization
        Then it should process efficiently without timeouts
        And provide effective compression strategies.
        """
        # Arrange
        large_context_size = 900000  # 90% of 1M window
        mock_claude_tools["Bash"].return_value = str(large_context_size)

        # Act - simulate large context optimization
        current_context = int(mock_claude_tools["Bash"]("echo $CURRENT_CONTEXT_TOKENS"))
        window_size = ONE_MILLION
        utilization = (current_context / window_size) * 100

        # Determine optimization strategy
        if utilization > EIGHTY:
            strategy = "aggressive_compression"
            target_reduction = 0.4  # Reduce by 40%
        elif utilization > SIXTY:
            strategy = "moderate_compression"
            target_reduction = 0.2  # Reduce by 20%
        else:
            strategy = "light_optimization"
            target_reduction = 0.1  # Reduce by 10%

        # Calculate target context size
        target_tokens = int(current_context * (1 - target_reduction))

        # Assert
        assert current_context == large_context_size
        assert utilization == NINETY_POINT_ZERO
        assert strategy == "aggressive_compression"
        assert target_tokens == FIVE_HUNDRED_FORTY_THOUSAND  # 60% of 900K input
        # Verify mock was called once with the expected command
        mock_claude_tools["Bash"].assert_called_once_with(
            "echo $CURRENT_CONTEXT_TOKENS"
        )


class TestSubagentCoordinationModuleContent:
    """Feature: Subagent coordination module guides Claude's agent dispatch decisions.

    As a module interpreted by Claude Code for multi-agent orchestration
    I want version-gated features to be accurately documented
    So that Claude makes correct decisions about agent isolation and delegation.

    Level 2: Version references are internally consistent.
    Level 3: Delegation decision framework produces correct outcomes.
    """

    @pytest.fixture
    def module_path(self) -> Path:
        return (
            Path(__file__).parents[THREE]
            / "skills"
            / "context-optimization"
            / "modules"
            / "subagent-coordination.md"
        )

    @pytest.fixture
    def module_content(self, module_path: Path) -> str:
        return module_path.read_text()

    # --- Level 2: Version gate consistency ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_worktree_features_are_version_gated(self, module_content: str) -> None:
        """Given worktree isolation features in the module
        When Claude reads about worktree capabilities
        Then each capability must have a version gate so Claude doesn't
        recommend features unavailable in the user's version.
        """
        worktree_section_match = re.search(
            r"### Worktree Isolation.*?(?=###|\Z)", module_content, re.DOTALL
        )
        assert worktree_section_match, "Module must have a Worktree Isolation section"
        worktree_section = worktree_section_match.group()

        # Must contain version-gated entries
        version_refs = re.findall(r"\d+\.\d+\.\d+", worktree_section)
        min_version_refs = 2
        assert len(version_refs) >= min_version_refs, (
            f"Worktree section has {len(version_refs)} version refs, "
            f"need at least {min_version_refs} for proper version gating"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_version_refs_cross_reference_compatibility_docs(
        self, module_content: str
    ) -> None:
        """Given version references in the module
        Then each referenced version must exist in compatibility docs.

        This prevents Claude from citing nonexistent versions.
        Checks both main and 2025 archive compatibility files.
        """
        versions = set(re.findall(r"2\.1\.(\d+)", module_content))
        compat_dir = (
            Path(__file__).parents[FOUR] / "abstract" / "docs" / "compatibility"
        )
        # Combine all compatibility docs content
        compat_content = ""
        for compat_file in compat_dir.glob("compatibility-features*.md"):
            compat_content += compat_file.read_text()

        for minor in versions:
            version_str = f"2.1.{minor}"
            assert version_str in compat_content, (
                f"Module references {version_str} but it's not in any "
                "compatibility-features*.md file"
            )

    # --- Level 3: Delegation decision framework ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_delegation_framework_has_efficiency_threshold(
        self, module_content: str
    ) -> None:
        """Given the delegation decision framework
        When Claude decides whether to spawn a subagent
        Then the framework must include a minimum efficiency threshold
        to prevent wasteful delegation of simple tasks.
        """
        assert (
            "MIN_EFFICIENCY" in module_content or "efficiency" in module_content.lower()
        )
        assert "BASE_OVERHEAD" in module_content or "overhead" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_delegation_framework_has_pre_invocation_check(
        self, module_content: str
    ) -> None:
        """Given the delegation framework
        When Claude is about to spawn a subagent
        Then the framework must instruct a pre-invocation complexity check.

        Without this, Claude wastes ~8k tokens on subagent overhead for simple tasks.
        """
        assert "pre-invocation" in module_content.lower()
        # Must include explicit "do it directly" guidance for simple tasks
        assert "directly" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_worktree_config_sharing_documented(self, module_content: str) -> None:
        """Given worktree-isolated agents share configs since 2.1.63
        When Claude dispatches a worktree agent
        Then it should know configs and memory are inherited, not blank.

        Without this, Claude might add unnecessary config-copying steps.
        """
        assert "2.1.63" in module_content
        # Must mention what is shared
        content_lower = module_content.lower()
        assert "config" in content_lower or "settings" in content_lower
        assert "memory" in content_lower or "auto-memory" in content_lower
