"""Repr-packed analysis for Rust review.

Flags `#[repr(packed)]` struct attributes. The packed representation
drops the padding that keeps fields naturally aligned, so borrowing a
field produces an unaligned reference, which is undefined behavior (the
`unaligned_references` hard error).

Grounded in the Rust Reference type-layout chapter (src/type-layout.md).
See modules/repr-packed-audit.md.
"""

from __future__ import annotations

from typing import Any

from ..rust_review_data import (
    REPR_PACKED_EXCLUSION_PATTERNS_RE,
    REPR_PACKED_RE,
    REPR_PACKED_REC,
    Finding,
)
from .line_cache import LineCacheMixin

__all__ = ["ReprPackedMixin"]


class ReprPackedMixin(LineCacheMixin):
    """Mixin flagging `#[repr(packed)]` layouts that under-align fields."""

    def analyze_repr_packed(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect `#[repr(packed)]` attributes.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with repr_packed_issues findings
        """
        content = context.get_file_content(file_path)
        lines = self._get_lines(content)
        issues: list[Finding] = []

        for i, line in enumerate(lines):
            if any(rx.search(line) for rx in REPR_PACKED_EXCLUSION_PATTERNS_RE):
                continue

            if REPR_PACKED_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "repr_packed",
                        "recommendation": REPR_PACKED_REC,
                        "clippy_lint": "unaligned_references",
                    }
                )

        return {"repr_packed_issues": issues}
