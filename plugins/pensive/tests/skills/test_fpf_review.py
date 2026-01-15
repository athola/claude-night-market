"""Tests for fpf-review skill scoring and analysis logic.

This module tests the FPF (Functional, Practical, Foundation) architecture
review methodology, including perspective analysis, scoring, and report
generation logic.

Following TDD/BDD principles to ensure the three perspectives are
evaluated correctly and findings are properly prioritized.
"""

import pytest


class TestFunctionalPerspective:
    """Feature: Functional perspective evaluates what the system does.

    As an architecture reviewer
    I want to analyze system capabilities and behaviors
    So that I can identify feature gaps and integration issues
    """

    @pytest.fixture
    def sample_feature_inventory(self):
        """Sample feature inventory for analysis."""
        return {
            "authentication": {
                "status": "complete",
                "capabilities": ["login", "logout", "token_refresh"],
                "integration_points": ["user_service", "session_store"],
            },
            "authorization": {
                "status": "partial",
                "capabilities": ["role_check"],
                "missing": ["permission_inheritance", "audit_logging"],
                "integration_points": ["policy_engine"],
            },
            "user_management": {
                "status": "complete",
                "capabilities": ["create", "read", "update", "delete"],
                "integration_points": ["database", "cache"],
            },
        }

    @pytest.fixture
    def sample_behavior_traces(self):
        """Sample behavior traces for end-to-end analysis."""
        return [
            {
                "name": "user_login_flow",
                "steps": ["validate_credentials", "create_session", "return_token"],
                "success_rate": 0.99,
                "edge_cases_covered": True,
            },
            {
                "name": "password_reset_flow",
                "steps": ["request_reset", "validate_token", "update_password"],
                "success_rate": 0.95,
                "edge_cases_covered": False,
            },
        ]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_feature_completeness_score(self, sample_feature_inventory) -> None:
        """Scenario: Feature completeness is scored from inventory.

        Given a feature inventory with status indicators
        When calculating feature completeness
        Then it should return percentage of complete features.
        """
        # Arrange
        inventory = sample_feature_inventory

        # Act
        total_features = len(inventory)
        complete_features = sum(
            1 for f in inventory.values() if f["status"] == "complete"
        )
        completeness = complete_features / total_features

        # Assert
        assert completeness == 2 / 3  # 2 complete out of 3
        assert abs(completeness - 0.667) < 0.01

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_capability_gap_detection(self, sample_feature_inventory) -> None:
        """Scenario: Capability gaps are identified from partial features.

        Given a feature inventory with partial features
        When analyzing for gaps
        Then it should list missing capabilities.
        """
        # Arrange
        inventory = sample_feature_inventory

        # Act
        gaps = []
        for name, feature in inventory.items():
            if feature["status"] == "partial" and "missing" in feature:
                gaps.extend(
                    {"feature": name, "missing": cap} for cap in feature["missing"]
                )

        # Assert
        assert len(gaps) == 2
        assert gaps[0]["feature"] == "authorization"
        assert "permission_inheritance" in [g["missing"] for g in gaps]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_integration_point_analysis(self, sample_feature_inventory) -> None:
        """Scenario: Integration points are aggregated across features.

        Given a feature inventory with integration points
        When analyzing integrations
        Then it should provide a dependency map.
        """
        # Arrange
        inventory = sample_feature_inventory

        # Act
        all_integrations = set()
        for feature in inventory.values():
            all_integrations.update(feature.get("integration_points", []))

        # Assert
        expected = {
            "user_service",
            "session_store",
            "policy_engine",
            "database",
            "cache",
        }
        assert all_integrations == expected
        assert len(all_integrations) == 5

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_behavior_trace_analysis(self, sample_behavior_traces) -> None:
        """Scenario: Behavior traces identify edge case coverage.

        Given behavior traces with success rates
        When analyzing traces
        Then it should flag flows with uncovered edge cases.
        """
        # Arrange
        traces = sample_behavior_traces

        # Act
        uncovered_flows = [t for t in traces if not t["edge_cases_covered"]]
        avg_success_rate = sum(t["success_rate"] for t in traces) / len(traces)

        # Assert
        assert len(uncovered_flows) == 1
        assert uncovered_flows[0]["name"] == "password_reset_flow"
        assert abs(avg_success_rate - 0.97) < 0.01


