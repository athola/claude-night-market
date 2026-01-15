"""Tests for workflow-monitor skill detection and analysis logic.

This module tests the workflow monitoring functionality including
error detection, efficiency analysis, and issue creation logic.

Following TDD/BDD principles to ensure workflow issues are properly
detected, classified, and reported.
"""

from collections import Counter

import pytest


class TestErrorDetection:
    """Feature: Workflow errors are detected and classified.

    As a workflow operator
    I want errors automatically detected
    So that workflow issues can be addressed systematically
    """

    @pytest.fixture
    def sample_command_results(self):
        """Sample command execution results for analysis."""
        return [
            {
                "command": "npm install",
                "exit_code": 0,
                "duration_ms": 5000,
                "output_lines": 150,
            },
            {
                "command": "npm test",
                "exit_code": 1,
                "duration_ms": 12000,
                "output_lines": 500,
                "error": "Test suite failed: 3 tests failed",
            },
            {
                "command": "git push",
                "exit_code": 128,
                "duration_ms": 2000,
                "output_lines": 10,
                "error": "remote: Permission denied",
            },
        ]

    @pytest.fixture
    def sample_timeout_events(self):
        """Sample timeout events for analysis."""
        return [
            {
                "command": "npm run build",
                "timeout_ms": 120000,
                "actual_ms": 125000,
                "event": "timeout",
            },
            {
                "command": "docker build .",
                "timeout_ms": 300000,
                "actual_ms": 310000,
                "event": "timeout",
            },
        ]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_failure_detection(self, sample_command_results) -> None:
        """Scenario: Command failures are detected by exit code.

        Given command execution results
        When analyzing for failures
        Then commands with exit_code > 0 are flagged.
        """
        # Arrange
        results = sample_command_results

        # Act
        failures = [r for r in results if r["exit_code"] > 0]

        # Assert
        assert len(failures) == 2
        assert failures[0]["command"] == "npm test"
        assert failures[1]["command"] == "git push"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_failure_severity_classification(self, sample_command_results) -> None:
        """Scenario: Failures are classified by severity.

        Given command failures
        When classifying severity
        Then exit codes map to severity levels.
        """
        # Arrange
        results = sample_command_results

        # Act
        def classify_severity(exit_code: int) -> str:
            if exit_code == 0:
                return "none"
            elif exit_code == 1:
                return "high"  # Test/lint failure
            elif exit_code >= 128:
                return "high"  # System/permission error
            else:
                return "medium"

        severities = {r["command"]: classify_severity(r["exit_code"]) for r in results}

        # Assert
        assert severities["npm install"] == "none"
        assert severities["npm test"] == "high"
        assert severities["git push"] == "high"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_timeout_detection(self, sample_timeout_events) -> None:
        """Scenario: Timeout events are detected.

        Given command execution events
        When analyzing for timeouts
        Then commands exceeding timeout are flagged.
        """
        # Arrange
        events = sample_timeout_events

        # Act
        timeouts = [e for e in events if e["event"] == "timeout"]
        exceeded_by = [e["actual_ms"] - e["timeout_ms"] for e in timeouts]

        # Assert
        assert len(timeouts) == 2
        assert exceeded_by[0] == 5000  # 5 seconds over
        assert exceeded_by[1] == 10000  # 10 seconds over

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_retry_loop_detection(self) -> None:
        """Scenario: Retry loops are detected as patterns.

        Given command history
        When analyzing for retries
        Then repeated commands >3 times are flagged.
        """
        # Arrange
        command_history = [
            "git fetch origin",
            "git fetch origin",
            "git fetch origin",
            "git fetch origin",  # 4th retry
            "npm install",
            "npm install",  # Only 2 retries - OK
        ]
        retry_threshold = 3

        # Act
        command_counts = Counter(command_history)
        retry_loops = {
            cmd: count
            for cmd, count in command_counts.items()
            if count > retry_threshold
        }

        # Assert
        assert "git fetch origin" in retry_loops
        assert retry_loops["git fetch origin"] == 4
        assert "npm install" not in retry_loops

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_context_exhaustion_detection(self) -> None:
        """Scenario: Context exhaustion is flagged at threshold.

        Given context usage metrics
        When usage exceeds threshold
        Then context exhaustion is flagged.
        """
        # Arrange
        context_metrics = {
            "total_tokens": 200000,
            "used_tokens": 185000,
            "threshold_percent": 0.90,
        }

        # Act
        usage_percent = context_metrics["used_tokens"] / context_metrics["total_tokens"]
        is_exhausted = usage_percent >= context_metrics["threshold_percent"]

        # Assert
        assert abs(usage_percent - 0.925) < 0.01
        assert is_exhausted is True


