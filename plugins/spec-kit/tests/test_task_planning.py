"""Tests for task-planning skill functionality.

This module tests the task planning system using BDD-style test structure:
- Behavior-focused test names (test_should_X_when_Y)
- Given-When-Then comments for clarity
- Parameterized tests for comprehensive coverage
- Edge case and negative testing
"""

import re

import pytest

# Constants for magic numbers
MAX_DAYS_PER_TASK = 5
MIN_MINUTES_PER_TASK = 15


class TestTaskPlanning:
    """Test cases for the Task Planning skill."""

    def test_should_maintain_phase_order_when_organizing_tasks(
        self, valid_task_list
    ) -> None:
        """Test task list follows proper phase structure."""
        # Given: Expected phase ordering
        expected_phases = [
            "0 - Setup",
            "1 - Foundation",
            "2 - Core Implementation",
            "3 - Integration",
            "4 - Polish",
        ]

        # When: Extracting actual phases from task list
        actual_phases = [phase["phase"] for phase in valid_task_list]

        # Then: Phases should be in proper order
        for i, expected_phase in enumerate(expected_phases[: len(actual_phases)]):
            assert actual_phases[i] == expected_phase, (
                f"Phase {i} should be {expected_phase}"
            )

    def test_should_include_all_required_fields_when_validating_tasks(
        self, valid_task_list
    ) -> None:
        """Test tasks have all required fields."""
        # Given: A valid task list
        required_fields = [
            "id",
            "title",
            "description",
            "dependencies",
            "estimated_time",
            "priority",
        ]

        # When: Checking all tasks across all phases
        for phase in valid_task_list:
            for task in phase["tasks"]:
                # Then: Each task should have all required fields
                for field in required_fields:
                    assert field in task, f"Task missing {field}: {task}"

    def test_should_store_dependencies_as_list_when_defining_tasks(
        self, valid_task_list
    ) -> None:
        """Test task dependencies are stored as lists."""
        # Given: A valid task list
        # When: Checking dependency structure
        for phase in valid_task_list:
            for task in phase["tasks"]:
                # Then: Dependencies should be a list
                assert isinstance(task["dependencies"], list), (
                    f"Dependencies should be list, got {type(task['dependencies'])}"
                )

    def test_should_reference_valid_tasks_when_defining_dependencies(
        self, valid_task_list
    ) -> None:
        """Test task dependencies reference existing tasks."""
        # Given: A valid task list with dependencies
        # When: Building task ID map
        all_task_ids = set()
        for phase in valid_task_list:
            for task in phase["tasks"]:
                all_task_ids.add(task["id"])

        # Then: All dependencies should reference existing tasks
        for phase in valid_task_list:
            for task in phase["tasks"]:
                for dep_id in task["dependencies"]:
                    assert dep_id in all_task_ids, (
                        f"Task {task['id']} has invalid dependency: {dep_id}"
                    )

    def test_should_have_setup_phase_when_organizing_tasks(
        self, valid_task_list
    ) -> None:
        """Test Phase 0 Setup exists and has tasks."""
        # Given: A valid task list
        # When: Looking for Setup phase
        setup_phase = next(
            (phase for phase in valid_task_list if phase["phase"] == "0 - Setup"),
            None,
        )

        # Then: Setup phase should exist and have tasks
        assert setup_phase is not None, "Should have Setup phase"
        assert len(setup_phase["tasks"]) > 0, "Setup phase should have tasks"

    def test_should_allow_sequential_dependencies_when_in_setup_phase(
        self, valid_task_list
    ) -> None:
        """Test setup tasks can have dependencies on earlier setup tasks."""
        # Given: Setup phase from task list
        setup_phase = next(
            (phase for phase in valid_task_list if phase["phase"] == "0 - Setup"),
            None,
        )
        assert setup_phase is not None

        setup_tasks = setup_phase["tasks"]
        setup_task_ids = {task["id"] for task in setup_tasks}

        # When: Checking dependencies within setup phase
        # Then: Dependencies should exist (tasks can depend on earlier tasks)
        # This is valid and expected - e.g., install deps depends on init project
        for task in setup_tasks:
            for dep_id in task["dependencies"]:
                if dep_id in setup_task_ids:
                    # Ensure it's not a self-dependency
                    assert dep_id != task["id"], (
                        f"Setup task {task['id']} has self-dependency"
                    )

    @pytest.mark.parametrize(
        "priority",
        ["high", "medium", "low", "critical"],
    )
    def test_should_use_valid_priority_when_setting_task_priority(
        self, valid_task_list, priority
    ) -> None:
        """Test tasks use valid priority levels."""
        # Given: A valid task list with various priorities
        # When: Collecting all priorities
        all_priorities = []
        for phase in valid_task_list:
            for task in phase["tasks"]:
                all_priorities.append(task["priority"])

        # Then: All priorities should be valid
        for task_priority in all_priorities:
            assert task_priority in ["high", "medium", "low", "critical"], (
                f"Invalid priority: {task_priority}"
            )

    def test_should_match_time_format_when_estimating_tasks(
        self, valid_task_list
    ) -> None:
        """Test time estimations follow consistent format."""
        # Given: Expected time estimation pattern
        estimation_pattern = (
            r"^\d+[hm]$|^(\d+\.?\d*)\s*(hour|hours|day|days|week|weeks)s?$"
        )

        # When: Checking all task estimations
        for phase in valid_task_list:
            for task in phase["tasks"]:
                estimation = task["estimated_time"]

                # Then: Estimation should match the pattern
                assert re.match(estimation_pattern, estimation.lower()), (
                    f"Invalid time format: {estimation}"
                )

    def test_should_detect_cycle_when_dependencies_are_circular(
        self, task_with_circular_dependency
    ) -> None:
        """Test detection of circular task dependencies."""
        # Given: Tasks with circular dependencies (A->B->C->A)
        def has_cycle(task_list):
            """Helper function to detect cycles using DFS."""
            # Flatten task list
            tasks = []
            for phase in task_list:
                tasks.extend(phase["tasks"])

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

        # When: Checking for cycles
        # Then: Should detect the circular dependency
        assert has_cycle(task_with_circular_dependency), (
            "Should detect dependency cycle"
        )

    def test_should_not_detect_cycle_when_dependencies_are_valid(
        self, valid_task_list
    ) -> None:
        """Test that valid task dependencies don't trigger cycle detection."""
        # Given: Valid task list with proper dependencies
        def has_cycle(task_list):
            """Helper function to detect cycles using DFS."""
            tasks = []
            for phase in task_list:
                tasks.extend(phase["tasks"])

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

        # When: Checking for cycles
        # Then: Should not detect any cycles
        assert not has_cycle(valid_task_list), (
            "Valid task list should not have cycles"
        )

    def test_should_identify_parallel_tasks_when_no_dependencies_exist(
        self, valid_task_list
    ) -> None:
        """Test identification of tasks that can run in parallel."""
        # Given: A task list with tasks
        parallel_count = 0

        # When: Identifying tasks that can run in parallel
        for phase in valid_task_list:
            tasks = phase["tasks"]
            phase_task_ids = {task["id"] for task in tasks}

            for task in tasks:
                # Check if task has no dependencies on tasks in same phase
                has_phase_dependency = any(
                    dep_id in phase_task_ids for dep_id in task["dependencies"]
                )

                # Count tasks with no phase dependencies
                if not has_phase_dependency:
                    parallel_count += 1

        # Then: Should identify some tasks that could potentially run in parallel
        # At minimum, the first task of each phase has no phase dependencies
        assert parallel_count >= len(valid_task_list), (
            f"Should identify tasks without phase dependencies, found {parallel_count}"
        )

    def test_should_find_entry_points_when_analyzing_critical_path(
        self, valid_task_list
    ) -> None:
        """Test identification of tasks with no dependencies (entry points)."""
        # Given: A task list with dependencies
        task_map = {}

        # When: Building dependency graph
        for phase in valid_task_list:
            for task in phase["tasks"]:
                task_map[task["id"]] = {
                    "task": task,
                    "dependencies": task["dependencies"],
                    "phase": phase["phase"],
                }

        # Find tasks with no dependencies (start points)
        start_tasks = [
            task_id
            for task_id, task_info in task_map.items()
            if not task_info["dependencies"]
        ]

        # Then: Should have at least one entry point
        assert len(start_tasks) > 0, (
            "Should have at least one task with no dependencies"
        )

    def test_should_be_longer_than_title_when_writing_description(
        self, valid_task_list
    ) -> None:
        """Test task descriptions are more detailed than titles."""
        # Given: A valid task list
        # When: Comparing description length to title
        for phase in valid_task_list:
            for task in phase["tasks"]:
                description = task["description"]
                title = task["title"]

                # Then: Description should be longer than title
                assert len(description) > len(title), (
                    f"Description should be longer than title for {task['id']}"
                )

    def test_should_avoid_vague_words_when_writing_descriptions(
        self, valid_task_list
    ) -> None:
        """Test task descriptions are specific and clear."""
        # Given: List of vague words to avoid
        vague_words = ["various", "multiple", "several", "some", "related"]

        # When: Checking task descriptions
        for phase in valid_task_list:
            for task in phase["tasks"]:
                description = task["description"]
                description_lower = description.lower()

                # Count vague words
                vague_found = [
                    word for word in vague_words if word in description_lower
                ]

                # Then: Should use minimal vague words
                assert len(vague_found) <= 1, (
                    f"Task description too vague: {description}"
                )

    def test_should_start_with_action_verb_when_writing_descriptions(
        self, valid_task_list
    ) -> None:
        """Test task descriptions start with action verbs."""
        # Given: List of action verbs
        action_verbs = [
            "create",
            "implement",
            "add",
            "build",
            "design",
            "develop",
            "setup",
            "configure",
            "install",
            "write",
            "define",
            "establish",
        ]

        # When: Checking task descriptions
        actionable_count = 0
        total_count = 0

        for phase in valid_task_list:
            for task in phase["tasks"]:
                description = task["description"]
                total_count += 1

                # Check if starts with action verb
                if any(description.lower().startswith(verb) for verb in action_verbs):
                    actionable_count += 1

        # Then: Majority of descriptions should start with action verbs
        # (Not strictly required but good practice)
        assert actionable_count / total_count > 0.5, (
            "Most descriptions should start with action verbs"
        )

    @pytest.mark.parametrize(
        "phase_name,expected_keywords",
        [
            ("0 - Setup", ["project", "directory", "install", "configure", "init"]),
            (
                "1 - Foundation",
                ["model", "schema", "interface", "type", "structure"],
            ),
            (
                "2 - Core Implementation",
                ["implement", "build", "create", "develop"],
            ),
            (
                "3 - Integration",
                ["integrate", "connect", "middleware", "service"],
            ),
            (
                "4 - Polish",
                ["optimize", "document", "test", "cleanup", "refactor"],
            ),
        ],
    )
    def test_should_contain_appropriate_tasks_when_in_specific_phase(
        self, valid_task_list, phase_name, expected_keywords
    ) -> None:
        """Test each phase contains contextually appropriate tasks."""
        # Given: Expected keywords for a specific phase
        phase = next(
            (p for p in valid_task_list if p["phase"] == phase_name),
            None,
        )

        if phase is None:
            pytest.skip(f"Phase {phase_name} not in test data")

        # When: Checking task content for expected keywords
        found_keywords = []
        for task in phase["tasks"]:
            task_text = f"{task['title']} {task['description']}".lower()
            for keyword in expected_keywords:
                if keyword in task_text:
                    found_keywords.append(keyword)
                    break

        # Then: Phase should contain relevant task types
        # (Not strictly required but indicates good phase organization)
        assert len(found_keywords) > 0 or len(phase["tasks"]) == 0, (
            f"Phase {phase_name} should contain expected types of tasks"
        )

    def test_should_not_exceed_max_days_when_estimating_large_tasks(
        self, valid_task_list
    ) -> None:
        """Test tasks don't exceed maximum duration threshold."""
        # Given: Maximum task duration threshold
        # When: Checking all task estimations
        for phase in valid_task_list:
            for task in phase["tasks"]:
                time_est = task["estimated_time"].lower()

                # Then: Tasks with day estimates should not be too large
                if "day" in time_est:
                    days_match = re.search(r"(\d+(?:\.\d+)?)\s*day", time_est)
                    if days_match:
                        days = float(days_match.group(1))
                        assert days <= MAX_DAYS_PER_TASK, (
                            f"Task too large: {task['id']} - {days} days"
                        )

    def test_should_meet_minimum_duration_when_estimating_small_tasks(
        self, valid_task_list
    ) -> None:
        """Test tasks meet minimum duration threshold."""
        # Given: Minimum task duration threshold
        # When: Checking all task estimations
        for phase in valid_task_list:
            for task in phase["tasks"]:
                time_est = task["estimated_time"].lower()

                # Then: Tasks with minute estimates should not be too small
                if "m" in time_est or "minute" in time_est:
                    minutes_match = re.search(r"(\d+(?:\.\d+)?)\s*m", time_est)
                    if minutes_match:
                        minutes = float(minutes_match.group(1))
                        assert minutes >= MIN_MINUTES_PER_TASK, (
                            f"Task too small: {task['id']} - {minutes} minutes"
                        )

    def test_should_follow_naming_pattern_when_assigning_task_ids(
        self, valid_task_list
    ) -> None:
        """Test task IDs follow consistent naming pattern."""
        # Given: Expected task ID pattern (prefix-###)
        id_pattern = r"^[a-z]+-\d{3}$"

        # When: Checking all task IDs
        for phase in valid_task_list:
            for task in phase["tasks"]:
                # Then: Each ID should match the pattern
                assert re.match(id_pattern, task["id"]), (
                    f"Task ID doesn't match pattern: {task['id']}"
                )

    def test_should_prevent_forward_dependencies_when_organizing_phases(
        self, valid_task_list
    ) -> None:
        """Test phases don't have forward cross-phase dependencies."""
        # Given: Task list with multiple phases
        phase_tasks = {}
        for phase in valid_task_list:
            phase_tasks[phase["phase"]] = {task["id"] for task in phase["tasks"]}

        phase_order = [
            "0 - Setup",
            "1 - Foundation",
            "2 - Core Implementation",
            "3 - Integration",
            "4 - Polish",
        ]

        # When: Checking dependencies across phases
        for phase in valid_task_list:
            phase_name = phase["phase"]

            for task in phase["tasks"]:
                for dep_id in task["dependencies"]:
                    # Find which phase the dependency belongs to
                    dep_phase = None
                    for other_phase_name, task_ids in phase_tasks.items():
                        if dep_id in task_ids:
                            dep_phase = other_phase_name
                            break

                    # Then: Dependencies should be in same or earlier phase
                    if dep_phase:
                        current_index = phase_order.index(phase_name)
                        dep_index = phase_order.index(dep_phase)

                        assert dep_index <= current_index, (
                            f"Cross-phase forward dependency: "
                            f"{task['id']} depends on {dep_id}"
                        )

    # Edge Cases and Negative Tests

    def test_should_handle_empty_task_list_when_validating(
        self, empty_task_list
    ) -> None:
        """Test graceful handling of empty task list."""
        # Given: An empty task list
        # When: Processing the list
        # Then: Should not raise any errors
        assert isinstance(empty_task_list, list)
        assert len(empty_task_list) == 0

    def test_should_reject_missing_dependencies_when_validating_tasks(
        self, task_with_missing_dependency
    ) -> None:
        """Test detection of references to non-existent tasks."""
        # Given: Tasks with missing dependencies
        all_task_ids = set()
        for phase in task_with_missing_dependency:
            for task in phase["tasks"]:
                all_task_ids.add(task["id"])

        # When: Checking dependencies
        missing_deps = []
        for phase in task_with_missing_dependency:
            for task in phase["tasks"]:
                for dep_id in task["dependencies"]:
                    if dep_id not in all_task_ids:
                        missing_deps.append(dep_id)

        # Then: Should detect missing dependencies
        assert len(missing_deps) > 0, "Should detect missing dependencies"
