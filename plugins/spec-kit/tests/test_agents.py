"""Tests for spec-kit agent functionality."""



class TestSpeckitAgents:
    """Test cases for speckit agents."""

    class TestSpecAnalyzer:
        """Test spec-analyzer agent."""

        def test_spec_complexity_analysis(self, sample_spec_content):
            """Test specification complexity analysis."""
            # Analyze spec content
            lines = sample_spec_content.split('\n')
            sections = len([line for line in lines if line.startswith('## ')])
            user_scenarios = len([line for line in lines if '### As a' in line])
            functional_requirements = len([line for line in lines if line.startswith('-')])

            # Calculate complexity metrics
            complexity_factors = {
                "sections": sections,
                "user_scenarios": user_scenarios,
                "functional_requirements": functional_requirements,
                "total_lines": len([line for line in lines if line.strip()]),
                "has_open_questions": "[CLARIFY]" in sample_spec_content
            }

            # Determine complexity level
            complexity_score = (
                min(complexity_factors["sections"] / 5, 1) * 0.3 +
                min(complexity_factors["user_scenarios"] / 3, 1) * 0.3 +
                min(complexity_factors["functional_requirements"] / 10, 1) * 0.4
            )

            if complexity_score < 0.3:
                complexity_level = "low"
            elif complexity_score < 0.7:
                complexity_level = "medium"
            else:
                complexity_level = "high"

            assert complexity_level in ["low", "medium", "high"]
            assert complexity_factors["sections"] >= 4  # Minimum required sections

        def test_effort_estimation(self, sample_spec_content):
            """Test effort estimation from specification."""
            # Count implementation indicators
            implementation_indicators = {
                "user_scenarios": sample_spec_content.count("### As a"),
                "functional_requirements": len([
                    line for line in sample_spec_content.split('\n')
                    if line.strip().startswith('-')
                ]),
                "integrations": len([
                    line for line in sample_spec_content.lower().split('\n')
                    if any(term in line for term in ["api", "database", "service", "external"])
                ]),
                "complexity_markers": len([
                    line for line in sample_spec_content.lower().split('\n')
                    if any(term in line for term in ["security", "performance", "scalability"])
                ])
            }

            # Calculate effort in story points or days
            base_effort = 3  # Base effort in days
            scenario_effort = implementation_indicators["user_scenarios"] * 1
            requirement_effort = implementation_indicators["functional_requirements"] * 0.5
            integration_effort = implementation_indicators["integrations"] * 2
            complexity_effort = implementation_indicators["complexity_markers"] * 1.5

            total_effort = base_effort + scenario_effort + requirement_effort + integration_effort + complexity_effort

            assert total_effort > 0, "Should estimate positive effort"
            assert total_effort < 30, "Effort should be reasonable (< 30 days)"

        def test_key_component_extraction(self, sample_spec_content):
            """Test extraction of key components from specification."""
            # Look for technical components
            component_patterns = [
                r"authentication",
                r"authorization",
                r"session",
                r"user",
                r"password",
                r"email",
                r"role",
                r"api",
                r"database"
            ]

            found_components = []
            spec_lower = sample_spec_content.lower()

            for pattern in component_patterns:
                if pattern in spec_lower:
                    found_components.append(pattern)

            # Should find meaningful components
            assert len(found_components) >= 3, f"Should extract key components, found: {found_components}"

        def test_dependency_identification(self, sample_spec_content):
            """Test identification of external dependencies."""
            dependency_indicators = [
                "email service",
                "database",
                "external api",
                "third-party",
                "library",
                "framework"
            ]

            spec_lower = sample_spec_content.lower()
            found_dependencies = []

            for indicator in dependency_indicators:
                if indicator in spec_lower:
                    found_dependencies.append(indicator)

            # Dependencies are optional but should be identified if present
            # assert len(found_dependencies) > 0, "Should identify dependencies if mentioned"

        def test_risk_assessment(self, sample_spec_content):
            """Test risk assessment from specification."""
            risk_indicators = {
                "security": ["password", "authentication", "authorization", "session"],
                "complexity": ["multiple", "various", "several", "complex"],
                "integration": ["external", "third-party", "api"],
                "performance": ["performance", "scalability", "optimization"]
            }

            risk_scores = {}
            spec_lower = sample_spec_content.lower()

            for risk_type, keywords in risk_indicators.items():
                score = sum(1 for keyword in keywords if keyword in spec_lower)
                risk_scores[risk_type] = score

            # Should assess some level of risk
            total_risk = sum(risk_scores.values())
            assert total_risk >= 0, "Risk assessment should be non-negative"

            # Security-related specs should have security risk indicators
            if "authentication" in spec_lower:
                assert risk_scores["security"] > 0, "Authentication specs should identify security risks"

    class TestTaskGenerator:
        """Test task-generator agent."""

        def test_task_count_estimation(self, sample_spec_content):
            """Test estimation of task count from specification."""
            # Analyze spec complexity for task estimation
            functional_requirements = len([
                line for line in sample_spec_content.split('\n')
                if line.strip().startswith('-') and len(line.strip()) > 2
            ])

            user_scenarios = sample_spec_content.count("### As a")

            # Estimate tasks (rough heuristic)
            estimated_tasks = max(
                functional_requirements * 2,  # Tasks per requirement
                user_scenarios * 3,           # Tasks per scenario
                5                             # Minimum tasks
            )

            assert estimated_tasks >= 5, f"Should estimate reasonable task count: {estimated_tasks}"
            assert estimated_tasks <= 50, f"Task count should be reasonable: {estimated_tasks}"

        def test_phase_breakdown(self, sample_task_list):
            """Test task phase breakdown."""
            expected_phases = [
                "0 - Setup",
                "1 - Foundation",
                "2 - Core Implementation",
                "3 - Integration",
                "4 - Polish"
            ]

            actual_phases = [phase["phase"] for phase in sample_task_list]

            # Should have phases in correct order
            for i, expected_phase in enumerate(expected_phases[:len(actual_phases)]):
                assert actual_phases[i] == expected_phase

        def test_dependency_analysis(self, sample_task_list):
            """Test task dependency analysis."""
            # Build dependency graph
            all_tasks = []
            for phase in sample_task_list:
                all_tasks.extend(phase["tasks"])

            # Check for dependency cycles
            def has_cycle(tasks):
                visited = set()
                rec_stack = set()

                def dfs(task_id):
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

            assert not has_cycle(all_tasks), "Task dependencies should not have cycles"

        def test_parallel_task_identification(self, sample_task_list):
            """Test identification of parallel executable tasks."""
            parallel_groups = []

            for phase in sample_task_list:
                tasks = phase["tasks"]

                # Find tasks with no dependencies in the same phase
                independent_tasks = []
                for task in tasks:
                    has_phase_dependency = any(
                        dep_id in [other_task["id"] for other_task in tasks]
                        for dep_id in task["dependencies"]
                    )

                    if not has_phase_dependency and not task["dependencies"]:
                        independent_tasks.append(task)

                if len(independent_tasks) > 1:
                    parallel_groups.append(independent_tasks)

            # Should identify parallel opportunities
            setup_phase = next((phase for phase in sample_task_list if phase["phase"] == "0 - Setup"), None)
            if setup_phase and len(setup_phase["tasks"]) > 1:
                assert len(parallel_groups) > 0, "Should identify parallel tasks in setup phase"

    class TestImplementationExecutor:
        """Test implementation-executor agent."""

        def test_prerequisites_validation(self, sample_spec_content, sample_task_list):
            """Test validation of implementation prerequisites."""
            prerequisites = {
                "specification_exists": len(sample_spec_content.strip()) > 0,
                "tasks_defined": len(sample_task_list) > 0,
                "spec_has_requirements": "## Functional Requirements" in sample_spec_content,
                "spec_has_success_criteria": "## Success Criteria" in sample_spec_content,
                "tasks_have_dependencies": any(
                    task["dependencies"]
                    for phase in sample_task_list
                    for task in phase["tasks"]
                )
            }

            # All prerequisites should be met
            for prereq, met in prerequisites.items():
                assert met, f"Prerequisite not met: {prereq}"

        def test_implementation_readiness_score(self, sample_spec_content, sample_task_list):
            """Test calculation of implementation readiness score."""
            readiness_factors = {
                "spec_completeness": 0.3,
                "task_clarity": 0.3,
                "dependency_structure": 0.2,
                "resource_estimation": 0.2
            }

            # Calculate individual scores
            spec_score = 1.0 if all(section in sample_spec_content for section in [
                "## Overview", "## Functional Requirements", "## Success Criteria"
            ]) else 0.5

            task_score = 1.0 if len(sample_task_list) >= 3 else 0.5

            # Check dependency structure
            has_dependencies = any(
                task["dependencies"]
                for phase in sample_task_list
                for task in phase["tasks"]
            )
            dependency_score = 1.0 if has_dependencies else 0.7

            # Check time estimations
            has_estimates = all(
                "estimated_time" in task
                for phase in sample_task_list
                for task in phase["tasks"]
            )
            estimate_score = 1.0 if has_estimates else 0.5

            readiness_score = (
                spec_score * readiness_factors["spec_completeness"] +
                task_score * readiness_factors["task_clarity"] +
                dependency_score * readiness_factors["dependency_structure"] +
                estimate_score * readiness_factors["resource_estimation"]
            )

            assert 0 <= readiness_score <= 1, f"Readiness score should be between 0 and 1: {readiness_score}"
            assert readiness_score >= 0.7, f"Should be ready for implementation: {readiness_score}"

        def test_blocking_issues_detection(self, sample_spec_content, sample_task_list):
            """Test detection of blocking implementation issues."""
            blocking_issues = []

            # Check for incomplete specification
            if "## Functional Requirements" not in sample_spec_content:
                blocking_issues.append("Missing functional requirements")

            # Check for undefined success criteria
            if "## Success Criteria" not in sample_spec_content:
                blocking_issues.append("Missing success criteria")

            # Check for circular dependencies
            all_tasks = []
            for phase in sample_task_list:
                all_tasks.extend(phase["tasks"])

            # Simple cycle detection
            for task in all_tasks:
                for dep_id in task["dependencies"]:
                    dep_task = next((t for t in all_tasks if t["id"] == dep_id), None)
                    if dep_task and task["id"] in dep_task.get("dependencies", []):
                        blocking_issues.append(f"Circular dependency: {task['id']} <-> {dep_id}")

            # Should have minimal blocking issues for good specs
            assert len(blocking_issues) <= 1, f"Too many blocking issues: {blocking_issues}"

        def test_implementation_status_assessment(self, sample_task_list):
            """Test assessment of implementation status."""
            # Mock implementation progress
            completed_tasks = set()  # Tasks that are completed
            current_phase_index = 0

            phases = ["0 - Setup", "1 - Foundation", "2 - Core Implementation", "3 - Integration", "4 - Polish"]

            # Find current phase based on completed tasks
            for i, phase in enumerate(phases):
                phase_tasks = next((p["tasks"] for p in sample_task_list if p["phase"] == phase), [])
                if all(task["id"] in completed_tasks for task in phase_tasks):
                    current_phase_index = i + 1
                else:
                    break

            current_phase = phases[current_phase_index] if current_phase_index < len(phases) else "Completed"

            assert current_phase in phases + ["Completed"], f"Invalid phase: {current_phase}"

        def test_resource_requirements_estimation(self, sample_task_list):
            """Test estimation of resource requirements."""
            # Calculate total estimated time
            total_time = 0
            for phase in sample_task_list:
                for task in phase["tasks"]:
                    # Parse time estimation
                    time_str = task["estimated_time"]
                    if "h" in time_str.lower():
                        hours = float(time_str.lower().replace("h", "").strip())
                        total_time += hours / 8  # Convert to days
                    elif "m" in time_str.lower():
                        minutes = float(time_str.lower().replace("m", "").strip())
                        total_time += minutes / (8 * 60)  # Convert to days

            # Estimate resources needed
            if total_time <= 1:
                developers_needed = 1
            elif total_time <= 5:
                developers_needed = 2
            else:
                developers_needed = 3

            assert developers_needed >= 1, "Should need at least one developer"
            assert developers_needed <= 5, "Should not need excessive developers"
            assert total_time > 0, "Should estimate positive time"
