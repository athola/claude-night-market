"""
Integration tests for the parseltongue plugin.

Tests end-to-end workflows, agent coordination,
and real-world usage scenarios.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from parseltongue.agents.python_pro import PythonProAgent
from parseltongue.skills.language_detection import LanguageDetectionSkill

# Import parseltongue components for testing
from parseltongue.workflows.code_review import CodeReviewWorkflow


class TestParseltongueIntegration:
    """Integration tests for parseltongue plugin."""

    @pytest.mark.integration
    async def test_end_to_end_python_code_analysis(self, temp_project_directory):
        """Given a Python project, when analyzing, then provides comprehensive insights."""
        # Arrange
        workflow = CodeReviewWorkflow()
        project_path = temp_project_directory

        # Add some Python-specific files
        (project_path / "requirements.txt").write_text("""
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
        """)

        (project_path / "src" / "main.py").write_text("""
import asyncio
from typing import List, Optional
from dataclasses import dataclass
import httpx

@dataclass
class User:
    id: int
    name: str
    email: str
    is_active: bool = True

class AsyncUserClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def get_user(self, user_id: int) -> Optional[User]:
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = await self.client.get(f"/users/{user_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return User(**data)

    async def get_multiple_users(self, user_ids: List[int]) -> List[Optional[User]]:
        tasks = [self.get_user(uid) for uid in user_ids]
        return await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    async with AsyncUserClient("https://api.example.com") as client:
        users = await client.get_multiple_users([1, 2, 3])
        for user in users:
            if isinstance(user, User):
                print(f"User: {user.name} ({user.email})")

if __name__ == "__main__":
    asyncio.run(main())
        """)

        # Add tests
        (project_path / "tests" / "test_main.py").write_text("""
import pytest
from unittest.mock import AsyncMock
import httpx

from src.main import AsyncUserClient, User

@pytest.fixture
def mock_client():
    client = AsyncUserClient("https://test.com")
    return client

@pytest.mark.asyncio
async def test_get_user_success(mock_client):
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
        "is_active": True
    }

    with pytest.MonkeyPatch().context() as m:
        m.setattr(httpx.AsyncClient, "get", AsyncMock(return_value=mock_response))
        client.client = httpx.AsyncClient()

        user = await client.get_user(1)
        assert user.name == "Test User"
        assert user.email == "test@example.com"

