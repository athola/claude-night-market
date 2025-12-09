"""
Unit tests for the API review skill.

Tests API surface detection, interface validation,
and public API quality assessment.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

# Import the skill we're testing
from pensive.skills.api_review import ApiReviewSkill


class TestApiReviewSkill:
    """Test suite for ApiReviewSkill business logic."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.skill = ApiReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path("/tmp/test_repo")
        self.mock_context.working_dir = Path("/tmp/test_repo")

    @pytest.mark.unit
    def test_detects_typescript_exports(self, mock_skill_context):
        """Given TypeScript code with exports, when skill analyzes, then identifies API exports."""
        # Arrange
        mock_skill_context.get_file_content.return_value = """
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

        # Act
        api_surface = self.skill.analyze_typescript_api(
            mock_skill_context, "src/auth.ts"
        )

        # Assert
        assert "exports" in api_surface
        assert (
            api_surface["exports"] >= 4
        )  # User interface, AuthService class, API_VERSION, validateEmail
        assert "classes" in api_surface
        assert api_surface["classes"] >= 1  # AuthService
        assert "interfaces" in api_surface
        assert api_surface["interfaces"] >= 1  # User

    @pytest.mark.unit
    def test_detects_rust_public_api(self, mock_skill_context):
        """Given Rust code with pub items, when skill analyzes, then identifies public API."""
        # Arrange
        mock_skill_context.get_file_content.return_value = """
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

        # Act
        api_surface = self.skill.analyze_rust_api(
            mock_skill_context, "src/user_service.rs"
        )

        # Assert
        assert "structs" in api_surface
        assert api_surface["structs"] >= 2  # User, UserService
        assert "functions" in api_surface
        assert api_surface["functions"] >= 2  # new(), add_user(), fetch_user()
        assert "public_methods" in api_surface
        assert api_surface["public_methods"] >= 3

    @pytest.mark.unit
    def test_detects_python_exports(self, mock_skill_context):
        """Given Python code with __all__, when skill analyzes, then identifies public API."""
        # Arrange
        mock_skill_context.get_file_content.return_value = """
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

        # Act
        api_surface = self.skill.analyze_python_api(
            mock_skill_context, "auth_service.py"
        )

        # Assert
        assert "exports" in api_surface
        assert (
            api_surface["exports"] >= 4
        )  # User, AuthService, calculate_total, API_VERSION
        assert "classes" in api_surface
        assert api_surface["classes"] >= 2  # User, AuthService
        assert "functions" in api_surface
        assert api_surface["functions"] >= 1  # calculate_total

    @pytest.mark.unit
    def test_detects_javascript_es6_exports(self, mock_skill_context):
        """Given JavaScript ES6 modules, when skill analyzes, then identifies exports."""
        # Arrange
        mock_skill_context.get_file_content.return_value = """
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

        # Act
        api_surface = self.skill.analyze_javascript_api(
            mock_skill_context, "calculator.js"
        )

        # Assert
        assert "exports" in api_surface
        assert (
            api_surface["exports"] >= 4
        )  # Calculator class, PI constant, factorial function, default export
        assert "classes" in api_surface
        assert api_surface["classes"] >= 1  # Calculator
        assert "functions" in api_surface
        assert api_surface["functions"] >= 1  # factorial

    @pytest.mark.unit
    def test_identifies_missing_documentation(self, mock_skill_context):
        """Given undocumented API exports, when skill analyzes, then flags missing docs."""
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
        issues = self.skill.check_documentation(mock_skill_context, "service.ts")

        # Assert
        assert len(issues) > 0
        doc_issues = [
            issue for issue in issues if "documentation" in issue["issue"].lower()
        ]
        assert len(doc_issues) >= 2  # Should flag missing docs for class and function

    @pytest.mark.unit
    def test_identifies_inconsistent_naming(self, mock_skill_context):
        """Given API with inconsistent naming, when skill analyzes, then flags naming issues."""
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
            mock_skill_context, "user_service.ts"
        )

        # Assert
        assert len(issues) > 0
        naming_issues = [
            issue for issue in issues if "naming" in issue["issue"].lower()
        ]
        assert len(naming_issues) >= 1  # Should detect inconsistent naming patterns

    @pytest.mark.unit
    def test_identifies_missing_error_handling(self, mock_skill_context):
        """Given API without error handling, when skill analyzes, then flags missing error handling."""
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
        issues = self.skill.check_error_handling(mock_skill_context, "api_client.ts")

        # Assert
        assert len(issues) > 0
        error_issues = [issue for issue in issues if "error" in issue["issue"].lower()]
        assert (
            len(error_issues) >= 2
        )  # Should flag both methods for missing error handling

    @pytest.mark.unit
    def test_identifies_breaking_changes(self, mock_skill_context):
        """Given potential breaking changes, when skill analyzes, then flags compatibility issues."""
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
            {
                "previous_version": True  # Simulate we have previous version context
            },
        )

        # Assert
        assert len(issues) > 0
        breaking_issues = [
            issue for issue in issues if "breaking" in issue["issue"].lower()
        ]
        assert len(breaking_issues) >= 1

    @pytest.mark.unit
    def test_validates_rest_api_patterns(self, mock_skill_context):
        """Given REST API implementation, when skill analyzes, then validates REST patterns."""
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
                return fetch(`${this.baseURL}/users/delete/${id}`);  // Should use DELETE
            }
        }
        """

        # Act
        issues = self.skill.validate_rest_patterns(mock_skill_context, "user_api.ts")

        # Assert
        rest_issues = [
            issue
            for issue in issues
            if "rest" in issue["issue"].lower() or "method" in issue["issue"].lower()
        ]
        assert len(rest_issues) >= 1  # Should detect improper HTTP method usage

    @pytest.mark.unit
    def test_checks_input_validation(self, mock_skill_context):
        """Given API methods without validation, when skill analyzes, then flags missing validation."""
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
            mock_skill_context, "user_service.ts"
        )

        # Assert
        assert len(issues) > 0
        validation_issues = [
            issue for issue in issues if "validation" in issue["issue"].lower()
        ]
        assert len(validation_issues) >= 2  # Should flag multiple methods

    @pytest.mark.unit
    def test_analyzes_api_versioning(self, mock_skill_context):
        """Given API implementation, when skill analyzes, then checks versioning strategy."""
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
        versioning_analysis = self.skill.analyze_versioning(
            mock_skill_context, "auth_service.ts"
        )

        # Assert
        assert "versioning_detected" in versioning_analysis
        assert "inconsistencies" in versioning_analysis
        # Should detect inconsistent versioning
        assert len(versioning_analysis["inconsistencies"]) > 0

    @pytest.mark.unit
    def test_checks_api_security_practices(self, mock_skill_context):
        """Given API implementation, when skill analyzes, then checks security practices."""
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
            mock_skill_context, "api_client.ts"
        )

        # Assert
        assert len(security_issues) > 0
        critical_issues = [
            issue
            for issue in security_issues
            if issue["severity"] == "critical" or "api key" in issue["issue"].lower()
        ]
        assert len(critical_issues) >= 1  # Should detect API key exposure

    @pytest.mark.unit
    def test_analyzes_api_performance_implications(self, mock_skill_context):
        """Given API implementation, when skill analyzes, then identifies performance issues."""
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
                    const order = await database.collection('orders').findOne({id: orderId});
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
            mock_skill_context, "data_service.ts"
        )

        # Assert
        assert len(performance_issues) > 0
        perf_issues = [
            issue
            for issue in performance_issues
            if "performance" in issue["issue"].lower()
            or "pagination" in issue["issue"].lower()
        ]
        assert len(perf_issues) >= 1  # Should detect pagination or N+1 issues

    @pytest.mark.unit
    def test_handles_empty_api_surface(self, mock_skill_context):
        """Given file with no exports, when skill analyzes, then handles gracefully."""
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
            mock_skill_context, "internal.ts"
        )

        # Assert
        assert api_surface is not None
        assert "exports" in api_surface
        assert api_surface["exports"] == 0  # Should detect no public exports

    @pytest.mark.unit
    def test_generates_api_summary_report(self, sample_findings):
        """Given API analysis findings, when skill generates report, then creates comprehensive summary."""
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
        assert "## API Surface Summary" in report
        assert "## Issues Found" in report
        assert "## Recommendations" in report
        assert "15" in report  # Total exports count
        assert "typescript" in report.lower()
        assert "rust" in report.lower()
