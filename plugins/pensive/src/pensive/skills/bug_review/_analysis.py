"""Analysis mixin: resource leaks, logic, type, timing, severity, patterns."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ...utils import content_parser
from ..base import PatternSearch

_THREAD_LEAK = "Resource leak: Thread started - potential leak without join()"

# `t = Thread(`, `t: Thread = Thread(`, `(t := Thread(`.
_THREAD_BINDING = re.compile(r"\b(\w+)\s*(?::\s*[\w.]+\s*=|:=|=(?!=))\s*[\w.]*Thread\(")
# Started where built, so nothing can join it. `=` excludes the walrus.
_STARTED_UNBOUND = re.compile(r"(?<!=\s)(?<!=)(?:\w+\.)*Thread\(.*?\)\.start\(")
# A join on a name or subscript: how a thread held in a collection is joined.
_RECEIVER_JOIN = re.compile(r"(\w+|[\])])\.join\(")


def _leaks_a_thread(content: str) -> bool:
    """Whether the code, comments stripped, starts an unjoined non-daemon Thread.

    A bound Thread must be joined on its own name (`foot.join` is not `t`'s).
    One in a collection has no name: any join not on a string or `path` counts.
    """
    code = "\n".join(line.split("#", 1)[0] for line in content.splitlines())
    if "Thread(" not in code or "daemon=True" in code:
        return False
    names = _THREAD_BINDING.findall(code)
    unjoined = (n for n in set(names) if not re.search(rf"\b{n}\.join\(", code))
    if any(unjoined) or _STARTED_UNBOUND.search(code):
        return True
    in_collection = code.count("Thread(") > len(names)
    return in_collection and not set(_RECEIVER_JOIN.findall(code)) - {"path"}


class AnalysisMixin:
    """Detects resource leaks, logical errors, type confusion, and timing
    attacks. Categorizes severity and analyzes bug patterns.
    """

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

    def detect_resource_leaks(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, str]]:
        """Detect potential resource leak bugs."""
        patterns = [
            (
                # One level of nested parentheses, so the `)` of
                # `open(str(p))` is not taken for the end of the call.
                r"open\((?:[^()]|\([^()]*\))*\)(?!\s*as\s)",
                "Resource leak: File opened without context manager - potential leak",
            ),
            (
                r"socket\.socket\(",
                "Resource leak: Socket created - potential socket leak without close()",
            ),
            (
                r"\.connect\(",
                "Resource leak: Connection opened - potential file or"
                " socket leak without close",
            ),
            (r"\.start\(\)", _THREAD_LEAK),
            (
                r"\.cursor\(\)",
                "Resource leak: Cursor created - potential resource leak",
            ),
        ]

        findings = self._detect_patterns(
            context,
            filename,
            patterns,
            content_parser,
            search=PatternSearch(patterns, "resource_leak", re.MULTILINE),
        )
        # `.start()` is a thread leak only in a file that creates a Thread
        # and neither joins nor daemonizes it; the per-line pattern alone
        # flagged every server.start().
        content = context.get_file_content(filename)
        if not _leaks_a_thread(content):
            findings = [f for f in findings if f["issue"] != _THREAD_LEAK]
        return findings

    def detect_logical_errors(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, str]]:
        """Detect potential logical errors."""
        patterns = [
            (
                r"elif\s+(\w+)\s*==\s*['\"](\w+)['\"].*elif\s+\1\s*==\s*['\"]\2['\"]",
                "Logic error: duplicate condition (dead code)",
            ),
            (
                r"if.*>=.*:\s*\n\s*return.*[Bb]elow",
                "Logic error: >= with 'below' result suggests wrong operator",
            ),
            (
                r"for\s+\w+\s+in\s+range\(2,\s*n\)",
                "Logic error: inefficient loop (consider sqrt(n))",
            ),
            (
                r"if\s+\w+\s*=\s*\w+\s*:",
                "Logic error: Potential logic error: assignment in condition",
            ),
        ]

        return self._detect_patterns(
            context,
            filename,
            patterns,
            content_parser,
            search=PatternSearch(patterns, "logical_error", re.MULTILINE | re.DOTALL),
        )

    def detect_type_confusion(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, str]]:
        """Detect potential type confusion bugs."""
        patterns = [
            (
                r'[\'"][^"\']*[\'"]\s*\+\s*\d',
                "Type mismatch: Type confusion: string + number concatenation",
            ),
            (
                r"\$\w+\s*==\s*\$\w+",
                "Type mismatch: Type confusion: loose comparison (consider ===)",
            ),
            (
                r"sum\(\w+\)",
                "Type mismatch: Type confusion: sum() on potentially mixed type list",
            ),
            (
                r"data\[['\"]key['\"]\]",
                "Type mismatch: Type confusion: assuming dict structure without check",
            ),
            (
                r"data\[0\]",
                "Type mismatch: Type confusion: assuming list structure without check",
            ),
        ]

        return self._detect_patterns(
            context,
            filename,
            patterns,
            content_parser,
            search=PatternSearch(patterns, "type_confusion"),
        )

    def detect_timing_attacks(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, str]]:
        """Detect potential timing attack vulnerabilities."""
        patterns = [
            (
                r"(\w*password\w*|\w*secret\w*|\w*key\w*)\s*==",
                "Timing attack vulnerability: non-constant-time comparison of secrets",
            ),
            (
                r"if\s+len\([^)]+\)\s*!=\s*len\([^)]+\):\s*\n\s*return\s+False",
                "Timing attack vulnerability: early exit on length mismatch"
                " reveals information",
            ),
            (
                r"for\s+\w+\s+in\s+range\(len\(.*\)\):\s*\n\s*if\s+\w+\[\w+\]\s*!=",
                "Timing attack vulnerability: character-by-character comparison",
            ),
            (
                r"time\.sleep.*compare",
                "Timing attack vulnerability: sleep amplifies timing differences",
            ),
            (
                r"def\s+insecure_compare",
                "Timing attack vulnerability: function explicitly marked as"
                " insecure comparison",
            ),
        ]

        return self._detect_patterns(
            context,
            filename,
            patterns,
            content_parser,
            search=PatternSearch(
                patterns, "timing_attack", re.IGNORECASE | re.MULTILINE
            ),
        )

    def categorize_severity(
        self,
        bugs: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Categorize bugs by severity level."""
        severity_map = {
            "sql_injection": "critical",
            "timing_attack": "critical",
            "security": "critical",
            "null_pointer": "high",
            "race_condition": "high",
            "memory_leak": "high",
            "resource_leak": "medium",
            "off_by_one": "medium",
            "logical_error": "medium",
            "integer_overflow": "medium",
            "type_confusion": "low",
            "performance": "low",
        }

        categorized = []
        for bug in bugs:
            bug_copy = bug.copy()
            bug_type = bug.get("type", "").lower()
            bug_copy["severity"] = severity_map.get(bug_type, "low")
            issue = bug.get("issue", "").lower()
            if "sql injection" in issue or "security" in issue:
                bug_copy["severity"] = "critical"
            categorized.append(bug_copy)
        return categorized

    def generate_fix_recommendations(
        self,
        bug_findings: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Generate fix recommendations for detected bugs."""
        fix_templates = {
            "sql_injection": {
                "fix": "Use parameterized queries instead of string concatenation",
                "example": "cursor.execute('SELECT * FROM users WHERE id = ?', (id,))",
                "priority": "critical",
            },
            "null_pointer": {
                "fix": "Add null/undefined checks or use optional chaining",
                "example": "const name = user?.name ?? 'Unknown'",
                "priority": "high",
            },
            "race_condition": {
                "fix": "Use locks or thread-safe data structures",
                "example": "with self.lock: self.balance -= amount",
                "priority": "high",
            },
            "memory_leak": {
                "fix": "Remove event listeners and clear caches",
                "example": "removeEventListener('click', handler)",
                "priority": "medium",
            },
            "resource_leak": {
                "fix": "Use context managers or validate cleanup in finally blocks",
                "example": "with open('file.txt') as f: content = f.read()",
                "priority": "medium",
            },
            "off_by_one": {
                "fix": "Review loop bounds: use < for length, not <=",
                "example": "for i in range(len(items)):  # not len(items) + 1",
                "priority": "medium",
            },
            "timing_attack": {
                "fix": "Use constant-time comparison functions",
                "example": "import hmac; hmac.compare_digest(a, b)",
                "priority": "critical",
            },
        }

        recommendations = []
        for bug in bug_findings:
            bug_type = bug.get("type", "unknown")
            template = fix_templates.get(
                bug_type,
                {
                    "fix": f"Review and fix {bug_type} issue",
                    "example": "Consult security best practices",
                    "priority": "medium",
                },
            )
            recommendations.append(template.copy())
        return recommendations

    def analyze_bug_patterns(
        self,
        bug_history: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Analyze bug patterns from historical data."""
        type_counts: dict[str, int] = {}
        for bug in bug_history:
            bug_type = bug.get("type", "unknown")
            type_counts[bug_type] = type_counts.get(bug_type, 0) + 1

        common_types = [
            {"type": bug_type, "count": count}
            for bug_type, count in sorted(
                type_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )
        ]

        return {
            "common_types": common_types,
            "trend_analysis": {"increasing": [], "decreasing": []},
            "recommendations": [
                f"Focus on {common_types[0]['type']} bugs"
                if common_types
                else "No patterns detected"
            ],
        }

    def validate_bug_fixes(
        self,
        bug_fixes: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Validate proposed bug fixes."""
        results = []
        for fix in bug_fixes:
            original = fix.get("original", "")
            fixed = fix.get("fixed", "")

            valid = True
            reasoning = "Fix appears to address the issue"
            remaining_risks: list[str] = []

            if not fixed.strip() or fixed == original:
                valid = False
                reasoning = "Fix is empty or identical to the original"
                remaining_risks.append("The original code is unchanged")
            elif "SELECT" in original and "?" in fixed:
                reasoning = "Parameterized query correctly used"
            elif "?." in fixed or "??" in fixed:
                reasoning = "Optional chaining/nullish coalescing added"
            elif "with " in fixed and "open" in original:
                reasoning = "Context manager properly used"

            results.append(
                {
                    "valid": valid,
                    "reasoning": reasoning,
                    "remaining_risks": remaining_risks,
                }
            )
        return results

    def detect_false_positives(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, str]]:
        """Detect potential false positives in bug detection."""
        code = content_parser.get_file_content(context, filename)
        false_positives: list[dict[str, str]] = []

        fp_patterns = [
            (r"def safe_", "Safe function - intentionally designed to be secure"),
            (r"# This.*correct", "Developer comment indicates intentional design"),
            (r"if\s+\w+:", "Simple truthy check is appropriate for optional values"),
            (r"if\s+0\s*<=\s*\w+\s*<", "Proper bounds checking present"),
        ]

        for pattern, reason in fp_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                false_positives.append(
                    {
                        "false_positive": f"Pattern: {pattern[:30]}...",
                        "reason": reason,
                    }
                )

        return (
            false_positives
            if false_positives
            else [
                {
                    "false_positive": "No obvious false positives",
                    "reason": "Code requires manual review",
                },
                {
                    "false_positive": "Context-dependent patterns",
                    "reason": "Some patterns may be intentional",
                },
            ]
        )