@pytest.mark.asyncio
async def test_get_user_not_found(mock_client):
    mock_response = AsyncMock()
    mock_response.status_code = 404

    with pytest.MonkeyPatch().context() as m:
        m.setattr(httpx.AsyncClient, "get", AsyncMock(return_value=mock_response))
        client.client = httpx.AsyncClient()

        user = await client.get_user(999)
        assert user is None
        """)

        # Act
        analysis_result = await workflow.analyze_project(project_path)

        # Assert
        assert analysis_result is not None
        assert "languages_detected" in analysis_result
        assert "python" in analysis_result["languages_detected"]
        assert analysis_result["languages_detected"]["python"] >= 0.9

        assert "insights" in analysis_result
        insights = analysis_result["insights"]

        # Should detect async patterns
        assert "async_patterns" in insights
        assert any("AsyncUserClient" in str(insight) for insight in insights["async_patterns"])

        # Should detect testing patterns
        assert "testing_insights" in insights
        assert "pytest" in str(insights["testing_insights"])

        # Should detect dependencies
        assert "dependencies" in analysis_result
        assert "fastapi" in str(analysis_result["dependencies"])
        assert "pytest" in str(analysis_result["dependencies"])

    @pytest.mark.integration
    async def test_agent_coordination_for_code_review(self, temp_project_directory):
        """Given code review request, when agents coordinate, then provides comprehensive analysis."""
        # Arrange
        python_code = '''
import asyncio
from typing import List

class DataProcessor:
    def __init__(self):
        self.cache = []

    async def process_items(self, items: List[str]):
        """Process items sequentially - potential performance issue."""
        results = []
        for item in items:
            result = await self.process_item(item)
            results.append(result)
            self.cache.append(result)  # Memory leak potential
        return results

    async def process_item(self, item: str):
        await asyncio.sleep(0.1)  # Simulate async work
        return item.upper()

def test_data_processor():
    processor = DataProcessor()
    # Testing implementation details - bad practice
    assert hasattr(processor, 'cache')
        '''

        # Act
        from parseltongue.agents.python_optimizer import PythonOptimizerAgent
        from parseltongue.agents.python_tester import PythonTesterAgent

        # Coordinate multiple agents
        python_pro = PythonProAgent()
        python_tester = PythonTesterAgent()
        python_optimizer = PythonOptimizerAgent()

        # Get analysis from each agent
        pro_analysis = await python_pro.analyze_code(python_code)
        tester_analysis = await python_tester.analyze_code(python_code)
        optimizer_analysis = await python_optimizer.analyze_code(python_code)

        # Assert - Python Pro Agent analysis
        assert pro_analysis is not None
        assert "modern_features" in pro_analysis
        assert "async_functions" in pro_analysis
        assert pro_analysis["async_functions"]["process_items"]["detected"] is True

        # Assert - Python Tester Agent analysis
        assert tester_analysis is not None
        assert "testing_issues" in tester_analysis
        assert any("implementation_details" in issue for issue in tester_analysis["testing_issues"])
        assert "recommendations" in tester_analysis

        # Assert - Python Optimizer Agent analysis
        assert optimizer_analysis is not None
        assert "performance_issues" in optimizer_analysis
        assert "sequential_processing" in str(optimizer_analysis["performance_issues"])
        assert "memory_leak" in str(optimizer_analysis["performance_issues"])

        # Should provide optimization suggestions
        assert len(optimizer_analysis["optimizations"]) >= 2

    @pytest.mark.integration
    async def test_skill_workflow_coordination(self, language_samples):
        """Given multi-language code, when skills coordinate, then provides comprehensive analysis."""
        # Arrange
        multi_language_code = {
            "python": language_samples["python"],
            "typescript": language_samples["typescript"],
            "javascript": language_samples["javascript"]
        }

        # Act
        from parseltongue.skills.code_transformation import CodeTransformationSkill
        from parseltongue.skills.pattern_matching import PatternMatchingSkill

        detection_skill = LanguageDetectionSkill()
        pattern_skill = PatternMatchingSkill()
        transformation_skill = CodeTransformationSkill()

        results = {}
        for language, code in multi_language_code.items():
            # Step 1: Detect language and features
            language_result = detection_skill.analyze_features(code, language)

            # Step 2: Identify patterns
            pattern_result = pattern_skill.recognize_patterns(code, language)

            # Step 3: Suggest improvements
            transformation_result = transformation_skill.suggest_improvements(code, language)

            results[language] = {
                "language_features": language_result,
                "patterns": pattern_result,
                "improvements": transformation_result
            }

        # Assert
        for language, result in results.items():
            assert "language_features" in result
            assert "patterns" in result
            assert "improvements" in result

            # Should detect language-specific features
            features = result["language_features"]["features"]
            assert len(features) > 0

            # Should identify patterns
            patterns = result["patterns"]["recognized_patterns"]
            assert len(patterns) > 0

            # Should provide improvement suggestions
            result["improvements"]["suggestions"]
            # (May be empty for good code, but structure should exist)

    @pytest.mark.integration
    async def test_command_execution_workflow(self, temp_project_directory):
        """Given command execution, when workflow runs, then integrates all components."""
        # Arrange
        from parseltongue.commands.analyze_tests import AnalyzeTestsCommand
        from parseltongue.commands.check_async import CheckAsyncCommand
        from parseltongue.commands.run_profiler import RunProfilerCommand

        # Add test files with issues
        (project_path / "src" / "slow_code.py").write_text("""
import time
import asyncio

class SlowProcessor:
    def __init__(self):
        self.cache = []

    def process_sequential(self, items):
        '''O(n^2) sequential processing.'''
        results = []
        for item in items:
            for other_item in items:
                if item != other_item:
                    results.append(self.combine(item, other_item))
        return results

    async def async_blocking(self, items):
        '''Async code with blocking operations.'''
        for item in items:
            time.sleep(0.1)  # Blocks event loop
            await self.process_item(item)

    async def process_item(self, item):
        await asyncio.sleep(0.01)
        return item.upper()

    def process_and_store(self, item):
        result = self.process_item(item)
        self.cache.append(result)  # Memory leak
        return result

    def process_item(self, item):
        return f"processed_{item}"
        """)

        (project_path / "tests" / "test_slow.py").write_text("""
from src.slow_code import SlowProcessor

def test_process_sequential():
    processor = SlowProcessor()
    # No fixture, creates new instance each time
    items = ["a", "b", "c"]
    result = processor.process_sequential(items)
    assert len(result) > 0

