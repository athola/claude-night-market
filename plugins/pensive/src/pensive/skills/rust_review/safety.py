"""Unsafe code and memory safety analysis for Rust review."""

from __future__ import annotations

import re
from typing import Any

__all__ = ["SafetyMixin"]


class SafetyMixin:
    """Mixin providing unsafe code block and memory safety analysis."""

    def _has_safety_doc(
        self, lines: list[str], line_idx: int, lookback: int = 5
    ) -> bool:
        pattern = r"(?i)safety|# SAFETY|/// # Safety"
        for j in range(max(0, line_idx - lookback), line_idx):
            if re.search(pattern, lines[j]):
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

        unsafe_block_pattern = r"unsafe\s*\{"
        unsafe_fn_pattern = r"unsafe\s+fn\s+(\w+)"

        lines = self._get_lines(content)  # type: ignore[attr-defined]
        for i, line in enumerate(lines):
            if re.search(unsafe_block_pattern, line):
                unsafe_blocks.append(
                    {
                        "line": i + 1,
                        "type": "unsafe_block",
                        "lacks_documentation": not self._has_safety_doc(lines, i),
                    }
                )

            if re.search(unsafe_fn_pattern, line):
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

        lines = self._get_lines(content)  # type: ignore[attr-defined]
        for i, line in enumerate(lines):
            # Detect raw pointer operations
            if re.search(r"\*\w+\.offset\(", line):
                unsafe_operations.append(
                    {
                        "line": i + 1,
                        "type": "pointer_offset",
                        "description": "Raw pointer offset operation",
                    }
                )
                # Check if offset is out of bounds
                if re.search(r"\.offset\((10|[2-9]\d+)\)", line):
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
            if re.search(r"fn\s+\w+<'a>.*->.*&'a", line) or "lifetime" in line.lower():
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
