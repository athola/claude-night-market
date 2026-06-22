"""Detection mixin: null pointer, race, memory, SQL, bounds, overflow."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ...utils import content_parser
from ..base import PatternSearch


class DetectionMixin:
    """Detects null pointer, race conditions, memory leaks, SQL injection,
    off-by-one, and integer overflow bugs."""

    if TYPE_CHECKING:

        def _detect_patterns(
            self,
            context: Any,
            filename: str,
            patterns: list[tuple[str, str]],
            content_parser_: Any,
            *,
            search: PatternSearch | None = None,
        ) -> list[dict[str, str]]: ...

    def detect_null_pointer_dereference(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, str]]:
        """Detect potential null pointer dereference bugs."""
        patterns = [
            (
                r"(\w+)\.(\w+)\.(\w+)",
                "Null/undefined dereference: Potential null/undefined dereference"
                " on chained access",
            ),
            (
                r"const\s+(\w+)\s*=\s*\w+\(\);\s*\n.*\1\.(\w+)",
                "Null/undefined dereference: Accessing property after function"
                " that might return null",
            ),
            (
                r"return\s+(\w+)\.(\w+)",
                "Null/undefined dereference: Potential null dereference in"
                " return statement",
            ),
        ]

        return self._detect_patterns(
            context,
            filename,
            patterns,
            content_parser,
            search=PatternSearch(patterns, "null_pointer", re.MULTILINE),
        )

    def detect_race_conditions(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, str]]:
        """Detect potential race condition bugs."""
        patterns = [
            (
                r"threading\.Thread\(target=",
                "Race condition or thread safety issue: Thread created"
                " - race condition without synchronization",
            ),
            (
                r"if\s+self\.(\w+).*:\s*\n\s*.*self\.\1",
                "Race condition or thread safety issue: Check-then-act"
                " pattern: race condition or thread safety",
            ),
            (
                r"self\.(\w+)\s*[+\-*/]?=",
                "Race condition or thread safety issue: Shared state"
                " modification without lock - thread safety concern",
            ),
            (
                r"time\.sleep\(",
                "Race condition or thread safety issue: Sleep in potential"
                " critical section - race condition window",
            ),
        ]

        return self._detect_patterns(
            context,
            filename,
            patterns,
            content_parser,
            search=PatternSearch(patterns, "race_condition", re.MULTILINE | re.DOTALL),
        )

    def detect_memory_leaks(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, str]]:
        """Detect potential memory leak bugs."""
        patterns = [
            (
                r"addEventListener\(",
                "Memory leak or event listener issue: Event listener added"
                " - potential memory leak if not removed",
            ),
            (
                r"\.push\(.*\)",
                "Memory leak or event listener issue: Array/cache growing"
                " - potential memory leak without cleanup",
            ),
            (
                r"var\s+\w*[Cc]ache\s*=\s*\[\]",
                "Memory leak or event listener issue: Global cache"
                " - potential memory leak",
            ),
            (
                r"\.set\(",
                "Memory leak or event listener issue: Map/Set growing"
                " - potential memory leak without eviction",
            ),
            (
                r"(\w+)\.ref\s*=\s*(\w+).*\n.*\2\.ref\s*=\s*\1",
                "Memory leak or event listener issue: Circular reference"
                " - potential memory leak",
            ),
        ]

        return self._detect_patterns(
            context,
            filename,
            patterns,
            content_parser,
            search=PatternSearch(patterns, "memory_leak", re.MULTILINE),
        )

    def detect_sql_injection(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, str]]:
        """Detect potential SQL injection vulnerabilities."""
        patterns = [
            (
                r'f"SELECT.*\{',
                "SQL injection vulnerability: f-string with user input in query",
            ),
            (
                r"f'SELECT.*\{",
                "SQL injection vulnerability: f-string with user input in query",
            ),
            (
                r'"SELECT.*\+.*\+',
                "SQL injection vulnerability: string concatenation in query",
            ),
            (
                r"'SELECT.*\+.*\+",
                "SQL injection vulnerability: string concatenation in query",
            ),
            (
                r'"SELECT.*%s',
                "SQL injection vulnerability: format string in query"
                " (use parameterized queries)",
            ),
            (
                r'"SELECT.*\.format\(',
                "SQL injection vulnerability: .format() in query",
            ),
        ]

        return self._detect_patterns(
            context,
            filename,
            patterns,
            content_parser,
            search=PatternSearch(patterns, "sql_injection", re.IGNORECASE),
        )

    def detect_off_by_one_errors(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, str]]:
        """Detect potential off-by-one errors."""
        patterns = [
            (
                r"for.*<=\s*\w+\.length",
                "Off-by-one error: using <= with .length (should be <)",
            ),
            (
                r"for.*<=\s*len\(",
                "Off-by-one error: using <= with len() (should be <)",
            ),
            (
                r"range\(len\(\w+\)\s*\+\s*1\)",
                "Off-by-one error: range with len() + 1 may exceed bounds",
            ),
            (
                r"for\s*\(.*<=.*\.length",
                "Off-by-one error: <= in array iteration",
            ),
            (
                r"\[\w+:\w+\+1\]",
                "Off-by-one error: Potential off-by-one: slice with +1 adjustment",
            ),
        ]

        return self._detect_patterns(
            context,
            filename,
            patterns,
            content_parser,
            search=PatternSearch(patterns, "off_by_one", re.MULTILINE),
        )

    def detect_integer_overflow(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, str]]:
        """Detect potential integer overflow bugs."""
        code = content_parser.get_file_content(context, filename)
        bugs: list[dict[str, str]] = []

        patterns = [
            (r"\w+\s*\*\s*\w+", "Potential overflow in multiplication"),
            (r"\d{10,}", "Large number literal - potential overflow or precision loss"),
            (r"<<\s*\d+", "Bit shift operation - potential overflow"),
            (
                r"\w+\s*\+\s*\w+\s*#.*overflow",
                "Addition flagged for potential overflow",
            ),
            (r"\w+_size\s*=.*\+", "Buffer size calculation - potential overflow"),
        ]

        for pattern, issue_desc in patterns:
            for match in re.finditer(pattern, code, re.IGNORECASE):
                line_num = content_parser.find_line_number(code, match.start())
                bugs.append(
                    {
                        "type": "integer_overflow",
                        "location": f"{filename}:{line_num}",
                        "issue": f"Overflow risk: {issue_desc}",
                        "code": content_parser.extract_code_snippet(code, line_num),
                    }
                )

        return bugs
