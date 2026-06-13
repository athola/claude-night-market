"""Transmute-audit analysis for Rust review.

Flags `mem::transmute` and `transmute_copy` calls. A transmute
reinterprets the source bytes as the target type with no layout check,
so it is undefined behavior whenever the two layouts disagree; the
Reference lists producing such an invalid value under behavior
considered undefined (src/behavior-considered-undefined.md).

Grounded in the Rust Reference and clippy::transmute_* family. See
modules/transmute-audit.md.
"""

from __future__ import annotations

from typing import Any

from ..rust_review_data import (
    TRANSMUTE_COPY_RE,
    TRANSMUTE_COPY_REC,
    TRANSMUTE_EXCLUSION_PATTERNS_RE,
    TRANSMUTE_RE,
    TRANSMUTE_REC,
)
from .line_cache import LineCacheMixin

__all__ = ["TransmuteAuditMixin"]


class TransmuteAuditMixin(LineCacheMixin):
    """Mixin flagging byte-reinterpreting `transmute` calls."""

    def analyze_transmute_safety(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect `transmute` / `transmute_copy` calls.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with transmute_issues findings
        """
        content = context.get_file_content(file_path)
        lines = self._get_lines(content)
        issues: list[dict[str, Any]] = []

        for i, line in enumerate(lines):
            if any(rx.search(line) for rx in TRANSMUTE_EXCLUSION_PATTERNS_RE):
                continue

            if TRANSMUTE_COPY_RE.search(line):
                # Check the more dangerous sibling first: `transmute_copy`
                # is never matched by TRANSMUTE_RE (the name is followed by
                # `_`, not a call), so the two are mutually exclusive.
                issues.append(
                    {
                        "line": i + 1,
                        "type": "transmute_copy",
                        "recommendation": TRANSMUTE_COPY_REC,
                        "clippy_lint": "clippy::transmute_copy",
                    }
                )
            elif TRANSMUTE_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "transmute",
                        "recommendation": TRANSMUTE_REC,
                        "clippy_lint": "clippy::transmute_int_to_float",
                    }
                )

        return {"transmute_issues": issues}
