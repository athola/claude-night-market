"""Unit tests for testing guidance capabilities.

Tests test quality assessment, TDD guidance,
and testing best practices recommendations.
"""

from __future__ import annotations

import pytest

# Import the skills we're testing
from parseltongue.skills.testing_guide import TestingGuideSkill


class TestTestingGuideSkill:
    """Test suite for TestingGuideSkill."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = TestingGuideSkill()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_test_structure(self, sample_test_patterns) -> None:
        """Given test code, when skill analyzes, then evaluates test structure."""
        # Arrange
        test_code = sample_test_patterns["pytest_fixture"]

        # Act
        result = self.skill.analyze_test_structure(test_code)

        # Assert
        structure = result["test_structure"]

        # Should detect test class
        assert "test_classes" in structure
        assert "TestUserService" in structure["test_classes"]

        # Should detect test methods
        assert "test_methods" in structure
        assert len(structure["test_methods"]) >= 1
        assert "test_create_user" in [
            method["name"] for method in structure["test_methods"]
        ]

        # Should detect fixtures
        assert "fixtures" in structure
        assert "sample_data" in structure["fixtures"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_identifies_anti_patterns(self, testing_issues) -> None:
        """Given problematic test code, when skill analyzes, then identifies testing anti-patterns."""
        # Arrange
        anti_pattern_code = testing_issues["no_fixtures"]

        # Act
        result = self.skill.identify_anti_patterns(anti_pattern_code)

        # Assert
        anti_patterns = result["anti_patterns"]

        # Should detect no fixture usage
        assert "no_fixture_reuse" in anti_patterns
        assert anti_patterns["no_fixture_reuse"]["creates_new_instance"] is True

        # Should provide recommendations
        assert len(anti_patterns["recommendations"]) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_coverage_gaps(self) -> None:
        """Given test code and source code, when skill analyzes, then identifies coverage gaps."""
        # Arrange
        source_code = """
class UserService:
    def __init__(self):
        self.users = []

    def create_user(self, name, email):
        self.users.append({"name": name, "email": email})
        return self.users[-1]

    def get_user(self, index):
        if 0 <= index < len(self.users):
            return self.users[index]
        raise IndexError("User not found")

    def delete_user(self, index):
        if 0 <= index < len(self.users):
            return self.users.pop(index)
        raise IndexError("User not found")
        """

        test_code = """
def test_create_user():
    service = UserService()
    user = service.create_user("Alice", "alice@example.com")
    assert user["name"] == "Alice"

def test_get_user():
    service = UserService()
    service.create_user("Alice", "alice@example.com")
    user = service.get_user(0)
    assert user["name"] == "Alice"
        """

        # Act
        result = self.skill.analyze_coverage_gaps(source_code, test_code)

        # Assert
        coverage = result["coverage_analysis"]

        # Should identify uncovered methods
        assert "uncovered_methods" in coverage
        assert "delete_user" in coverage["uncovered_methods"]

        # Should identify uncovered branches
        assert "uncovered_branches" in coverage
        assert "index_error_branch" in coverage["uncovered_branches"]

        # Should calculate coverage percentage
        assert coverage["estimated_coverage"] < 100
        assert coverage["estimated_coverage"] > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evaluates_test_quality(self, sample_test_patterns) -> None:
        """Given test code, when skill analyzes, then evaluates overall test quality."""
        # Arrange
        test_code = sample_test_patterns["pytest_fixture"]

        # Act
        result = self.skill.evaluate_test_quality(test_code)

        # Assert
        quality = result["quality_assessment"]

        # Should provide quality score
        assert "score" in quality
        assert 0 <= quality["score"] <= 100

        # Should evaluate different aspects
        aspects = quality["aspects"]
        assert "readability" in aspects
        assert "maintainability" in aspects
        assert "coverage" in aspects
        assert "organization" in aspects

        # Should provide strengths and weaknesses
        assert "strengths" in quality
        assert "weaknesses" in quality
        assert "improvements" in quality

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recommends_tdd_workflow(self) -> None:
        """Given feature requirements, when skill analyzes, then recommends TDD workflow."""
        # Arrange
        feature_description = """
User Authentication System:
- Users can register with email and password
- Users can login with email and password
- Passwords must be hashed
- Login should return JWT token
- Failed login attempts should be tracked
        """

        # Act
        result = self.skill.recommend_tdd_workflow(feature_description)

        # Assert
        workflow = result["tdd_workflow"]

        # Should provide step-by-step TDD process
        assert "steps" in workflow
        assert len(workflow["steps"]) >= 3

        # Should identify test cases for each step
        first_step = workflow["steps"][0]
        assert "test_cases" in first_step
        assert len(first_step["test_cases"]) >= 2

        # Should provide implementation guidance
        for step in workflow["steps"]:
            assert "description" in step
            assert "test_name" in step
            assert "implementation_hint" in step

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_suggests_improvements(self, testing_issues) -> None:
        """Given problematic test code, when skill analyzes, then suggests improvements."""
        # Arrange
        problematic_code = testing_issues["testing_implementation"]

        # Act
        result = self.skill.suggest_improvements(problematic_code)

        # Assert
        suggestions = result["suggestions"]

        # Should identify testing private methods issue
        assert any("private_method" in s["issue"] for s in suggestions)

        # Should provide concrete improvements
        for suggestion in suggestions:
            assert "issue" in suggestion
            assert "improvement" in suggestion
            assert "example" in suggestion
            assert "rationale" in suggestion

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_generates_test_fixtures(self) -> None:
        """Given source code, when skill analyzes, then generates appropriate test fixtures."""
        # Arrange
        source_code = """
