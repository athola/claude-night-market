"""Float-equality analysis for Rust review.

Flags `==`/`!=` comparisons against a floating-point literal. IEEE-754
arithmetic rounds, so values that are mathematically equal often differ
in their last bits; an exact equality test then silently misbehaves.

Grounded in the Rust Reference numeric types (src/types/numeric.md) and
clippy::float_cmp. See modules/float-equality.md.
"""

from __future__ import annotations

from typing import Any

from ..rust_review_data import (
    FLOAT_CMP_EXCLUSION_PATTERNS_RE,
    FLOAT_CMP_LHS_RE,
    FLOAT_CMP_REC,
    FLOAT_CMP_RHS_RE,
    Finding,
)
from .line_cache import LineCacheMixin

__all__ = ["FloatEqualityMixin"]


class FloatEqualityMixin(LineCacheMixin):
    """Mixin flagging exact equality tests on floating-point literals."""

    def analyze_float_equality(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect `==`/`!=` against a float literal.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with float_cmp_issues findings
        """
        content = context.get_file_content(file_path)
        lines = self._get_lines(content)
        issues: list[Finding] = []

        for i, line in enumerate(lines):
            if any(rx.search(line) for rx in FLOAT_CMP_EXCLUSION_PATTERNS_RE):
                continue

            # The literal may sit on either side; one finding per line is
            # enough, so report on the first direction that matches.
            if FLOAT_CMP_RHS_RE.search(line) or FLOAT_CMP_LHS_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "float_exact_compare",
                        "recommendation": FLOAT_CMP_REC,
                        "clippy_lint": "clippy::float_cmp",
                    }
                )

        return {"float_cmp_issues": issues}
