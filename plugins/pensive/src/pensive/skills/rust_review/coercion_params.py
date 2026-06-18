"""Coercion-params analysis for Rust review.

Flags borrowed-owned parameter types that defeat deref coercion:

- `&String` -> `&str`
- `&Vec<T>` -> `&[T]`
- `&PathBuf` -> `&Path`

A `&str`/`&[T]`/`&Path` parameter accepts both an owned value's borrow
(via deref coercion) and an already-borrowed one, so it is strictly more
general than the owned-type reference. Grounded in the Rust Reference
type-coercions chapter (src/type-coercions.md) and clippy::ptr_arg. See
modules/coercion-params.md.
"""

from __future__ import annotations

from typing import Any

from ..rust_review_data import (
    COERCION_COMMENT_RE,
    COERCION_PATHBUF_PARAM_RE,
    COERCION_PATHBUF_PARAM_REC,
    COERCION_STRING_PARAM_RE,
    COERCION_STRING_PARAM_REC,
    COERCION_VEC_PARAM_RE,
    COERCION_VEC_PARAM_REC,
    Finding,
)
from .line_cache import LineCacheMixin

__all__ = ["CoercionParamsMixin"]

# Each tuple is (compiled pattern, finding recommendation). The shared
# `type`/`clippy_lint` keys are identical across the three shapes.
_COERCION_CHECKS = (
    (COERCION_STRING_PARAM_RE, COERCION_STRING_PARAM_REC),
    (COERCION_VEC_PARAM_RE, COERCION_VEC_PARAM_REC),
    (COERCION_PATHBUF_PARAM_RE, COERCION_PATHBUF_PARAM_REC),
)


class CoercionParamsMixin(LineCacheMixin):
    """Mixin flagging owned-type refs that should be borrowed slices."""

    def analyze_coercion_params(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect `&String`/`&Vec<T>`/`&PathBuf` typed bindings.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with coercion_params_issues findings
        """
        content = context.get_file_content(file_path)
        lines = self._get_lines(content)
        issues: list[Finding] = []

        for i, line in enumerate(lines):
            if COERCION_COMMENT_RE.match(line):
                continue
            for pattern, rec in _COERCION_CHECKS:
                if pattern.search(line):
                    issues.append(
                        {
                            "line": i + 1,
                            "type": "ptr_arg",
                            "recommendation": rec,
                            "clippy_lint": "clippy::ptr_arg",
                        }
                    )

        return {"coercion_params_issues": issues}
