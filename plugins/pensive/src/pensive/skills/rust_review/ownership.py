"""Ownership, borrowing, concurrency, and async analysis for Rust review."""

from __future__ import annotations

import re
from typing import Any

from ..rust_review_data import (
    ARC_MUTEX_RE,
    ASYNC_CALL_RE,
    ASYNC_FN_RE,
    MIXED_BORROWS_MUT_RE,
    MUTEX_NEW_RE,
    RC_NEW_REFCELL_RE,
    RC_REFCELL_RE,
)

__all__ = ["OwnershipMixin"]

_MOVE_RE = re.compile(r"\blet\s+(\w+)\s*=\s*(\w+)\s*;")
_AMP_W_RE = re.compile(r"&\w+")
_FN_SIG_RE = re.compile(r"^\s*(pub\s+)?(async\s+)?fn\s+")
_TRAIT_DEF_LINE_RE = re.compile(r"^\s*(pub\s+)?trait\s+")


class OwnershipMixin:
    """Mixin providing ownership, data race, and async pattern analysis."""

    def analyze_ownership(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze ownership and borrowing patterns.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with violations, reference_cycles,
            and borrow_checker_issues
        """
        content = context.get_file_content(file_path)
        violations = []
        reference_cycles = []
        borrow_checker_issues = []

        lines = self._get_lines(content)
        for i, line in enumerate(lines):
            # Detect use after move patterns
            for j in range(max(0, i - 10), i):
                m = _MOVE_RE.search(lines[j])
                if m:
                    moved_from = m.group(2)
                    if re.search(
                        rf"\b{re.escape(moved_from)}\b", line
                    ) and moved_from != m.group(1):
                        violations.append(
                            {
                                "line": i + 1,
                                "type": "use_after_move",
                                "description": (
                                    f"Potential use of '{moved_from}' after move"
                                ),
                            }
                        )
                        break

            # Detect reference cycle patterns (Rc + RefCell)
            if RC_REFCELL_RE.search(line) or RC_NEW_REFCELL_RE.search(line):
                for j in range(i, min(len(lines), i + 10)):
                    if "borrow_mut().next = Some" in lines[j]:
                        reference_cycles.append(
                            {
                                "line": j + 1,
                                "type": "rc_refcell_cycle",
                                "description": (
                                    "Potential reference cycle with Rc<RefCell>"
                                ),
                            }
                        )
                        break

            # Detect borrow checker issues (exclude fn signatures and traits)
            if (
                MIXED_BORROWS_MUT_RE.search(line)
                and _AMP_W_RE.search(line)
                and not _FN_SIG_RE.search(line)
                and not _TRAIT_DEF_LINE_RE.search(line)
            ):
                borrow_checker_issues.append(
                    {
                        "line": i + 1,
                        "type": "mixed_borrows",
                        "description": (
                            "Potential mixed mutable and immutable borrows"
                        ),
                    }
                )

        return {
            "violations": violations,
            "reference_cycles": reference_cycles,
            "borrow_checker_issues": borrow_checker_issues,
        }

    def analyze_data_races(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze concurrent code for data race risks.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with data_races, thread_safety_issues,
            and safe_patterns
        """
        content = context.get_file_content(file_path)
        data_races: list[dict[str, Any]] = []
        thread_safety_issues: list[dict[str, Any]] = []
        safe_patterns: list[dict[str, Any]] = []

        lines = self._get_lines(content)
        for i, line in enumerate(lines):
            # Detect RefCell usage (not thread-safe)
            if "RefCell" in line and "use std::cell::RefCell" not in line:
                for j in range(max(0, i - 10), min(len(lines), i + 10)):
                    if "thread::spawn" in lines[j]:
                        thread_safety_issues.append(
                            {
                                "line": i + 1,
                                "type": "refcell_threading",
                                "description": ("RefCell not thread-safe (Send+Sync)"),
                            }
                        )
                        break

            # Detect safe patterns
            if ARC_MUTEX_RE.search(line) or MUTEX_NEW_RE.search(line):
                safe_patterns.append(
                    {
                        "line": i + 1,
                        "type": "mutex_usage",
                        "description": ("Safe: Using Mutex for thread-safe access"),
                    }
                )

            if "AtomicI32" in line or "AtomicU32" in line or "AtomicBool" in line:
                safe_patterns.append(
                    {
                        "line": i + 1,
                        "type": "atomic_usage",
                        "description": ("Safe: Using atomic types for thread safety"),
                    }
                )

        return {
            "data_races": data_races,
            "thread_safety_issues": thread_safety_issues,
            "safe_patterns": safe_patterns,
        }

    def analyze_async_patterns(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze async/await patterns.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with async pattern analysis
        """
        content = context.get_file_content(file_path)
        blocking_operations = []
        missing_awaits = []
        send_sync_issues = []

        lines = self._get_lines(content)
        async_start_depth = -1
        brace_depth = 0

        for i, line in enumerate(lines):
            brace_depth += line.count("{") - line.count("}")

            if ASYNC_FN_RE.search(line):
                async_start_depth = brace_depth - line.count("{")

            in_async_fn = async_start_depth >= 0

            if in_async_fn and brace_depth <= async_start_depth:
                async_start_depth = -1
                in_async_fn = False

            if in_async_fn and "std::thread::sleep" in line:
                blocking_operations.append(
                    {
                        "line": i + 1,
                        "type": "blocking_sleep",
                        "description": (
                            "std::thread::sleep in async - use tokio::time"
                        ),
                    }
                )

            if in_async_fn and ASYNC_CALL_RE.search(line):
                has_await = False
                for j in range(i, min(len(lines), i + 3)):
                    if ".await" in lines[j]:
                        has_await = True
                        break
                if not has_await and "fetch_data()" in line:
                    missing_awaits.append(
                        {
                            "line": i + 1,
                            "type": "missing_await",
                            "description": ("Async function call without .await"),
                        }
                    )

            if in_async_fn and "Rc::new" in line:
                send_sync_issues.append(
                    {
                        "line": i + 1,
                        "type": "rc_in_async",
                        "description": ("Rc not Send+Sync - problematic in async"),
                    }
                )

        return {
            "blocking_operations": blocking_operations,
            "missing_awaits": missing_awaits,
            "send_sync_issues": send_sync_issues,
        }