class TestPracticalPerspective:
    """Feature: Practical perspective evaluates how well the system works.

    As an architecture reviewer
    I want to analyze performance, usability, and operations
    So that I can identify practical improvements
    """

    @pytest.fixture
    def sample_performance_metrics(self):
        """Sample performance metrics for analysis."""
        return {
            "api_latency": {
                "p50": 45,  # ms
                "p95": 120,
                "p99": 350,
                "target_p95": 100,
            },
            "throughput": {
                "current": 1200,  # req/s
                "target": 1000,
                "headroom": 0.2,
            },
            "resource_usage": {
                "cpu_avg": 0.45,
                "memory_avg": 0.72,
                "cpu_peak": 0.85,
                "memory_peak": 0.91,
            },
        }

    @pytest.fixture
    def sample_usability_issues(self):
        """Sample usability issues for DX analysis."""
        return [
            {
                "id": "UX001",
                "area": "API design",
                "severity": "medium",
                "description": "Inconsistent error response format",
            },
            {
                "id": "UX002",
                "area": "documentation",
                "severity": "low",
                "description": "Missing examples in API docs",
            },
            {
                "id": "UX003",
                "area": "CLI",
                "severity": "high",
                "description": "Non-intuitive command structure",
            },
        ]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_performance_target_evaluation(self, sample_performance_metrics) -> None:
        """Scenario: Performance metrics are evaluated against targets.

        Given performance metrics with targets
        When evaluating performance
        Then it should identify metrics missing targets.
        """
        # Arrange
        metrics = sample_performance_metrics

        # Act
        latency_ok = (
            metrics["api_latency"]["p95"] <= metrics["api_latency"]["target_p95"]
        )
        throughput_ok = (
            metrics["throughput"]["current"] >= metrics["throughput"]["target"]
        )

        # Assert
        assert latency_ok is False  # 120 > 100
        assert throughput_ok is True  # 1200 >= 1000

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_resource_headroom_calculation(self, sample_performance_metrics) -> None:
        """Scenario: Resource headroom indicates scaling capacity.

        Given resource usage metrics
        When calculating headroom
        Then it should indicate available capacity.
        """
        # Arrange
        resources = sample_performance_metrics["resource_usage"]

        # Act
        cpu_headroom = 1.0 - resources["cpu_peak"]
        memory_headroom = 1.0 - resources["memory_peak"]

        # Assert
        assert abs(cpu_headroom - 0.15) < 0.01
        assert abs(memory_headroom - 0.09) < 0.01
        # Memory is the bottleneck
        assert memory_headroom < cpu_headroom

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_usability_severity_prioritization(self, sample_usability_issues) -> None:
        """Scenario: Usability issues are prioritized by severity.

        Given usability issues with severities
        When prioritizing
        Then high severity issues should come first.
        """
        # Arrange
        issues = sample_usability_issues
        severity_order = {"high": 0, "medium": 1, "low": 2}

        # Act
        sorted_issues = sorted(issues, key=lambda x: severity_order[x["severity"]])

        # Assert
        assert sorted_issues[0]["severity"] == "high"
        assert sorted_issues[0]["id"] == "UX003"
        assert sorted_issues[-1]["severity"] == "low"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_operational_readiness_checklist(self) -> None:
        """Scenario: Operational readiness is checked against criteria.

        Given an operational readiness checklist
        When evaluating system
        Then it should identify missing operational capabilities.
        """
        # Arrange
        required_capabilities = [
            "logging",
            "metrics",
            "alerting",
            "health_checks",
            "graceful_shutdown",
        ]
        system_capabilities = ["logging", "metrics", "health_checks"]

        # Act
        missing = set(required_capabilities) - set(system_capabilities)
        readiness_score = len(system_capabilities) / len(required_capabilities)

        # Assert
        assert missing == {"alerting", "graceful_shutdown"}
        assert readiness_score == 0.6


