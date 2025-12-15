"""Test configuration and shared fixtures for the pensive plugin test suite.

This module provides common fixtures, test data, and utilities
for testing pensive skills, agents, and workflows.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

# Test data constants
SAMPLE_REPOSITORY_CONTENT = """
// Core application logic
export class AuthService {
    private apiKey: string;

    constructor(apiKey: string) {
        if (!apiKey) {
            throw new Error("API key is required");
        }
        this.apiKey = apiKey;
    }

    public async authenticate(token: string): Promise<boolean> {
        try {
            const response = await fetch('/api/auth', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'X-API-Key': this.apiKey
                }
            });
            return response.ok;
        } catch (error) {
            console.error("Authentication failed:", error);
            return false;
        }
    }

    public refreshToken(oldToken: string): string {
        // Simple token refresh logic
        return oldToken + "_refreshed";
    }
}

// Utility functions
export function calculateTotal(
    items: Array<{price: number, quantity: number}>
): number {
    return items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
}

// Constants
export const API_ENDPOINTS = {
    AUTH: '/api/auth',
    USERS: '/api/users',
    ORDERS: '/api/orders'
} as const;
"""

SAMPLE_RUST_CONTENT = """
use std::sync::{Arc, Mutex};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: u64,
    pub name: String,
    pub email: String,
}

pub struct UserService {
    users: Arc<Mutex<Vec<User>>>,
}

impl UserService {
    pub fn new() -> Self {
        Self {
            users: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub fn add_user(&self, user: User) -> Result<(), String> {
        let mut users = self.users.lock().unwrap();
        if users.iter().any(|u| u.email == user.email) {
            return Err("Email already exists".to_string());
        }
        users.push(user);
        Ok(())
    }

    pub fn get_user(&self, id: u64) -> Option<User> {
        let users = self.users.lock().unwrap();
        users.iter().find(|u| u.id == id).cloned()
    }

    pub fn update_user(&self, id: u64, name: String) -> Result<(), String> {
        let mut users = self.users.lock().unwrap();
        if let Some(user) = users.iter_mut().find(|u| u.id == id) {
            user.name = name;
            Ok(())
        } else {
            Err("User not found".to_string())
        }
    }
}

unsafe impl Send for UserService {}
unsafe impl Sync for UserService {}
"""

SAMPLE_MAKEFILE = """
# Makefile for build automation

.PHONY: all build test clean lint format

# Default target
all: build test

# Build the application
build:
	@echo "Building application..."
	cargo build --release

# Run tests
test:
	@echo "Running tests..."
	cargo test --all-features

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	cargo clean
	rm -rf dist/

# Run linter
lint:
	@echo "Running linter..."
	cargo clippy -- -D warnings

# Format code
format:
	@echo "Formatting code..."
	cargo fmt

# Build documentation
docs:
	@echo "Building documentation..."
	cargo doc --no-deps

# Run security audit
audit:
	@echo "Running security audit..."
	cargo audit
"""

SAMPLE_PYTHON_TESTS = """
import pytest
from unittest.mock import Mock, patch
from auth_service import AuthService

class TestAuthService:
    \"\"\"Test suite for AuthService functionality.\"\"\"

    def setup_method(self):
        \"\"\"Set up test fixtures before each test.\"\"\"
        self.api_key = "test-api-key-123"
        self.auth_service = AuthService(self.api_key)

    def test_init_with_valid_key(self):
        \"\"\"Test successful initialization with valid API key.\"\"\"
        assert self.auth_service.api_key == self.api_key

    def test_init_with_empty_key_raises_error(self):
        \"\"\"Test that empty API key raises ValueError.\"\"\"
        with pytest.raises(ValueError, match="API key is required"):
            AuthService("")

    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        \"\"\"Test successful authentication with valid token.\"\"\"
        with patch('auth_service.fetch') as mock_fetch:
            mock_fetch.return_value.ok = True
            result = await self.auth_service.authenticate("valid-token")
            assert result is True

    def test_refresh_token(self):
        \"\"\"Test token refresh functionality.\"\"\"
        old_token = "old-token"
        new_token = self.auth_service.refreshToken(old_token)
        assert new_token == old_token + "_refreshed"
"""


@pytest.fixture
def temp_repository():
    """Create a temporary repository structure with sample files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)

        # Create source files
        src_dir = repo_path / "src"
        src_dir.mkdir()

        # JavaScript/TypeScript files
        (src_dir / "auth.ts").write_text(SAMPLE_REPOSITORY_CONTENT)
        (src_dir / "utils.ts").write_text("export function helper() { return true; }")

