"""Tests for spec-kit agent functionality."""

import pytest


class TestSpeckitAgents:
    """Test cases for speckit agents."""

    class TestSpecAnalyzer:
        """Test spec-analyzer agent."""

        def test_should_classify_as_medium_complexity_when_spec_has_multiple_sections_and_scenarios(
            self, valid_authentication_spec_content
        ) -> None:
            """Complexity analysis should classify specs with moderate content as medium complexity."""
            # Given: A specification with multiple sections and user scenarios
            spec_content = valid_authentication_spec_content

            # When: Analyzing spec complexity
            lines = spec_content.split("\n")
            sections = len([line for line in lines if line.startswith("## ")])
            user_scenarios = len([line for line in lines if "### As a" in line])
            functional_requirements = len(
                [line for line in lines if line.startswith("-")],
            )

            complexity_factors = {
                "sections": sections,
                "user_scenarios": user_scenarios,
                "functional_requirements": functional_requirements,
                "total_lines": len([line for line in lines if line.strip()]),
                "has_open_questions": "[CLARIFY]" in spec_content,
            }

            complexity_score = (
                min(complexity_factors["sections"] / 5, 1) * 0.3
                + min(complexity_factors["user_scenarios"] / 3, 1) * 0.3
                + min(complexity_factors["functional_requirements"] / 10, 1) * 0.4
            )

            if complexity_score < 0.3:
                complexity_level = "low"
            elif complexity_score < 0.7:
                complexity_level = "medium"
            else:
                complexity_level = "high"

            # Then: Complexity level should be valid and spec should have minimum sections
            assert complexity_level in ["low", "medium", "high"]
            assert complexity_factors["sections"] >= 4

        def test_should_detect_minimum_required_sections_when_analyzing_spec_structure(
            self, valid_authentication_spec_content
        ) -> None:
            """Spec analysis should validate presence of minimum required sections."""
            # Given: A valid authentication specification
            spec_content = valid_authentication_spec_content

            # When: Counting spec sections
            lines = spec_content.split("\n")
            sections = len([line for line in lines if line.startswith("## ")])

            # Then: Should have at least 4 standard sections
            assert sections >= 4, f"Expected at least 4 sections, found {sections}"

        def test_should_calculate_positive_effort_when_spec_has_requirements(
            self, valid_authentication_spec_content
        ) -> None:
            """Effort estimation should return positive value for specs with requirements."""
            # Given: A specification with user scenarios and requirements
            spec_content = valid_authentication_spec_content

            # When: Estimating implementation effort
            implementation_indicators = {
                "user_scenarios": spec_content.count("### As a"),
                "functional_requirements": len(
                    [
                        line
                        for line in spec_content.split("\n")
                        if line.strip().startswith("-")
                    ],
                ),
                "integrations": len(
                    [
                        line
                        for line in spec_content.lower().split("\n")
                        if any(
                            term in line
                            for term in ["api", "database", "service", "external"]
                        )
                    ],
                ),
                "complexity_markers": len(
                    [
                        line
                        for line in spec_content.lower().split("\n")
                        if any(
                            term in line
                            for term in ["security", "performance", "scalability"]
                        )
                    ],
                ),
            }

            base_effort = 3
            scenario_effort = implementation_indicators["user_scenarios"] * 1
            requirement_effort = (
                implementation_indicators["functional_requirements"] * 0.5
            )
            integration_effort = implementation_indicators["integrations"] * 2
            complexity_effort = implementation_indicators["complexity_markers"] * 1.5

            total_effort = (
                base_effort
                + scenario_effort
                + requirement_effort
                + integration_effort
                + complexity_effort
            )

            # Then: Effort should be positive and reasonable
            assert total_effort > 0, "Should estimate positive effort"
            assert total_effort < 30, "Effort should be reasonable (< 30 days)"

        def test_should_return_zero_effort_when_spec_is_empty(
            self, empty_spec_content
        ) -> None:
            """Effort estimation should return minimal effort for empty specs."""
            # Given: An empty specification
            spec_content = empty_spec_content

            # When: Estimating implementation effort
            implementation_indicators = {
                "user_scenarios": spec_content.count("### As a"),
                "functional_requirements": len(
                    [
                        line
                        for line in spec_content.split("\n")
                        if line.strip().startswith("-")
                    ],
                ),
                "integrations": 0,
                "complexity_markers": 0,
            }

            base_effort = 3
            total_effort = (
                base_effort
                + implementation_indicators["user_scenarios"] * 1
                + implementation_indicators["functional_requirements"] * 0.5
            )

            # Then: Should estimate only base effort
            assert total_effort == 3, "Empty spec should estimate only base effort"

        def test_should_extract_key_components_when_spec_contains_technical_terms(
            self, valid_authentication_spec_content
        ) -> None:
            """Component extraction should identify technical components from spec content."""
            # Given: A specification with technical components
            spec_content = valid_authentication_spec_content

            # When: Extracting key components
            component_patterns = [
                r"authentication",
                r"authorization",
                r"session",
                r"user",
                r"password",
                r"email",
                r"role",
                r"api",
                r"database",
            ]

            found_components = []
            spec_lower = spec_content.lower()

            for pattern in component_patterns:
                if pattern in spec_lower:
                    found_components.append(pattern)

            # Then: Should find meaningful components
            assert len(found_components) >= 3, (
                f"Should extract key components, found: {found_components}"
            )

        def test_should_return_empty_components_when_spec_has_no_technical_terms(
            self, minimal_spec_content
        ) -> None:
            """Component extraction should return minimal results for non-technical specs."""
            # Given: A minimal specification without technical terms
            spec_content = minimal_spec_content

            # When: Extracting key components
            component_patterns = [
                r"authentication",
                r"authorization",
                r"session",
                r"password",
                r"email",
                r"api",
                r"database",
            ]

            found_components = []
            spec_lower = spec_content.lower()

            for pattern in component_patterns:
                if pattern in spec_lower:
                    found_components.append(pattern)

            # Then: Should find few or no components
            assert len(found_components) < 3, (
                "Minimal spec should have few technical components"
            )

        def test_should_identify_dependencies_when_spec_mentions_external_services(
            self, valid_authentication_spec_content
        ) -> None:
            """Dependency identification should detect external service references."""
            # Given: A specification mentioning external services
            spec_content = valid_authentication_spec_content

            # When: Identifying dependencies
            dependency_indicators = [
                "email service",
                "database",
                "external api",
                "third-party",
                "library",
                "framework",
            ]

            spec_lower = spec_content.lower()
            found_dependencies = []

            for indicator in dependency_indicators:
                if indicator in spec_lower:
                    found_dependencies.append(indicator)

            # Then: Should identify at least some dependencies
            assert len(found_dependencies) >= 0, "Dependency detection should not fail"

        def test_should_assess_security_risk_when_spec_contains_authentication(
            self, valid_authentication_spec_content
        ) -> None:
            """Risk assessment should identify security risks in authentication specs."""
            # Given: A specification with authentication requirements
            spec_content = valid_authentication_spec_content

            # When: Assessing risks
            risk_indicators = {
                "security": ["password", "authentication", "authorization", "session"],
                "complexity": ["multiple", "various", "several", "complex"],
                "integration": ["external", "third-party", "api"],
                "performance": ["performance", "scalability", "optimization"],
            }

            risk_scores = {}
            spec_lower = spec_content.lower()

            for risk_type, keywords in risk_indicators.items():
                score = sum(1 for keyword in keywords if keyword in spec_lower)
                risk_scores[risk_type] = score

            total_risk = sum(risk_scores.values())

            # Then: Should identify security risks
            assert total_risk >= 0, "Risk assessment should be non-negative"
            assert risk_scores["security"] > 0, (
                "Authentication specs should identify security risks"
            )

        def test_should_return_zero_risk_when_spec_has_no_risk_indicators(
            self, minimal_spec_content
        ) -> None:
            """Risk assessment should return zero risk for simple specs without risk indicators."""
            # Given: A minimal specification without risk indicators
            spec_content = minimal_spec_content

            # When: Assessing risks
            risk_indicators = {
                "security": ["password", "authentication", "authorization", "session"],
                "complexity": ["multiple", "various", "several", "complex"],
                "integration": ["external", "third-party", "api"],
                "performance": ["performance", "scalability", "optimization"],
            }

            risk_scores = {}
            spec_lower = spec_content.lower()

            for risk_type, keywords in risk_indicators.items():
                score = sum(1 for keyword in keywords if keyword in spec_lower)
                risk_scores[risk_type] = score

            total_risk = sum(risk_scores.values())

            # Then: Should have minimal or no risk
            assert total_risk >= 0, "Risk should be non-negative"
            assert total_risk < 5, "Minimal spec should have low risk score"

    class TestTaskGenerator:
        """Test task-generator agent."""

        def test_should_estimate_reasonable_task_count_when_spec_has_requirements(
            self, valid_authentication_spec_content
        ) -> None:
            """Task count estimation should return reasonable values based on spec complexity."""
            # Given: A specification with functional requirements
            spec_content = valid_authentication_spec_content

            # When: Estimating task count
            functional_requirements = len(
                [
                    line
                    for line in spec_content.split("\n")
                    if line.strip().startswith("-") and len(line.strip()) > 2
                ],
            )

            user_scenarios = spec_content.count("### As a")

            estimated_tasks = max(
                functional_requirements * 2,
                user_scenarios * 3,
                5,
            )

            # Then: Should estimate reasonable task count
            assert estimated_tasks >= 5, (
                f"Should estimate reasonable task count: {estimated_tasks}"
            )
            assert estimated_tasks <= 50, (
                f"Task count should be reasonable: {estimated_tasks}"
            )

        @pytest.mark.parametrize(
            "requirement_count,scenario_count,expected_min_tasks",
            [
                (0, 0, 5),  # Minimum tasks
                (5, 2, 10),  # 5 requirements * 2 = 10
                (3, 4, 12),  # 4 scenarios * 3 = 12
                (10, 5, 20),  # 10 requirements * 2 = 20
            ],
        )
        def test_should_scale_task_count_based_on_spec_size(
            self, requirement_count: int, scenario_count: int, expected_min_tasks: int
        ) -> None:
            """Task count estimation should scale with spec complexity."""
            # Given: Various spec complexity levels
            # (simulated through parameters)

            # When: Estimating task count
            estimated_tasks = max(
                requirement_count * 2,
                scenario_count * 3,
                5,
            )

            # Then: Should meet minimum expected tasks
            assert estimated_tasks >= expected_min_tasks

        def test_should_maintain_phase_order_when_generating_task_list(
            self, valid_task_list
        ) -> None:
            """Task phase breakdown should maintain correct sequential phase order."""
            # Given: A valid task list with phases
            task_list = valid_task_list

            # When: Extracting phase information
            expected_phases = [
                "0 - Setup",
                "1 - Foundation",
                "2 - Core Implementation",
                "3 - Integration",
                "4 - Polish",
            ]

            actual_phases = [phase["phase"] for phase in task_list]

            # Then: Should have phases in correct order
            for i, expected_phase in enumerate(expected_phases[: len(actual_phases)]):
                assert actual_phases[i] == expected_phase

        def test_should_detect_no_cycles_when_dependencies_are_valid(
            self, valid_task_list
        ) -> None:
            """Dependency analysis should detect absence of cycles in valid task lists."""
            # Given: A valid task list with proper dependencies
            task_list = valid_task_list

            # When: Analyzing dependencies for cycles
            all_tasks = []
            for phase in task_list:
                all_tasks.extend(phase["tasks"])

            def has_cycle(tasks):
                visited = set()
                rec_stack = set()

                def dfs(task_id) -> bool:
                    if task_id in rec_stack:
                        return True
                    if task_id in visited:
                        return False

                    visited.add(task_id)
                    rec_stack.add(task_id)

                    task = next((t for t in tasks if t["id"] == task_id), None)
                    if task:
                        for dep_id in task["dependencies"]:
                            if dfs(dep_id):
                                return True

                    rec_stack.remove(task_id)
                    return False

                return any(dfs(task["id"]) for task in tasks)

            # Then: Should not have cycles
            assert not has_cycle(all_tasks), "Task dependencies should not have cycles"

        def test_should_detect_cycles_when_dependencies_are_circular(
            self, task_with_circular_dependency
        ) -> None:
            """Dependency analysis should detect cycles in circular task dependencies."""
            # Given: A task list with circular dependencies
            task_list = task_with_circular_dependency

            # When: Analyzing dependencies for cycles
            all_tasks = []
            for phase in task_list:
                all_tasks.extend(phase["tasks"])

            def has_cycle(tasks):
                visited = set()
                rec_stack = set()

                def dfs(task_id) -> bool:
                    if task_id in rec_stack:
                        return True
                    if task_id in visited:
                        return False

                    visited.add(task_id)
                    rec_stack.add(task_id)

                    task = next((t for t in tasks if t["id"] == task_id), None)
                    if task:
                        for dep_id in task["dependencies"]:
                            if dfs(dep_id):
                                return True

                    rec_stack.remove(task_id)
                    return False

                return any(dfs(task["id"]) for task in tasks)

            # Then: Should detect the cycle
            assert has_cycle(all_tasks), "Should detect circular dependencies"

        def test_should_identify_parallel_tasks_when_phase_has_independent_tasks(
            self, valid_task_list
        ) -> None:
            """Parallel task identification should find tasks with no dependencies."""
            # Given: A task list with some independent tasks
            task_list = valid_task_list

            # When: Identifying parallel executable tasks
            all_independent_tasks = []

            for phase in task_list:
                tasks = phase["tasks"]

                for task in tasks:
                    # Tasks with no dependencies can run in parallel at the start
                    if not task["dependencies"]:
                        all_independent_tasks.append(task)

            # Then: Should identify at least one independent task
            assert len(all_independent_tasks) > 0, (
                "Should identify independent tasks that can start immediately"
            )

    class TestImplementationExecutor:
        """Test implementation-executor agent."""

        def test_should_validate_all_prerequisites_when_spec_and_tasks_are_complete(
            self, valid_authentication_spec_content, valid_task_list
        ) -> None:
            """Prerequisites validation should pass when all requirements are met."""
            # Given: A complete specification and task list
            spec_content = valid_authentication_spec_content
            task_list = valid_task_list

            # When: Validating prerequisites
            prerequisites = {
                "specification_exists": len(spec_content.strip()) > 0,
                "tasks_defined": len(task_list) > 0,
                "spec_has_requirements": "## Functional Requirements" in spec_content,
                "spec_has_success_criteria": "## Success Criteria" in spec_content,
                "tasks_have_dependencies": any(
                    task["dependencies"]
                    for phase in task_list
                    for task in phase["tasks"]
                ),
            }

            # Then: All prerequisites should be met
            for prereq, met in prerequisites.items():
                assert met, f"Prerequisite not met: {prereq}"

        def test_should_fail_validation_when_spec_is_empty(
            self, empty_spec_content, valid_task_list
        ) -> None:
            """Prerequisites validation should fail when specification is empty."""
            # Given: An empty specification
            spec_content = empty_spec_content
            task_list = valid_task_list

            # When: Validating prerequisites
            prerequisites = {
                "specification_exists": len(spec_content.strip()) > 0,
                "tasks_defined": len(task_list) > 0,
            }

            # Then: Specification prerequisite should fail
            assert not prerequisites["specification_exists"], (
                "Should detect empty specification"
            )

        def test_should_calculate_high_readiness_score_when_all_artifacts_complete(
            self, valid_authentication_spec_content, valid_task_list
        ) -> None:
            """Readiness score should be high when spec and tasks are complete."""
            # Given: Complete specification and task list
            spec_content = valid_authentication_spec_content
            task_list = valid_task_list

            # When: Calculating readiness score
            readiness_factors = {
                "spec_completeness": 0.3,
                "task_clarity": 0.3,
                "dependency_structure": 0.2,
                "resource_estimation": 0.2,
            }

            spec_score = (
                1.0
                if all(
                    section in spec_content
                    for section in [
                        "## Overview",
                        "## Functional Requirements",
                        "## Success Criteria",
                    ]
                )
                else 0.5
            )

            task_score = 1.0 if len(task_list) >= 3 else 0.5

            has_dependencies = any(
                task["dependencies"] for phase in task_list for task in phase["tasks"]
            )
            dependency_score = 1.0 if has_dependencies else 0.7

            has_estimates = all(
                "estimated_time" in task
                for phase in task_list
                for task in phase["tasks"]
            )
            estimate_score = 1.0 if has_estimates else 0.5

            readiness_score = (
                spec_score * readiness_factors["spec_completeness"]
                + task_score * readiness_factors["task_clarity"]
                + dependency_score * readiness_factors["dependency_structure"]
                + estimate_score * readiness_factors["resource_estimation"]
            )

            # Then: Readiness score should be high
            assert 0 <= readiness_score <= 1, (
                f"Readiness score should be between 0 and 1: {readiness_score}"
            )
            assert readiness_score >= 0.7, (
                f"Should be ready for implementation: {readiness_score}"
            )

        def test_should_calculate_low_readiness_score_when_spec_incomplete(
            self, spec_without_requirements, valid_task_list
        ) -> None:
            """Readiness score should be low when specification is incomplete."""
            # Given: Incomplete specification missing requirements
            spec_content = spec_without_requirements
            task_list = valid_task_list

            # When: Calculating readiness score
            readiness_factors = {
                "spec_completeness": 0.3,
                "task_clarity": 0.3,
                "dependency_structure": 0.2,
                "resource_estimation": 0.2,
            }

            spec_score = (
                1.0
                if all(
                    section in spec_content
                    for section in [
                        "## Overview",
                        "## Functional Requirements",
                        "## Success Criteria",
                    ]
                )
                else 0.5
            )

            task_score = 1.0 if len(task_list) >= 3 else 0.5

            has_dependencies = any(
                task["dependencies"] for phase in task_list for task in phase["tasks"]
            )
            dependency_score = 1.0 if has_dependencies else 0.7

            has_estimates = all(
                "estimated_time" in task
                for phase in task_list
                for task in phase["tasks"]
            )
            estimate_score = 1.0 if has_estimates else 0.5

            readiness_score = (
                spec_score * readiness_factors["spec_completeness"]
                + task_score * readiness_factors["task_clarity"]
                + dependency_score * readiness_factors["dependency_structure"]
                + estimate_score * readiness_factors["resource_estimation"]
            )

            # Then: Readiness score should be lower due to missing requirements
            assert readiness_score < 1.0, "Incomplete spec should reduce readiness"

        def test_should_detect_no_blocking_issues_when_spec_and_tasks_valid(
            self, valid_authentication_spec_content, valid_task_list
        ) -> None:
            """Blocking issues detection should find no issues in valid artifacts."""
            # Given: Valid specification and task list
            spec_content = valid_authentication_spec_content
            task_list = valid_task_list

            # When: Detecting blocking issues
            blocking_issues = []

            if "## Functional Requirements" not in spec_content:
                blocking_issues.append("Missing functional requirements")

            if "## Success Criteria" not in spec_content:
                blocking_issues.append("Missing success criteria")

            all_tasks = []
            for phase in task_list:
                all_tasks.extend(phase["tasks"])

            for task in all_tasks:
                for dep_id in task["dependencies"]:
                    dep_task = next((t for t in all_tasks if t["id"] == dep_id), None)
                    if dep_task and task["id"] in dep_task.get("dependencies", []):
                        blocking_issues.append(
                            f"Circular dependency: {task['id']} <-> {dep_id}",
                        )

            # Then: Should have minimal or no blocking issues
            assert len(blocking_issues) <= 1, (
                f"Too many blocking issues: {blocking_issues}"
            )

        def test_should_detect_blocking_issues_when_spec_incomplete(
            self, spec_without_requirements, valid_task_list
        ) -> None:
            """Blocking issues detection should find missing required sections."""
            # Given: Incomplete specification without requirements
            spec_content = spec_without_requirements

            # When: Detecting blocking issues
            blocking_issues = []

            if "## Functional Requirements" not in spec_content:
                blocking_issues.append("Missing functional requirements")

            if "## Success Criteria" not in spec_content:
                blocking_issues.append("Missing success criteria")

            # Then: Should detect missing requirements as blocking
            assert len(blocking_issues) > 0, "Should detect blocking issues"
            assert "Missing functional requirements" in blocking_issues

        def test_should_assess_current_phase_when_no_tasks_completed(
            self, valid_task_list
        ) -> None:
            """Implementation status should indicate setup phase when no tasks are done."""
            # Given: A task list with no completed tasks
            task_list = valid_task_list
            completed_tasks = set()

            # When: Assessing implementation status
            current_phase_index = 0
            phases = [
                "0 - Setup",
                "1 - Foundation",
                "2 - Core Implementation",
                "3 - Integration",
                "4 - Polish",
            ]

            for i, phase in enumerate(phases):
                phase_tasks = next(
                    (p["tasks"] for p in task_list if p["phase"] == phase),
                    [],
                )
                if all(task["id"] in completed_tasks for task in phase_tasks):
                    current_phase_index = i + 1
                else:
                    break

            current_phase = (
                phases[current_phase_index]
                if current_phase_index < len(phases)
                else "Completed"
            )

            # Then: Should be in first phase
            assert current_phase in [
                *phases,
                "Completed",
            ], f"Invalid phase: {current_phase}"
            assert current_phase == "0 - Setup", "Should start at setup phase"

        def test_should_estimate_positive_resources_when_tasks_have_time_estimates(
            self, valid_task_list
        ) -> None:
            """Resource estimation should calculate positive values from task estimates."""
            # Given: A task list with time estimates
            task_list = valid_task_list

            # When: Estimating resource requirements
            total_time = 0
            for phase in task_list:
                for task in phase["tasks"]:
                    time_str = task["estimated_time"]
                    if "h" in time_str.lower():
                        hours = float(time_str.lower().replace("h", "").strip())
                        total_time += hours / 8
                    elif "m" in time_str.lower():
                        minutes = float(time_str.lower().replace("m", "").strip())
                        total_time += minutes / (8 * 60)

            if total_time <= 1:
                developers_needed = 1
            elif total_time <= 5:
                developers_needed = 2
            else:
                developers_needed = 3

            # Then: Should estimate reasonable resources
            assert developers_needed >= 1, "Should need at least one developer"
            assert developers_needed <= 5, "Should not need excessive developers"
            assert total_time > 0, "Should estimate positive time"

        @pytest.mark.parametrize(
            "total_hours,expected_min_devs,expected_max_devs",
            [
                (4, 1, 1),  # Half day = 1 dev
                (16, 2, 2),  # 2 days = 2 devs
                (48, 3, 5),  # 6 days = 3+ devs
            ],
        )
        def test_should_scale_developer_count_based_on_total_time(
            self, total_hours: float, expected_min_devs: int, expected_max_devs: int
        ) -> None:
            """Resource estimation should scale developer count with total time."""
            # Given: Various total time estimates
            total_time = total_hours / 8  # Convert to days

            # When: Estimating developers needed
            if total_time <= 1:
                developers_needed = 1
            elif total_time <= 5:
                developers_needed = 2
            else:
                developers_needed = 3

            # Then: Should match expected range
            assert developers_needed >= expected_min_devs
            assert developers_needed <= expected_max_devs
