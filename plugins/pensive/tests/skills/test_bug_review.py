"""Unit tests for the bug review skill.

Tests systematic bug detection, pattern matching,
and fix recommendation generation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

# Import the skill we're testing
from pensive.skills.bug_review import BugReviewSkill


class TestBugReviewSkill:
    """Test suite for BugReviewSkill business logic."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = BugReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path(tempfile.gettempdir()) / "test_repo"
        self.mock_context.working_dir = Path(tempfile.gettempdir()) / "test_repo"

    @pytest.mark.unit
    def test_detects_null_pointer_dereference(self, mock_skill_context) -> None:
        """Given potential null pointer usage, when skill analyzes, then flags NPD risks."""
        # Arrange
        code_with_npd = """
        function processUser(user) {
            // No null check before accessing user.name
            console.log(user.name.toUpperCase());
            return user.email.length;
        }

        function getAdmin() {
            // Function might return null
            if (Math.random() > 0.5) {
                return null;
            }
            return {name: "admin"};
        }

        const admin = getAdmin();
        console.log(admin.name);  // Potential NPD
        """

        mock_skill_context.get_file_content.return_value = code_with_npd

        # Act
        bugs = self.skill.detect_null_pointer_dereference(mock_skill_context, "user.js")

        # Assert
        assert len(bugs) > 0
        npd_bugs = [
            bug
            for bug in bugs
            if "null" in bug["issue"].lower() or "undefined" in bug["issue"].lower()
        ]
        assert len(npd_bugs) >= 2  # Should detect both NPD instances

    @pytest.mark.unit
    def test_detects_race_conditions(self, mock_skill_context) -> None:
        """Given concurrent code patterns, when skill analyzes, then flags race condition risks."""
        # Arrange
        race_condition_code = """
        import threading

        class BankAccount:
            def __init__(self, balance):
                self.balance = balance

            def deposit(self, amount):
                # Race condition: check-then-act without locking
                if self.balance >= 0:
                    self.balance += amount
                return self.balance

            def withdraw(self, amount):
                # Race condition: non-atomic operation
                if self.balance >= amount:
                    time.sleep(0.1)  # Context switch window
                    self.balance -= amount
                return self.balance

        # Shared account accessed by multiple threads
        account = BankAccount(100)
        threads = []
        for i in range(10):
            t = threading.Thread(target=account.withdraw, args=(10,))
            threads.append(t)
            t.start()
        """

        mock_skill_context.get_file_content.return_value = race_condition_code

        # Act
        race_bugs = self.skill.detect_race_conditions(
            mock_skill_context,
            "bank_account.py",
        )

        # Assert
        assert len(race_bugs) > 0
        assert any("race condition" in bug["issue"].lower() for bug in race_bugs)
        assert any("thread safety" in bug["issue"].lower() for bug in race_bugs)

    @pytest.mark.unit
    def test_detects_memory_leaks(self, mock_skill_context) -> None:
        """Given memory management code, when skill analyzes, then flags memory leak risks."""
        # Arrange
        memory_leak_code = """
        // JavaScript memory leaks
        class DataProcessor {
            constructor() {
                this.cache = new Map();
                this.eventListeners = [];
            }

            process(data) {
                // Memory leak: cache never cleared
                this.cache.set(data.id, data);

                // Memory leak: event listeners never removed
                const listener = () => console.log('processing');
                document.addEventListener('click', listener);
                this.eventListeners.push(listener);
            }

            // Missing cleanup method
        }

        // Global objects growing without bound
        var globalCache = [];
        function addItem(item) {
            globalCache.push(item);  // Never cleared
        }

        // Circular references
        function createCircularRefs() {
            const obj1 = {name: 'obj1'};
            const obj2 = {name: 'obj2'};
            obj1.ref = obj2;
            obj2.ref = obj1;  // Circular reference
            return {obj1, obj2};
        }
        """

        mock_skill_context.get_file_content.return_value = memory_leak_code

        # Act
        memory_bugs = self.skill.detect_memory_leaks(mock_skill_context, "processor.js")

        # Assert
        assert len(memory_bugs) > 0
        leak_types = [bug["issue"].lower() for bug in memory_bugs]
        assert any("memory leak" in leak_type for leak_type in leak_types)
        assert any("event listener" in leak_type for leak_type in leak_types)

    @pytest.mark.unit
    def test_detects_sql_injection_vulnerabilities(self, mock_skill_context) -> None:
        """Given database queries, when skill analyzes, then flags SQL injection risks."""
        # Arrange
        sql_injection_code = """
        import sqlite3

        class UserService:
            def __init__(self):
                self.db = sqlite3.connect('users.db')

            def get_user(self, user_id):
                # SQL injection vulnerability
                query = f"SELECT * FROM users WHERE id = {user_id}"
                cursor = self.db.execute(query)
                return cursor.fetchone()

            def search_users(self, name):
                # SQL injection vulnerability
                query = "SELECT * FROM users WHERE name = '" + name + "'"
                cursor = self.db.execute(query)
                return cursor.fetchall()

            def get_user_safe(self, user_id):
                # Safe parameterized query
                query = "SELECT * FROM users WHERE id = ?"
                cursor = self.db.execute(query, (user_id,))
                return cursor.fetchone()
        """

        mock_skill_context.get_file_content.return_value = sql_injection_code

        # Act
        sql_bugs = self.skill.detect_sql_injection(
            mock_skill_context,
            "user_service.py",
        )

        # Assert
        assert len(sql_bugs) >= 2  # Should detect 2 vulnerabilities, not the safe one
        vuln_bugs = [bug for bug in sql_bugs if "sql injection" in bug["issue"].lower()]
        assert len(vuln_bugs) >= 2

    @pytest.mark.unit
    def test_detects_off_by_one_errors(self, mock_skill_context) -> None:
        """Given loop and array access code, when skill analyzes, then flags off-by-one risks."""
        # Arrange
        off_by_one_code = """
        function processArray(items) {
            const result = [];
            // Off-by-one error: should be < items.length, not <=
            for (let i = 0; i <= items.length; i++) {
                result.push(items[i] * 2);
            }
            return result;
        }

        function getSubarray(array, start, end) {
            const subarray = [];
            // Off-by-one error: exclusive vs inclusive bounds
            for (let i = start; i <= end; i++) {
                subarray.push(array[i]);
            }
            return subarray;
        }

        // Python version
        def process_list(items):
            result = []
            # Off-by-one error: range should be len(items), not len(items) + 1
            for i in range(len(items) + 1):
                result.append(items[i] * 2)
            return result

        def get_slice(lst, start, end):
            # Off-by-one error: slicing inconsistency
            return lst[start:end+1]  # Might be intentional but risky
        """

        mock_skill_context.get_file_content.return_value = off_by_one_code

        # Act
        off_by_one_bugs = self.skill.detect_off_by_one_errors(
            mock_skill_context,
            "arrays.js",
        )

        # Assert
        assert len(off_by_one_bugs) > 0
        assert any("off-by-one" in bug["issue"].lower() for bug in off_by_one_bugs)

    @pytest.mark.unit
    def test_detects_integer_overflow(self, mock_skill_context) -> None:
        """Given numeric operations, when skill analyzes, then flags overflow risks."""
        # Arrange
        overflow_code = """
        # Integer overflow vulnerabilities
        def calculate_total_price(quantity, unit_price):
            # No overflow check
            return quantity * unit_price

        def process_transaction(amount):
            # Unsafe addition
            balance = get_balance()
            new_balance = balance + amount  # Could overflow
            return new_balance

        # Buffer size calculation
        buffer_size = user_input + 100  # Could overflow to small value
        buffer = malloc(buffer_size)

        # JavaScript number precision issues
        function calculateLargeNumber(value) {
            return value * 10000000000000000;  // Could lose precision
        }

        # Bit shift overflow
        def shift_value(value):
            return value << 32  # Overflow in 32-bit integers
        """

        mock_skill_context.get_file_content.return_value = overflow_code

        # Act
        overflow_bugs = self.skill.detect_integer_overflow(
            mock_skill_context,
            "calculator.py",
        )

        # Assert
        assert len(overflow_bugs) > 0
        assert any("overflow" in bug["issue"].lower() for bug in overflow_bugs)

    @pytest.mark.unit
    def test_detects_resource_leaks(self, mock_skill_context) -> None:
        """Given resource management code, when skill analyzes, then flags resource leaks."""
        # Arrange
        resource_leak_code = """
        import os
        import threading
        import socket

        def process_files():
            # File handle leak
            f = open('data.txt', 'r')
            content = f.read()
            # Missing f.close()

        def network_operation():
            # Socket leak
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('example.com', 80))
            sock.send(b'GET / HTTP/1.1\\r\\n\\r\\n')
            # Missing sock.close()

        class DatabaseConnection:
            def __init__(self):
                self.connection = self._create_connection()

            def query(self, sql):
                cursor = self.connection.cursor()
                cursor.execute(sql)
                # Missing cursor.close() and connection cleanup

        # Thread leak
        def start_worker():
            thread = threading.Thread(target=worker_function)
            thread.start()
            # Missing thread.join() or daemon thread management
        """

        mock_skill_context.get_file_content.return_value = resource_leak_code

        # Act
        resource_bugs = self.skill.detect_resource_leaks(
            mock_skill_context,
            "resource_manager.py",
        )

        # Assert
        assert len(resource_bugs) > 0
        leak_types = [bug["issue"].lower() for bug in resource_bugs]
        assert any(
            "file" in leak_type and "leak" in leak_type for leak_type in leak_types
        )
        assert any(
            "socket" in leak_type and "leak" in leak_type for leak_type in leak_types
        )

    @pytest.mark.unit
    def test_detects_logical_errors(self, mock_skill_context) -> None:
        """Given conditional logic, when skill analyzes, then flags logical fallacies."""
        # Arrange
        logical_error_code = """
        def validate_age(age):
            # Logic error: should be age >= 18, not age > 18
            if age > 18:
                return "Adult"
            else:
                return "Minor"

        def is_prime(n):
            if n < 2:
                return False
            # Logic error: should check up to sqrt(n), not n
            for i in range(2, n):
                if n % i == 0:
                    return False
            return True

        def calculate_discount(customer_type, amount):
            # Logic error: conditions are mutually exclusive but order matters
            if customer_type == "premium":
                return amount * 0.9
            elif customer_type == "vip":
                return amount * 0.8
            elif customer_type == "premium":  # Dead code
                return amount * 0.7
            else:
                return amount

        # Wrong comparison operator
        def check_threshold(value):
            # Should be <= not >=
            if value >= 100:
                return "Below threshold"
            return "Above threshold"
        """

        mock_skill_context.get_file_content.return_value = logical_error_code

        # Act
        logic_bugs = self.skill.detect_logical_errors(
            mock_skill_context,
            "validator.py",
        )

        # Assert
        assert len(logic_bugs) > 0
        assert any("logic error" in bug["issue"].lower() for bug in logic_bugs)

    @pytest.mark.unit
    def test_detects_type_confusion_bugs(self, mock_skill_context) -> None:
        """Given dynamic typing code, when skill analyzes, then flags type confusion risks."""
        # Arrange
        type_confusion_code = """
        # JavaScript type confusion
        function processValue(value) {
            // Type confusion: value might be string or number
            if (value > 100) {
                return value * 2;
            }
            return "small";
        }

        function addNumbers(a, b) {
            // Type confusion: string concatenation vs addition
            return a + b;  // "5" + 3 = "53", not 8
        }

        # Python type confusion
        def calculate_average(values):
            # Type confusion: values might contain non-numeric types
            total = sum(values)  # TypeError if values contains strings
            return total / len(values)

        def process_data(data):
            # Type confusion: data structure assumptions
            if isinstance(data, dict):
                return data['key']  # KeyError if key missing
            elif isinstance(data, list):
                return data[0]  # IndexError if list empty
            return data  # Unhandled types

        # PHP type juggling vulnerabilities
        function validate_password($input) {
            $expected = "0e123456789";  // String that evaluates to 0 in loose comparison
            if ($input == $expected) {  // Type juggling vulnerability
                return true;
            }
            return false;
        }
        """

        mock_skill_context.get_file_content.return_value = type_confusion_code

        # Act
        type_bugs = self.skill.detect_type_confusion(mock_skill_context, "processor.js")

        # Assert
        assert len(type_bugs) > 0
        assert any("type" in bug["issue"].lower() for bug in type_bugs)

    @pytest.mark.unit
    def test_detects_timing_attacks(self, mock_skill_context) -> None:
        """Given authentication/authorization code, when skill analyzes, then flags timing attack risks."""
        # Arrange
        timing_attack_code = """
        import time

        def insecure_compare(user_input, secret):
            # Timing attack vulnerable: early exit on first mismatch
            if len(user_input) != len(secret):
                return False

            for i in range(len(secret)):
                if user_input[i] != secret[i]:
                    return False
                time.sleep(0.01)  # Amplifies timing difference
            return True

        def verify_password(entered_password, stored_hash):
            # Timing attack: string comparison
            return entered_password == stored_hash

        def check_api_key(provided_key, valid_key):
            # Timing attack: character by character comparison
            if len(provided_key) != len(valid_key):
                return False

            result = True
            for i in range(len(valid_key)):
                if provided_key[i] != valid_key[i]:
                    result = False
            return result

        # Secure version for comparison
        def secure_compare(a, b):
            # Use constant-time comparison
            return hmac.compare_digest(a, b)
        """

        mock_skill_context.get_file_content.return_value = timing_attack_code

        # Act
        timing_bugs = self.skill.detect_timing_attacks(mock_skill_context, "auth.py")

        # Assert
        assert len(timing_bugs) >= 3  # Should detect 3 vulnerable functions
        assert any("timing attack" in bug["issue"].lower() for bug in timing_bugs)

    @pytest.mark.unit
    def test_categorizes_bug_severity(self) -> None:
        """Given various bugs, when skill categorizes, then assigns appropriate severity."""
        # Arrange
        bugs = [
            {"type": "sql_injection", "issue": "SQL injection in user query"},
            {"type": "null_pointer", "issue": "Potential null dereference"},
            {"type": "off_by_one", "issue": "Array index out of bounds"},
            {"type": "performance", "issue": "Inefficient algorithm"},
        ]

        # Act
        categorized_bugs = self.skill.categorize_severity(bugs)

        # Assert
        severity_map = {bug["issue"]: bug["severity"] for bug in categorized_bugs}
        assert "sql injection" in severity_map
        assert (
            categorized_bugs[0]["severity"] == "critical"
        )  # SQL injection should be critical
        assert categorized_bugs[1]["severity"] in [
            "high",
            "medium",
        ]  # NPD should be high/medium
        assert categorized_bugs[2]["severity"] in [
            "medium",
            "low",
        ]  # Off-by-one should be medium/low

    @pytest.mark.unit
    def test_generates_fix_recommendations(self, mock_skill_context) -> None:
        """Given detected bugs, when skill generates fixes, then provides actionable solutions."""
        # Arrange
        bug_findings = [
            {
                "type": "sql_injection",
                "location": "user_service.py:15",
                "issue": "String concatenation in SQL query",
                "code": 'query = "SELECT * FROM users WHERE name = \'" + name + "\'"',
            },
            {
                "type": "null_pointer",
                "location": "processor.js:25",
                "issue": "Accessing user.name without null check",
                "code": "console.log(user.name.toUpperCase())",
            },
        ]

        # Act
        recommendations = self.skill.generate_fix_recommendations(bug_findings)

        # Assert
        assert len(recommendations) == len(bug_findings)
        for rec in recommendations:
            assert "fix" in rec
            assert "example" in rec
            assert "priority" in rec
            assert len(rec["fix"]) > 0
            assert len(rec["example"]) > 0

    @pytest.mark.unit
    def test_analyzes_bug_patterns(self, mock_skill_context) -> None:
        """Given bug history, when skill analyzes patterns, then identifies common bug types."""
        # Arrange
        bug_history = [
            {"type": "sql_injection", "file": "database.py", "date": "2024-01-01"},
            {"type": "sql_injection", "file": "user_service.py", "date": "2024-01-15"},
            {"type": "null_pointer", "file": "processor.js", "date": "2024-01-20"},
            {"type": "sql_injection", "file": "auth.py", "date": "2024-02-01"},
            {"type": "memory_leak", "file": "cache.js", "date": "2024-02-10"},
            {"type": "null_pointer", "file": "utils.py", "date": "2024-02-15"},
        ]

        # Act
        pattern_analysis = self.skill.analyze_bug_patterns(bug_history)

        # Assert
        assert "common_types" in pattern_analysis
        assert "trend_analysis" in pattern_analysis
        assert "recommendations" in pattern_analysis

        # SQL injection should be most common
        common_bugs = pattern_analysis["common_types"]
        assert common_bugs[0]["type"] == "sql_injection"
        assert common_bugs[0]["count"] == 3

    @pytest.mark.unit
    def test_validates_bug_fixes(self, mock_skill_context) -> None:
        """Given proposed bug fixes, when skill validates, then checks for correctness."""
        # Arrange
        bug_fixes = [
            {
                "bug": "SQL injection vulnerability",
                "original": "query = 'SELECT * FROM users WHERE id = ' + user_id",
                "fixed": "query = 'SELECT * FROM users WHERE id = ?', (user_id,)",
            },
            {
                "bug": "Null pointer dereference",
                "original": "return user.name.toUpperCase()",
                "fixed": "return user?.name?.toUpperCase() || 'Unknown'",
            },
        ]

        # Act
        validation_results = self.skill.validate_bug_fixes(bug_fixes)

        # Assert
        assert len(validation_results) == len(bug_fixes)
        for result in validation_results:
            assert "valid" in result
            assert "reasoning" in result
            assert "remaining_risks" in result

    @pytest.mark.unit
    def test_handles_false_positives(self, mock_skill_context) -> None:
        """Given benign code patterns, when skill analyzes, then avoids false positives."""
        # Arrange
        benign_code = """
        # These look like bugs but are actually correct
        def safe_string_concat(a, b):
            # This is intentional string concatenation, not SQL
            return a + " " + b

        def check_boundary(value):
            # This boundary check is correct
            if value >= 100:  # 100 is the valid upper bound
                return "valid"
            return "invalid"

        def safe_array_access(arr, index):
            # This has proper bounds checking
            if 0 <= index < len(arr):
                return arr[index]
            return None

        # This null check is sufficient for the context
        def process_optional_value(value):
            if value:  # Simple null check is appropriate here
                return value.upper()
            return "DEFAULT"
        """

        mock_skill_context.get_file_content.return_value = benign_code

        # Act
        false_positives = self.skill.detect_false_positives(
            mock_skill_context,
            "safe_code.py",
        )

        # Assert
        # Should identify these as potential false positives
        assert len(false_positives) >= 2
        for fp in false_positives:
            assert "false_positive" in fp
            assert "reason" in fp

    @pytest.mark.unit
    def test_creates_bug_summary_report(self, sample_findings) -> None:
        """Given comprehensive bug analysis, when skill creates report, then generates structured summary."""
        # Arrange
        bug_analysis = {
            "total_bugs": 15,
            "critical_bugs": 2,
            "high_priority_bugs": 5,
            "medium_priority_bugs": 6,
            "low_priority_bugs": 2,
            "bug_categories": {
                "security": 5,
                "performance": 3,
                "logic": 4,
                "memory": 3,
            },
            "fix_recommendations": sample_findings,
        }

        # Act
        report = self.skill.create_bug_report(bug_analysis)

        # Assert
        assert "## Bug Analysis Summary" in report
        assert "## Critical Issues" in report
        assert "## Bug Categories" in report
        assert "## Recommendations" in report
        assert "15" in report  # Total bugs
        assert "2" in report  # Critical bugs
        assert "security" in report.lower()
