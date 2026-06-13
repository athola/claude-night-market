"""Match wildcard exhaustiveness analysis for Rust review.

Flags catch-all `_ =>` arms that defeat the compiler's exhaustiveness
check. When the scrutinee is an enum, an explicit-variant match makes a
newly added variant a compile error; a `_` arm that panics or is empty
turns it into a runtime panic or a silently ignored case instead.

Only the panic / empty forms are flagged. A `_ =>` arm returning a real
value is a legitimate default over an open set (integers, chars, strings)
and is left alone. Grounded in the Rust Reference match chapter
(src/expressions/match-expr.md) and clippy::wildcard_enum_match_arm.

See modules/match-wildcard.md.
"""

from __future__ import annotations

from typing import Any

from ..rust_review_data import (
    MATCH_WILDCARD_EMPTY_RE,
    MATCH_WILDCARD_EMPTY_REC,
    MATCH_WILDCARD_EXCLUSION_PATTERNS_RE,
    MATCH_WILDCARD_PANIC_RE,
    MATCH_WILDCARD_PANIC_REC,
    MATCH_WILDCARD_UNREACHABLE_RE,
    MATCH_WILDCARD_UNREACHABLE_REC,
)
from .line_cache import LineCacheMixin

__all__ = ["MatchWildcardMixin"]


class MatchWildcardMixin(LineCacheMixin):
    """Mixin flagging wildcard arms that hide non-exhaustive matches."""

    def analyze_match_exhaustiveness(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect panic/empty `_ =>` catch-all match arms.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with match_wildcard_issues findings
        """
        content = context.get_file_content(file_path)
        lines = self._get_lines(content)
        issues: list[dict[str, Any]] = []

        for i, line in enumerate(lines):
            if any(rx.search(line) for rx in MATCH_WILDCARD_EXCLUSION_PATTERNS_RE):
                continue

            if MATCH_WILDCARD_UNREACHABLE_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "wildcard_unreachable",
                        "recommendation": MATCH_WILDCARD_UNREACHABLE_REC,
                        "clippy_lint": "clippy::wildcard_enum_match_arm",
                    }
                )
            elif MATCH_WILDCARD_PANIC_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "wildcard_panic",
                        "recommendation": MATCH_WILDCARD_PANIC_REC,
                        "clippy_lint": "clippy::wildcard_enum_match_arm",
                    }
                )
            elif MATCH_WILDCARD_EMPTY_RE.search(line):
                issues.append(
                    {
                        "line": i + 1,
                        "type": "wildcard_empty_arm",
                        "recommendation": MATCH_WILDCARD_EMPTY_REC,
                        "clippy_lint": "clippy::wildcard_enum_match_arm",
                    }
                )

        return {"match_wildcard_issues": issues}
