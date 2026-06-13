"""Native type-modeling analysis for Rust review.

Detects code that compares or branches on bare primitives where a
native Rust enum would let the compiler check every case. Two crisp,
low-false-positive ports are flagged:

- stringly-typed comparisons (`status == "active"`) that should be an
  enum compared with `matches!`/`==`
- boolean-blind signatures (two or more `: bool` params) that should
  take two-variant enums

Newtype and type-state are intentionally documentation-only (see
modules/native-type-modeling.md); reliable static detection of them
produces too many false positives at I/O and storage boundaries.
"""

from __future__ import annotations

from typing import Any

from ..rust_review_data import (
    NATIVE_BOOLEAN_BLINDNESS_RE,
    NATIVE_BOOLEAN_BLINDNESS_REC,
    NATIVE_INT_STATE_CONST_RE,
    NATIVE_INT_STATE_CONST_REC,
    NATIVE_MODELING_EXCLUSION_PATTERNS_RE,
    NATIVE_STRINGLY_COMPARISON_RE,
    NATIVE_STRINGLY_COMPARISON_REC,
)
from .line_cache import LineCacheMixin

__all__ = ["NativeModelingMixin"]


class NativeModelingMixin(LineCacheMixin):
    """Mixin suggesting ports to native enum-based type modeling."""

    def analyze_native_type_modeling(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect primitives that should be modeled as enums.

        Flags stringly-typed comparisons and boolean-blind function
        signatures, recommending native enum modeling so the compiler
        checks the cases exhaustively.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with native_type_modeling_issues findings
        """
        content = context.get_file_content(file_path)
        issues: list[dict[str, Any]] = []
        lines = self._get_lines(content)

        for i, line in enumerate(lines):
            if any(rx.search(line) for rx in NATIVE_MODELING_EXCLUSION_PATTERNS_RE):
                continue

            if NATIVE_STRINGLY_COMPARISON_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "stringly_typed_comparison",
                        "recommendation": NATIVE_STRINGLY_COMPARISON_REC,
                        "clippy_lint": "clippy::match_like_matches_macro",
                    }
                )

            if NATIVE_BOOLEAN_BLINDNESS_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "boolean_blindness",
                        "recommendation": NATIVE_BOOLEAN_BLINDNESS_REC,
                        "clippy_lint": "clippy::fn_params_excessive_bools",
                    }
                )

            if NATIVE_INT_STATE_CONST_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "magic_number_state_constant",
                        "recommendation": NATIVE_INT_STATE_CONST_REC,
                        "clippy_lint": "",
                    }
                )

        return {"native_type_modeling_issues": issues}
