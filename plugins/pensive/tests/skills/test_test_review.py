"""
Unit tests for the test review skill.

Tests test suite quality assessment, TDD/BDD compliance,
and testing best practices evaluation.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import ast

# Import the skill we're testing
from pensive.skills.test_review import TestReviewSkill


class TestTestReviewSkill:
    """Test suite for TestReviewSkill business logic."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.skill = TestReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path("/tmp/test_repo")
        self.mock_context.working_dir = Path("/tmp/test_repo")

    @pytest.mark.unit
    def test_analyzes_test_coverage(self, mock_skill_context):
        """Given source and test files, when skill analyzes, then calculates coverage metrics."""
        # Arrange
        source_files = [
            ("src/calculator.py", """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def divide(a, b):
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

def complex_calculation(x, y, z):
    if x > 0:
        if y > 0:
            return x * y + z
        else:
            return x - y + z
    else:
        return z
            """)
        ]

        test_files = [
            ("tests/test_calculator.py", """
import pytest
from calculator import add, subtract

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2

def test_add_negative():
    assert add(-1, 1) == 0
            """)
        ]

        def mock_get_file_content(path):
            if "src/" in str(path):
                return source_files[0][1]
            elif "tests/" in str(path):
                return test_files[0][1]
            return ""

        mock_skill_context.get_file_content.side_effect = mock_get_file_content
        mock_skill_context.get_files.return_value = [
            "src/calculator.py",
            "tests/test_calculator.py"
        ]

        # Act
        coverage_analysis = self.skill.analyze_test_coverage(mock_skill_context)

        # Assert
        assert "overall_coverage" in coverage_analysis
        assert "file_coverage" in coverage_analysis
        assert "uncovered_functions" in coverage_analysis
        assert "branch_coverage" in coverage_analysis
        assert coverage_analysis["overall_coverage"] < 100  # Should detect incomplete coverage
        assert len(coverage_analysis["uncovered_functions"]) >= 2  # divide and complex_calculation

    @pytest.mark.unit
    def test_detects_test_structure_quality(self, mock_skill_context):
        """Given test files, when skill analyzes, then evaluates test structure and organization."""
        # Arrange
        well_structured_test = """
import pytest
from unittest.mock import Mock, patch
from calculator import Calculator

class TestCalculator:
    \"\"\"Test suite for Calculator functionality.\"\"\"

    def setup_method(self):
        \"\"\"Set up test fixtures before each test.\"\"\"
        self.calculator = Calculator()

    def teardown_method(self):
        \"\"\"Clean up after each test.\"\"\"
        self.calculator = None

    def test_add_positive_numbers(self):
        \"\"\"Test adding two positive numbers.\"\"\"
        result = self.calculator.add(2, 3)
        assert result == 5
        assert isinstance(result, (int, float))

    @pytest.mark.parametrize("a,b,expected", [
        (1, 2, 3),
        (-1, 1, 0),
        (0, 0, 0),
    ])
    def test_add_parameterized(self, a, b, expected):
        \"\"\"Test add function with various inputs.\"\"\"
        assert self.calculator.add(a, b) == expected

    def test_divide_by_zero_raises_error(self):
        \"\"\"Test that division by zero raises appropriate error.\"\"\"
        with pytest.raises(ValueError, match="Division by zero"):
            self.calculator.divide(1, 0)

    @patch('calculator.external_service')
    def test_with_mock(self, mock_service):
        \"\"\"Test with external dependency mocked.\"\"\"
        mock_service.return_value = 42
        result = self.calculator.external_operation()
        assert result == 42
        mock_service.assert_called_once()
        """

        poorly_structured_test = """
def test_1():
    assert add(1, 2) == 3

def test_something():
    x = 5
    # No assertion

def test_multiple_things():
    # Testing multiple things in one test
    assert add(1, 2) == 3
    assert subtract(3, 2) == 1
    # Should be separate tests
    import time
    time.sleep(1)  # Slow test
    assert True  # Trivial assertion
    """

        mock_skill_context.get_file_content.return_value = well_structured_test

        # Act
        structure_analysis = self.skill.analyze_test_structure(mock_skill_context, "test_calculator.py")

        # Assert
        assert "structure_score" in structure_analysis
        assert "organization_issues" in structure_analysis
        assert "best_practices" in structure_analysis
        assert "documentation_quality" in structure_analysis
        assert structure_analysis["structure_score"] > 0.8  # Well-structured test should score high

    @pytest.mark.unit
    def test_evaluates_tdd_compliance(self, mock_skill_context):
        """Given development workflow, when skill analyzes, then checks TDD compliance."""
        # Arrange
        development_history = [
            {"file": "tests/test_user.py", "action": "created", "content": "def test_user_creation(): pass"},
            {"file": "src/user.py", "action": "created", "content": "def create_user(): pass"},
            {"file": "tests/test_user.py", "action": "modified", "content": "def test_user_creation(): assert create_user('name')"},
            {"file": "src/user.py", "action": "modified", "content": "def create_user(name): return User(name)"},
        ]

        mock_skill_context.get_git_history.return_value = development_history

        # Act
        tdd_analysis = self.skill.evaluate_tdd_compliance(mock_skill_context)

        # Assert
        assert "tdd_score" in tdd_analysis
        assert "test_first_pattern" in tdd_analysis
        assert "red_green_refactor" in tdd_analysis
        assert "compliance_issues" in tdd_analysis
        assert tdd_analysis["test_first_pattern"] is True

    @pytest.mark.unit
    def test_detects_bdd_patterns(self, mock_skill_context):
        """Given test specifications, when skill analyzes, then identifies BDD patterns."""
        # Arrange
        bdd_style_test = """
import pytest
from behave import given, when, then

@given('a calculator is available')
def step_impl(context):
    context.calculator = Calculator()

@when('I add {a:d} and {b:d}')
def step_impl(context, a, b):
    context.result = context.calculator.add(a, b)

@then('the result should be {expected:d}')
def step_impl(context, expected):
    assert context.result == expected

# pytest-bdd style
def test_user_login_success():
    \"\"\"
    Given a registered user exists
    When they provide valid credentials
    Then they should be logged in successfully
    \"\"\"
    user = create_test_user()
    result = authenticate(user.email, user.password)
    assert result.success is True
    assert result.token is not None

# Plain BDD-style test
def test_calculator_addition():
    \"\"\"Calculator addition feature.\"\"\"
    # Given: I have a calculator
    calculator = Calculator()

    # When: I add 2 and 3
    result = calculator.add(2, 3)

    # Then: The result should be 5
    assert result == 5
    """

        mock_skill_context.get_file_content.return_value = bdd_style_test

        # Act
        bdd_analysis = self.skill.analyze_bdd_patterns(mock_skill_context, "test_features.py")

        # Assert
        assert "bdd_detected" in bdd_analysis
        assert "given_when_then" in bdd_analysis
        assert "behavior_specifications" in bdd_analysis
        assert "gherkin_features" in bdd_analysis
        assert bdd_analysis["bdd_detected"] is True
        assert len(bdd_analysis["given_when_then"]) >= 2

    @pytest.mark.unit
    def test_identifies_test_anti_patterns(self, mock_skill_context):
        """Given test code, when skill analyzes, then detects testing anti-patterns."""
        # Arrange
        anti_pattern_test = """
import pytest
import requests
import time

def test_with_external_dependencies():
    # Anti-pattern: Depending on external services
    response = requests.get("https://api.example.com/data")
    assert response.status_code == 200

def test_with_shared_state():
    # Anti-pattern: Shared state between tests
    global counter
    counter += 1
    assert counter > 0

def test_with_hardcoded_values():
    # Anti-pattern: Magic numbers and hardcoded values
    result = process_data([1, 2, 3, 4, 5])
    assert result == 42  # Where does 42 come from?

def test_slow_test():
    # Anti-pattern: Unnecessary delays
    time.sleep(10)  # Why 10 seconds?
    assert True

def test_no_assertions():
    # Anti-pattern: Test without assertions
    data = load_data()
    process(data)

def test_multiple_assertions():
    # Anti-pattern: Testing too many things
    data = load_data()
    assert data is not None
    assert len(data) > 0
    assert data[0]['id'] > 0
    assert data[0]['name'] is not None
    assert validate_format(data)
    assert check_business_rules(data)

def test_exception_handling():
    # Anti-pattern: Catching all exceptions
    try:
        risky_operation()
    except:
        pass  # Swallowing all exceptions

counter = 0
        """

        mock_skill_context.get_file_content.return_value = anti_pattern_test

        # Act
        anti_patterns = self.skill.identify_test_anti_patterns(mock_skill_context, "anti_patterns.py")

        # Assert
        assert len(anti_patterns) >= 6  # Should detect multiple anti-patterns
        pattern_types = [pattern["type"] for pattern in anti_patterns]
        assert "external_dependency" in pattern_types
        assert "shared_state" in pattern_types
        assert "hardcoded_values" in pattern_types
        assert "slow_test" in pattern_types

    @pytest.mark.unit
    def test_analyzes_test_data_management(self, mock_skill_context):
        """Given test fixtures and data, when skill analyzes, then evaluates data management."""
        # Arrange
        test_with_fixtures = """
import pytest
from factories import UserFactory

@pytest.fixture
def sample_user():
    \"\"\"Create a sample user for testing.\"\"\"
    return UserFactory.create(
        name="Test User",
        email="test@example.com",
        active=True
    )

@pytest.fixture
def user_database():
    \"\"\"Create a temporary database with sample data.\"\"\"
    db = create_test_database()
    db.add_user(User(name="Alice", email="alice@test.com"))
    db.add_user(User(name="Bob", email="bob@test.com"))
    yield db
    db.cleanup()

def test_user_creation(sample_user):
    assert sample_user.name == "Test User"
    assert sample_user.is_active()

def test_user_operations(user_database):
    users = user_database.get_all_users()
    assert len(users) == 2

def test_with_factory():
    # Using factory pattern for test data
    users = UserFactory.create_batch(10, active=True)
    assert all(user.is_active() for user in users)

# Hardcoded test data (bad practice)
def test_hardcoded_data():
    user_data = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "zip": "12345"
        }
    }
    user = User(**user_data)
    assert user.email == "john@example.com"
        """

        mock_skill_context.get_file_content.return_value = test_with_fixtures

        # Act
        data_analysis = self.skill.analyze_test_data_management(mock_skill_context, "test_data.py")

        # Assert
        assert "fixture_quality" in data_analysis
        assert "factory_usage" in data_analysis
        assert "hardcoded_data" in data_analysis
        assert "data_isolation" in data_analysis
        assert len(data_analysis["hardcoded_data"]) >= 1

    @pytest.mark.unit
    def test_evaluates_mock_usage_quality(self, mock_skill_context):
        """Given test mocks, when skill analyzes, then evaluates mock usage patterns."""
        # Arrange
        mock_usage_test = """
import pytest
from unittest.mock import Mock, patch, MagicMock

def test_good_mock_usage():
    # Good: Specific mock configuration
    with patch('services.external_api.fetch_data') as mock_fetch:
        mock_fetch.return_value = {"result": "success"}
        result = process_data()
        assert result["status"] == "success"
        mock_fetch.assert_called_once_with(endpoint="api/data")

def test_over_mocking():
    # Anti-pattern: Mocking too much
    with patch('module.ClassA') as mock_a, \\
         patch('module.ClassB') as mock_b, \\
         patch('module.ClassC') as mock_c:
        mock_a.method1.return_value = "result1"
        mock_b.method2.return_value = "result2"
        mock_c.method3.return_value = "result3"
        # Testing mocks, not actual logic

def test_mock_verification():
    # Good: Verifying mock interactions
    mock_service = Mock()
    result = use_service(mock_service, "input")
    assert result == "processed"
    mock_service.process.assert_called_once_with("input")

def test_magic_mock_overuse():
    # Anti-pattern: Using MagicMock for everything
    mock_obj = MagicMock()
    mock_obj.some_method.return_value = MagicMock()
    mock_obj.some_method.return_value.get_data.return_value = "data"
    # Too much magic, unclear expectations

def test_spy_usage():
    # Good: Using spy to partially mock
    real_service = RealService()
    with patch.object(real_service, 'expensive_method', return_value="mocked"):
        result = real_service.test_method()
        assert result == "test_with_mocked_expensive"
        real_service.expensive_method.assert_not_called()
        """

        mock_skill_context.get_file_content.return_value = mock_usage_test

        # Act
        mock_analysis = self.skill.analyze_mock_usage(mock_skill_context, "test_mocks.py")

        # Assert
        assert "mock_patterns" in mock_analysis
        assert "over_mocking" in mock_analysis
        assert "verification_quality" in mock_analysis
        assert "spy_usage" in mock_analysis
        assert len(mock_analysis["over_mocking"]) >= 1

    @pytest.mark.unit
    def test_analyzes_test_performance(self, mock_skill_context):
        """Given test suite, when skill analyzes, then evaluates test performance."""
        # Arrange
        performance_test_info = {
            "tests": [
                {"name": "test_fast_operation", "duration": 0.001},
                {"name": "test_database_query", "duration": 2.5},
                {"name": "test_api_call", "duration": 5.2},
                {"name": "test_file_processing", "duration": 15.7},
                {"name": "test_quick_check", "duration": 0.0005}
            ],
            "total_duration": 23.405,
            "parallelizable": ["test_fast_operation", "test_quick_check"]
        }

        mock_skill_context.get_test_performance_data.return_value = performance_test_info

        # Act
        performance_analysis = self.skill.analyze_test_performance(mock_skill_context)

        # Assert
        assert "slow_tests" in performance_analysis
        assert "performance_bottlenecks" in performance_analysis
        assert "optimization_opportunities" in performance_analysis
        assert "parallelization_potential" in performance_analysis
        assert len(performance_analysis["slow_tests"]) >= 2

    @pytest.mark.unit
    def test_evaluates_integration_test_coverage(self, mock_skill_context):
        """Given test suite, when skill analyzes, then assesses integration vs unit test balance."""
        # Arrange
        test_files = [
            ("tests/unit/test_calculator.py", """
def test_add():
    from calculator import add
    assert add(2, 3) == 5
            """),

            ("tests/integration/test_user_flow.py", """
def test_user_registration_flow():
    # Tests database, email, and user service integration
    user_service = UserService(database=TestDatabase(), email_service=MockEmailService())
    result = user_service.register_user("test@example.com", "password123")
    assert result.success
            """),

            ("tests/test_api.py", """
def test_api_endpoint():
    # Full stack integration test
    client = TestClient(app)
    response = client.post("/api/users", json={"email": "test@example.com"})
    assert response.status_code == 201
            """)
        ]

        def mock_get_file_content(path):
            for file_path, content in test_files:
                if file_path in str(path):
                    return content
            return ""

        mock_skill_context.get_file_content.side_effect = mock_get_file_content
        mock_skill_context.get_files.return_value = [file[0] for file in test_files]

        # Act
        integration_analysis = self.skill.analyze_integration_test_coverage(mock_skill_context)

        # Assert
        assert "unit_test_ratio" in integration_analysis
        assert "integration_scenarios" in integration_analysis
        assert "coverage_gaps" in integration_analysis
        assert "test_pyramid_balance" in integration_analysis
        assert integration_analysis["unit_test_ratio"] < 1.0  # More integration than unit tests

    @pytest.mark.unit
    def test_detects_test_flakiness_patterns(self, mock_skill_context):
        """Given test history, when skill analyzes, then identifies flaky test patterns."""
        # Arrange
        test_execution_history = [
            {"test": "test_random_data", "results": ["pass", "fail", "pass", "fail"]},
            {"test": "test_time_sensitive", "results": ["pass", "pass", "fail", "pass"]},
            {"test": "test_concurrent_operations", "results": ["fail", "pass", "fail", "pass"]},
            {"test": "test_stable_operation", "results": ["pass", "pass", "pass", "pass"]},
            {"test": "test_external_dependency", "results": ["pass", "fail", "fail", "pass"]}
        ]

        mock_skill_context.get_test_history.return_value = test_execution_history

        # Act
        flakiness_analysis = self.skill.detect_test_flakiness(mock_skill_context)

        # Assert
        assert "flaky_tests" in flakiness_analysis
        assert "flakiness_patterns" in flakiness_analysis
        assert "root_causes" in flakiness_analysis
        assert "recommendations" in flakiness_analysis
        assert len(flakiness_analysis["flaky_tests"]) >= 3

    @pytest.mark.unit
    def test_generates_test_quality_report(self, sample_findings):
        """Given comprehensive test analysis, when skill generates report, then creates structured summary."""
        # Arrange
        test_analysis = {
            "overall_score": 7.8,
            "coverage_percentage": 75,
            "test_count": 150,
            "unit_tests": 90,
            "integration_tests": 45,
            "end_to_end_tests": 15,
            "slow_tests": 12,
            "flaky_tests": 3,
            "anti_patterns": 8,
            "tdd_compliance": 0.6,
            "findings": sample_findings
        }

        # Act
        report = self.skill.create_test_quality_report(test_analysis)

        # Assert
        assert "## Test Quality Assessment" in report
        assert "## Coverage Analysis" in report
        assert "## Test Pyramid" in report
        assert "## Quality Issues" in report
        assert "## Recommendations" in report
        assert "7.8" in report  # Overall score
        assert "75%" in report  # Coverage percentage
        assert "150" in report  # Test count

    @pytest.mark.unit
    def test_recommends_testing_improvements(self, mock_skill_context):
        """Given test analysis, when skill recommends, then provides actionable testing improvements."""
        # Arrange
        current_state = {
            "coverage": 65,
            "tdd_compliance": 0.3,
            "integration_ratio": 0.2,
            "avg_test_duration": 2.5,
            "flaky_tests": 5,
            "anti_patterns": 12
        }

        # Act
        recommendations = self.skill.generate_testing_recommendations(current_state)

        # Assert
        assert len(recommendations) > 0
        categories = [rec["category"] for rec in recommendations]
        assert "coverage" in categories
        assert "tdd" in categories
        assert "performance" in categories
        assert "quality" in categories

        for rec in recommendations:
            assert "priority" in rec
            assert "action" in rec
            assert "benefit" in rec
            assert "implementation" in rec