def test_private_method():
    processor = SlowProcessor()
    # Testing private method - bad practice
    result = processor._internal_method()
    assert result is not None

# No assertions - bad test
def test_no_assertion():
    processor = SlowProcessor()
    processor.process_and_store("test")
    print("Test completed")
        """)

        # Act
        # Execute analyze tests command
        test_command = AnalyzeTestsCommand()
        test_analysis = await test_command.execute(temp_project_directory)

        # Execute profiler command
        profiler_command = RunProfilerCommand()
        profiler_analysis = await profiler_command.execute(temp_project_directory / "src" / "slow_code.py")

        # Execute async check command
        async_command = CheckAsyncCommand()
        async_analysis = await async_command.execute(temp_project_directory / "src" / "slow_code.py")

        # Assert
        # Test analysis should detect issues
        assert test_analysis is not None
        assert "issues_found" in test_analysis
        assert len(test_analysis["issues_found"]) >= 2  # No fixture, testing private method

        # Profiler analysis should detect performance issues
        assert profiler_analysis is not None
        assert "performance_issues" in profiler_analysis
        assert "sequential_processing" in str(profiler_analysis["performance_issues"])

        # Async analysis should detect blocking calls
        assert async_analysis is not None
        assert "blocking_operations" in async_analysis
        assert len(async_analysis["blocking_operations"]) >= 1

    @pytest.mark.integration
    async def test_error_handling_and_recovery(self):
        """Given error scenarios, when workflow encounters errors, then handles gracefully."""
        # Arrange
        invalid_code = '''
def syntax_error(
    # Missing closing parenthesis
    pass

class AnotherClass:
    def method(self
        # Missing closing parenthesis and colon
            return "syntax error"
        '''

        # Act

        skill = LanguageDetectionSkill()

        # Should not crash on invalid syntax
        try:
            result = skill.detect_language(invalid_code)
            # If successful, should indicate issues
            assert result["language"] == "unknown" or "error" in result
        except Exception as e:
            # Should handle gracefully
            assert isinstance(e, (SyntaxError, ValueError))

    @pytest.mark.integration
    async def test_configuration_driven_workflow(self, temp_project_directory):
        """Given custom configuration, when workflow runs, then respects settings."""
        # Arrange
        config = {
            "python_version": "3.11",
            "focus_areas": ["performance", "async", "testing"],
            "exclude_patterns": ["*_test.py", "test_*.py"],
            "quality_thresholds": {
                "complexity": 10,
                "coverage": 80
            }
        }

        # Add configuration file
        (temp_project_directory / "parseltongue.json").write_text(json.dumps(config, indent=2))

        # Add some code files
        (temp_project_directory / "app.py").write_text('''
import asyncio
from typing import List

class AppConfig:
    def __init__(self):
        self.settings = {}

async def main():
    config = AppConfig()
    print("Application started")
    await asyncio.sleep(1)
    print("Application finished")

if __name__ == "__main__":
    asyncio.run(main)
        ''')

        (temp_project_directory / "test_app.py").write_text('''
def test_app_config():
    config = AppConfig()
    assert config.settings == {}
        ''')

        # Act
        from parseltongue.workflow.configurable_workflow import ConfigurableWorkflow

        workflow = ConfigurableWorkflow(config)
        analysis = await workflow.analyze_project(temp_project_directory)

        # Assert
        assert analysis is not None
        assert "configuration_applied" in analysis
        assert analysis["configuration_applied"]["python_version"] == "3.11"

        # Should exclude test files based on config
        analyzed_files = analysis["analyzed_files"]
        test_files = [f for f in analyzed_files if "test" in f]
        assert len(test_files) == 0  # Should be excluded

    @pytest.mark.integration
    async def test_performance_with_large_codebase(self):
        """Given large codebase, when analyzing, then maintains acceptable performance."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create many Python files
            for i in range(50):
                file_path = project_path / f"module_{i}.py"
                file_path.write_text(f'''
class Module{i}:
    def __init__(self):
        self.name = "module_{i}"
        self.items = []

    def process_item(self, item):
        return f"processed_{{item}}"

    async def async_process(self, items):
        results = []
        for item in items:
            result = await self.async_process_item(item)
            results.append(result)
        return results

    async def async_process_item(self, item):
        await asyncio.sleep(0.001)
        return item.upper()
                ''')

            # Act
            import time
            start_time = time.time()

            from parseltongue.workflows.batch_analyzer import BatchAnalyzer

            analyzer = BatchAnalyzer()
            results = await analyzer.analyze_directory(project_path)

            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 10.0  # Should complete within 10 seconds
            assert len(results) >= 50
            assert all("analysis" in result for result in results.values())

    @pytest.mark.integration
    async def test_plugin_lifecycle_management(self):
        """Given plugin usage, when managing lifecycle, then handles resources properly."""
        # Arrange
        from parseltongue.plugin import ParseltonguePlugin

        plugin = ParseltonguePlugin()

        # Act
        # Initialize plugin
        await plugin.initialize()

        # Use plugin
        result = await plugin.analyze_code("print('hello world')")

        # Cleanup plugin
        await plugin.cleanup()

        # Assert
        assert result is not None
        assert plugin.is_initialized is False  # Should be cleaned up

    @pytest.mark.integration
    async def test_real_world_scenario_analysis(self, temp_project_directory):
        """Given realistic Python project, when analyzing, then provides actionable insights."""
        # Arrange - Create a realistic FastAPI project
        (temp_project_directory / "src" / "api" / "__init__.py").write_text("")

        (temp_project_directory / "src" / "api" / "models.py").write_text("""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

class UserUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
        """)

        (temp_project_directory / "src" / "api" / "services.py").write_text("""
from typing import List, Optional
import asyncio
from .models import User, UserCreate

class UserService:
    def __init__(self, db_session):
        self.db = db_session
        self.cache = {}

    async def create_user(self, user_data: UserCreate) -> User:
        # Hash password
        hashed_password = hash_password(user_data.password)

        # Check if email exists
        existing = await self.get_user_by_email(user_data.email)
        if existing:
            raise ValueError("Email already exists")

        # Create user
        user = User(
            email=user_data.email,
            name=user_data.name,
            hashed_password=hashed_password
        )

        self.db.add(user)
        await self.db.commit()

        # Clear cache
        self.cache.pop(f"user:{user_data.email}", None)

        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        cache_key = f"user:{email}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        user = await self.db.query(User).filter(User.email == email).first()

        # Cache the result
        self.cache[cache_key] = user

        return user

    async def get_users_paginated(self, skip: int = 0, limit: int = 100):
        return await self.db.query(User).offset(skip).limit(limit).all()
        """)

        (temp_project_directory / "tests" / "test_services.py").write_text("""
import pytest
from unittest.mock import AsyncMock
from src.api.services import UserService
from src.api.models import UserCreate

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def user_service(mock_db):
    return UserService(mock_db)

@pytest.mark.asyncio
async def test_create_user_success(user_service, mock_db):
    user_data = UserCreate(
        email="test@example.com",
        name="Test User",
        password="password123"
    )

    # Mock database operations
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add.return_value = None
    mock_db.commit.return_value = None

    user = await user_service.create_user(user_data)

    assert user.email == "test@example.com"
    assert user.name == "Test User"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_duplicate_email(user_service, mock_db):
    user_data = UserCreate(
        email="test@example.com",
        name="Test User",
        password="password123"
    )

    # Mock existing user
    existing_user = User(id=1, email="test@example.com", name="Existing")
    mock_db.query.return_value.filter.return_value.first.return_value = existing_user

    with pytest.raises(ValueError, match="Email already exists"):
        await user_service.create_user(user_data)
        """)

        # Act
        from parseltongue.workflows.fastapi_analyzer import FastAPIAnalyzer

        analyzer = FastAPIAnalyzer()
        analysis = await analyzer.analyze_project(temp_project_directory)

        # Assert
        assert analysis is not None
        assert "project_type" in analysis
        assert analysis["project_type"] == "fastapi"

        # Should detect FastAPI patterns
        assert "fastapi_patterns" in analysis
        assert "pydantic_models" in analysis["fastapi_patterns"]
        assert "async_services" in analysis["fastapi_patterns"]

        # Should analyze security patterns
        assert "security_analysis" in analysis
        assert "password_handling" in analysis["security_analysis"]
        assert "email_validation" in analysis["security_analysis"]

        # Should analyze performance patterns
        assert "performance_analysis" in analysis
        assert "caching" in analysis["performance_analysis"]
        assert "database_queries" in analysis["performance_analysis"]

        # Should provide recommendations
        assert "recommendations" in analysis
        assert len(analysis["recommendations"]) >= 2
