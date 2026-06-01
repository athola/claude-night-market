"""Performance review skill: module decomposition.

Public API preserved verbatim from the prior 745-line
``performance_review.py`` module so existing imports keep
working:

    from pensive.skills.performance_review import PerformanceReviewSkill
"""

from __future__ import annotations

import ast
from typing import Any, ClassVar

from ..base import AnalysisResult, BaseReviewSkill, ReviewFinding
from ._helpers import _collect_non_list_names
from ._visitor import _PerfVisitor

# Optional cross-plugin enrichment. These imports are best-effort:
# if gauntlet isn't installed, sentinels stay None and the relevant
# tier helpers no-op. Tier 1 (Python AST) always runs.
try:
    from gauntlet.treesitter_parser import parse_file as _gt_parse
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    _gt_parse = None

try:
    from gauntlet.graph import GraphStore as _GraphStore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    _GraphStore = None


class PerformanceReviewSkill(BaseReviewSkill):
    """Skill for reviewing time + space complexity hotspots."""

    skill_name: ClassVar[str] = "performance_review"
    supported_languages: ClassVar[list[str]] = [
        "python",
        # Tier-2 (gauntlet tree-sitter) extends to JS/TS, Go, Rust, Java,
        # C/C++ when gauntlet is installed.
    ]

    # ---- public entry point ----------------------------------------

    def analyze(self, context: Any, file_path: str) -> AnalysisResult:
        """Analyze a file and return findings.

        Tier 1 (always): Python AST detection.
        Tier 2 (optional): gauntlet tree-sitter for non-Python files.
        Tier 3 (optional): graph-based transitive severity upgrade.
        """
        result = AnalysisResult()
        code = context.get_file_content(file_path)
        if not code:
            return result

        # Tier 1 only applies to Python source. For non-.py files we
        # let Tier 2 handle them (or no-op when gauntlet is missing).
        if file_path.endswith(".py"):
            try:
                tree = ast.parse(code)
            except SyntaxError as exc:
                result.warnings.append(f"AST parse failed for {file_path}: {exc}")
                return result
            non_list_names = _collect_non_list_names(tree)
            visitor = _PerfVisitor(file_path, non_list_names=non_list_names)
            visitor.visit(tree)
            result.issues.extend(visitor.findings)

        result.issues.extend(self._tier2_findings(context, file_path))
        result.issues.extend(
            self._tier3_findings(context, list(result.issues), file_path)
        )
        return result

    # ---- Tier 2: gauntlet tree-sitter ------------------------------

    def _tier2_findings(self, _context: Any, file_path: str) -> list[ReviewFinding]:
        """Multi-language detection via gauntlet's tree-sitter parser.

        Returns [] when gauntlet is not installed (sentinel is None).
        """
        if _gt_parse is None:
            return []
        # When gauntlet IS available, defer to its parser. Concrete
        # language-specific patterns are documented in
        # `skills/performance-review/modules/gauntlet-integration.md`
        # and added incrementally; this stub keeps the integration
        # surface honest and testable.
        try:
            _nodes, _edges = _gt_parse(file_path)
        except (OSError, ValueError):  # pragma: no cover
            # When this stub is filled in, surface the parse error
            # via result.warnings rather than swallowing silently;
            # see I8 in PR #470 review.
            return []
        return []

    # ---- Tier 3: gauntlet graph ------------------------------------

    def _tier3_findings(
        self,
        _context: Any,
        _existing: list[ReviewFinding],
        _file_path: str,
    ) -> list[ReviewFinding]:
        """Transitive severity upgrade via gauntlet's GraphStore.

        Returns [] when GraphStore is not available or no graph DB
        exists for the working tree.
        """
        if _GraphStore is None:
            return []
        # When the graph IS available, find functions transitively
        # reachable from existing hotspots and upgrade severity if any
        # downstream function is itself a hotspot. The full algorithm
        # lives in gauntlet-integration.md; until graph fixtures are
        # wired, this stub keeps the contract honest and the tier
        # boundary testable.
        return []


__all__ = ["PerformanceReviewSkill"]
