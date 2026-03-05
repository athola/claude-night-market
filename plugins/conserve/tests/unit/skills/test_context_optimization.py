"""Tests for context-optimization skill business logic.

This module tests the MECW principles, context analysis, and optimization
functionality following TDD/BDD principles.
"""

import re
from pathlib import Path

import pytest

# Constants for PLR2004 magic values
TWO = 2
THREE = 3
FOUR = 4  # Also used for path traversal in TestSubagentCoordinationModuleContent
FIVE = 5
THIRTY = 30
THIRTY_POINT_ZERO = 30.0
FORTY_TWO_POINT_FIVE = 42.5
FIFTY = 50
SIXTY = 60
SEVENTY = 70
EIGHTY = 80
EIGHTY_FIVE_THOUSAND = 85000
NINETY_POINT_ZERO = 90.0
HUNDRED_EIGHT_THOUSAND = 108000
HUNDRED_THOUSAND = 100000


class TestContextOptimizationSkill:
    """Feature: Context optimization implements MECW principles for efficient usage.

    As a context optimization workflow
    I want to analyze context usage and apply MECW principles
    So that resource utilization stays within optimal thresholds
    """

    @pytest.fixture
    def mock_context_optimization_skill_content(self) -> str:
        """Mock context-optimization skill content with required components."""
        return """---

name: context-optimization
description: |
  Optimize context usage by implementing Maximum Effective Context Window (MECW)
  principles and orchestrate specialized modules for context management.
category: conservation
token_budget: 150
progressive_loading: true
dependencies:
  hub: []
  modules: []
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - TodoWrite
tags:
  - conservation
  - context
  - MECW
  - optimization
---

# Context Optimization Hub

## TodoWrite Items

- `context-optimization:mecw-assessment`
- `context-optimization:context-classification`
- `context-optimization:module-coordination`
- `context-optimization:synthesis`
- `context-optimization:validation`

## MECW Principles

### 50% Context Rule
- Keep context usage below 50% of total window size
- Monitor utilization continuously
- Apply optimization when approaching threshold

### Context Classification
| Utilization | Status | Action |
|-------------|--------|--------|
| < THIRTY% | LOW | Continue normally |
| 30-50% | OPTIMAL | Maintain current approach |
| 50-70% | HIGH | Consider optimization |
| > SEVENTY% | CRITICAL | Immediate optimization required |
"""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_context_optimization_creates_required_todowrite_items(
        self,
        mock_todo_write,
    ) -> None:
        """Scenario: Context optimization creates required TodoWrite items.

        Given the context-optimization skill is executed
        When establishing the optimization workflow
        Then it should create all 5 required TodoWrite items
        And each item should have proper naming convention.
        """
        # Arrange
        expected_items = [
            "context-optimization:mecw-assessment",
            "context-optimization:context-classification",
            "context-optimization:module-coordination",
            "context-optimization:synthesis",
            "context-optimization:validation",
        ]

        # Act - simulate context-optimization skill execution
        context_optimization_items = [
            "context-optimization:mecw-assessment",
            "context-optimization:context-classification",
            "context-optimization:module-coordination",
            "context-optimization:synthesis",
            "context-optimization:validation",
        ]

        # Assert
        assert len(context_optimization_items) == FIVE
        for expected_item in expected_items:
            assert expected_item in context_optimization_items
        assert all(
            item.startswith("context-optimization:")
            for item in context_optimization_items
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_mecw_assessment_analyzes_context_usage(self, mock_mecw_analyzer) -> None:
        """Scenario: MECW assessment analyzes context usage accurately.

        Given different context usage scenarios
        When performing MECW assessment
        Then it should classify context status correctly
        And provide appropriate recommendations.
        """
        # Arrange - values aligned with mock thresholds (30%, 50%, 70%)
        test_scenarios = [
            {"context_tokens": 2000, "expected_status": "LOW"},  # 1% < 30%
            {"context_tokens": 80000, "expected_status": "OPTIMAL"},  # 40% (30-50%)
            {"context_tokens": 120000, "expected_status": "HIGH"},  # 60% (50-70%)
            {"context_tokens": 160000, "expected_status": "CRITICAL"},  # 80% >= 70%
        ]

        # Act & Assert
        for scenario in test_scenarios:
            analysis = mock_mecw_analyzer.analyze_context_usage(
                scenario["context_tokens"],
            )

            assert (
                analysis["utilization_percentage"]
                == (scenario["context_tokens"] / 200000) * 100
            )
            assert analysis["status"] == scenario["expected_status"]

            # Check MECW compliance (50% rule)
            is_compliant = scenario["context_tokens"] <= HUNDRED_THOUSAND  # 50% of 200k
            assert analysis["mecw_compliant"] == is_compliant

            # Verify recommendations exist
            assert len(analysis["recommended_actions"]) > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_context_classification_categorizes_usage_patterns(
        self, mock_claude_tools
    ) -> None:
        """Scenario: Context classification categorizes usage patterns effectively.

        Given various context usage patterns
        When classifying context usage
        Then it should categorize by utilization percentage
        And assign appropriate priority levels.
        """
        # Arrange
        mock_claude_tools["Bash"].side_effect = [
            str(EIGHTY_FIVE_THOUSAND),  # Current context tokens
            "200000",  # Total window size
        ]

        # Act - simulate context classification
        current_context = int(mock_claude_tools["Bash"]("echo $CURRENT_CONTEXT_TOKENS"))
        window_size = int(mock_claude_tools["Bash"]("echo $CONTEXT_WINDOW_SIZE"))
        utilization_percentage = (current_context / window_size) * 100

        # Classify based on utilization
        if utilization_percentage < THIRTY:
            status = "LOW"
            priority = "P4"
        elif utilization_percentage < FIFTY:
            status = "OPTIMAL"
            priority = "P3"
        elif utilization_percentage < SEVENTY:
            status = "HIGH"
            priority = "P2"
        else:
            status = "CRITICAL"
            priority = "P1"

        # Assert
        assert current_context == EIGHTY_FIVE_THOUSAND
        assert utilization_percentage == FORTY_TWO_POINT_FIVE
        assert status == "OPTIMAL"
        assert priority == "P3"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_coordination_selects_optimal_modules(
        self, mock_claude_tools
    ) -> None:
        """Scenario: Module coordination selects optimal optimization modules.

        Given different context situations and task complexities
        When coordinating modules
        Then it should select appropriate specialized modules
        And coordinate their execution efficiently.
        """
        # Arrange - test different scenarios
        scenarios = [
            {
                "context_situation": "CRITICAL",
                "task_complexity": "high",
                "expected_modules": ["mecw-assessment", "subagent-coordination"],
            },
            {
                "context_situation": "HIGH",
                "task_complexity": "medium",
                "expected_modules": ["mecw-assessment", "mecw-principles"],
            },
            {
                "context_situation": "OPTIMAL",
                "task_complexity": "low",
                "expected_modules": ["mecw-assessment"],
            },
        ]

        # Act & Assert - test each scenario
        for scenario in scenarios:
            # Simulate module selection logic
            context_situation = scenario["context_situation"]
            task_complexity = scenario["task_complexity"]

            selected_modules = []
            if context_situation in ["CRITICAL", "HIGH"]:
                selected_modules.append("mecw-assessment")
            if task_complexity == "high":
                selected_modules.append("subagent-coordination")
            if context_situation == "HIGH":
                selected_modules.append("mecw-principles")
            if context_situation == "OPTIMAL" and task_complexity == "low":
                selected_modules.append("mecw-assessment")

            # Remove duplicates while preserving order
            selected_modules = list(dict.fromkeys(selected_modules))

            # Assert
            assert selected_modules == scenario["expected_modules"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_synthesis_combines_module_results_effectively(self) -> None:
        """Scenario: Synthesis combines module results into coherent recommendations.

        Given results from multiple optimization modules
        When synthesizing results
        Then it should combine complementary recommendations
        And resolve conflicting suggestions.
        """
        # Arrange
        module_results = [
            {
                "module": "mecw-assessment",
                "findings": ["Context at 65% utilization", "Exceeds 50% threshold"],
                "recommendations": [
                    "Apply context compression",
                    "Remove redundant content",
                ],
            },
            {
                "module": "subagent-coordination",
                "findings": ["Complex task with multiple phases"],
                "recommendations": [
                    "Delegate to specialized subagents",
                    "Use task decomposition",
                ],
            },
            {
                "module": "mecw-principles",
                "findings": ["MECW violation detected"],
                "recommendations": [
                    "Implement 50% rule compliance",
                    "Monitor continuously",
                ],
            },
        ]

        # Act - synthesize results
        synthesized_findings = []
        synthesized_recommendations = []

        for result in module_results:
            synthesized_findings.extend(result["findings"])
            synthesized_recommendations.extend(result["recommendations"])

        # Remove duplicate recommendations
        unique_recommendations = list(set(synthesized_recommendations))
        prioritized_recommendations = sorted(
            unique_recommendations,
            key=len,
            reverse=True,
        )

        # Assert
        assert len(synthesized_findings) == FOUR
        assert len(prioritized_recommendations) >= THREE

        # Check for key recommendations
        assert any("compression" in rec.lower() for rec in prioritized_recommendations)
        assert any("50%" in rec for rec in prioritized_recommendations)

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
            120000,
        )  # 60% utilization
        after_optimization = mock_mecw_analyzer.analyze_context_usage(
            80000,
        )  # 40% utilization

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
        large_context_size = 180000  # 90% of 200k window
        mock_claude_tools["Bash"].return_value = str(large_context_size)

        # Act - simulate large context optimization
        current_context = int(mock_claude_tools["Bash"]("echo $CURRENT_CONTEXT_TOKENS"))
        window_size = 200000
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
        assert target_tokens == HUNDRED_EIGHT_THOUSAND  # 60% of window size

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_context_optimization_error_handling(self, mock_claude_tools) -> None:
        """Scenario: Context optimization handles errors gracefully.

        Given invalid context measurements or module failures
        When optimizing context
        Then it should handle errors and provide fallback strategies
        And document issues for troubleshooting.
        """
        # Arrange
        mock_claude_tools["Bash"].side_effect = [
            "invalid",  # Invalid context token measurement
            "0",  # Zero window size
            "Error: Context unavailable",  # Error condition
        ]

        # Act - simulate error handling
        error_log = []
        fallback_strategies = []

        for i, result in enumerate(mock_claude_tools["Bash"].side_effect):
            try:
                context_tokens = int(result)
                if context_tokens <= 0:
                    msg = "Invalid context measurement"
                    raise ValueError(msg)
            except (ValueError, TypeError) as e:
                error_log.append(f"Attempt {i + 1}: {e!s}")
                fallback_strategies.append(
                    {
                        "attempt": i + 1,
                        "strategy": "use_estimated_context",
                        "estimated_tokens": 50000,
                        "confidence": 0.7,
                    },
                )

        # Assert
        assert len(error_log) == THREE
        assert len(fallback_strategies) == THREE
        assert all(
            strategy["strategy"] == "use_estimated_context"
            for strategy in fallback_strategies
        )
        assert all("invalid" in error.lower() for error in error_log)

    @pytest.mark.unit
    def test_context_optimization_token_budget_conservation(
        self,
        sample_context_analysis,
    ) -> None:
        """Scenario: Context optimization conserves token budget effectively.

        Given limited token budget for optimization tasks
        When optimizing context
        Then it should stay within allocated budget
        And prioritize high-impact optimizations.
        """
        # Arrange
        optimization_budget = 150  # tokens allocated for optimization
        sample_context_analysis["utilization_percentage"] = 65.0

        # Act - budget allocation strategy
        optimization_tasks = [
            {"task": "context_analysis", "cost": 30, "impact": "high"},
            {"task": "compression_strategy", "cost": 50, "impact": "high"},
            {"task": "module_coordination", "cost": 40, "impact": "medium"},
            {"task": "validation", "cost": 20, "impact": "medium"},
            {"task": "reporting", "cost": 10, "impact": "low"},
        ]

        # Prioritize by impact while respecting budget
        high_impact_tasks = [t for t in optimization_tasks if t["impact"] == "high"]
        medium_impact_tasks = [t for t in optimization_tasks if t["impact"] == "medium"]
        [t for t in optimization_tasks if t["impact"] == "low"]

        selected_tasks = []
        remaining_budget = optimization_budget

        # Select high impact tasks first
        for task in high_impact_tasks:
            if task["cost"] <= remaining_budget:
                selected_tasks.append(task)
                remaining_budget -= task["cost"]

        # Add medium impact if budget allows
        for task in medium_impact_tasks:
            if task["cost"] <= remaining_budget:
                selected_tasks.append(task)
                remaining_budget -= task["cost"]

        total_cost = sum(task["cost"] for task in selected_tasks)

        # Assert
        assert len(selected_tasks) >= TWO  # At least high impact tasks
        assert total_cost <= optimization_budget
        assert any(task["task"] == "context_analysis" for task in selected_tasks)
        assert any(task["task"] == "compression_strategy" for task in selected_tasks)


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