class TestFoundationPerspective:
    """Feature: Foundation perspective evaluates what the system is built on.

    As an architecture reviewer
    I want to analyze patterns, principles, and technical debt
    So that I can assess architectural health
    """

    @pytest.fixture
    def sample_pattern_analysis(self):
        """Sample pattern analysis results."""
        return {
            "patterns_used": [
                {
                    "name": "Repository Pattern",
                    "locations": ["src/repos/"],
                    "assessment": "appropriate",
                },
                {
                    "name": "Singleton",
                    "locations": ["src/config.py", "src/logger.py"],
                    "assessment": "appropriate",
                },
                {
                    "name": "God Object",
                    "locations": ["src/utils.py"],
                    "assessment": "problematic",
                },
            ],
            "patterns_missing": ["Circuit Breaker", "Retry with Backoff"],
        }

    @pytest.fixture
    def sample_principle_adherence(self):
        """Sample SOLID principle adherence scores."""
        return {
            "single_responsibility": 0.8,
            "open_closed": 0.6,
            "liskov_substitution": 0.9,
            "interface_segregation": 0.7,
            "dependency_inversion": 0.5,
        }

    @pytest.fixture
    def sample_tech_debt_inventory(self):
        """Sample technical debt inventory."""
        return [
            {
                "id": "TD001",
                "description": "Legacy authentication module",
                "severity": "high",
                "effort": "large",
                "age_days": 180,
            },
            {
                "id": "TD002",
                "description": "Missing test coverage in utils",
                "severity": "medium",
                "effort": "small",
                "age_days": 30,
            },
            {
                "id": "TD003",
                "description": "Outdated dependency versions",
                "severity": "medium",
                "effort": "medium",
                "age_days": 90,
            },
        ]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_pattern_assessment_scoring(self, sample_pattern_analysis) -> None:
        """Scenario: Pattern usage is scored by appropriateness.

        Given pattern analysis results
        When scoring patterns
        Then problematic patterns should reduce score.
        """
        # Arrange
        patterns = sample_pattern_analysis["patterns_used"]
        assessment_scores = {"appropriate": 1.0, "problematic": 0.0, "neutral": 0.5}

        # Act
        total_score = sum(assessment_scores[p["assessment"]] for p in patterns)
        pattern_score = total_score / len(patterns)

        # Assert
        assert pattern_score == 2 / 3  # 2 appropriate, 1 problematic
        assert abs(pattern_score - 0.667) < 0.01

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_solid_principle_average(self, sample_principle_adherence) -> None:
        """Scenario: SOLID adherence is averaged across principles.

        Given principle adherence scores
        When calculating overall adherence
        Then it should be the weighted average.
        """
        # Arrange
        principles = sample_principle_adherence

        # Act
        avg_adherence = sum(principles.values()) / len(principles)
        weakest = min(principles, key=principles.get)

        # Assert
        assert abs(avg_adherence - 0.7) < 0.01  # (0.8+0.6+0.9+0.7+0.5)/5
        assert weakest == "dependency_inversion"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tech_debt_priority_calculation(self, sample_tech_debt_inventory) -> None:
        """Scenario: Tech debt is prioritized by severity and effort.

        Given technical debt items
        When calculating priority
        Then high severity + low effort items rank highest.
        """
        # Arrange
        debt = sample_tech_debt_inventory
        severity_weight = {"high": 3, "medium": 2, "low": 1}
        effort_weight = {"small": 3, "medium": 2, "large": 1}

        # Act
        def priority_score(item):
            return severity_weight[item["severity"]] * effort_weight[item["effort"]]

        prioritized = sorted(debt, key=priority_score, reverse=True)

        # Assert
        # TD002: medium(2) * small(3) = 6
        # TD003: medium(2) * medium(2) = 4
        # TD001: high(3) * large(1) = 3
        assert prioritized[0]["id"] == "TD002"  # Best ROI
        assert prioritized[-1]["id"] == "TD001"  # High effort despite high severity

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_debt_age_impact(self, sample_tech_debt_inventory) -> None:
        """Scenario: Older debt items are flagged for attention.

        Given technical debt with age data
        When analyzing debt age
        Then items older than threshold should be flagged.
        """
        # Arrange
        debt = sample_tech_debt_inventory
        age_threshold_days = 60

        # Act
        old_debt = [d for d in debt if d["age_days"] > age_threshold_days]
        avg_age = sum(d["age_days"] for d in debt) / len(debt)

        # Assert
        assert len(old_debt) == 2  # TD001 (180) and TD003 (90)
        assert avg_age == 100  # (180+30+90)/3