class TestEfficiencyAnalysis:
    """Feature: Workflow efficiency is analyzed and scored.

    As a workflow optimizer
    I want inefficiencies identified
    So that workflows can be improved
    """

    @pytest.fixture
    def sample_execution_log(self):
        """Sample execution log for efficiency analysis."""
        return [
            {"tool": "Read", "target": "src/main.py", "tokens": 500},
            {"tool": "Read", "target": "src/main.py", "tokens": 500},  # Redundant
            {"tool": "Read", "target": "src/utils.py", "tokens": 300},
            {"tool": "Bash", "command": "npm install", "output_lines": 1500},  # Verbose
            {"tool": "Bash", "command": "git status", "output_lines": 10},
            {"tool": "Read", "target": "src/main.py", "tokens": 500},  # 3rd read!
        ]

    @pytest.fixture
    def sample_parallel_opportunity(self):
        """Sample tasks that could be parallelized."""
        return [
            {"task": "lint_python", "duration_ms": 3000, "depends_on": []},
            {"task": "lint_js", "duration_ms": 2500, "depends_on": []},
            {"task": "typecheck", "duration_ms": 4000, "depends_on": []},
            {
                "task": "test",
                "duration_ms": 10000,
                "depends_on": ["lint_python", "typecheck"],
            },
        ]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_redundant_read_detection(self, sample_execution_log) -> None:
        """Scenario: Redundant file reads are detected.

        Given an execution log
        When analyzing read operations
        Then files read >2 times are flagged.
        """
        # Arrange
        log = sample_execution_log
        max_reads = 2

        # Act
        read_ops = [e for e in log if e["tool"] == "Read"]
        read_counts = Counter(e["target"] for e in read_ops)
        redundant = {f: c for f, c in read_counts.items() if c > max_reads}

        # Assert
        assert "src/main.py" in redundant
        assert redundant["src/main.py"] == 3
        assert "src/utils.py" not in redundant

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_verbose_output_detection(self, sample_execution_log) -> None:
        """Scenario: Verbose command output is flagged.

        Given command outputs
        When output exceeds threshold
        Then command is flagged as verbose.
        """
        # Arrange
        log = sample_execution_log
        verbose_threshold = 500

        # Act
        bash_ops = [e for e in log if e["tool"] == "Bash"]
        verbose_ops = [
            e for e in bash_ops if e.get("output_lines", 0) > verbose_threshold
        ]

        # Assert
        assert len(verbose_ops) == 1
        assert verbose_ops[0]["command"] == "npm install"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_parallel_opportunity_detection(self, sample_parallel_opportunity) -> None:
        """Scenario: Tasks that could run in parallel are identified.

        Given tasks with dependencies
        When analyzing for parallelization
        Then independent tasks are identified.
        """
        # Arrange
        tasks = sample_parallel_opportunity

        # Act
        independent = [t for t in tasks if not t["depends_on"]]
        potential_savings_ms = sum(t["duration_ms"] for t in independent) - max(
            t["duration_ms"] for t in independent
        )

        # Assert
        assert len(independent) == 3
        # Sequential: 3000+2500+4000 = 9500ms
        # Parallel: max(3000,2500,4000) = 4000ms
        # Savings: 9500-4000 = 5500ms
        assert potential_savings_ms == 5500

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_efficiency_score_calculation(self, sample_execution_log) -> None:
        """Scenario: Overall efficiency score is calculated.

        Given efficiency metrics
        When calculating score
        Then it reflects detected inefficiencies.
        """
        # Arrange
        log = sample_execution_log

        # Metrics
        read_ops = [e for e in log if e["tool"] == "Read"]
        read_counts = Counter(e["target"] for e in read_ops)
        redundant_reads = sum(1 for c in read_counts.values() if c > 2)

        bash_ops = [e for e in log if e["tool"] == "Bash"]
        verbose_commands = sum(1 for e in bash_ops if e.get("output_lines", 0) > 500)

        # Act - simple scoring model
        penalties = {
            "redundant_reads": redundant_reads * 0.10,
            "verbose_output": verbose_commands * 0.05,
        }
        total_penalty = sum(penalties.values())
        efficiency_score = max(0, 1.0 - total_penalty)

        # Assert
        assert penalties["redundant_reads"] == 0.10  # 1 file read 3 times
        assert penalties["verbose_output"] == 0.05  # 1 verbose command
        assert abs(efficiency_score - 0.85) < 0.01

    @pytest.mark.unit
    def test_over_fetching_detection(self) -> None:
        """Scenario: Over-fetching (reading entire files) is flagged.

        Given file read operations
        When offset/limit not used on large files
        Then over-fetching is flagged.
        """
        # Arrange
        read_ops = [
            {"file": "src/main.py", "lines": 50, "used_offset": False},  # Small, OK
            {
                "file": "src/large.py",
                "lines": 2000,
                "used_offset": False,
            },  # Large, issue
            {"file": "src/huge.py", "lines": 5000, "used_offset": True},  # Large but OK
        ]
        large_file_threshold = 500

        # Act
        over_fetched = [
            r
            for r in read_ops
            if r["lines"] > large_file_threshold and not r["used_offset"]
        ]

        # Assert
        assert len(over_fetched) == 1
        assert over_fetched[0]["file"] == "src/large.py"


