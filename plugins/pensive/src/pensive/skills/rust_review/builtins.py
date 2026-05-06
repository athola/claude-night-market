"""Builtin trait preference analysis for Rust review.

Detects helper functions that should be standard trait
implementations: From/Into/TryFrom/FromStr conversions,
Default/Display/AsRef replacements, error conversion
wrappers, and manual combinator reimplementations.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ..rust_review_data import (
    BUILTIN_CONVERSION_PATTERNS,
    BUILTIN_CONVERSION_PATTERNS_RE,
    BUILTIN_ERROR_CONVERSION_PATTERNS,
    BUILTIN_ERROR_CONVERSION_PATTERNS_RE,
    BUILTIN_EXCLUSION_PATTERNS,
    BUILTIN_EXCLUSION_PATTERNS_RE,
    BUILTIN_MANUAL_COMBINATOR_PATTERNS,
    BUILTIN_MANUAL_COMBINATOR_PATTERNS_RE,
    BUILTIN_STANDARD_TRAIT_PATTERNS,
    BUILTIN_STANDARD_TRAIT_PATTERNS_RE,
    BUILTIN_TO_METHOD_RE,
    BUILTIN_TO_METHOD_REC,
    BUILTIN_TO_METHOD_TRAIT,
    BUILTIN_TO_STRING_RE,
    BUILTIN_TO_STRING_REC,
    BUILTIN_TO_STRING_TRAIT,
)

__all__ = ["BuiltinsMixin"]


class BuiltinsMixin:
    """Mixin providing builtin trait preference analysis."""

    _BUILTIN_CONVERSION_PATTERNS: ClassVar[list[tuple[str, str, str]]] = (
        BUILTIN_CONVERSION_PATTERNS
    )
    _BUILTIN_STANDARD_TRAIT_PATTERNS: ClassVar[list[tuple[str, str, str]]] = (
        BUILTIN_STANDARD_TRAIT_PATTERNS
    )
    _BUILTIN_ERROR_CONVERSION_PATTERNS: ClassVar[list[tuple[str, str, str]]] = (
        BUILTIN_ERROR_CONVERSION_PATTERNS
    )
    _BUILTIN_MANUAL_COMBINATOR_PATTERNS: ClassVar[list[tuple[str, str, str, str]]] = (
        BUILTIN_MANUAL_COMBINATOR_PATTERNS
    )
    _BUILTIN_EXCLUSION_PATTERNS: ClassVar[list[str]] = BUILTIN_EXCLUSION_PATTERNS

    def analyze_builtin_preference(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect helper functions that should be standard trait impls.

        Flags conversion helpers (From/Into/TryFrom/FromStr),
        standard trait replacements (Default/Display/AsRef),
        error conversion wrappers, and manual combinator
        reimplementations.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with builtin_preference_issues findings
        """
        content = context.get_file_content(file_path)
        issues: list[dict[str, Any]] = []
        lines = self._get_lines(content)

        for i, line in enumerate(lines):
            if any(rx.search(line) for rx in BUILTIN_EXCLUSION_PATTERNS_RE):
                continue

            for (
                rx,
                trait_name,
                recommendation,
            ) in BUILTIN_CONVERSION_PATTERNS_RE:
                if rx.search(line):
                    issues.append(
                        {
                            "line": i + 1,
                            "type": "conversion_helper",
                            "trait": trait_name,
                            "recommendation": recommendation,
                            "clippy_lint": "",
                        }
                    )
                    break

            if BUILTIN_TO_STRING_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "conversion_helper",
                        "trait": BUILTIN_TO_STRING_TRAIT,
                        "recommendation": BUILTIN_TO_STRING_REC,
                        "clippy_lint": "",
                    }
                )
            elif BUILTIN_TO_METHOD_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "conversion_helper",
                        "trait": BUILTIN_TO_METHOD_TRAIT,
                        "recommendation": BUILTIN_TO_METHOD_REC,
                        "clippy_lint": "",
                    }
                )

            for (
                rx,
                trait_name,
                recommendation,
            ) in BUILTIN_STANDARD_TRAIT_PATTERNS_RE:
                if rx.search(line):
                    clippy = (
                        "clippy::derivable_impls" if trait_name == "Default" else ""
                    )
                    issues.append(
                        {
                            "line": i + 1,
                            "type": "standard_trait",
                            "trait": trait_name,
                            "recommendation": recommendation,
                            "clippy_lint": clippy,
                        }
                    )
                    break

            for (
                rx,
                trait_name,
                recommendation,
            ) in BUILTIN_ERROR_CONVERSION_PATTERNS_RE:
                if rx.search(line):
                    issues.append(
                        {
                            "line": i + 1,
                            "type": "error_conversion",
                            "trait": trait_name,
                            "recommendation": recommendation,
                            "clippy_lint": "",
                        }
                    )
                    break

        joined = "\n".join(lines)
        for (
            rx,
            lint_name,
            replacement,
            clippy_lint,
        ) in BUILTIN_MANUAL_COMBINATOR_PATTERNS_RE:
            for match in rx.finditer(joined):
                line_num = joined[: match.start()].count("\n") + 1
                issues.append(
                    {
                        "line": line_num,
                        "type": "manual_combinator",
                        "trait": lint_name,
                        "replacement": replacement,
                        "clippy_lint": clippy_lint,
                    }
                )

        return {"builtin_preference_issues": issues}
