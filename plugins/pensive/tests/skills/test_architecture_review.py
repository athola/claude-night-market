"""Unit tests for the architecture review skill.

Tests system design analysis, ADR compliance assessment,
and architectural pattern validation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

# Import the skill we're testing
from pensive.skills.architecture_review import ArchitectureReviewSkill


class TestArchitectureReviewSkill:
    """Test suite for ArchitectureReviewSkill business logic."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = ArchitectureReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path(tempfile.gettempdir()) / "test_repo"
        self.mock_context.working_dir = Path(tempfile.gettempdir()) / "test_repo"

    @pytest.mark.unit
    def test_detects_layered_architecture(self, mock_skill_context) -> None:
        """Given layered architecture, when skill analyzes, then identifies layer structure."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "src/controllers/user_controller.py",
            "src/services/user_service.py",
            "src/repositories/user_repository.py",
            "src/models/user.py",
        ]

        # Act
        architecture = self.skill.detect_architecture_pattern(mock_skill_context)

        # Assert
        assert "layered" in architecture["patterns"]
        assert "controllers" in architecture["layers"]
        assert "services" in architecture["layers"]
        assert "repositories" in architecture["layers"]
        assert "models" in architecture["layers"]

    @pytest.mark.unit
    def test_detects_hexagonal_architecture(self, mock_skill_context) -> None:
        """Given hexagonal architecture, when skill analyzes, then identifies ports and adapters."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "src/ports/input/user_port.py",
            "src/ports/output/database_port.py",
            "src/adapters/database/mongodb_adapter.py",
            "src/adapters/web/rest_adapter.py",
            "src/core/domain/user.py",
        ]

        # Act
        architecture = self.skill.detect_architecture_pattern(mock_skill_context)

        # Assert
        assert "hexagonal" in architecture["patterns"]
        assert "ports" in architecture["components"]
        assert "adapters" in architecture["components"]
        assert "domain" in architecture["components"]

    @pytest.mark.unit
    def test_detects_microservices_architecture(self, mock_skill_context) -> None:
        """Given microservices architecture, when skill analyzes, then identifies service boundaries."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "services/user-service/src/main.py",
            "services/order-service/src/main.py",
            "services/payment-service/src/main.py",
            "services/notification-service/src/main.py",
            "api-gateway/src/main.py",
        ]

        # Act
        architecture = self.skill.detect_architecture_pattern(mock_skill_context)

        # Assert
        assert "microservices" in architecture["patterns"]
        assert len(architecture["services"]) >= 4
        assert "api-gateway" in [
            service["name"] for service in architecture["services"]
        ]

    @pytest.mark.unit
    def test_detects_event_driven_architecture(self, mock_skill_context) -> None:
        """Given event-driven architecture, when skill analyzes, then identifies event components."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "src/events/user_created_event.py",
            "src/handlers/user_event_handler.py",
            "src/publishers/event_publisher.py",
            "src/subscribers/event_subscriber.py",
            "src/event_bus/event_bus.py",
        ]

        # Act
        architecture = self.skill.detect_architecture_pattern(mock_skill_context)

        # Assert
        assert "event_driven" in architecture["patterns"]
        assert "events" in architecture["components"]
        assert "handlers" in architecture["components"]
        assert "publishers" in architecture["components"]

    @pytest.mark.unit
    def test_analyzes_coupling_between_modules(self, mock_skill_context) -> None:
        """Given module dependencies, when skill analyzes, then assesses coupling levels."""
        # Arrange
        dependencies = [
            {"from": "controller.py", "to": "service.py", "type": "import"},
            {"from": "service.py", "to": "repository.py", "type": "import"},
            {"from": "repository.py", "to": "database.py", "type": "import"},
            {
                "from": "controller.py",
                "to": "database.py",
                "type": "import",
            },  # Violates layering
        ]

        mock_skill_context.analyze_dependencies.return_value = dependencies

        # Act
        coupling_analysis = self.skill.analyze_coupling(mock_skill_context)

        # Assert
        assert "coupling_score" in coupling_analysis
        assert "violations" in coupling_analysis
        assert (
            len(coupling_analysis["violations"]) >= 1
        )  # Should detect controller directly accessing database
        assert coupling_analysis["coupling_score"] > 0

    @pytest.mark.unit
    def test_analyzes_cohesion_within_modules(self, mock_skill_context) -> None:
        """Given module content, when skill analyzes, then assesses cohesion levels."""
        # Arrange
        module_content = """
        class UserService:
            def create_user(self, user_data): pass
            def update_user(self, id, data): pass
            def delete_user(self, id): pass
            def send_notification_email(self, user, message): pass  # Low cohesion - notification logic
            def calculate_invoice_total(self, user_id): pass      # Low cohesion - billing logic
            def validate_user_data(self, data): pass
        """

        mock_skill_context.get_file_content.return_value = module_content

        # Act
        cohesion_analysis = self.skill.analyze_cohesion(
            mock_skill_context,
            "user_service.py",
        )

        # Assert
        assert "cohesion_score" in cohesion_analysis
        assert "responsibilities" in cohesion_analysis
        assert cohesion_analysis["cohesion_score"] < 0.8  # Should detect low cohesion
        assert (
            len(cohesion_analysis["responsibilities"]) >= 3
        )  # Should detect multiple responsibilities

    @pytest.mark.unit
    def test_checks_separation_of_concerns(self, mock_skill_context) -> None:
        """Given mixed responsibilities, when skill analyzes, then flags SoC violations."""
        # Arrange
        mixed_concerns_code = """
        class UserHandler:
            def handle_request(self, request):
                # Business logic
                user = self.validate_user(request.json)

                # Data access
                db_connection = sqlite3.connect('users.db')
                cursor = db_connection.cursor()
                cursor.execute("INSERT INTO users VALUES (?)", (user.name,))

                # HTTP response formatting
                response = Response(f"User {user.name} created", status=201)

                # Logging
                print(f"User created: {user.name}")

                return response
        """

        mock_skill_context.get_file_content.return_value = mixed_concerns_code

        # Act
        soc_violations = self.skill.check_separation_of_concerns(
            mock_skill_context,
            "handler.py",
        )

        # Assert
        assert len(soc_violations) > 0
        concern_types = [v["type"] for v in soc_violations]
        assert "data_access" in concern_types
        assert "business_logic" in concern_types
        assert "presentation" in concern_types

    @pytest.mark.unit
    def test_validates_dependency_inversion_principle(self, mock_skill_context) -> None:
        """Given dependency violations, when skill analyzes, then flags DIP violations."""
        # Arrange
        violating_code = """
        class OrderService:
            def __init__(self):
                self.database = MySQLDatabase()  # Direct dependency on concrete class
                self.email_sender = SMTPEmailSender()  # Direct dependency on concrete class

            def process_order(self, order):
                self.database.save(order)
                self.email_sender.send_order_confirmation(order)
        """

        mock_skill_context.get_file_content.return_value = violating_code

        # Act
        dip_violations = self.skill.check_dependency_inversion(
            mock_skill_context,
            "order_service.py",
        )

        # Assert
        assert len(dip_violations) > 0
        concrete_deps = [v for v in dip_violations if "concrete" in v["issue"].lower()]
        assert (
            len(concrete_deps) >= 2
        )  # Should detect MySQLDatabase and SMTPEmailSender

    @pytest.mark.unit
    def test_analyzes_sOLID_principles_compliance(self, mock_skill_context) -> None:
        """Given code implementation, when skill analyzes, then checks SOLID principles."""
        # Arrange
        code_with_violations = """
        # Single Responsibility Violation
        class UserManager:
            def create_user(self, user): pass
            def send_email(self, user, message): pass
            def generate_report(self, users): pass
            def backup_database(self): pass

        # Open/Closed Violation
        class Shape:
            def draw(self):
                if self.type == "circle":
                    # draw circle
                elif self.type == "square":
                    # draw square
                # Need to modify for new shapes

        # Liskov Substitution Violation
        class Rectangle:
            def set_width(self, w): self.width = w
            def set_height(self, h): self.height = h

        class Square(Rectangle):
            def set_width(self, w):
                self.width = w
                self.height = w  # Violates rectangle behavior
        """

        mock_skill_context.get_file_content.return_value = code_with_violations

        # Act
        solid_analysis = self.skill.analyze_solid_principles(
            mock_skill_context,
            "shapes.py",
        )

        # Assert
        assert "single_responsibility" in solid_analysis
        assert "open_closed" in solid_analysis
        assert "liskov_substitution" in solid_analysis
        assert solid_analysis["single_responsibility"]["violations"] > 0
        assert solid_analysis["open_closed"]["violations"] > 0
        assert solid_analysis["liskov_substitution"]["violations"] > 0

    @pytest.mark.unit
    def test_checks_architectural_decision_records(self, mock_skill_context) -> None:
        """Given ADR files, when skill analyzes, then validates ADR structure and compliance."""
        # Arrange
        adr_files = [
            "docs/adr/0001-use-microservices.md",
            "docs/adr/0002-database-selection.md",
            "docs/adr/0003-communication-pattern.md",
        ]

        mock_adr_content = """
        # ADR-0001: Use Microservices Architecture

        ## Status
        Accepted

        ## Context
        We need to scale our application...

        ## Decision
        We will use microservices architecture...

        ## Consequences
        - Increased deployment complexity
        - Better team autonomy
        - Service mesh required
        """

        mock_skill_context.get_files.return_value = adr_files
        mock_skill_context.get_file_content.return_value = mock_adr_content

        # Act
        adr_analysis = self.skill.analyze_adrs(mock_skill_context)

        # Assert
        assert "total_adrs" in adr_analysis
        assert adr_analysis["total_adrs"] >= 3
        assert "completeness_score" in adr_analysis
        assert (
            adr_analysis["completeness_score"] > 0.8
        )  # Should find proper ADR structure

    @pytest.mark.unit
    def test_analyzes_data_flow_architecture(self, mock_skill_context) -> None:
        """Given data flow implementation, when skill analyzes, then maps data flow patterns."""
        # Arrange
        data_flow_files = [
            "src/pipes/user_data_pipe.py",
            "src/filters/data_filter.py",
            "src/transforms/data_transformer.py",
            "src/sinks/data_sink.py",
        ]

        mock_skill_context.get_files.return_value = data_flow_files

        # Act
        data_flow_analysis = self.skill.analyze_data_flow(mock_skill_context)

        # Assert
        assert "pattern_detected" in data_flow_analysis
        assert data_flow_analysis["pattern_detected"] in [
            "pipes_filters",
            "batch_sequential",
            "streams",
        ]
        assert "flow_components" in data_flow_analysis

    @pytest.mark.unit
    def test_checks_scalability_patterns(self, mock_skill_context) -> None:
        """Given architecture implementation, when skill analyzes, then evaluates scalability patterns."""
        # Arrange
        scalability_code = """
        # Good: Horizontal scaling ready
        class StatelessService:
            def process_request(self, request):
                # No state in the service
                return self.process_data(request.data)

        # Issue: Stateful singleton
        class CacheManager:
            _instance = None

            def __new__(cls):
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.cache = {}  # In-memory cache
                return cls._instance

        # Issue: Monolithic processing
        def process_all_items(items):
            results = []
            for item in items:  # Sequential processing
                result = expensive_operation(item)
                results.append(result)
            return results
        """

        mock_skill_context.get_file_content.return_value = scalability_code

        # Act
        scalability_analysis = self.skill.analyze_scalability_patterns(
            mock_skill_context,
        )

        # Assert
        assert "scalability_score" in scalability_analysis
        assert "bottlenecks" in scalability_analysis
        assert (
            len(scalability_analysis["bottlenecks"]) >= 2
        )  # Should detect stateful and sequential issues

    @pytest.mark.unit
    def test_analyzes_security_architecture(self, mock_skill_context) -> None:
        """Given security implementation, when skill analyzes, then evaluates security patterns."""
        # Arrange
        security_code = """
        # Good: Proper authentication
        class AuthService:
            def authenticate(self, token):
                if self.validate_token(token):
                    return self.get_user_permissions(token)
                raise UnauthorizedError()

        # Issue: No authorization checks
        class AdminService:
            def delete_all_users(self):
                # No admin role check
                database.delete_all_users()

        # Issue: Sensitive data logging
        class UserService:
            def create_user(self, user_data):
                logger.info(f"Creating user with password: {user_data.password}")
                return database.save_user(user_data)
        """

        mock_skill_context.get_file_content.return_value = security_code

        # Act
        security_analysis = self.skill.analyze_security_architecture(mock_skill_context)

        # Assert
        assert "security_score" in security_analysis
        assert "vulnerabilities" in security_analysis
        vuln_types = [v["type"] for v in security_analysis["vulnerabilities"]]
        assert "authorization" in vuln_types
        assert "data_exposure" in vuln_types

    @pytest.mark.unit
    def test_detects_architectural_drift(self, mock_skill_context) -> None:
        """Given codebase evolution, when skill analyzes, then detects architectural drift."""
        # Arrange
        # Simulate detected patterns vs intended architecture
        intended_patterns = ["layered", "dependency_injection"]
        detected_patterns = ["layered", "spaghetti", "tight_coupling"]

        mock_skill_context.get_intended_architecture.return_value = intended_patterns
        mock_skill_context.get_detected_patterns.return_value = detected_patterns

        # Act
        drift_analysis = self.skill.detect_architectural_drift(mock_skill_context)

        # Assert
        assert "drift_detected" in drift_analysis
        assert drift_analysis["drift_detected"] is True
        assert "deviations" in drift_analysis
        assert "spaghetti" in [d["pattern"] for d in drift_analysis["deviations"]]

    @pytest.mark.unit
    def test_generates_architecture_recommendations(self, sample_findings) -> None:
        """Given architecture analysis findings, when skill generates recommendations, then provides actionable advice."""
        # Arrange
        architecture_findings = [
            {
                "type": "coupling",
                "severity": "high",
                "issue": "Controller directly accesses database",
                "location": "user_controller.py:25",
            },
            {
                "type": "cohesion",
                "severity": "medium",
                "issue": "UserService handles multiple responsibilities",
                "location": "user_service.py:10-50",
            },
            {
                "type": "scalability",
                "severity": "low",
                "issue": "Sequential processing in batch job",
                "location": "batch_processor.py:100",
            },
        ]

        # Act
        recommendations = self.skill.generate_recommendations(architecture_findings)

        # Assert
        assert len(recommendations) == len(architecture_findings)
        for rec in recommendations:
            assert "priority" in rec
            assert "action" in rec
            assert "rationale" in rec
            assert rec["action"] is not None
            assert len(rec["action"]) > 0

    @pytest.mark.unit
    def test_handles_missing_architecture_docs(self, mock_skill_context) -> None:
        """Given missing architecture documentation, when skill analyzes, then flags documentation gaps."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "src/main.py",
            "src/utils.py",
            # No architecture documentation files
        ]

        # Act
        doc_analysis = self.skill.analyze_architecture_documentation(mock_skill_context)

        # Assert
        assert "documentation_found" in doc_analysis
        assert doc_analysis["documentation_found"] is False
        assert "missing_docs" in doc_analysis
        assert len(doc_analysis["missing_docs"]) > 0

    @pytest.mark.unit
    def test_analyzes_technical_debt_impact(self, mock_skill_context) -> None:
        """Given technical debt indicators, when skill analyzes, then quantifies impact."""
        # Arrange
        debt_indicators = [
            {"type": "code_smell", "count": 15, "impact": "medium"},
            {"type": "architectural_violation", "count": 5, "impact": "high"},
            {"type": "duplicate_code", "count": 8, "impact": "low"},
        ]

        # Act
        debt_analysis = self.skill.analyze_technical_debt(debt_indicators)

        # Assert
        assert "overall_score" in debt_analysis
        assert "priority_areas" in debt_analysis
        assert "remediation_effort" in debt_analysis
        assert debt_analysis["overall_score"] > 0
        assert len(debt_analysis["priority_areas"]) > 0

    @pytest.mark.unit
    def test_creates_architecture_quality_report(self, sample_findings) -> None:
        """Given comprehensive analysis, when skill creates report, then generates structured summary."""
        # Arrange
        analysis_results = {
            "patterns_detected": ["layered", "dependency_injection"],
            "architecture_score": 7.5,
            "violations": sample_findings,
            "recommendations": ["Implement interfaces", "Add service layer"],
            "technical_debt_score": 3.2,
        }

        # Act
        report = self.skill.create_architecture_report(analysis_results)

        # Assert
        assert "## Architecture Assessment" in report
        assert "## Patterns Identified" in report
        assert "## Issues Found" in report
        assert "## Recommendations" in report
        assert "7.5" in report  # Architecture score
        assert "layered" in report
        assert len(report) > 500  # Should be comprehensive
