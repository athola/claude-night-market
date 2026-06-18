"""Mem-forget analysis for Rust review.

Flags `mem::forget(x)` (skips the destructor, leaking the resource) and
`drop(&x)` (drops a borrow: a no-op, so the owned value lives on). Both
defeat the deterministic cleanup the destructors chapter describes.

Grounded in the Rust Reference destructors chapter (src/destructors.md)
and clippy::mem_forget / clippy::drop_ref. See modules/mem-forget-audit.md.
"""

from __future__ import annotations

from typing import Any

from ..rust_review_data import (
    DROP_REF_RE,
    DROP_REF_REC,
    MEM_FORGET_EXCLUSION_PATTERNS_RE,
    MEM_FORGET_RE,
    MEM_FORGET_REC,
    Finding,
)
from .line_cache import LineCacheMixin

__all__ = ["MemForgetMixin"]


class MemForgetMixin(LineCacheMixin):
    """Mixin flagging skipped (`forget`) and no-op (`drop(&x)`) cleanup."""

    def analyze_mem_forget(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect `mem::forget` calls and reference drops.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with mem_forget_issues findings
        """
        content = context.get_file_content(file_path)
        lines = self._get_lines(content)
        issues: list[Finding] = []

        for i, line in enumerate(lines):
            if any(rx.search(line) for rx in MEM_FORGET_EXCLUSION_PATTERNS_RE):
                continue

            if MEM_FORGET_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "mem_forget",
                        "recommendation": MEM_FORGET_REC,
                        "clippy_lint": "clippy::mem_forget",
                    }
                )

            if DROP_REF_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "drop_ref",
                        "recommendation": DROP_REF_REC,
                        "clippy_lint": "clippy::drop_ref",
                    }
                )

        return {"mem_forget_issues": issues}
