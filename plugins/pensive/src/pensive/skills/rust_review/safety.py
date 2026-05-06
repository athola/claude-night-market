"""Unsafe code and memory safety analysis for Rust review."""

from __future__ import annotations

import re
from typing import Any

from ..rust_review_data import (
    LARGE_OFFSET_RE,
    LIFETIME_ANNOTATION_RE,
    POINTER_OFFSET_RE,
    UNSAFE_BLOCK_RE,
    UNSAFE_FN_RE,
)

__all__ = ["SafetyMixin"]

_SAFETY_DOC_RE = re.compile(r"(?i)safety|# SAFETY|/// # Safety")


class SafetyMixin:
    """Mixin providing unsafe code block and memory safety analysis."""

    def _has_safety_doc(
        self, lines: list[str], line_idx: int, lookback: int = 5
    ) -> bool:
        for j in range(max(0, line_idx - lookback), line_idx):
            if _SAFETY_DOC_RE.search(lines[j]):
                return True
        return False

    def analyze_unsafe_code(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze unsafe code blocks in Rust files.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with unsafe_blocks analysis
        """
        content = context.get_file_content(file_path)
        unsafe_blocks = []

        lines = self._get_lines(content)
        for i, line in enumerate(lines):
            if UNSAFE_BLOCK_RE.search(line):
                unsafe_blocks.append(
                    {
                        "line": i + 1,
                        "type": "unsafe_block",
                        "lacks_documentation": not self._has_safety_doc(lines, i),
                    }
                )

            if UNSAFE_FN_RE.search(line):
                unsafe_blocks.append(
                    {
                        "line": i + 1,
                        "type": "unsafe_function",
                        "lacks_documentation": not self._has_safety_doc(lines, i),
                    }
                )

        return {
            "unsafe_blocks": unsafe_blocks,
        }

    def analyze_memory_safety(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze memory safety issues.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with memory safety analysis
        """
        content = context.get_file_content(file_path)
        unsafe_operations = []
        buffer_overflows = []
        use_after_free = []
        lifetime_issues = []

        lines = self._get_lines(content)
        for i, line in enumerate(lines):
            # Detect raw pointer operations
            if POINTER_OFFSET_RE.search(line):
                unsafe_operations.append(
                    {
                        "line": i + 1,
                        "type": "pointer_offset",
                        "description": "Raw pointer offset operation",
                    }
                )
                # Check if offset is out of bounds
                if LARGE_OFFSET_RE.search(line):
                    buffer_overflows.append(
                        {
                            "line": i + 1,
                            "type": "potential_overflow",
                            "description": "Large offset - buffer overflow risk",
                        }
                    )

            # Detect Box::into_raw and Box::from_raw patterns
            if "Box::into_raw" in line:
                # Look for potential use after free
                for j in range(i + 1, min(len(lines), i + 20)):
                    if "Box::from_raw" in lines[j]:
                        use_after_free.append(
                            {
                                "line": j + 1,
                                "type": "box_free",
                                "description": "Box::from_raw - validate no use after",
                            }
                        )
                        break

            if "Box::from_raw" in line:
                unsafe_operations.append(
                    {
                        "line": i + 1,
                        "type": "box_from_raw",
                        "description": "Box::from_raw - manual memory management",
                    }
                )

            # Detect lifetime issues
            if LIFETIME_ANNOTATION_RE.search(line) or "lifetime" in line.lower():
                lifetime_issues.append(
                    {
                        "line": i + 1,
                        "type": "lifetime_annotation",
                        "description": "Lifetime annotation - verify correctness",
                    }
                )

        return {
            "unsafe_operations": unsafe_operations,
            "buffer_overflows": buffer_overflows,
            "use_after_free": use_after_free,
            "lifetime_issues": lifetime_issues,
        }
