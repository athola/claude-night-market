"""Code pattern analysis for Rust review.

Covers silent returns, collection types, SQL injection,
cfg(test) misuse, error message quality, and duplicate
validators.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

__all__ = ["PatternsMixin"]

# A-01: pre-compile patterns once at module load.

_SILENT_RETURN_RE = tuple(
    re.compile(p)
    for p in (
        r"else\s*\{\s*return\s*;",
        r"else\s*\{\s*continue\s*;",
        r"=>\s*(?:return|continue)\b",
    )
)
_COLLECTION_TYPE_RE = tuple(
    re.compile(p)
    for p in (
        r"\.contains\(&",
        r"\.dedup\(\)",
        r"\.iter\(\)\.find\(",
        r"\.iter\(\)\.position\(",
    )
)
_SQL_INJECTION_RE = tuple(
    re.compile(p)
    for p in (
        r'format!\s*\(\s*"[^"]*\b(?:SELECT|INSERT|UPDATE|DELETE|DROP|WHERE)\b[^"]*\{\}',
        r'format!\s*\(\s*"[^"]*\{\}[^"]*\b(?:SELECT|INSERT|UPDATE|DELETE|DROP|WHERE)\b',
        r'format!\s*\(\s*"[^"]*\b(?:select|insert|update|delete|drop|where)\b[^"]*\{\}',
        r'format!\s*\(\s*"[^"]*\{\}[^"]*\b(?:select|insert|update|delete|drop|where)\b',
    )
)
_CFG_TEST_MISUSE_RE = tuple(
    re.compile(p)
    for p in (
        r"#\[cfg\(test\)\]\s*\n\s*(?:pub\s+)?fn\s+",
        r"#\[cfg\(test\)\]\s*\n\s*(?:pub\s+)?impl\s+",
        r"#\[cfg\(test\)\]\s*\n\s*(?:pub\s+)?struct\s+",
    )
)
_ERROR_MESSAGE_RE = tuple(
    re.compile(p)
    for p in (
        r'Err\s*\(\s*"[^"]{1,19}"\s*\)',
        r'panic!\s*\(\s*"[^"]{1,19}"\s*\)',
        r'\.expect\s*\(\s*"[^"]{1,19}"\s*\)',
        r'Err\s*\(\s*"[^"]{1,19}"\.(?:to_string|into)\(\)\s*\)',
    )
)
_DUPLICATE_VALIDATOR_RE = tuple(
    re.compile(p)
    for p in (
        r"\bfn\s+(validate_\w+)\s*\(",
        r"\bfn\s+(check_\w+)\s*\(",
        r"\bfn\s+(verify_\w+)\s*\(",
    )
)
_MOD_TESTS_RE = re.compile(r"\bmod\s+tests\s*\{")


class PatternsMixin:
    """Mixin providing Rust code pattern detection analysis."""

    _MIN_CONSOLIDATION_COUNT: ClassVar[int] = 3

    def analyze_silent_returns(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze let-else/if-let/match arms that silently discard values.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with silent_returns findings
        """
        content = context.get_file_content(file_path)
        silent_returns = []
        lines = self._get_lines(content)
        for i, line in enumerate(lines):
            for rx in _SILENT_RETURN_RE:
                if rx.search(line):
                    silent_returns.append(
                        {
                            "line": i + 1,
                            "type": "silent_discard",
                            "description": (
                                "Silent return/continue discards Result/Option value"
                            ),
                        }
                    )
                    break
        return {"silent_returns": silent_returns}

    def analyze_collection_types(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze Vec usage where set or map semantics are more appropriate.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with collection_type_suggestions findings
        """
        content = context.get_file_content(file_path)
        suggestions = []
        lines = self._get_lines(content)
        for i, line in enumerate(lines):
            for rx in _COLLECTION_TYPE_RE:
                if rx.search(line):
                    suggestions.append(
                        {
                            "line": i + 1,
                            "type": "vec_as_set_or_map",
                            "description": (
                                "Vec used with set/map semantics; "
                                "consider HashSet or HashMap"
                            ),
                        }
                    )
                    break
        return {"collection_type_suggestions": suggestions}

    def analyze_sql_injection(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze format! calls that interpolate values into SQL strings.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with sql_injection_risks findings
        """
        content = context.get_file_content(file_path)
        risks = []
        lines = self._get_lines(content)
        for i, line in enumerate(lines):
            for rx in _SQL_INJECTION_RE:
                if rx.search(line):
                    risks.append(
                        {
                            "line": i + 1,
                            "type": "sql_format_interpolation",
                            "description": (
                                "format! with SQL keywords and {} "
                                "interpolation; use parameterized queries"
                            ),
                        }
                    )
                    break
        return {"sql_injection_risks": risks}

    def analyze_cfg_test_misuse(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze #[cfg(test)] applied to items outside a mod tests block.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with cfg_test_misuse findings
        """
        content = context.get_file_content(file_path)
        misuses = []
        lines = self._get_lines(content)
        in_mod_tests = False
        brace_depth = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if _MOD_TESTS_RE.search(line):
                in_mod_tests = True
            if in_mod_tests:
                brace_depth += stripped.count("{") - stripped.count("}")
                if brace_depth <= 0:
                    in_mod_tests = False
                    brace_depth = 0
                continue
            for rx in _CFG_TEST_MISUSE_RE:
                window = line + ("\n" + lines[i + 1] if i + 1 < len(lines) else "")
                if rx.search(window):
                    misuses.append(
                        {
                            "line": i + 1,
                            "type": "cfg_test_outside_mod",
                            "description": (
                                "#[cfg(test)] on item outside mod tests "
                                "block; move into mod tests or use "
                                "#[test] attribute"
                            ),
                        }
                    )
                    break
        return {"cfg_test_misuse": misuses}

    def analyze_error_messages(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze error strings that are too short to be actionable.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with poor_error_messages findings
        """
        content = context.get_file_content(file_path)
        poor_messages = []
        lines = self._get_lines(content)
        for i, line in enumerate(lines):
            for rx in _ERROR_MESSAGE_RE:
                if rx.search(line):
                    poor_messages.append(
                        {
                            "line": i + 1,
                            "type": "short_error_message",
                            "description": (
                                "Error/panic message is too short; "
                                "add context and recovery hints"
                            ),
                        }
                    )
                    break
        return {"poor_error_messages": poor_messages}

    def analyze_duplicate_validators(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze validate_*/check_*/verify_* functions for consolidation.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with duplicate_validators and
            consolidation_candidates
        """
        content = context.get_file_content(file_path)
        found: dict[str, list[int]] = {}
        lines = self._get_lines(content)
        for i, line in enumerate(lines):
            for rx in _DUPLICATE_VALIDATOR_RE:
                match = rx.search(line)
                if match:
                    name = match.group(1)
                    found.setdefault(name, []).append(i + 1)
                    break
        validators = [
            {"name": name, "lines": line_nums} for name, line_nums in found.items()
        ]
        prefix_groups: dict[str, list[str]] = {}
        for name in found:
            for prefix in ("validate_", "check_", "verify_"):
                if name.startswith(prefix):
                    prefix_groups.setdefault(prefix, []).append(name)
                    break
        consolidation_candidates = [
            {
                "prefix": prefix,
                "functions": names,
                "description": (
                    f"{len(names)} {prefix}* functions detected; "
                    "consider consolidating into a single validator"
                ),
            }
            for prefix, names in prefix_groups.items()
            if len(names) >= self._MIN_CONSOLIDATION_COUNT
        ]
        return {
            "duplicate_validators": validators,
            "consolidation_candidates": consolidation_candidates,
        }
