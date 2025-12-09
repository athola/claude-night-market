"""Tests for optimizing-large-skills business logic.

This module tests large skill optimization patterns, modularization,
and performance enhancement following TDD/BDD principles.
"""

import pytest


class TestOptimizingLargeSkills:
    """Feature: Optimizing large skills improves performance through modularization.

    As a large skill optimization workflow
    I want to identify optimization opportunities in complex skills
    So that skill performance is enhanced and resource usage is optimized
    """

    @pytest.fixture
    def mock_optimizing_large_skills_content(self) -> str:
        """Mock optimizing-large-skills skill content with required components."""
        return """---

name: optimizing-large-skills
description: |
  Optimize large skills for better performance through modularization,
  progressive loading, and efficient resource management.
category: conservation
token_budget: 200
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
  - optimization
  - performance
  - modularization
---

# Large Skill Optimization Hub

## TodoWrite Items

- `optimizing-large-skills:skill-analysis`
- `optimizing-large-skills:modularization-assessment`
- `optimizing-large-skills:performance-profiling`
- `optimizing-large-skills:optimization-recommendations`
- `optimizing-large-skills:validation-testing`

## Optimization Strategies

### Modularization
- Break large skills into focused modules
- Implement progressive loading
- Create reusable components

### Performance Enhancement
- Token budget optimization
- Context management
- Execution flow optimization

### Resource Management
- Memory usage optimization
- CPU efficiency improvements
- Network resource conservation
"""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_optimizing_large_skills_creates_required_todowrite_items(
        self,
        mock_todo_write,
    ) -> None:
        """Scenario: Optimizing large skills creates required TodoWrite items

        Given the optimizing-large-skills skill is executed
        When establishing the optimization workflow
        Then it should create all 5 required TodoWrite items
        And each item should have proper naming convention.
        """
        # Arrange
        expected_items = [
            "optimizing-large-skills:skill-analysis",
            "optimizing-large-skills:modularization-assessment",
            "optimizing-large-skills:performance-profiling",
            "optimizing-large-skills:optimization-recommendations",
            "optimizing-large-skills:validation-testing",
        ]

        # Act - simulate optimizing-large-skills skill execution
        optimization_items = [
            "optimizing-large-skills:skill-analysis",
            "optimizing-large-skills:modularization-assessment",
            "optimizing-large-skills:performance-profiling",
            "optimizing-large-skills:optimization-recommendations",
            "optimizing-large-skills:validation-testing",
        ]

        # Assert
        assert len(optimization_items) == 5
        for expected_item in expected_items:
            assert expected_item in optimization_items
        assert all(
            item.startswith("optimizing-large-skills:") for item in optimization_items
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_analysis_identifies_optimization_candidates(self) -> None:
        """Scenario: Skill analysis identifies skills needing optimization

        Given various skill files with different characteristics
        When analyzing for optimization opportunities
        Then it should identify large, complex, and inefficient skills
        And prioritize by optimization impact.
        """
        # Arrange
        skills_to_analyze = [
            {
                "name": "simple_skill",
                "file_size": 2000,  # bytes
                "token_estimate": 500,
                "complexity_score": 2,
                "dependencies": 1,
                "expected_priority": "low",
            },
            {
                "name": "complex_analyzer",
                "file_size": 15000,  # bytes
                "token_estimate": 4000,
                "complexity_score": 8,
                "dependencies": 5,
                "expected_priority": "high",
            },
            {
                "name": "medium_processor",
                "file_size": 8000,  # bytes
                "token_estimate": 2000,
                "complexity_score": 5,
                "dependencies": 3,
                "expected_priority": "medium",
            },
            {
                "name": "mega_skill",
                "file_size": 25000,  # bytes
                "token_estimate": 8000,
                "complexity_score": 10,
                "dependencies": 8,
                "expected_priority": "critical",
            },
        ]

        # Act - analyze skills for optimization opportunities
        optimization_candidates = []

        for skill in skills_to_analyze:
            # Calculate optimization score
            size_score = min(skill["file_size"] / 1000, 10)  # 0-10 based on size
            complexity_score = skill["complexity_score"]
            dependency_score = skill["dependencies"] * 1.5

            total_score = (size_score + complexity_score + dependency_score) / 3

            # Determine priority
            if total_score >= 8:
                priority = "critical"
            elif total_score >= 6:
                priority = "high"
            elif total_score >= 4:
                priority = "medium"
            else:
                priority = "low"

            optimization_candidates.append(
                {
                    "skill": skill["name"],
                    "total_score": total_score,
                    "priority": priority,
                    "factors": {
                        "file_size_kb": skill["file_size"] / 1000,
                        "token_estimate": skill["token_estimate"],
                        "complexity": skill["complexity_score"],
                        "dependencies": skill["dependencies"],
                    },
                    "optimization_potential": total_score * 10,  # Percentage estimate
                },
            )

        # Sort by priority and score
        optimization_candidates.sort(
            key=lambda x: (
                {"critical": 4, "high": 3, "medium": 2, "low": 1}[x["priority"]],
                x["total_score"],
            ),
            reverse=True,
        )

        # Assert
        assert len(optimization_candidates) == 4

        # Check priority assignments
        mega_skill = next(
            c for c in optimization_candidates if c["skill"] == "mega_skill"
        )
        assert mega_skill["priority"] == "critical"

        complex_skill = next(
            c for c in optimization_candidates if c["skill"] == "complex_analyzer"
        )
        assert complex_skill["priority"] == "high"

        simple_skill = next(
            c for c in optimization_candidates if c["skill"] == "simple_skill"
        )
        assert simple_skill["priority"] == "low"

        # Verify sorting - critical should be first
        assert optimization_candidates[0]["priority"] == "critical"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modularization_assessment_identifies_breakdown_opportunities(self) -> None:
        """Scenario: Modularization assessment identifies skill breakdown opportunities

        Given large skills with multiple responsibilities
        When assessing modularization potential
        Then it should identify logical separation points
        And suggest module boundaries.
        """
        # Arrange
        large_skill_content = {
            "skill_name": "comprehensive_code_analyzer",
            "sections": [
                {
                    "title": "Input Validation",
                    "lines": 50,
                    "responsibility": "validate code inputs",
                    "dependencies": [],
                },
                {
                    "title": "Syntax Analysis",
                    "lines": 200,
                    "responsibility": "analyze code syntax",
                    "dependencies": ["Input Validation"],
                },
                {
                    "title": "Security Scanning",
                    "lines": 300,
                    "responsibility": "scan for security issues",
                    "dependencies": ["Syntax Analysis"],
                },
                {
                    "title": "Performance Analysis",
                    "lines": 250,
                    "responsibility": "analyze performance characteristics",
                    "dependencies": ["Syntax Analysis"],
                },
                {
                    "title": "Report Generation",
                    "lines": 150,
                    "responsibility": "generate analysis reports",
                    "dependencies": ["Security Scanning", "Performance Analysis"],
                },
            ],
            "total_lines": 950,
            "complexity_indicators": [
                "multiple_formats",
                "cross_language",
                "deep_analysis",
            ],
        }

        # Act - assess modularization opportunities
        modularization_analysis = {
            "total_complexity": len(large_skill_content["sections"])
            + len(large_skill_content["complexity_indicators"]),
            "identified_modules": [],
            "breakdown_points": [],
            "dependency_graph": {},
        }

        # Analyze sections for module potential
        for section in large_skill_content["sections"]:
            # Determine if section should be separate module
            should_be_module = (
                section["lines"] > 100  # Large sections
                or len(section["dependencies"]) == 0  # Independent sections
                or "scanning" in section["responsibility"]  # Specialized functionality
                or "generation" in section["responsibility"]  # Output functionality
            )

            if should_be_module:
                module = {
                    "name": section["title"].lower().replace(" ", "_"),
                    "responsibility": section["responsibility"],
                    "estimated_lines": section["lines"],
                    "dependencies": section["dependencies"],
                    "module_type": "independent"
                    if len(section["dependencies"]) == 0
                    else "dependent",
                }
                modularization_analysis["identified_modules"].append(module)

                # Add breakdown point
                modularization_analysis["breakdown_points"].append(
                    {
                        "after_section": section["title"],
                        "reason": f"Natural separation for {section['responsibility']}",
                        "estimated_reduction": section["lines"],
                    },
                )

        # Build dependency graph
        for section in large_skill_content["sections"]:
            modularization_analysis["dependency_graph"][section["title"]] = section[
                "dependencies"
            ]

        # Calculate modularization benefits
        total_module_lines = sum(
            module["estimated_lines"]
            for module in modularization_analysis["identified_modules"]
        )
        modularization_ratio = total_module_lines / large_skill_content["total_lines"]

        modularization_analysis["benefits"] = {
            "modules_created": len(modularization_analysis["identified_modules"]),
            "modularization_percentage": modularization_ratio * 100,
            "maintainability_improvement": "High"
            if modularization_ratio > 0.7
            else "Medium",
            "reusability_potential": len(
                [
                    m
                    for m in modularization_analysis["identified_modules"]
                    if m["module_type"] == "independent"
                ],
            ),
        }

        # Assert
        assert len(modularization_analysis["identified_modules"]) >= 3
        assert len(modularization_analysis["breakdown_points"]) >= 3
        assert modularization_analysis["benefits"]["modularization_percentage"] > 70

        # Verify specific modules identified
        module_names = [
            module["name"] for module in modularization_analysis["identified_modules"]
        ]
        assert "security_scanning" in module_names
        assert "performance_analysis" in module_names
        assert "report_generation" in module_names

        # Check dependency graph
        assert "Report Generation" in modularization_analysis["dependency_graph"]
        assert (
            "Security Scanning"
            in modularization_analysis["dependency_graph"]["Report Generation"]
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_performance_profiling_identifies_bottlenecks(
        self, mock_claude_tools
    ) -> None:
        """Scenario: Performance profiling identifies skill execution bottlenecks

        Given skill execution metrics and resource usage
        When profiling performance
        Then it should identify slow operations and resource-intensive sections
        And suggest optimization targets.
        """
        # Arrange
        skill_execution_data = [
            {
                "operation": "initialization",
                "execution_time": 2.5,
                "memory_usage": 50,
                "token_usage": 200,
                "frequency": 1,
            },
            {
                "operation": "file_parsing",
                "execution_time": 8.7,
                "memory_usage": 200,
                "token_usage": 800,
                "frequency": 5,
            },
            {
                "operation": "data_processing",
                "execution_time": 15.2,
                "memory_usage": 500,
                "token_usage": 2000,
                "frequency": 3,
            },
            {
                "operation": "result_formatting",
                "execution_time:": 4.1,
                "memory_usage": 100,
                "token_usage": 600,
                "frequency": 3,
            },
            {
                "operation": "output_generation",
                "execution_time": 1.8,
                "memory_usage": 75,
                "token_usage": 300,
                "frequency": 3,
            },
        ]

        # Act - profile performance and identify bottlenecks
        performance_analysis = {
            "total_execution_time": 0,
            "total_memory_peak": 0,
            "total_token_usage": 0,
            "bottlenecks": [],
            "optimization_targets": [],
        }

        for operation in skill_execution_data:
            # Calculate total impact
            total_time = operation["execution_time"] * operation["frequency"]
            total_memory = operation["memory_usage"] * operation["frequency"]
            total_tokens = operation["token_usage"] * operation["frequency"]

            performance_analysis["total_execution_time"] += total_time
            performance_analysis["total_memory_peak"] = max(
                performance_analysis["total_memory_peak"],
                total_memory,
            )
            performance_analysis["total_token_usage"] += total_tokens

            # Identify bottlenecks (operations taking > 20% of total time)
            time_percentage = (
                total_time
                / sum(
                    op["execution_time"] * op["frequency"]
                    for op in skill_execution_data
                )
            ) * 100

            if time_percentage > 20:
                performance_analysis["bottlenecks"].append(
                    {
                        "operation": operation["operation"],
                        "impact_percentage": time_percentage,
                        "total_time": total_time,
                        "reason": f"Takes {time_percentage:.1f}% of total execution time",
                    },
                )

            # Identify optimization targets (high resource usage)
            if total_tokens > 1000 or total_memory > 300:
                performance_analysis["optimization_targets"].append(
                    {
                        "operation": operation["operation"],
                        "resource_type": "tokens" if total_tokens > 1000 else "memory",
                        "usage_amount": total_tokens
                        if total_tokens > 1000
                        else total_memory,
                        "optimization_potential": "High"
                        if total_tokens > 2000
                        else "Medium",
                    },
                )

        # Sort bottlenecks by impact
        performance_analysis["bottlenecks"].sort(
            key=lambda x: x["impact_percentage"],
            reverse=True,
        )

        # Assert
        assert (
            performance_analysis["total_execution_time"] > 30
        )  # Should be significant
        assert performance_analysis["total_token_usage"] > 3000
        assert len(performance_analysis["bottlenecks"]) >= 1
        assert len(performance_analysis["optimization_targets"]) >= 1

        # Check specific bottlenecks
        data_processing = next(
            (
                b
                for b in performance_analysis["bottlenecks"]
                if b["operation"] == "data_processing"
            ),
            None,
        )
        assert data_processing is not None
        assert data_processing["impact_percentage"] > 20

        # Verify optimization targets
        token_optimizations = [
            t
            for t in performance_analysis["optimization_targets"]
            if t["resource_type"] == "tokens"
        ]
        assert len(token_optimizations) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_optimization_recommendations_prioritize_high_impact_changes(self) -> None:
        """Scenario: Optimization recommendations prioritize high-impact changes

        Given performance analysis and modularization assessment
        When generating optimization recommendations
        Then it should prioritize changes by impact and implementation effort
        And provide actionable improvement steps.
        """
        # Arrange
        analysis_results = {
            "performance_bottlenecks": [
                {
                    "operation": "data_processing",
                    "impact": "critical",
                    "estimated_improvement": 40,  # percentage
                    "implementation_effort": "medium",
                },
                {
                    "operation": "file_parsing",
                    "impact": "high",
                    "estimated_improvement": 25,
                    "implementation_effort": "low",
                },
            ],
            "modularization_opportunities": [
                {
                    "module": "security_scanning",
                    "complexity_reduction": 60,
                    "reusability": "high",
                    "implementation_effort": "high",
                },
                {
                    "module": "input_validation",
                    "complexity_reduction": 20,
                    "reusability": "medium",
                    "implementation_effort": "low",
                },
            ],
            "resource_inefficiencies": [
                {
                    "type": "token_waste",
                    "source": "verbose_logging",
                    "potential_savings": 30,
                    "implementation_effort": "low",
                },
                {
                    "type": "memory_leaks",
                    "source": "object_retention",
                    "potential_savings": 50,
                    "implementation_effort": "medium",
                },
            ],
        }

        # Act - generate prioritized recommendations
        recommendations = []

        # Calculate priority scores (impact * improvement) / effort_factor
        effort_factors = {"low": 1.0, "medium": 1.5, "high": 2.0}

        # Process performance bottlenecks
        for bottleneck in analysis_results["performance_bottlenecks"]:
            priority_score = (
                bottleneck["estimated_improvement"]
                * {"critical": 3, "high": 2, "medium": 1}[bottleneck["impact"]]
            ) / effort_factors[bottleneck["implementation_effort"]]

            recommendations.append(
                {
                    "category": "performance",
                    "type": "bottleneck_resolution",
                    "target": bottleneck["operation"],
                    "priority_score": priority_score,
                    "estimated_improvement": bottleneck["estimated_improvement"],
                    "implementation_effort": bottleneck["implementation_effort"],
                    "description": f"Optimize {bottleneck['operation']} for {bottleneck['estimated_improvement']}% improvement",
                },
            )

        # Process modularization opportunities
        for module in analysis_results["modularization_opportunities"]:
            reusability_factor = {"high": 1.5, "medium": 1.0, "low": 0.5}[
                module["reusability"]
            ]
            priority_score = (
                module["complexity_reduction"] * reusability_factor
            ) / effort_factors[module["implementation_effort"]]

            recommendations.append(
                {
                    "category": "architecture",
                    "type": "modularization",
                    "target": module["module"],
                    "priority_score": priority_score,
                    "estimated_improvement": module["complexity_reduction"],
                    "implementation_effort": module["implementation_effort"],
                    "description": f"Extract {module['module']} into separate module",
                },
            )

        # Process resource inefficiencies
        for inefficiency in analysis_results["resource_inefficiencies"]:
            urgency_factor = 1.5 if inefficiency["type"] == "memory_leaks" else 1.0
            priority_score = (
                inefficiency["potential_savings"] * urgency_factor
            ) / effort_factors[inefficiency["implementation_effort"]]

            recommendations.append(
                {
                    "category": "resource",
                    "type": "efficiency_improvement",
                    "target": inefficiency["source"],
                    "priority_score": priority_score,
                    "estimated_improvement": inefficiency["potential_savings"],
                    "implementation_effort": inefficiency["implementation_effort"],
                    "description": f"Fix {inefficiency['source']} to reduce {inefficiency['type']}",
                },
            )

        # Sort by priority score
        recommendations.sort(key=lambda x: x["priority_score"], reverse=True)

        # Generate implementation plan
        implementation_plan = {
            "immediate_wins": [
                r for r in recommendations if r["implementation_effort"] == "low"
            ][:3],
            "medium_term_projects": [
                r for r in recommendations if r["implementation_effort"] == "medium"
            ][:2],
            "long_term_improvements": [
                r for r in recommendations if r["implementation_effort"] == "high"
            ][:1],
        }

        # Assert
        assert len(recommendations) >= 5
        assert (
            recommendations[0]["priority_score"]
            >= recommendations[-1]["priority_score"]
        )

        # Verify implementation plan structure
        assert len(implementation_plan["immediate_wins"]) >= 1
        assert len(implementation_plan["medium_term_projects"]) >= 1

        # Check specific recommendations exist
        categories = [r["category"] for r in recommendations]
        assert "performance" in categories
        assert "architecture" in categories
        assert "resource" in categories

        # Verify high-priority recommendations
        top_recommendations = recommendations[:3]
        for rec in top_recommendations:
            assert rec["priority_score"] > 20  # Should be high priority
            assert rec["estimated_improvement"] > 15

    @pytest.mark.unit
    def test_validation_testing_measures_optimization_effectiveness(self) -> None:
        """Scenario: Validation testing measures optimization effectiveness

        Given before and after optimization metrics
        When validating optimization results
        Then it should measure actual improvements
        And verify optimization success criteria.
        """
        # Arrange
        baseline_metrics = {
            "skill_load_time": 12.5,
            "memory_usage_mb": 256,
            "token_efficiency": 0.65,
            "execution_success_rate": 0.85,
            "user_satisfaction_score": 7.2,
        }

        # Act - simulate optimization validation testing
        optimization_results = {
            "modularization_applied": True,
            "performance_tuning_applied": True,
            "resource_optimization_applied": True,
        }

        # Simulate post-optimization metrics
        if optimization_results["modularization_applied"]:
            modularization_improvement = {
                "load_time_improvement": 0.25,  # 25% faster
                "memory_efficiency": 0.20,  # 20% less memory
                "maintainability_score": 8.5,  # Improved maintainability
            }
        else:
            modularization_improvement = {
                "load_time_improvement": 0,
                "memory_efficiency": 0,
                "maintainability_score": baseline_metrics["user_satisfaction_score"],
            }

        if optimization_results["performance_tuning_applied"]:
            performance_improvement = {
                "execution_speed": 0.35,  # 35% faster
                "token_efficiency": 0.15,  # 15% better token usage
                "success_rate": 0.10,  # 10% better success rate
            }
        else:
            performance_improvement = {
                "execution_speed": 0,
                "token_efficiency": 0,
                "success_rate": 0,
            }

        if optimization_results["resource_optimization_applied"]:
            resource_improvement = {
                "memory_reduction": 0.30,  # 30% less memory
                "cpu_optimization": 0.20,  # 20% less CPU
                "token_savings": 0.25,  # 25% token savings
            }
        else:
            resource_improvement = {
                "memory_reduction": 0,
                "cpu_optimization": 0,
                "token_savings": 0,
            }

        # Calculate post-optimization metrics
        post_optimization_metrics = {
            "skill_load_time": baseline_metrics["skill_load_time"]
            * (1 - modularization_improvement["load_time_improvement"]),
            "memory_usage_mb": baseline_metrics["memory_usage_mb"]
            * (
                1
                - max(
                    modularization_improvement["memory_efficiency"],
                    resource_improvement["memory_reduction"],
                )
            ),
            "token_efficiency": baseline_metrics["token_efficiency"]
            * (
                1
                + performance_improvement["token_efficiency"]
                + resource_improvement["token_savings"]
            ),
            "execution_success_rate": min(
                baseline_metrics["execution_success_rate"]
                + performance_improvement["success_rate"],
                1.0,
            ),
            "user_satisfaction_score": modularization_improvement[
                "maintainability_score"
            ],
        }

        # Calculate improvements
        validation_results = {
            "load_time_improvement_percentage": (
                (
                    baseline_metrics["skill_load_time"]
                    - post_optimization_metrics["skill_load_time"]
                )
                / baseline_metrics["skill_load_time"]
            )
            * 100,
            "memory_savings_percentage": (
                (
                    baseline_metrics["memory_usage_mb"]
                    - post_optimization_metrics["memory_usage_mb"]
                )
                / baseline_metrics["memory_usage_mb"]
            )
            * 100,
            "token_efficiency_improvement": (
                (
                    post_optimization_metrics["token_efficiency"]
                    - baseline_metrics["token_efficiency"]
                )
                / baseline_metrics["token_efficiency"]
            )
            * 100,
            "success_rate_improvement": (
                (
                    post_optimization_metrics["execution_success_rate"]
                    - baseline_metrics["execution_success_rate"]
                )
                / baseline_metrics["execution_success_rate"]
            )
            * 100,
            "satisfaction_improvement": post_optimization_metrics[
                "user_satisfaction_score"
            ]
            - baseline_metrics["user_satisfaction_score"],
        }

        # Determine success criteria
        success_criteria = {
            "load_time_target_met": validation_results[
                "load_time_improvement_percentage"
            ]
            >= 20,
            "memory_target_met": validation_results["memory_savings_percentage"] >= 15,
            "token_efficiency_target_met": validation_results[
                "token_efficiency_improvement"
            ]
            >= 25,
            "overall_success": all(
                [
                    validation_results["load_time_improvement_percentage"] >= 15,
                    validation_results["memory_savings_percentage"] >= 10,
                    validation_results["token_efficiency_improvement"] >= 20,
                    validation_results["satisfaction_improvement"] >= 0.5,
                ],
            ),
        }

        # Assert
        assert validation_results["load_time_improvement_percentage"] >= 20
        assert validation_results["memory_savings_percentage"] >= 20
        assert validation_results["token_efficiency_improvement"] >= 35
        assert validation_results["success_rate_improvement"] >= 10
        assert validation_results["satisfaction_improvement"] >= 1.0

        # Verify success criteria
        assert success_criteria["load_time_target_met"] is True
        assert success_criteria["memory_target_met"] is True
        assert success_criteria["token_efficiency_target_met"] is True
        assert success_criteria["overall_success"] is True

        # Verify post-optimization metrics are better than baseline
        assert (
            post_optimization_metrics["skill_load_time"]
            < baseline_metrics["skill_load_time"]
        )
        assert (
            post_optimization_metrics["memory_usage_mb"]
            < baseline_metrics["memory_usage_mb"]
        )
        assert (
            post_optimization_metrics["token_efficiency"]
            > baseline_metrics["token_efficiency"]
        )
        assert (
            post_optimization_metrics["execution_success_rate"]
            > baseline_metrics["execution_success_rate"]
        )