class TestFPFSynthesis:
    """Feature: FPF perspectives are synthesized into recommendations.

    As an architecture reviewer
    I want findings from all perspectives combined
    So that I can provide actionable recommendations
    """

    @pytest.fixture
    def sample_perspective_findings(self):
        """Sample findings from all three perspectives."""
        return {
            "functional": {
                "score": 0.75,
                "critical_gaps": ["permission_inheritance"],
                "finding_count": 3,
            },
            "practical": {
                "score": 0.65,
                "critical_gaps": ["alerting", "latency_target"],
                "finding_count": 5,
            },
            "foundation": {
                "score": 0.70,
                "critical_gaps": ["dependency_inversion", "god_object"],
                "finding_count": 4,
            },
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_overall_health_score(self, sample_perspective_findings) -> None:
        """Scenario: Overall health score combines all perspectives.

        Given scores from all three perspectives
        When calculating overall health
        Then it should be the weighted average.
        """
        # Arrange
        findings = sample_perspective_findings
        weights = {"functional": 0.4, "practical": 0.35, "foundation": 0.25}

        # Act
        overall = sum(findings[p]["score"] * weights[p] for p in findings)

        # Assert
        expected = 0.75 * 0.4 + 0.65 * 0.35 + 0.70 * 0.25
        assert abs(overall - expected) < 0.01
        assert abs(overall - 0.7025) < 0.01

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_cross_perspective_issue_detection(
        self, sample_perspective_findings
    ) -> None:
        """Scenario: Issues spanning perspectives are identified.

        Given findings from all perspectives
        When analyzing cross-cutting concerns
        Then related issues should be grouped.
        """
        # Arrange
        findings = sample_perspective_findings

        # Act
        all_gaps = []
        for perspective, data in findings.items():
            for gap in data["critical_gaps"]:
                all_gaps.append({"perspective": perspective, "gap": gap})

        total_critical = len(all_gaps)

        # Assert
        assert total_critical == 5
        # Practical has most critical gaps
        practical_gaps = [g for g in all_gaps if g["perspective"] == "practical"]
        assert len(practical_gaps) == 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recommendation_prioritization(self) -> None:
        """Scenario: Recommendations are prioritized by impact and effort.

        Given recommendations with impact and effort estimates
        When prioritizing
        Then high impact + low effort items rank highest.
        """
        # Arrange
        recommendations = [
            {"id": "R1", "impact": "high", "effort": "low", "perspective": "practical"},
            {
                "id": "R2",
                "impact": "high",
                "effort": "high",
                "perspective": "foundation",
            },
            {
                "id": "R3",
                "impact": "medium",
                "effort": "low",
                "perspective": "functional",
            },
            {"id": "R4", "impact": "low", "effort": "low", "perspective": "practical"},
        ]
        impact_score = {"high": 3, "medium": 2, "low": 1}
        effort_score = {"low": 3, "medium": 2, "high": 1}

        # Act
        def priority(rec):
            return impact_score[rec["impact"]] * effort_score[rec["effort"]]

        sorted_recs = sorted(recommendations, key=priority, reverse=True)

        # Assert
        assert sorted_recs[0]["id"] == "R1"  # high impact, low effort = 9
        assert sorted_recs[1]["id"] == "R3"  # medium impact, low effort = 6
        # R2 and R4 both have score 3, so check they're in the bottom two
        bottom_ids = {sorted_recs[-1]["id"], sorted_recs[-2]["id"]}
        assert bottom_ids == {"R2", "R4"}  # Both score 3 (high*high=3, low*low=3)

    @pytest.mark.unit
    def test_report_section_generation(self) -> None:
        """Scenario: Report sections are generated from findings.

        Given findings and recommendations
        When generating report
        Then it should have required sections.
        """
        # Arrange
        required_sections = [
            "executive_summary",
            "functional_perspective",
            "practical_perspective",
            "foundation_perspective",
            "recommendations",
            "action_items",
        ]

        # Act - simulate report structure
        report = {section: f"Content for {section}" for section in required_sections}

        # Assert
        assert all(section in report for section in required_sections)
        assert len(report) == 6


class TestFPFConfiguration:
    """Feature: FPF review is configurable.

    As a reviewer
    I want to configure scope and depth
    So that I can focus the review appropriately
    """

    @pytest.mark.unit
    def test_scope_filtering(self) -> None:
        """Scenario: Review scope can be filtered to specific paths.

        Given include/exclude path patterns
        When filtering files
        Then only matching files are reviewed.
        """
        # Arrange
        all_files = [
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "docs/api.md",
            "node_modules/pkg/index.js",
        ]
        include = ["src/"]
        exclude = ["node_modules/", "docs/"]

        # Act
        def matches_scope(path):
            if any(path.startswith(e) for e in exclude):
                return False
            if include:
                return any(path.startswith(i) for i in include)
            return True

        filtered = [f for f in all_files if matches_scope(f)]

        # Assert
        assert filtered == ["src/main.py", "src/utils.py"]
        assert len(filtered) == 2

    @pytest.mark.unit
    def test_depth_configuration(self) -> None:
        """Scenario: Review depth affects analysis detail.

        Given depth configuration (full/summary)
        When analyzing
        Then detail level should match depth.
        """
        # Arrange
        depth_configs = {
            "full": {"include_code_snippets": True, "max_findings": None},
            "summary": {"include_code_snippets": False, "max_findings": 10},
        }

        # Assert
        assert depth_configs["full"]["include_code_snippets"] is True
        assert depth_configs["summary"]["max_findings"] == 10

    @pytest.mark.unit
    def test_severity_threshold_filtering(self) -> None:
        """Scenario: Findings can be filtered by severity threshold.

        Given a severity threshold
        When filtering findings
        Then only findings at or above threshold are included.
        """
        # Arrange
        findings = [
            {"id": "F1", "severity": "high"},
            {"id": "F2", "severity": "medium"},
            {"id": "F3", "severity": "low"},
            {"id": "F4", "severity": "medium"},
        ]
        severity_order = {"high": 3, "medium": 2, "low": 1}
        threshold = "medium"

        # Act
        filtered = [
            f
            for f in findings
            if severity_order[f["severity"]] >= severity_order[threshold]
        ]

        # Assert
        assert len(filtered) == 3  # high + 2 medium
        assert all(f["severity"] != "low" for f in filtered)