        # Rust files
        rust_dir = repo_path / "rust"
        rust_dir.mkdir()
        (rust_dir / "user_service.rs").write_text(SAMPLE_RUST_CONTENT)
        (rust_dir / "Cargo.toml").write_text("""
[package]
name = "user-service"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.0", features = ["full"] }
        """)

        # Python test files
        test_dir = repo_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_auth.py").write_text(SAMPLE_PYTHON_TESTS)

        # Build files
        (repo_path / "Makefile").write_text(SAMPLE_MAKEFILE)
        (repo_path / "package.json").write_text("""
{
    "name": "test-app",
    "version": "1.0.0",
    "scripts": {
        "test": "jest",
        "build": "webpack",
        "lint": "eslint src/"
    },
    "dependencies": {
        "express": "^4.18.0"
    }
}
        """)

        # Initialize git repository
        subprocess.run(["git", "init"], check=False, cwd=repo_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            check=False,
            cwd=repo_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            check=False,
            cwd=repo_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "add", "."],
            check=False,
            cwd=repo_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            check=False,
            cwd=repo_path,
            capture_output=True,
        )

        yield repo_path


@pytest.fixture
def mock_skill_context():
    """Create a mock skill context for testing."""
    context = Mock()
    context.repo_path = Path(tempfile.gettempdir()) / "test_repo"
    context.working_dir = Path(tempfile.gettempdir()) / "test_repo"
    context.get_file_diffs.return_value = []
    context.get_staged_files.return_value = []
    context.get_unstaged_files.return_value = []
    return context


@pytest.fixture
def sample_findings():
    """Sample code review findings for testing."""
    return [
        {
            "id": "SEC001",
            "title": "Hardcoded API Key",
            "location": "src/auth.ts:5",
            "severity": "high",
            "issue": "API key is hardcoded in source code",
            "fix": "Use environment variables or secret management",
            "code_snippet": "private apiKey: string = 'hardcoded-key';",
        },
        {
            "id": "BUG001",
            "title": "Uncaught Exception",
            "location": "src/auth.ts:18",
            "severity": "medium",
            "issue": "Generic exception catching may mask errors",
            "fix": "Catch specific exception types",
            "code_snippet": "} catch (error) { console.error('Auth failed:', error); }",
        },
        {
            "id": "PERF001",
            "title": "Inefficient Loop",
            "location": "rust/user_service.rs:25",
            "severity": "low",
            "issue": "Linear search through users for every query",
            "fix": "Consider using HashMap for O(1) lookup",
            "code_snippet": "users.iter().find(|u| u.id == id)",
        },
    ]


@pytest.fixture
def mock_agent_response() -> str:
    """Create a mock agent response for testing."""
    return """## Summary
Overall code quality is good with some security improvements needed.

## Findings
### [SEC001] Hardcoded API Key
- **Location**: src/auth.ts:5
- **Severity**: High
- **Issue**: API key is hardcoded in source code
- **Fix**: Use environment variables or secret management
- **Code**: `private apiKey: string = 'hardcoded-key';`

### [BUG001] Uncaught Exception
- **Location**: src/auth.ts:18
- **Severity**: Medium
- **Issue**: Generic exception catching may mask errors
- **Fix**: Catch specific exception types
- **Code**: `} catch (error) { console.error('Auth failed:', error); }`

## Action Items
- [high] Move API keys to environment variables - Security Team - Today
- [medium] Add specific exception handling - Dev Team - This week

## Recommendation
Approve with actions
"""


class MockTodoWrite:
    """Mock TodoWrite for testing progress tracking."""

    def __init__(self) -> None:
        self.todos = []

    def add(
        self,
        content: str,
        status: str = "pending",
        active_form: str | None = None,
    ) -> None:
        """Add a todo item."""
        self.todos.append(
            {
                "content": content,
                "status": status,
                "activeForm": active_form or content,
            },
        )

    def update_status(self, index: int, status: str) -> None:
        """Update todo status."""
        if 0 <= index < len(self.todos):
            self.todos[index]["status"] = status

    def get_by_status(self, status: str):
        """Get todos by status."""
        return [t for t in self.todos if t["status"] == status]


@pytest.fixture
def mock_todo_write():
    """Create a mock TodoWrite instance."""
    return MockTodoWrite()


# Test markers for categorization
pytest_plugins = []


def pytest_configure(config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Mark test as unit test")
    config.addinivalue_line("markers", "integration: Mark test as integration test")
    config.addinivalue_line("markers", "slow: Mark test as slow running")
    config.addinivalue_line("markers", "security: Mark test as security-focused")
    config.addinivalue_line(
        "markers",
        "architecture: Mark test as architecture-focused",
    )
    config.addinivalue_line("markers", "performance: Mark test as performance-focused")
