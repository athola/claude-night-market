"""Idiomatic elision analysis for Rust review.

Flags annotations the compiler already infers:

- needless explicit lifetimes that lifetime elision would supply
  (clippy::needless_lifetimes)
- trailing `return <expr>;` statements that the block's tail
  expression makes redundant (clippy::needless_return)
- explicit `-> ()` unit return types the compiler already elides
  (clippy::unused_unit)

Grounded in the Rust Reference: src/lifetime-elision.md and
src/expressions/block-expr.md. See modules/idiomatic-elision.md.
"""

from __future__ import annotations

import re
from typing import Any

from ..rust_review_data import (
    ELISION_FN_LIFETIME_SIG_RE,
    ELISION_NEEDLESS_LIFETIME_REC,
    ELISION_NEEDLESS_RETURN_REC,
    ELISION_RETURN_STMT_RE,
    ELISION_UNIT_RETURN_RE,
    ELISION_UNIT_RETURN_REC,
    Finding,
)
from .line_cache import LineCacheMixin

__all__ = ["IdiomaticElisionMixin"]


class IdiomaticElisionMixin(LineCacheMixin):
    """Mixin flagging lifetimes and returns the compiler infers."""

    def analyze_idiomatic_elision(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Detect needless lifetimes and trailing returns.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with idiomatic_elision_issues findings
        """
        content = context.get_file_content(file_path)
        lines = self._get_lines(content)
        issues: list[Finding] = []

        issues.extend(self._find_needless_lifetimes(content))
        issues.extend(self._find_needless_returns(lines))
        issues.extend(self._find_unit_returns(lines))

        return {"idiomatic_elision_issues": issues}

    @staticmethod
    def _find_unit_returns(lines: list[str]) -> list[Finding]:
        """Flag an explicit `-> ()` unit return type.

        The unit return type is the default and is elided, so writing
        `-> ()` states what the compiler already infers
        (clippy::unused_unit). Comment lines are skipped.
        """
        findings: list[Finding] = []
        for i, line in enumerate(lines):
            if line.lstrip().startswith("//"):
                continue
            if ELISION_UNIT_RETURN_RE.search(line):
                findings.append(
                    {
                        "line": i + 1,
                        "type": "unused_unit",
                        "recommendation": ELISION_UNIT_RETURN_REC,
                        "clippy_lint": "clippy::unused_unit",
                    }
                )
        return findings

    @staticmethod
    def _find_needless_lifetimes(content: str) -> list[Finding]:
        """Flag single-input-lifetime signatures that elision covers.

        Only flags when exactly one input reference uses the lifetime
        and the output reuses it (elision rules 2 and 3). Two inputs
        sharing a lifetime are load-bearing and are left alone.
        """
        findings: list[Finding] = []
        for match in ELISION_FN_LIFETIME_SIG_RE.finditer(content):
            lifetime, params, ret = match.group(1), match.group(2), match.group(3)
            token = re.compile(re.escape(lifetime) + r"\b")
            input_uses = len(token.findall(params))
            if input_uses == 1 and token.search(ret):
                findings.append(
                    {
                        "line": content[: match.start()].count("\n") + 1,
                        "type": "needless_lifetime",
                        "recommendation": ELISION_NEEDLESS_LIFETIME_REC,
                        "clippy_lint": "clippy::needless_lifetimes",
                    }
                )
        return findings

    @staticmethod
    def _find_needless_returns(lines: list[str]) -> list[Finding]:
        """Flag a `return <expr>;` in the function tail position.

        The return is in the tail position when it is immediately
        followed by one or more block-closing lines and then either the
        end of file or a new item (another `fn`, `impl`, attribute, ...).
        An early guard return is followed by more body statements, so
        the first non-closing line that follows is a continuation rather
        than an item boundary, and it is left alone.
        """
        findings: list[Finding] = []
        for i, line in enumerate(lines):
            if not ELISION_RETURN_STMT_RE.match(line):
                continue
            rest = [s.strip() for s in lines[i + 1 :] if s.strip()]
            if not rest or not _is_block_close(rest[0]):
                continue
            # Skip block-close AND comment lines to find the real continuation.
            # A comment can precede either the happy-path statement (an early
            # guard return) or the next item (a genuine tail return), so it is
            # not itself a boundary. Stopping at a comment misclassifies a
            # guard return whose continuation is preceded by a comment.
            follow = next(
                (s for s in rest if not _is_block_close(s) and not _is_comment(s)),
                "",
            )
            if follow == "" or _is_item_boundary(follow):
                findings.append(
                    {
                        "line": i + 1,
                        "type": "needless_return",
                        "recommendation": ELISION_NEEDLESS_RETURN_REC,
                        "clippy_lint": "clippy::needless_return",
                    }
                )
        return findings


def _is_block_close(stripped: str) -> bool:
    """True for a line that only closes blocks, e.g. `}`, `};`, `})`."""
    return bool(stripped) and all(c in "});," for c in stripped)


def _is_comment(stripped: str) -> bool:
    """True for a line comment (`//`, `///`, `//!`) or a block-comment open.

    Bare ``*`` is deliberately excluded: a continuation line such as
    ``*ptr = 1;`` must not be mistaken for a block-comment interior line.
    """
    return stripped.startswith(("//", "/*"))


# Item-level keywords: a line starting with one of these (after the
# function's closing brace) marks a new item, so the preceding return
# was the function tail rather than a guard before more statements.
# Comment prefixes are intentionally absent: comments are skipped while
# scanning for the continuation (see _find_needless_returns), not treated
# as boundaries, because a comment may precede a guard's happy path.
_ITEM_BOUNDARY_PREFIXES = (
    "fn ",
    "pub ",
    "impl",
    "mod ",
    "trait ",
    "struct ",
    "enum ",
    "const ",
    "static ",
    "type ",
    "use ",
    "unsafe ",
    "async ",
    "extern",
    "macro_rules!",
    "#[",
    "#!",
)


def _is_item_boundary(stripped: str) -> bool:
    """True when a line begins a new top-level item."""
    return stripped.startswith(_ITEM_BOUNDARY_PREFIXES)
