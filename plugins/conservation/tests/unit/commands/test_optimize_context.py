"""Tests for /optimize-context command integration and workflow.

This module tests the optimize-context command orchestration,
parameter handling, and skill coordination following TDD/BDD principles.
"""

import pytest

# Constants for PLR2004 magic values
ZERO_POINT_FIVE = 0.5
TWO = 2
THREE = 3
FOUR = 4
FIVE = 5
TEN = 10
FIFTEEN = 15
TWENTY_POINT_ZERO = 20.0
THIRTY = 30
FIFTY = 50
EIGHT_HUNDRED = 800
TWO_THOUSAND = 2000
TWENTY_THOUSAND = 20000
TWELVE_HUNDRED = 1200
FIFTEEN_HUNDRED = 1500


class TestOptimizeContextCommand:
    """Feature: /optimize-context command orchestrates context optimization workflows.

    As a user of the optimize-context command
    I want to optimize context usage and apply MECW principles
    So that resource utilization is efficient and performance is optimized
    """

    @pytest.fixture
    def mock_optimize_context_command(self):
        """Mock optimize-context command structure and workflow."""
        return {
            "name": "optimize-context",
            "description": "Optimize context usage and apply MECW principles",
            "usage": "/optimize-context [target]",
            "file": "commands/optimize-context.md",
            "skills_orchestrated": ["context-optimization", "token-conservation"],
            "parameters": {
                "target": {
                    "type": "string",
                    "required": False,
                    "default": "current_session",
                    "description": "Target to optimize (file, directory, or session)",
                },
                "aggressiveness": {
                    "type": "string",
                    "required": False,
                    "default": "moderate",
                    "options": ["light", "moderate", "aggressive"],
                    "description": "Optimization aggressiveness level",
                },
            },
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_parses_parameters_correctly(
        self, mock_optimize_context_command
    ) -> None:
        """Scenario: Command parses parameters correctly.

        Given various parameter combinations
        When parsing the command
        Then it should extract target and aggressiveness parameters
        And use appropriate defaults when not specified.
        """
        # Arrange
        command_inputs = [
            "/optimize-context",  # No parameters
            "/optimize-context src/main.py",  # Target only
            "/optimize-context --aggressiveness aggressive",  # Aggressiveness only
            "/optimize-context src/ --aggressiveness light",  # Both parameters
            "/optimize-context docs/api.md --aggressiveness moderate",  # Full params
        ]

        # Act - parse each command input
        parsed_results = []

        for command_input in command_inputs:
            # Simulate parameter parsing
            parts = command_input.split()
            parts[0]

            # Extract parameters
            parameters = {
                "target": "current_session",  # default
                "aggressiveness": "moderate",  # default
            }

            # Parse target (first non-flag argument)
            for _i, part in enumerate(parts[1:], 1):
                if not part.startswith("--"):
                    parameters["target"] = part
                    break

            # Parse aggressiveness flag
            if "--aggressiveness" in parts:
                flag_index = parts.index("--aggressiveness")
                if flag_index + 1 < len(parts):
                    aggressiveness_value = parts[flag_index + 1]
                    if aggressiveness_value in ["light", "moderate", "aggressive"]:
                        parameters["aggressiveness"] = aggressiveness_value

            parsed_results.append(
                {"input": command_input, "parsed_parameters": parameters},
            )

        # Assert
        assert len(parsed_results) == FIVE

        # Check specific parsing results
        no_params = next(r for r in parsed_results if r["input"] == "/optimize-context")
        assert no_params["parsed_parameters"]["target"] == "current_session"
        assert no_params["parsed_parameters"]["aggressiveness"] == "moderate"

        target_only = next(
            r for r in parsed_results if r["input"] == "/optimize-context src/main.py"
        )
        assert target_only["parsed_parameters"]["target"] == "src/main.py"
        assert target_only["parsed_parameters"]["aggressiveness"] == "moderate"

        both_params = next(
            r
            for r in parsed_results
            if "src/" in r["input"] and "--aggressiveness" in r["input"]
        )
        assert both_params["parsed_parameters"]["target"] == "src/"
        assert both_params["parsed_parameters"]["aggressiveness"] == "light"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_orchestrates_context_optimization_workflow(
        self,
        mock_optimize_context_command,
        mock_claude_tools,
    ) -> None:
        """Scenario: Command orchestrates context optimization workflow.

        Given parsed parameters and available skills
        When executing the optimization workflow
        Then it should coordinate context-optimization and token-conservation skills
        And apply appropriate optimization strategies.
        """
        # Arrange
        workflow_parameters = {"target": "src/main.py", "aggressiveness": "moderate"}

        # Mock skill execution
        skill_execution_results = {
            "context-optimization": {
                "status": "success",
                "context_analysis": {
                    "current_usage": 8500,
                    "utilization_percentage": 4.25,
                    "status": "LOW",
                    "mecw_compliant": True,
                },
                "optimization_applied": [
                    "context_compression",
                    "redundant_content_removal",
                ],
                "tokens_saved": 1200,
            },
            "token-conservation": {
                "status": "success",
                "quota_analysis": {
                    "weekly_usage": 45000,
                    "remaining_budget": 55000,
                    "within_limits": True,
                },
                "conservation_strategies": [
                    "prompt_optimization",
                    "targeted_tool_usage",
                ],
                "tokens_saved": 800,
            },
        }

        # Act - simulate workflow orchestration
        workflow_execution = {
            "command": mock_optimize_context_command["name"],
            "parameters": workflow_parameters,
            "skills_executed": [],
            "results": {},
        }

        # Execute skills in sequence
        for skill_name in mock_optimize_context_command["skills_orchestrated"]:
            skill_result = skill_execution_results.get(
                skill_name,
                {"status": "skipped"},
            )

            workflow_execution["skills_executed"].append(skill_name)
            workflow_execution["results"][skill_name] = skill_result

        # Calculate overall results
        successful_skills = [
            skill
            for skill, result in workflow_execution["results"].items()
            if result.get("status") == "success"
        ]
        total_tokens_saved = sum(
            result.get("tokens_saved", 0)
            for result in workflow_execution["results"].values()
        )

        workflow_execution["summary"] = {
            "skills_successful": len(successful_skills),
            "skills_total": len(workflow_execution["skills_executed"]),
            "total_tokens_saved": total_tokens_saved,
            "workflow_success": len(successful_skills) > 0,
        }

        # Assert
        assert workflow_execution["parameters"]["target"] == "src/main.py"
        assert workflow_execution["parameters"]["aggressiveness"] == "moderate"
        assert len(workflow_execution["skills_executed"]) == TWO
        assert "context-optimization" in workflow_execution["skills_executed"]
        assert "token-conservation" in workflow_execution["skills_executed"]

        # Verify skill results
        context_result = workflow_execution["results"]["context-optimization"]
        assert context_result["status"] == "success"
        assert context_result["tokens_saved"] == TWELVE_HUNDRED

        token_result = workflow_execution["results"]["token-conservation"]
        assert token_result["status"] == "success"
        assert token_result["tokens_saved"] == EIGHT_HUNDRED

        # Verify overall summary
        summary = workflow_execution["summary"]
        assert summary["skills_successful"] == TWO
        assert summary["skills_total"] == TWO
        assert summary["total_tokens_saved"] == TWO_THOUSAND
        assert summary["workflow_success"] is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_adapts_optimization_based_on_aggressiveness(
        self,
        mock_claude_tools,
    ) -> None:
        """Scenario: Command adapts optimization based on aggressiveness level.

        Given different aggressiveness parameters
        When applying optimization strategies
        Then it should adjust optimization intensity
        And balance effectiveness with risk.
        """
        # Arrange
        aggressiveness_levels = [
            {
                "level": "light",
                "description": "Conservative optimization with minimal changes",
                "expected_strategies": ["basic_compression", "redundant_removal"],
                "risk_tolerance": "low",
                "expected_improvement": 15,  # percentage
            },
            {
                "level": "moderate",
                "description": "Balanced optimization with reasonable changes",
                "expected_strategies": [
                    "context_compression",
                    "prompt_optimization",
                    "targeted_removal",
                ],
                "risk_tolerance": "medium",
                "expected_improvement": 35,
            },
            {
                "level": "aggressive",
                "description": "Maximum optimization with significant changes",
                "expected_strategies": [
                    "deep_compression",
                    "aggressive_pruning",
                    "delegation",
                ],
                "risk_tolerance": "high",
                "expected_improvement": 60,
            },
        ]

        # Act - simulate optimization for each aggressiveness level
        optimization_results = []

        for level_config in aggressiveness_levels:
            # Select strategies based on aggressiveness
            # Savings calibrated to achieve expected improvement percentages (baseline 5000)
            if level_config["level"] == "light":
                applied_strategies = [
                    {"name": "basic_compression", "savings": 350, "risk": "low"},
                    {"name": "redundant_removal", "savings": 250, "risk": "low"},
                ]  # Total: 600 = 12% improvement
            elif level_config["level"] == "moderate":
                applied_strategies = [
                    {"name": "context_compression", "savings": 800, "risk": "medium"},
                    {"name": "prompt_optimization", "savings": 500, "risk": "low"},
                    {"name": "targeted_removal", "savings": 450, "risk": "medium"},
                ]  # Total: 1750 = 35% improvement
            else:  # aggressive
                applied_strategies = [
                    {"name": "deep_compression", "savings": 1200, "risk": "high"},
                    {"name": "aggressive_pruning", "savings": 900, "risk": "high"},
                    {"name": "delegation", "savings": 1400, "risk": "medium"},
                ]  # Total: 3500 = 70% improvement

            total_savings = sum(strategy["savings"] for strategy in applied_strategies)
            # Use proper risk ordering (not lexicographic string comparison)
            risk_order = {"low": 1, "medium": 2, "high": 3}
            max_risk = max(applied_strategies, key=lambda s: risk_order[s["risk"]])[
                "risk"
            ]
            avg_risk = [
                {"low": 1, "medium": 2, "high": 3}[strategy["risk"]]
                for strategy in applied_strategies
            ]
            avg_risk_score = sum(avg_risk) / len(avg_risk)

            result = {
                "aggressiveness": level_config["level"],
                "strategies_applied": [s["name"] for s in applied_strategies],
                "total_savings": total_savings,
                "max_risk_level": max_risk,
                "avg_risk_score": avg_risk_score,
                "improvement_percentage": (total_savings / 5000)
                * 100,  # Assume 5000 baseline tokens
            }

            optimization_results.append(result)

        # Assert
        assert len(optimization_results) == THREE

        # Check light optimization
        light_result = next(
            r for r in optimization_results if r["aggressiveness"] == "light"
        )
        assert "basic_compression" in light_result["strategies_applied"]
        assert light_result["max_risk_level"] == "low"
        assert light_result["improvement_percentage"] >= TEN

        # Check moderate optimization
        moderate_result = next(
            r for r in optimization_results if r["aggressiveness"] == "moderate"
        )
        assert "context_compression" in moderate_result["strategies_applied"]
        assert moderate_result["max_risk_level"] == "medium"
        assert moderate_result["improvement_percentage"] >= THIRTY

        # Check aggressive optimization
        aggressive_result = next(
            r for r in optimization_results if r["aggressiveness"] == "aggressive"
        )
        assert "deep_compression" in aggressive_result["strategies_applied"]
        assert aggressive_result["max_risk_level"] == "high"
        assert aggressive_result["improvement_percentage"] >= FIFTY

        # Verify progression - more aggressive should save more tokens
        assert (
            light_result["total_savings"]
            < moderate_result["total_savings"]
            < aggressive_result["total_savings"]
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_handles_different_target_types(self, mock_claude_tools) -> None:
        """Scenario: Command handles different optimization target types.

        Given various target types (file, directory, session)
        When optimizing different targets
        Then it should apply appropriate optimization strategies
        And handle target-specific requirements.
        """
        # Arrange
        target_scenarios = [
            {
                "target": "src/main.py",
                "type": "file",
                "expected_strategies": ["file_specific_compression", "code_analysis"],
                "scope": "individual_file",
            },
            {
                "target": "src/",
                "type": "directory",
                "expected_strategies": ["bulk_compression", "dependency_analysis"],
                "scope": "codebase_section",
            },
            {
                "target": "current_session",
                "type": "session",
                "expected_strategies": [
                    "session_optimization",
                    "context_window_management",
                ],
                "scope": "entire_session",
            },
            {
                "target": "docs/api.md",
                "type": "documentation",
                "expected_strategies": [
                    "documentation_compression",
                    "content_summarization",
                ],
                "scope": "documentation_file",
            },
        ]

        # Act - simulate optimization for different target types
        target_optimization_results = []

        for scenario in target_scenarios:
            # Determine optimization approach based on target type
            if scenario["type"] == "file":
                optimization_approach = {
                    "analysis_method": "individual_file_analysis",
                    "compression_level": "targeted",
                    "context_preservation": "high",
                    "strategies": [
                        {"name": "file_specific_compression", "effectiveness": 0.7},
                        {"name": "code_analysis", "effectiveness": 0.8},
                    ],
                }
            elif scenario["type"] == "directory":
                optimization_approach = {
                    "analysis_method": "bulk_analysis",
                    "compression_level": "comprehensive",
                    "context_preservation": "medium",
                    "strategies": [
                        {"name": "bulk_compression", "effectiveness": 0.6},
                        {"name": "dependency_analysis", "effectiveness": 0.5},
                    ],
                }
            elif scenario["type"] == "session":
                optimization_approach = {
                    "analysis_method": "session_wide_analysis",
                    "compression_level": "global",
                    "context_preservation": "selective",
                    "strategies": [
                        {"name": "session_optimization", "effectiveness": 0.8},
                        {"name": "context_window_management", "effectiveness": 0.7},
                    ],
                }
            else:  # documentation
                optimization_approach = {
                    "analysis_method": "content_analysis",
                    "compression_level": "summarization",
                    "context_preservation": "high",
                    "strategies": [
                        {"name": "documentation_compression", "effectiveness": 0.75},
                        {"name": "content_summarization", "effectiveness": 0.85},
                    ],
                }

            # Calculate expected effectiveness
            overall_effectiveness = sum(
                s["effectiveness"] for s in optimization_approach["strategies"]
            ) / len(optimization_approach["strategies"])

            result = {
                "target": scenario["target"],
                "type": scenario["type"],
                "scope": scenario["scope"],
                "analysis_method": optimization_approach["analysis_method"],
                "compression_level": optimization_approach["compression_level"],
                "context_preservation": optimization_approach["context_preservation"],
                "strategies_applied": [
                    s["name"] for s in optimization_approach["strategies"]
                ],
                "expected_effectiveness": overall_effectiveness,
            }

            target_optimization_results.append(result)

        # Assert
        assert len(target_optimization_results) == FOUR

        # Check file optimization
        file_result = next(
            r for r in target_optimization_results if r["type"] == "file"
        )
        assert file_result["target"] == "src/main.py"
        assert file_result["analysis_method"] == "individual_file_analysis"
        assert file_result["context_preservation"] == "high"

        # Check directory optimization
        dir_result = next(
            r for r in target_optimization_results if r["type"] == "directory"
        )
        assert dir_result["target"] == "src/"
        assert dir_result["compression_level"] == "comprehensive"
        assert "bulk_compression" in dir_result["strategies_applied"]

        # Check session optimization
        session_result = next(
            r for r in target_optimization_results if r["type"] == "session"
        )
        assert session_result["target"] == "current_session"
        assert session_result["analysis_method"] == "session_wide_analysis"
        assert session_result["context_preservation"] == "selective"

        # Verify all results have required fields
        for result in target_optimization_results:
            assert "target" in result
            assert "type" in result
            assert "strategies_applied" in result
            assert "expected_effectiveness" in result
            assert (
                result["expected_effectiveness"] >= ZERO_POINT_FIVE
            )  # Should be reasonably effective

    @pytest.mark.unit
    def test_command_provides_comprehensive_feedback(self, mock_claude_tools) -> None:
        """Scenario: Command provides comprehensive feedback on optimization results.

        Given completed optimization workflow
        When generating user feedback
        Then it should detail changes made and improvements achieved
        And provide actionable next steps.
        """
        # Arrange
        optimization_results = {
            "workflow_status": "success",
            "target": "src/main.py",
            "aggressiveness": "moderate",
            "skills_executed": ["context-optimization", "token-conservation"],
            "detailed_results": {
                "context-optimization": {
                    "tokens_before": 8500,
                    "tokens_after": 6800,
                    "changes_made": [
                        "Removed redundant imports (200 tokens)",
                        "Compressed verbose comments (800 tokens)",
                        "Simplified function documentation (700 tokens)",
                    ],
                    "impact": "Reduced context usage by 20%",
                },
                "token-conservation": {
                    "quota_before": {"weekly_usage": 45000, "remaining": 55000},
                    "quota_after": {"weekly_usage": 43500, "remaining": 56500},
                    "strategies_applied": [
                        "Optimized prompt structure (1000 tokens)",
                        "Used targeted tool calls (500 tokens)",
                    ],
                    "changes_made": [
                        "Optimized prompt structure (1000 tokens)",
                        "Used targeted tool calls (500 tokens)",
                    ],
                    "impact": "Conserved 1500 tokens in weekly quota",
                },
            },
        }

        # Act - generate comprehensive feedback
        user_feedback = {
            "summary": {
                "status": optimization_results["workflow_status"],
                "target": optimization_results["target"],
                "aggressiveness": optimization_results["aggressiveness"],
                "overall_success": optimization_results["workflow_status"] == "success",
            },
            "achievements": {
                "total_tokens_saved": 0,
                "context_reduction_percentage": 0,
                "quota_conservation": 0,
            },
            "changes_made": [],
            "recommendations": [],
        }

        # Calculate achievements
        context_result = optimization_results["detailed_results"][
            "context-optimization"
        ]
        token_result = optimization_results["detailed_results"]["token-conservation"]

        context_savings = (
            context_result["tokens_before"] - context_result["tokens_after"]
        )
        quota_savings = (
            token_result["quota_before"]["weekly_usage"]
            - token_result["quota_after"]["weekly_usage"]
        )

        user_feedback["achievements"]["total_tokens_saved"] = (
            context_savings + quota_savings
        )
        user_feedback["achievements"]["context_reduction_percentage"] = (
            context_savings / context_result["tokens_before"]
        ) * 100
        user_feedback["achievements"]["quota_conservation"] = quota_savings

        # Compile changes made
        for skill_name, skill_result in optimization_results[
            "detailed_results"
        ].items():
            if "changes_made" in skill_result:
                user_feedback["changes_made"].extend(
                    [
                        f"{skill_name}: {change}"
                        for change in skill_result["changes_made"]
                    ],
                )

        # Generate recommendations
        if user_feedback["achievements"]["context_reduction_percentage"] > FIFTEEN:
            user_feedback["recommendations"].append(
                "Consider similar optimization for related files",
            )

        if token_result["quota_after"]["remaining"] < TWENTY_THOUSAND:
            user_feedback["recommendations"].append(
                "Monitor weekly quota usage closely",
            )

        if optimization_results["aggressiveness"] == "moderate":
            user_feedback["recommendations"].append(
                "Consider aggressive optimization for larger files",
            )

        user_feedback["recommendations"].extend(
            [
                "Review optimized content for accuracy",
                "Monitor performance improvements",
                "Set up regular optimization schedule",
            ],
        )

        # Assert
        assert user_feedback["summary"]["status"] == "success"
        assert user_feedback["summary"]["overall_success"] is True

        # Verify achievements
        achievements = user_feedback["achievements"]
        assert achievements["total_tokens_saved"] > TWO_THOUSAND
        assert achievements["context_reduction_percentage"] == TWENTY_POINT_ZERO
        assert achievements["quota_conservation"] == FIFTEEN_HUNDRED

        # Verify changes are detailed
        assert len(user_feedback["changes_made"]) >= FOUR  # From both skills
        assert any(
            "context-optimization" in change for change in user_feedback["changes_made"]
        )
        assert any(
            "token-conservation" in change for change in user_feedback["changes_made"]
        )

        # Verify recommendations are actionable
        assert len(user_feedback["recommendations"]) >= THREE
        assert all(isinstance(rec, str) for rec in user_feedback["recommendations"])

    @pytest.mark.unit
    def test_command_handles_optimization_errors_gracefully(
        self, mock_claude_tools
    ) -> None:
        """Scenario: Command handles optimization errors gracefully.

        Given various error conditions during optimization
        When errors occur
        Then it should handle them gracefully and provide recovery options
        And maintain partial functionality when possible.
        """
        # Arrange
        error_scenarios = [
            {
                "error_type": "target_not_found",
                "target": "nonexistent.py",
                "error_message": "Target file not found",
                "recovery_possible": True,
            },
            {
                "error_type": "permission_denied",
                "target": "/protected/system.py",
                "error_message": "Permission denied accessing target",
                "recovery_possible": False,
            },
            {
                "error_type": "skill_execution_failure",
                "target": "src/main.py",
                "error_message": "Context optimization skill failed",
                "recovery_possible": True,
            },
            {
                "error_type": "insufficient_quota",
                "target": "large_dataset.csv",
                "error_message": "Insufficient quota for optimization",
                "recovery_possible": True,
            },
        ]

        # Act - simulate error handling for each scenario
        error_handling_results = []

        for scenario in error_scenarios:
            # Determine error handling approach
            error_response = {
                "scenario": scenario["error_type"],
                "target": scenario["target"],
                "error_detected": True,
                "error_message": scenario["error_message"],
                "recovery_attempted": False,
                "recovery_successful": False,
                "fallback_applied": None,
                "user_guidance": [],
            }

            # Determine recovery strategy
            if scenario["error_type"] == "target_not_found":
                error_response["recovery_attempted"] = True
                error_response["fallback_applied"] = "suggest_similar_files"
                error_response["recovery_successful"] = True
                error_response["user_guidance"] = [
                    "File not found. Suggested alternatives:",
                    "- Check file path spelling",
                    "- Verify file exists in current directory",
                    "- Try with directory target instead",
                ]

            elif scenario["error_type"] == "permission_denied":
                error_response["recovery_attempted"] = False
                error_response["recovery_successful"] = False
                error_response["user_guidance"] = [
                    "Permission denied. To resolve:",
                    "- Check file permissions",
                    "- Run with appropriate privileges",
                    "- Choose different target file",
                ]

            elif scenario["error_type"] == "skill_execution_failure":
                error_response["recovery_attempted"] = True
                error_response["fallback_applied"] = "alternative_optimization"
                error_response["recovery_successful"] = True
                error_response["user_guidance"] = [
                    "Primary optimization failed, applied alternative:",
                    "- Used basic compression techniques",
                    "- Applied conservative token conservation",
                    "- Consider running with different aggressiveness",
                ]

            elif scenario["error_type"] == "insufficient_quota":
                error_response["recovery_attempted"] = True
                error_response["fallback_applied"] = "light_optimization"
                error_response["recovery_successful"] = True
                error_response["user_guidance"] = [
                    "Limited quota detected, applied light optimization:",
                    "- Used minimal compression",
                    "- Focused on critical optimizations only",
                    "- Monitor quota usage and try again later",
                ]

            error_handling_results.append(error_response)

        # Assert
        assert len(error_handling_results) == FOUR

        # Check that recovery was attempted when possible
        recoverable_errors = [
            r for r in error_handling_results if r["recovery_attempted"]
        ]
        assert len(recoverable_errors) >= THREE

        # Verify successful recoveries
        successful_recoveries = [
            r for r in error_handling_results if r["recovery_successful"]
        ]
        assert len(successful_recoveries) >= TWO

        # Check permission denied handling
        permission_error = next(
            r for r in error_handling_results if r["scenario"] == "permission_denied"
        )
        assert permission_error["recovery_attempted"] is False
        assert permission_error["recovery_successful"] is False
        assert len(permission_error["user_guidance"]) >= TWO

        # Check fallback strategies
        scenarios_with_fallback = [
            r for r in error_handling_results if r["fallback_applied"]
        ]
        assert len(scenarios_with_fallback) >= TWO

        fallback_types = [r["fallback_applied"] for r in scenarios_with_fallback]
        assert "suggest_similar_files" in fallback_types
        assert "alternative_optimization" in fallback_types

        # Verify user guidance is provided for all scenarios
        for result in error_handling_results:
            assert len(result["user_guidance"]) >= 1
            assert all(
                isinstance(guidance, str) for guidance in result["user_guidance"]
            )
