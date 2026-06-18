"""Conversion-traits analysis for Rust review.

Two conversion smells:

- `impl Into<X> for Y` that should be `impl From<Y> for X`
  (clippy::from_over_into): From gives the Into impl for free and
  composes with `?` via the std error blanket impl.
- `.try_into().unwrap()` / `T::try_from(..).unwrap()` that discards the
  error `TryFrom` exists to surface.

Grounded in the Rust API Guidelines C-CONV-TRAITS and std::convert docs.
See modules/conversion-traits.md.
"""

from __future__ import annotations

from typing import Any

from ..rust_review_data import (
    CONVERSION_COMMENT_RE,
    CONVERSION_DISCARDED_ERROR_REC,
    CONVERSION_IMPL_INTO_RE,
    CONVERSION_IMPL_INTO_REC,
    CONVERSION_TRY_FROM_UNWRAP_RE,
    CONVERSION_TRY_INTO_UNWRAP_RE,
    Finding,
)
from .line_cache import LineCacheMixin

__all__ = ["ConversionTraitsMixin"]


class ConversionTraitsMixin(LineCacheMixin):
    """Mixin flagging Into impls and discarded conversion errors."""

    def analyze_conversion_traits(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect `impl Into` blocks and `try_*().unwrap()` discards.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with conversion_traits_issues findings
        """
        content = context.get_file_content(file_path)
        lines = self._get_lines(content)
        issues: list[Finding] = []

        for i, line in enumerate(lines):
            if CONVERSION_COMMENT_RE.match(line):
                continue
            issues.extend(self._check_from_over_into(line, i))
            issues.extend(self._check_discarded_error(line, i))

        return {"conversion_traits_issues": issues}

    @staticmethod
    def _check_from_over_into(line: str, index: int) -> list[Finding]:
        """Flag a line-leading `impl Into<X> for Y` block header.

        Anchored at the start of the line so a generic bound
        `T: Into<U>` (which is correct and idiomatic) is never matched.
        """
        match = CONVERSION_IMPL_INTO_RE.match(line)
        if not match:
            return []
        dst, src = match.group(1).strip(), match.group(2).strip()
        return [
            {
                "line": index + 1,
                "type": "from_over_into",
                "recommendation": CONVERSION_IMPL_INTO_REC.format(src=src, dst=dst),
                "clippy_lint": "clippy::from_over_into",
            }
        ]

    @staticmethod
    def _check_discarded_error(line: str, index: int) -> list[Finding]:
        """Flag `try_into()/try_from(..)` immediately unwrapped/expected."""
        if not (
            CONVERSION_TRY_INTO_UNWRAP_RE.search(line)
            or CONVERSION_TRY_FROM_UNWRAP_RE.search(line)
        ):
            return []
        return [
            {
                "line": index + 1,
                "type": "discarded_conversion_error",
                "recommendation": CONVERSION_DISCARDED_ERROR_REC,
                "clippy_lint": "clippy::unwrap_used",
            }
        ]