class Order:
    def __init__(self, id, customer_name, items, total):
        self.id = id
        self.customer_name = customer_name
        self.items = items
        self.total = total
        self.status = "pending"

    def add_item(self, item):
        self.items.append(item)
        self.total += item["price"]

    def mark_complete(self):
        self.status = "completed"
        """

        # Act
        result = self.skill.generate_test_fixtures(source_code)

        # Assert
        fixtures = result["fixtures"]

        # Should generate order fixture
        assert "order_fixture" in fixtures

        # Should provide different fixture types
        assert "minimal_fixture" in fixtures["order_fixture"]
        assert "complete_fixture" in fixtures["order_fixture"]
        assert "edge_case_fixture" in fixtures["order_fixture"]

        # Should include required imports
        assert "imports" in result
        assert "pytest" in str(result["imports"])

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_mock_usage(self) -> None:
        """Given test code, when skill analyzes, then evaluates mock usage patterns."""
        # Arrange
        test_with_mocks = """
import pytest
from unittest.mock import Mock, patch

def test_api_call():
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"data": "test"}
        result = fetch_data()
        assert result["data"] == "test"
        mock_get.assert_called_once_with("https://api.example.com")

def test_database_interaction():
    mock_db = Mock()
    mock_db.query.return_value = [{"id": 1, "name": "Test"}]

    service = DataService(mock_db)
    users = service.get_users()

    assert len(users) == 1
    mock_db.query.assert_called_once()
        """

        # Act
        result = self.skill.analyze_mock_usage(test_with_mocks)

        # Assert
        mock_analysis = result["mock_analysis"]

        # Should detect patch usage
        assert "patch_usage" in mock_analysis
        assert len(mock_analysis["patch_usage"]) >= 1

        # Should detect mock object creation
        assert "mock_objects" in mock_analysis
        assert len(mock_analysis["mock_objects"]) >= 1

        # Should evaluate assertion quality
        assert "assertions" in mock_analysis
        assert mock_analysis["assertions"]["uses_assert_called"] is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recommends_test_types(self) -> None:
        """Given code structure, when skill analyzes, then recommends types of tests needed."""
        # Arrange
        code_structure = """
src/
├── user/
│   ├── __init__.py
│   ├── models.py      # User model class
│   ├── services.py    # UserService class
│   └── views.py       # User endpoints
├── auth/
│   ├── __init__.py
│   ├── models.py      # Token, Permission models
│   ├── services.py    # AuthService
│   └── middleware.py  # Authentication middleware
        """

        # Act
        result = self.skill.recommend_test_types(code_structure)

        # Assert
        recommendations = result["test_recommendations"]

        # Should recommend unit tests for each module
        assert "unit_tests" in recommendations
        assert "user_models_test" in recommendations["unit_tests"]
        assert "user_services_test" in recommendations["unit_tests"]
        assert "auth_services_test" in recommendations["unit_tests"]

        # Should recommend integration tests
        assert "integration_tests" in recommendations
        assert "auth_flow_test" in recommendations["integration_tests"]

        # Should recommend test structure
        assert "test_structure" in recommendations
        assert recommendations["test_structure"]["conftest_py"] is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_validates_async_testing(self) -> None:
        """Given async test code, when skill analyzes, then validates async testing patterns."""
        # Arrange
        async_test_code = """
import pytest
import asyncio
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_service():
    service = AsyncService()
    result = await service.process_data()
    assert result.success is True

@pytest.mark.asyncio
async def test_with_async_mock():
    mock_client = AsyncMock()
    mock_client.fetch.return_value = {"data": "test"}

    service = ExternalAPIService(mock_client)
    result = await service.get_data()

    assert result["data"] == "test"
    mock_client.fetch.assert_called_once()
        """

        # Act
        result = self.skill.validate_async_testing(async_test_code)

        # Assert
        validation = result["async_validation"]

        # Should detect pytest.mark.asyncio usage
        assert "uses_pytest_asyncio" in validation
        assert validation["uses_pytest_asyncio"] is True

        # Should detect async test functions
        assert "async_test_count" in validation
        assert validation["async_test_count"] >= 2

        # Should detect AsyncMock usage
        assert "uses_asyncmock" in validation
        assert validation["uses_asyncmock"] is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_test_performance(self) -> None:
        """Given test suite, when skill analyzes, then evaluates test performance."""
        # Arrange
        slow_tests = """
