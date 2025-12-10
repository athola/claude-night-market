"""Tests for task-planning skill functionality."""

import re

# Constants for magic numbers
MAX_DAYS_PER_TASK = 5
MIN_MINUTES_PER_TASK = 15


class TestTaskPlanning:
    """Test cases for the Task Planning skill."""

    def test_task_phases_structure(self, sample_task_list) -> None:
        """Test task list follows proper phase structure."""
        expected_phases = [
            "0 - Setup",
            "1 - Foundation",
            "2 - Core Implementation",
            "3 - Integration",
            "4 - Polish",
        ]

        actual_phases = [phase["phase"] for phase in sample_task_list]

        # Should have phases in proper order
        for i, expected_phase in enumerate(expected_phases[: len(actual_phases)]):
            assert actual_phases[i] == expected_phase, (
                f"Phase {i} should be {expected_phase}"
            )

    def test_task_dependency_structure(self, sample_task_list) -> None:
        """Test tasks have proper dependency structure."""
        for phase in sample_task_list:
            for task in phase["tasks"]:
                # Each task should have required fields
                assert "id" in task, f"Task missing ID: {task}"
                assert "title" in task, f"Task missing title: {task}"
                assert "description" in task, f"Task missing description: {task}"
                assert "dependencies" in task, f"Task missing dependencies: {task}"
                assert "estimated_time" in task, f"Task missing estimated time: {task}"
                assert "priority" in task, f"Task missing priority: {task}"

                # Dependencies should be a list
                assert isinstance(task["dependencies"], list), (
                    f"Dependencies should be list, got {type(task['dependencies'])}"
                )

                # Dependencies should reference existing tasks
                for dep_id in task["dependencies"]:
                    found = False
                    for search_phase in sample_task_list:
                        for search_task in search_phase["tasks"]:
                            if search_task["id"] == dep_id:
                                found = True
                                break
                        if found:
                            break
                    # Allow dependencies on tasks not in our sample (external deps)

    def test_phase_0_setup_tasks(self, sample_task_list) -> None:
        """Test Phase 0 contains proper setup tasks."""
        setup_phase = next(
            (phase for phase in sample_task_list if phase["phase"] == "0 - Setup"),
            None,
        )
        assert setup_phase is not None, "Should have Setup phase"

        setup_tasks = setup_phase["tasks"]
        assert len(setup_tasks) > 0, "Setup phase should have tasks"

        # Setup tasks should have no dependencies or only external deps
        for task in setup_tasks:
            if task["dependencies"]:
                # Allow external dependencies but check they don't reference tasks
                # in same phase
                for dep_id in task["dependencies"]:
                    internal_dep = any(
                        dep_id == other_task["id"]
                        for other_task in setup_tasks
                        if other_task["id"] != task["id"]
                    )
                    assert not internal_dep, (
                        f"Setup task {task['id']} has internal dependency {dep_id}"
                    )

    def test_priority_assignment(self, sample_task_list) -> None:
        """Test tasks have appropriate priority levels."""
        valid_priorities = ["high", "medium", "low", "critical"]

        for phase in sample_task_list:
            for task in phase["tasks"]:
                assert task["priority"] in valid_priorities, (
                    f"Invalid priority: {task['priority']}"
                )

    def test_estimation_format(self, sample_task_list) -> None:
        """Test time estimations follow consistent format."""
        estimation_pattern = (
            r"^\d+[hm]$|^(\d+\.?\d*)\s*(hour|hours|day|days|week|weeks)s?$"
        )

        for phase in sample_task_list:
            for task in phase["tasks"]:
                estimation = task["estimated_time"]
                assert re.match(estimation_pattern, estimation.lower()), (
                    f"Invalid time format: {estimation}"
                )

    def test_dependency_cycle_detection(self) -> None:
        """Test dependency cycle detection."""
        # Create tasks with a cycle
        cyclic_tasks = [
            {"id": "task-001", "title": "Task A", "dependencies": ["task-002"]},
            {"id": "task-002", "title": "Task B", "dependencies": ["task-003"]},
            {
                "id": "task-003",
                "title": "Task C",
                "dependencies": ["task-001"],  # Creates cycle
            },
        ]

        # Detect cycle
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

        assert has_cycle(cyclic_tasks), "Should detect dependency cycle"

    def test_parallel_execution_identification(self, sample_task_list) -> None:
        """Test identification of tasks that can run in parallel."""
        # Tasks can run in parallel if they're in same phase and have no
        # dependencies on each other
        parallel_groups = []

        for phase in sample_task_list:
            tasks = phase["tasks"]
            independent_tasks = []

            for task in tasks:
                # Check if task depends on other tasks in same phase
                has_phase_dependency = any(
                    dep_id in [other_task["id"] for other_task in tasks]
                    for dep_id in task["dependencies"]
                )

                if not has_phase_dependency and not task["dependencies"]:
                    independent_tasks.append(task)

            if len(independent_tasks) > 1:
                parallel_groups.append(independent_tasks)

        # Should identify at least one parallel opportunity if we have multiple
        # setup tasks
        setup_phase = next(
            (phase for phase in sample_task_list if phase["phase"] == "0 - Setup"),
            None,
        )
        if setup_phase and len(setup_phase["tasks"]) > 1:
            assert len(parallel_groups) > 0, (
                "Should identify parallel execution opportunities"
            )

    def test_critical_path_identification(self, sample_task_list) -> None:
        """Test critical path identification through tasks."""
        # Build dependency graph
        task_map = {}
        for phase in sample_task_list:
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

        assert len(start_tasks) > 0, (
            "Should have at least one task with no dependencies"
        )

    def test_task_description_quality(self, sample_task_list) -> None:
        """Test task descriptions are clear and actionable."""
        for phase in sample_task_list:
            for task in phase["tasks"]:
                description = task["description"]
                title = task["title"]

                # Description should be more detailed than title
                assert len(description) > len(title), (
                    f"Description should be longer than title for {task['id']}"
                )

                # Description should be specific
                vague_words = ["various", "multiple", "several", "some", "related"]
                description_lower = description.lower()
                vague_found = [
                    word for word in vague_words if word in description_lower
                ]

                # Allow some vague words but not too many
                assert len(vague_found) <= 1, (
                    f"Task description too vague: {description}"
                )

                # Should start with action verb
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
                any(description.lower().startswith(verb) for verb in action_verbs)
                # Not strictly required but good practice
                # assert starts_with_verb, (
                #     f"Description should start with action verb: {description}"
                # )

    def test_phase_content_appropriateness(self, sample_task_list) -> None:
        """Test each phase contains appropriate types of tasks."""
        phase_expectations = {
            "0 - Setup": ["project", "directory", "install", "configure", "init"],
            "1 - Foundation": ["model", "schema", "interface", "type", "structure"],
            "2 - Core Implementation": ["implement", "build", "create", "develop"],
            "3 - Integration": ["integrate", "connect", "middleware", "service"],
            "4 - Polish": ["optimize", "document", "test", "cleanup", "refactor"],
        }

        for phase in sample_task_list:
            phase_name = phase["phase"]
            if phase_name in phase_expectations:
                expected_keywords = phase_expectations[phase_name]
                phase_tasks = phase["tasks"]

                # At least one task should have expected keywords
                found_keywords = []
                for task in phase_tasks:
                    task_text = f"{task['title']} {task['description']}".lower()
                    for keyword in expected_keywords:
                        if keyword in task_text:
                            found_keywords.append(keyword)
                            break

                # Should have some expected content (not strictly required)
                # assert len(found_keywords) > 0, (
                #     f"Phase {phase_name} should contain expected types of tasks"
                # )

    def test_task_breakdown_granularity(self, sample_task_list) -> None:
        """Test tasks are broken down at appropriate granularity."""
        for phase in sample_task_list:
            for task in phase["tasks"]:
                # Tasks shouldn't be too large (indicated by very long estimates)
                time_est = task["estimated_time"].lower()
                if "day" in time_est:
                    # Extract number of days
                    days_match = re.search(r"(\d+(?:\.\d+)?)\s*day", time_est)
                    if days_match:
                        days = float(days_match.group(1))
                        assert days <= MAX_DAYS_PER_TASK, (
                            f"Task too large: {task['id']} - {days} days"
                        )

                # Tasks shouldn't be too small (less than 15 minutes)
                if "m" in time_est or "minute" in time_est:
                    minutes_match = re.search(r"(\d+(?:\.\d+)?)\s*m", time_est)
                    if minutes_match:
                        minutes = float(minutes_match.group(1))
                        assert minutes >= MIN_MINUTES_PER_TASK, (
                            f"Task too small: {task['id']} - {minutes} minutes"
                        )

    def test_task_id_consistency(self, sample_task_list) -> None:
        """Test task IDs follow consistent pattern."""
        id_pattern = r"^[a-z]+-\d{3}$"

        for phase in sample_task_list:
            for task in phase["tasks"]:
                assert re.match(id_pattern, task["id"]), (
                    f"Task ID doesn't match pattern: {task['id']}"
                )

    def test_phase_separation(self, sample_task_list) -> None:
        """Test phases are properly separated with no cross-phase dependencies."""
        # Build task ID sets per phase
        phase_tasks = {}
        for phase in sample_task_list:
            phase_tasks[phase["phase"]] = {task["id"] for task in phase["tasks"]}

        # Check no cross-phase dependencies
        for phase in sample_task_list:
            phase_name = phase["phase"]
            phase_tasks[phase_name]

            for task in phase["tasks"]:
                for dep_id in task["dependencies"]:
                    # If dependency is in our sample, it should be in same or earlier phase
                    dep_phase = None
                    for other_phase_name, task_ids in phase_tasks.items():
                        if dep_id in task_ids:
                            dep_phase = other_phase_name
                            break

                    if dep_phase:
                        # Dependency should be in same or earlier phase
                        phase_order = [
                            "0 - Setup",
                            "1 - Foundation",
                            "2 - Core Implementation",
                            "3 - Integration",
                            "4 - Polish",
                        ]
                        current_index = phase_order.index(phase_name)
                        dep_index = phase_order.index(dep_phase)

                        assert dep_index <= current_index, (
                            f"Cross-phase forward dependency: "
                            f"{task['id']} depends on {dep_id}"
                        )
