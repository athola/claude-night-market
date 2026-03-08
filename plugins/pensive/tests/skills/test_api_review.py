"""Unit tests for the API review skill.

Tests API surface detection, interface validation,
and public API quality assessment.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add src directory to path for import
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# Import the skill we're testing
from pensive.skills.api_review import ApiReviewSkill


# ── Parametrized language API detection ─────────────────────

TYPESCRIPT_CODE = """
        export interface User {
            id: number;
            name: string;
            email: string;
        }

        export class AuthService {
            private apiKey: string;

            constructor(apiKey: string) {
                this.apiKey = apiKey;
            }

            public async login(credentials: Credentials): Promise<Token> {
                return await this.http.post('/auth/login', credentials);
            }

            public logout(): void {
                localStorage.removeItem('token');
            }
        }

        export const API_VERSION = 'v1';
        export function validateEmail(email: string): boolean {
            return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);
        }
        """

RUST_CODE = """
        use serde::{Deserialize, Serialize};

        #[derive(Debug, Serialize, Deserialize)]
        pub struct User {
            pub id: u64,
            pub name: String,
            email: String,  // Private field
        }

        pub struct UserService {
            users: Vec<User>,
        }

        impl UserService {
            pub fn new() -> Self {
                Self { users: Vec::new() }
            }

            pub fn add_user(&mut self, user: User) -> Result<(), String> {
                self.users.push(user);
                Ok(())
            }

            fn validate_user(&self, user: &User) -> bool {  // Private method
                !user.name.is_empty()
            }
        }

        pub async fn fetch_user(id: u64) -> Result<User, reqwest::Error> {
            let response = reqwest::get(&format!("/api/users/{}", id)).await?;
            response.json().await
        }
        """

PYTHON_CODE = """
        from typing import List, Optional
        from dataclasses import dataclass

        __all__ = ['User', 'AuthService', 'calculate_total', 'API_VERSION']

        @dataclass
        class User:
            id: int
            name: str
            email: str

        class AuthService:
            def __init__(self, api_key: str):
                self.api_key = api_key

            def authenticate(self, token: str) -> bool:
                return self._validate_token(token)

            def _validate_token(self, token: str) -> bool:  # Private method
                return len(token) > 10

        def calculate_total(items: List[dict]) -> float:
            return sum(item['price'] * item['quantity'] for item in items)

        API_VERSION = "1.0.0"
        """

JAVASCRIPT_CODE = """
        export class Calculator {
            constructor() {
                this.history = [];
            }

            add(a, b) {
                const result = a + b;
                this.history.push({operation: 'add', result});
                return result;
            }

            clear() {
                this.history = [];
            }
        }

        export const PI = 3.14159;

        export function factorial(n) {
            if (n <= 1) return 1;
            return n * factorial(n - 1);
        }

        export default Calculator;
        """

# Each tuple: (id, code, lang, method_name, expected_result)
LANGUAGE_API_CASES = [
    pytest.param(
        TYPESCRIPT_CODE,
        "typescript",
        "analyze_typescript_api",
        "src/auth.ts",
        {
            "exports": 4,
            "classes": 1,
            "interfaces": 1,
            "functions": 1,
            "default_exports": 0,
            "const_exports": 1,
        },
        id="typescript-exports",
    ),
    pytest.param(
        RUST_CODE,
        "rust",
        "analyze_rust_api",
        "src/user_service.rs",
        {
            "structs": 2,
            "functions": 3,
            "public_methods": 3,
        },
        id="rust-pub-api",
    ),
    pytest.param(
        PYTHON_CODE,
        "python",
        "analyze_python_api",
        "auth_service.py",
        {
            "exports": 4,
            "classes": 2,
            "functions": 4,
        },
        id="python-exports",
    ),
    pytest.param(
        JAVASCRIPT_CODE,
        "javascript",
        "analyze_javascript_api",
        "calculator.js",
        {
            "exports": 4,
            "classes": 1,
            "functions": 1,
            "default_exports": 1,
            "const_exports": 1,
        },
        id="javascript-es6-exports",
    ),
]


class TestApiReviewSkill:
    """Test suite for ApiReviewSkill business logic."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = ApiReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = (
            Path(tempfile.gettempdir()) / "test_repo"
        )
        self.mock_context.working_dir = (
            Path(tempfile.gettempdir()) / "test_repo"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "code,lang,method_name,filename,expected",
        LANGUAGE_API_CASES,
    )
    def test_detects_language_api_surface(
        self,
        mock_skill_context,
        code: str,
        lang: str,
        method_name: str,
        filename: str,
        expected: dict,
    ) -> None:
        """Given source code, when skill analyzes, then returns exact counts.

        Parametrized across TypeScript, Rust, Python, and JavaScript.
        """
        # Arrange
        mock_skill_context.get_file_content.return_value = code

        # Act
        method = getattr(self.skill, method_name)
        api_surface = method(mock_skill_context, filename)

        # Assert -- exact equality on every key
        for key, expected_value in expected.items():
            assert api_surface[key] == expected_value, (
                f"{lang} {key}: got {api_surface[key]}, "
                f"expected {expected_value}"
            )
        # Verify mock was called
        mock_skill_context.get_file_content.assert_called_once_with(
            filename,
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_identifies_missing_documentation(
        self, mock_skill_context
    ) -> None:
        """Given undocumented API exports, when skill analyzes,
        then flags missing docs with correct issue structure.
        """
        # Arrange
        mock_skill_context.get_file_content.return_value = """
        export class Service {
            constructor(config) {
                this.config = config;
            }

            processData(data) {
                return data.map(item => item.value);
            }
        }

        export function calculate(x, y) {
            return x * y;
        }
        """

        # Act
        issues = self.skill.check_documentation(
            mock_skill_context, "service.ts"
        )

        # Assert
        assert len(issues) == 2
        assert issues[0]["type"] == "missing_documentation"
        assert issues[0]["severity"] == "medium"
        assert "Service" in issues[0]["issue"]
        assert issues[1]["type"] == "missing_documentation"
        assert "calculate" in issues[1]["issue"]
        mock_skill_context.get_file_content.assert_called_once_with(
            "service.ts",
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_identifies_inconsistent_naming(
        self, mock_skill_context
    ) -> None:
        """Given inconsistent API naming, skill flags naming issues
        with correct severity and type.
        """
        # Arrange
        mock_skill_context.get_file_content.return_value = """
        export class UserService {
            getUser(id) { }  // camelCase

            GetUserByEmail(email) { }  // PascalCase

            get_user_preferences(id) { }  // snake_case

            GetUserRoles() { }  // PascalCase
        }

        export const API_ENDPOINT = '/api/users';
        export const api_version = 'v1';  // Inconsistent with above
        """

        # Act
        issues = self.skill.check_naming_consistency(
            mock_skill_context,
            "user_service.ts",
        )

        # Assert
        assert len(issues) == 1
        assert issues[0]["type"] == "naming_inconsistency"
        assert issues[0]["severity"] == "low"
        assert "api_version" in issues[0]["issue"]
        assert "naming" in issues[0]["issue"].lower()
        mock_skill_context.get_file_content.assert_called_once_with(
            "user_service.ts",
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_identifies_missing_error_handling(
        self, mock_skill_context
    ) -> None:
        """Given API lacks error handling, skill flags each method
        missing try-catch around fetch calls.
        """
        # Arrange
        mock_skill_context.get_file_content.return_value = """
        export class ApiClient {
            constructor(base_url) {
                this.base_url = base_url;
            }

            getUser(id) {
                // No error handling
                return fetch(`${this.base_url}/users/${id}`).then(res => res.json());
            }

            createUser(userData) {
                // No error handling for invalid data or network errors
                return fetch(`${this.base_url}/users`, {
                    method: 'POST',
                    body: JSON.stringify(userData)
                });
            }
        }
        """

        # Act
        issues = self.skill.check_error_handling(
            mock_skill_context, "api_client.ts"
        )

        # Assert
        assert len(issues) == 2
        for issue in issues:
            assert issue["type"] == "missing_error_handling"
            assert issue["severity"] == "high"
            assert "error" in issue["issue"].lower()
        method_names = {i["issue"].split()[1] for i in issues}
        assert "getUser" in method_names
        assert "createUser" in method_names
        mock_skill_context.get_file_content.assert_called_once_with(
            "api_client.ts",
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_identifies_breaking_changes(
        self, mock_skill_context
    ) -> None:
        """Given potential breaking changes, skill flags them with
        correct severity levels.
        """
        # Arrange
        mock_skill_context.get_file_content.return_value = """
        // Breaking change: removing existing export
        // export function oldMethod() { }

        // Breaking change: changing function signature
        export function processUser(userId, options = {}) {
            // Changed from (userData) to (userId, options)
        }

        // Breaking change: changing return type
        export function getUsers() {
            // Used to return array, now returns object with pagination
            return {
                users: [],
                total: 0,
                page: 1
            };
        }
        """

        # Act
        issues = self.skill.check_breaking_changes(
            mock_skill_context,
            "api.ts",
            {"previous_version": True},
        )

        # Assert
        assert len(issues) >= 1
        breaking_issues = [
            i for i in issues if i["type"] == "breaking_change"
        ]
        assert len(breaking_issues) >= 1
        severities = {i["severity"] for i in breaking_issues}
        assert severities <= {"critical", "high"}
        mock_skill_context.get_file_content.assert_called_once_with(
            "api.ts",
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_validates_rest_api_patterns(
        self, mock_skill_context
    ) -> None:
        """Given REST API with improper HTTP method usage, skill
        detects delete-via-GET violations.
        """
        # Arrange
        mock_skill_context.get_file_content.return_value = """
        export class UserAPI {
            constructor(baseURL) {
                this.baseURL = baseURL;
            }

            // Good: Proper REST patterns
            async getUsers() {
                return fetch(`${this.baseURL}/users`);
            }

            async getUser(id) {
                return fetch(`${this.baseURL}/users/${id}`);
            }

            async createUser(userData) {
                return fetch(`${this.baseURL}/users`, {
                    method: 'POST',
                    body: JSON.stringify(userData)
                });
            }

            // Issue: Using GET for mutation
            async deleteUser(id) {
                return fetch(`${this.baseURL}/users/delete/${id}`);
                // Should use DELETE
            }
        }
        """

        # Act
        issues = self.skill.validate_rest_patterns(
            mock_skill_context, "user_api.ts"
        )

        # Assert
        rest_issues = [
            i for i in issues if i["type"] == "rest_violation"
        ]
        assert len(rest_issues) >= 1
        assert rest_issues[0]["severity"] == "medium"
        mock_skill_context.get_file_content.assert_called_once_with(
            "user_api.ts",
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_checks_input_validation(
        self, mock_skill_context
    ) -> None:
        """Given API methods without input validation, skill flags
        each unvalidated parameter handler.
        """
        # Arrange
        mock_skill_context.get_file_content.return_value = """
        export class UserService {
            createUser(userData) {
                // No validation of userData
                users.push(userData);
                return userData;
            }

            updateUserEmail(userId, email) {
                // No email format validation
                const user = users.find(u => u.id === userId);
                user.email = email;
                return user;
            }

            searchUsers(query) {
                // No query validation or sanitization
                return users.filter(u =>
                    u.name.includes(query) || u.email.includes(query)
                );
            }
        }
        """

        # Act
        issues = self.skill.check_input_validation(
            mock_skill_context,
            "user_service.ts",
        )

        # Assert
        assert len(issues) >= 2
        for issue in issues:
            assert issue["type"] == "missing_validation"
            assert issue["severity"] == "medium"
            assert "validation" in issue["issue"].lower()
        mock_skill_context.get_file_content.assert_called_once_with(
            "user_service.ts",
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_api_versioning(
        self, mock_skill_context
    ) -> None:
        """Given mixed versioned and unversioned endpoints, skill
        detects the inconsistency.
        """
        # Arrange
        mock_skill_context.get_file_content.return_value = """
        // Good: Versioned API
        export const API_V1 = {
            BASE_URL: '/api/v1',
            ENDPOINTS: {
                USERS: '/users',
                AUTH: '/auth'
            }
        };

        // Issue: Mixed versioning
        export class AuthService {
            async login(credentials) {
                return fetch('/api/v1/auth/login', {  // v1
                    method: 'POST',
                    body: JSON.stringify(credentials)
                });
            }

            async getUserProfile(id) {
                return fetch(`/api/users/${id}`);  // No version
            }
        }
        """

        # Act
        result = self.skill.analyze_versioning(
            mock_skill_context,
            "auth_service.ts",
        )

        # Assert
        assert result["versioning_detected"] is True
        assert isinstance(result["inconsistencies"], list)
        assert len(result["inconsistencies"]) > 0
        mock_skill_context.get_file_content.assert_called_once_with(
            "auth_service.ts",
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_checks_api_security_practices(
        self, mock_skill_context
    ) -> None:
        """Given client code with security anti-patterns, skill
        detects API key exposure as critical.
        """
        # Arrange
        mock_skill_context.get_file_content.return_value = """
        export class APIClient {
            constructor(apiKey) {
                this.apiKey = apiKey;  // Security issue: API key in client code
            }

            async makeRequest(endpoint, data) {
                // Security issue: No authentication headers
                return fetch(endpoint, {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            }

            async uploadFile(file) {
                // Security issue: No file type validation
                const formData = new FormData();
                formData.append('file', file);
                return fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
            }
        }
        """

        # Act
        security_issues = self.skill.check_security_practices(
            mock_skill_context,
            "api_client.ts",
        )

        # Assert
        assert len(security_issues) >= 1
        critical_issues = [
            i for i in security_issues if i["severity"] == "critical"
        ]
        assert len(critical_issues) >= 1
        assert critical_issues[0]["type"] == "security_issue"
        assert "api key" in critical_issues[0]["issue"].lower()
        mock_skill_context.get_file_content.assert_called_once_with(
            "api_client.ts",
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_api_performance_implications(
        self, mock_skill_context
    ) -> None:
        """Given code with N+1 queries and missing pagination, skill
        detects performance issues.
        """
        # Arrange
        mock_skill_context.get_file_content.return_value = """
        export class DataService {
            async getAllUsers() {
                // Performance issue: No pagination, could return thousands of records
                const allUsers = await database.collection('users').find({}).toArray();
                return allUsers;
            }

            async getUserWithOrders(userId) {
                // Performance issue: N+1 query problem
                const user = await database.collection('users').findOne({id: userId});
                const orders = [];
                for (const orderId of user.orderIds) {
                    const order = await database
                        .collection("orders")
                        .findOne({ id: orderId });
                    orders.push(order);
                }
                return {user, orders};
            }

            async searchUsers(searchTerm) {
                // Performance issue: No search optimization
                const users = await database.collection('users').find({}).toArray();
                return users.filter(user =>
                    user.name.toLowerCase().includes(searchTerm.toLowerCase())
                );
            }
        }
        """

        # Act
        performance_issues = self.skill.analyze_performance_implications(
            mock_skill_context,
            "data_service.ts",
        )

        # Assert
        assert len(performance_issues) >= 1
        types = {i["type"] for i in performance_issues}
        assert types == {"performance_issue"}
        for issue in performance_issues:
            assert issue["severity"] in {"high", "medium"}
        mock_skill_context.get_file_content.assert_called_once_with(
            "data_service.ts",
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_empty_api_surface(
        self, mock_skill_context
    ) -> None:
        """Given file with no exports, when skill analyzes, then
        returns zero counts for every metric.
        """
        # Arrange
        mock_skill_context.get_file_content.return_value = """
        // Internal utility functions, no public API
        function internalHelper() {
            return 'internal';
        }

        const internalVariable = 'not exported';

        class InternalClass {
            privateMethod() {
                return 'private';
            }
        }
        """

        # Act
        api_surface = self.skill.analyze_typescript_api(
            mock_skill_context,
            "internal.ts",
        )

        # Assert
        assert api_surface["exports"] == 0
        assert api_surface["classes"] == 0
        assert api_surface["interfaces"] == 0
        assert api_surface["functions"] == 0
        assert api_surface["default_exports"] == 0
        assert api_surface["const_exports"] == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_generates_api_summary_report(self, sample_findings) -> None:
        """Given analysis data, skill generates markdown report
        containing all required sections and data.
        """
        # Arrange
        analysis_data = {
            "total_exports": 15,
            "languages": ["typescript", "rust"],
            "files_analyzed": 5,
            "issues_found": sample_findings,
        }

        # Act
        report = self.skill.generate_api_summary(analysis_data)

        # Assert
        assert report.startswith("## API Surface Summary")
        assert "Total exports: 15" in report
        assert "Files analyzed: 5" in report
        assert "Languages: typescript, rust" in report
        assert "## Issues Found" in report
        assert "## Recommendations" in report