class TestIssueCreation:
    """Feature: Workflow issues are formatted for GitHub.

    As a workflow maintainer
    I want issues auto-generated from detections
    So that improvements are tracked
    """

    @pytest.fixture
    def sample_detection(self):
        """Sample workflow issue detection."""
        return {
            "type": "command_failure",
            "command": "npm test",
            "exit_code": 1,
            "error": "3 tests failed",
            "session_id": "session-abc123",
            "timestamp": "2024-01-15T10:30:00Z",
        }

    @pytest.fixture
    def sample_efficiency_issue(self):
        """Sample efficiency issue detection."""
        return {
            "type": "verbose_output",
            "command": "npm install",
            "output_lines": 1500,
            "recommended_lines": 500,
            "suggestion": "Use --quiet flag",
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_issue_title_format(self, sample_detection) -> None:
        """Scenario: Issue titles follow standard format.

        Given a detection
        When generating issue title
        Then it should use conventional format.
        """
        # Arrange
        detection = sample_detection

        # Act
        type_prefix = {
            "command_failure": "fix(workflow)",
            "timeout": "fix(workflow)",
            "verbose_output": "perf(workflow)",
            "redundant_reads": "perf(workflow)",
        }
        prefix = type_prefix.get(detection["type"], "fix(workflow)")
        title = f"{prefix}: {detection['command']} - {detection['error']}"

        # Assert
        assert title == "fix(workflow): npm test - 3 tests failed"
        assert title.startswith("fix(workflow)")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_issue_labels_assignment(self, sample_detection) -> None:
        """Scenario: Issues get appropriate labels.

        Given a detection type
        When assigning labels
        Then relevant labels are included.
        """
        # Arrange
        detection = sample_detection
        type_labels = {
            "command_failure": ["workflow", "bug"],
            "timeout": ["workflow", "bug", "performance"],
            "verbose_output": ["workflow", "enhancement"],
            "redundant_reads": ["workflow", "enhancement"],
        }

        # Act
        labels = type_labels.get(detection["type"], ["workflow"])

        # Assert
        assert "workflow" in labels
        assert "bug" in labels  # command_failure is a bug

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_issue_body_structure(self, sample_detection) -> None:
        """Scenario: Issue body contains required sections.

        Given a detection
        When generating issue body
        Then it should have all required sections.
        """
        # Arrange
        detection = sample_detection
        required_sections = [
            "Background",
            "Problem",
            "Suggested Fix",
            "Acceptance Criteria",
        ]

        # Act - simulate body generation
        body_sections = {
            "Background": f"Detected during workflow execution on {detection['timestamp']}",
            "Problem": f"Command `{detection['command']}` failed with exit code {detection['exit_code']}",
            "Suggested Fix": "Review test failures and fix broken tests",
            "Acceptance Criteria": "- [ ] All tests pass\n- [ ] CI pipeline succeeds",
        }

        # Assert
        assert all(section in body_sections for section in required_sections)
        assert detection["command"] in body_sections["Problem"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_duplicate_detection(self) -> None:
        """Scenario: Duplicate issues are prevented.

        Given existing issues
        When checking for duplicates
        Then similar issues should be identified.
        """
        # Arrange
        existing_issues = [
            {"title": "fix(workflow): npm test - 3 tests failed", "state": "open"},
            {"title": "fix(workflow): git push - Permission denied", "state": "closed"},
            {"title": "perf(workflow): npm install verbose output", "state": "open"},
        ]
        new_issue_title = "fix(workflow): npm test - 3 tests failed"

        # Act
        def is_duplicate(title: str, issues: list) -> bool:
            return any(i["title"] == title and i["state"] == "open" for i in issues)

        # Assert
        assert is_duplicate(new_issue_title, existing_issues) is True
        assert is_duplicate("fix(workflow): new error", existing_issues) is False

    @pytest.mark.unit
    def test_rate_limiting(self) -> None:
        """Scenario: Issue creation is rate limited per session.

        Given session issue count
        When limit is reached
        Then new issues are blocked.
        """
        # Arrange
        session_issues = 5
        max_issues_per_session = 5

        # Act
        can_create = session_issues < max_issues_per_session

        # Assert
        assert can_create is False


class TestWorkflowConfiguration:
    """Feature: Workflow monitoring is configurable.

    As an operator
    I want to configure monitoring thresholds
    So that alerts match my needs
    """

    @pytest.fixture
    def default_config(self):
        """Return default workflow monitor configuration."""
        return {
            "enabled": True,
            "auto_create_issues": False,
            "severity_threshold": "medium",
            "efficiency_threshold": 0.7,
            "detection": {
                "command_failures": True,
                "timeouts": True,
                "retry_loops": True,
                "context_exhaustion": True,
                "tool_misuse": True,
            },
            "efficiency": {
                "verbose_output_limit": 500,
                "max_file_reads": 2,
                "parallel_detection": True,
            },
        }

    @pytest.mark.unit
    def test_severity_threshold_filtering(self, default_config) -> None:
        """Scenario: Only issues at/above threshold are reported.

        Given severity threshold configuration
        When filtering issues
        Then lower severity issues are excluded.
        """
        # Arrange
        issues = [
            {"id": "I1", "severity": "high"},
            {"id": "I2", "severity": "medium"},
            {"id": "I3", "severity": "low"},
        ]
        severity_order = {"high": 3, "medium": 2, "low": 1}
        threshold = default_config["severity_threshold"]

        # Act
        filtered = [
            i
            for i in issues
            if severity_order[i["severity"]] >= severity_order[threshold]
        ]

        # Assert
        assert len(filtered) == 2
        assert all(i["severity"] != "low" for i in filtered)

    @pytest.mark.unit
    def test_efficiency_threshold_flagging(self, default_config) -> None:
        """Scenario: Workflows below efficiency threshold are flagged.

        Given efficiency scores
        When below threshold
        Then workflow is flagged.
        """
        # Arrange
        workflow_scores = [
            {"session": "s1", "efficiency": 0.85},
            {"session": "s2", "efficiency": 0.65},
            {"session": "s3", "efficiency": 0.72},
        ]
        threshold = default_config["efficiency_threshold"]

        # Act
        flagged = [w for w in workflow_scores if w["efficiency"] < threshold]

        # Assert
        assert len(flagged) == 1
        assert flagged[0]["session"] == "s2"

    @pytest.mark.unit
    def test_detection_toggles(self, default_config) -> None:
        """Scenario: Detection types can be individually toggled.

        Given detection configuration
        When a detection is disabled
        Then that type is not checked.
        """
        # Arrange
        config = default_config.copy()
        config["detection"]["retry_loops"] = False

        # Act
        enabled_detections = [k for k, v in config["detection"].items() if v]

        # Assert
        assert "retry_loops" not in enabled_detections
        assert "command_failures" in enabled_detections
        assert len(enabled_detections) == 4

    @pytest.mark.unit
    def test_auto_create_requires_approval(self, default_config) -> None:
        """Scenario: Auto-create issues requires explicit opt-in.

        Given default configuration
        When checking auto_create_issues
        Then it should be disabled by default.
        """
        # Arrange
        config = default_config

        # Assert
        assert config["auto_create_issues"] is False


class TestEfficiencyReport:
    """Feature: Efficiency reports summarize workflow health.

    As a team lead
    I want efficiency reports
    So that I can track workflow improvements over time
    """

    @pytest.fixture
    def sample_session_metrics(self):
        """Sample session metrics for report."""
        return {
            "session_id": "session-xyz789",
            "duration_seconds": 754,
            "issues_detected": [
                {"type": "verbose_output", "count": 3},
                {"type": "redundant_reads", "count": 2},
                {"type": "sequential_tasks", "count": 1},
            ],
            "efficiency_score": 0.72,
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_report_summary_generation(self, sample_session_metrics) -> None:
        """Scenario: Report summary captures key metrics.

        Given session metrics
        When generating summary
        Then it should include session ID, duration, and score.
        """
        # Arrange
        metrics = sample_session_metrics

        # Act
        summary = {
            "session": metrics["session_id"],
            "duration": f"{metrics['duration_seconds'] // 60}m {metrics['duration_seconds'] % 60}s",
            "score": f"{metrics['efficiency_score']:.0%}",
        }

        # Assert
        assert summary["session"] == "session-xyz789"
        assert summary["duration"] == "12m 34s"
        assert summary["score"] == "72%"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_issue_impact_classification(self, sample_session_metrics) -> None:
        """Scenario: Issues are classified by impact.

        Given detected issues
        When classifying impact
        Then issues are categorized appropriately.
        """
        # Arrange
        issues = sample_session_metrics["issues_detected"]
        impact_map = {
            "verbose_output": "medium",
            "redundant_reads": "low",
            "sequential_tasks": "medium",
            "command_failure": "high",
            "timeout": "high",
        }

        # Act
        classified = [
            {**issue, "impact": impact_map.get(issue["type"], "low")}
            for issue in issues
        ]

        # Assert
        assert classified[0]["impact"] == "medium"
        assert classified[1]["impact"] == "low"

    @pytest.mark.unit
    def test_recommendation_generation(self) -> None:
        """Scenario: Recommendations are generated from issues.

        Given detected issue types
        When generating recommendations
        Then actionable suggestions are provided.
        """
        # Arrange
        issue_recommendations = {
            "verbose_output": "Use --quiet flags for npm/pip commands",
            "redundant_reads": "Cache file contents instead of re-reading",
            "sequential_tasks": "Parallelize independent file operations",
        }
        detected_issues = ["verbose_output", "redundant_reads"]

        # Act
        recommendations = [
            issue_recommendations[issue]
            for issue in detected_issues
            if issue in issue_recommendations
        ]

        # Assert
        assert len(recommendations) == 2
        assert "cache" in recommendations[1].lower()
