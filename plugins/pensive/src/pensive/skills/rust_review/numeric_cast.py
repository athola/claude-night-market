"""Numeric cast-safety analysis for Rust review.

Flags `as` casts that lose information, where the *shape* of the cast
makes the loss provable without type inference:

- a usize length/size (`.len()`/`.count()`/`.capacity()`) narrowed to a
  fixed-width integer (truncation)
- a cast to the smallest integer types `u8`/`i8`, which cannot widen
- a cast to `f32`, the precision-loss target for f64/i64/u64 sources

Grounded in the Rust Reference type-cast rules
(src/expressions/operator-expr.md) and clippy::cast_possible_truncation /
clippy::cast_precision_loss. See modules/numeric-cast-safety.md.
"""

from __future__ import annotations

from typing import Any

from ..rust_review_data import (
    NUMERIC_BYTE_CAST_RE,
    NUMERIC_BYTE_CAST_REC,
    NUMERIC_CAST_EXCLUSION_PATTERNS_RE,
    NUMERIC_F32_CAST_RE,
    NUMERIC_F32_CAST_REC,
    NUMERIC_LEN_TRUNCATION_CAST_RE,
    NUMERIC_LEN_TRUNCATION_CAST_REC,
    Finding,
)
from .line_cache import LineCacheMixin

__all__ = ["NumericCastMixin"]


class NumericCastMixin(LineCacheMixin):
    """Mixin flagging lossy `as` casts the compiler will not warn on."""

    def analyze_numeric_cast_safety(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect truncating and precision-losing `as` casts.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with numeric_cast_issues findings
        """
        content = context.get_file_content(file_path)
        lines = self._get_lines(content)
        issues: list[Finding] = []

        for i, line in enumerate(lines):
            if any(rx.search(line) for rx in NUMERIC_CAST_EXCLUSION_PATTERNS_RE):
                continue

            if NUMERIC_LEN_TRUNCATION_CAST_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "length_truncation_cast",
                        "recommendation": NUMERIC_LEN_TRUNCATION_CAST_REC,
                        "clippy_lint": "clippy::cast_possible_truncation",
                    }
                )
            elif NUMERIC_BYTE_CAST_RE.search(line):
                # `elif`: a `.len() as u8` is already the more specific
                # length-truncation finding; do not double-report it.
                issues.append(
                    {
                        "line": i + 1,
                        "type": "narrowing_to_byte_cast",
                        "recommendation": NUMERIC_BYTE_CAST_REC,
                        "clippy_lint": "clippy::cast_possible_truncation",
                    }
                )

            if NUMERIC_F32_CAST_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "precision_loss_cast",
                        "recommendation": NUMERIC_F32_CAST_REC,
                        "clippy_lint": "clippy::cast_precision_loss",
                    }
                )

        return {"numeric_cast_issues": issues}