import time
import pytest

def test_slow_operation():
    time.sleep(2)  # Slow test
    assert True

def test_inefficient_setup():
    # Expensive setup for each test
    large_dataset = create_large_dataset()  # Takes time
    result = process_dataset(large_dataset)
    assert result is not None

@pytest.mark.parametrize("item", range(1000))  # Many test cases
def test_parameterized_heavy(item):
    result = expensive_calculation(item)
    assert result > 0
        """

        # Act
        result = self.skill.analyze_test_performance(slow_tests)

        # Assert
        performance = result["performance_analysis"]

        # Should identify slow tests
        assert "slow_tests" in performance
        assert len(performance["slow_tests"]) >= 2

        # Should identify performance issues
        assert "issues" in performance
        assert "time_sleep" in performance["issues"]
        assert "expensive_setup" in performance["issues"]

        # Should provide optimization suggestions
        assert "optimizations" in performance
        assert len(performance["optimizations"]) >= 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recommends_testing_tools(self) -> None:
        """Given project context, when skill analyzes, then recommends appropriate testing tools."""
        # Arrange
        project_context = {
            "language": "python",
            "framework": "fastapi",
            "database": "postgresql",
            "async": True,
            "testing_requirements": ["unit", "integration", "api"],
        }

        # Act
        result = self.skill.recommend_testing_tools(project_context)

        # Assert
        recommendations = result["tool_recommendations"]

        # Should recommend core testing framework
        assert "testing_framework" in recommendations
        assert recommendations["testing_framework"] == "pytest"

        # Should recommend async testing tools
        assert "async_testing" in recommendations
        assert "pytest-asyncio" in recommendations["async_testing"]["tools"]

        # Should recommend API testing tools
        assert "api_testing" in recommendations
        assert (
            "httpx" in recommendations["api_testing"]["tools"]
            or "aiohttp" in recommendations["api_testing"]["tools"]
        )

        # Should recommend database testing tools
        assert "database_testing" in recommendations
        assert "factory_boy" in recommendations["database_testing"]["tools"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_generates_test_documentation(self) -> None:
        """Given test code, when skill analyzes, then generates test documentation."""
        # Arrange
        test_code = '''
class TestUserService:
    """Test suite for UserService functionality."""

    @pytest.fixture
    def user_service(self):
        """Create UserService instance for testing."""
        return UserService()

    def test_create_user_success(self, user_service):
        """Test successful user creation."""
        user = user_service.create_user("Alice", "alice@example.com")
        assert user.name == "Alice"
        assert user.email == "alice@example.com"
        assert user.is_active is True

    def test_create_user_duplicate_email(self, user_service):
        """Test user creation with duplicate email."""
        user_service.create_user("Alice", "alice@example.com")
        with pytest.raises(ValueError, match="Email already exists"):
            user_service.create_user("Bob", "alice@example.com")
        '''

        # Act
        result = self.skill.generate_test_documentation(test_code)

        # Assert
        documentation = result["documentation"]

        # Should generate overview
        assert "overview" in documentation
        assert documentation["overview"]["test_class"] == "TestUserService"
        assert (
            documentation["overview"]["purpose"]
            == "Test suite for UserService functionality"
        )

        # Should document test cases
        assert "test_cases" in documentation
        assert len(documentation["test_cases"]) >= 2

        # Should document each test case
        first_test = documentation["test_cases"][0]
        assert "name" in first_test
        assert "description" in first_test
        assert "setup" in first_test
        assert "assertions" in first_test

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evaluates_test_maintainability(self) -> None:
        """Given test code, when skill analyzes, then evaluates test maintainability."""
        # Arrange
        maintainable_code = '''
class TestUserService:
    @pytest.fixture
    def sample_user_data(self):
        """Provide consistent test data."""
        return {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "123-456-7890"
        }

    def test_user_creation_variations(self, sample_user_data):
        """Test user creation with different valid inputs."""
        valid_emails = ["user@test.com", "test.user@domain.co.uk", "user+tag@test.com"]

        for email in valid_emails:
            user_data = {**sample_user_data, "email": email}
            user = UserService.create_user(**user_data)
            assert user.email == email
    '''

        # Act
        result = self.skill.evaluate_maintainability(maintainable_code)

        # Assert
        maintainability = result["maintainability_analysis"]

        # Should provide maintainability score
        assert "score" in maintainability
        assert 0 <= maintainability["score"] <= 100

        # Should evaluate maintainability factors
        factors = maintainability["factors"]
        assert "fixture_usage" in factors
        assert "data_driven_testing" in factors
        assert "test_organization" in factors
        assert "readability" in factors

        # Should provide recommendations
        assert "recommendations" in maintainability
