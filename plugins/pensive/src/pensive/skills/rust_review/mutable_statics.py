"""Mutable static audit for Rust review.

Flags `static mut` declarations. A mutable static needs `unsafe` to read
or write and is a primary source of data races; the Rust Reference
(src/items/static-items.md) calls it "a very large source of race
conditions or other bugs", and accessing one through a reference is the
deny-by-default `static_mut_refs` lint in Rust 2024.

See modules/mutable-static-audit.md.
"""

from __future__ import annotations

from typing import Any

from ..rust_review_data import (
    MUTABLE_STATIC_EXCLUSION_PATTERNS_RE,
    MUTABLE_STATIC_RE,
    MUTABLE_STATIC_REC,
)
from .line_cache import LineCacheMixin

__all__ = ["MutableStaticMixin"]


class MutableStaticMixin(LineCacheMixin):
    """Mixin flagging `static mut` shared mutable globals."""

    def analyze_mutable_statics(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect mutable static declarations.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with mutable_static_issues findings
        """
        content = context.get_file_content(file_path)
        lines = self._get_lines(content)
        issues: list[dict[str, Any]] = []

        for i, line in enumerate(lines):
            if any(rx.search(line) for rx in MUTABLE_STATIC_EXCLUSION_PATTERNS_RE):
                continue
            if MUTABLE_STATIC_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "mutable_static",
                        "recommendation": MUTABLE_STATIC_REC,
                        "clippy_lint": "static_mut_refs",
                    }
                )

        return {"mutable_static_issues": issues}
