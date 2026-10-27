"""Performance review skill: module decomposition.

Public API preserved verbatim from the prior 745-line
``performance_review.py`` module so existing imports keep
working:

    from pensive.skills.performance_review import PerformanceReviewSkill
"""

from __future__ import annotations

import ast
import importlib
import sqlite3
from collections import deque
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from ..base import AnalysisResult, BaseReviewSkill, ReviewFinding
from ._helpers import _collect_non_list_names
from ._treesitter import EXTENSION_TO_LANGUAGE, SPECS, scan_tree
from ._visitor import _PerfVisitor

if TYPE_CHECKING:
    from types import ModuleType

# Optional cross-plugin enrichment. These imports are best-effort:
# when the `tiers` extra is not installed the sentinels stay None and the
# relevant tier helpers no-op. Tier 1 (Python AST) always runs.
_ts_pack: ModuleType | None
try:
    _ts_pack = importlib.import_module("tree_sitter_language_pack")
except ImportError:  # pragma: no cover
    _ts_pack = None
# None marks the extra as absent. The pack exports ``Error`` from 1.8, and
# 1.x needs Python 3.10. Python 3.9 resolves 0.9.x, which has no ``Error``
# and whose get_parser raises LookupError, a class the parse handler catches.
_ts_get_parser = getattr(_ts_pack, "get_parser", None)
_TsPackError: type[Exception] = getattr(_ts_pack, "Error", LookupError)

try:
    from gauntlet.treesitter_parser import detect_language as _gt_detect_language
except ImportError:  # pragma: no cover
    _gt_detect_language = None

try:
    from gauntlet.graph import GraphStore as _GraphStore
except ImportError:  # pragma: no cover
    _GraphStore = None

_SEVERITY_LADDER = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
_MAX_CALL_DEPTH = 10
_FUNCTION_KINDS = frozenset({"Function", "Test"})


def _upgrade_severity(severity: str) -> str:
    """Move one step up the ladder. CRITICAL and unknown values stay put."""
    if severity not in _SEVERITY_LADDER:
        return severity
    index = _SEVERITY_LADDER.index(severity)
    return _SEVERITY_LADDER[min(index + 1, len(_SEVERITY_LADDER) - 1)]


def _language_for(file_path: str) -> str | None:
    """Tier 2 grammar name for ``file_path``, or None when unsupported."""
    suffix = Path(file_path).suffix
    if suffix == ".tsx":
        return "tsx"  # gauntlet maps .tsx to typescript, which cannot parse JSX
    if _gt_detect_language is not None:
        language = _gt_detect_language(file_path)
    else:
        language = EXTENSION_TO_LANGUAGE.get(suffix)
    return language if language in SPECS else None


def _find_graph_db(file_path: str) -> Path | None:
    """Walk up from the scanned file looking for ``.gauntlet/graph.db``."""
    start = Path(file_path).resolve().parent
    for directory in (start, *start.parents):
        candidate = directory / ".gauntlet" / "graph.db"
        if candidate.is_file():
            return candidate
    return None


def _python_findings(file_path: str, code: str) -> list[ReviewFinding]:
    """Tier 1 over one source string. Raises SyntaxError on bad source."""
    tree = ast.parse(code)
    visitor = _PerfVisitor(file_path, non_list_names=_collect_non_list_names(tree))
    visitor.visit(tree)
    return visitor.findings


def _treesitter_findings(
    file_path: str, code: str, warnings: list[str]
) -> list[ReviewFinding]:
    """Tier 2 over one source string. Parse problems go to ``warnings``."""
    language = _language_for(file_path)
    if _ts_get_parser is None or language is None:
        return []
    try:
        tree = _ts_get_parser(language).parse(code.encode("utf-8"))
    except (_TsPackError, LookupError, ValueError, RuntimeError, OSError) as exc:
        warnings.append(f"tree-sitter parse failed for {file_path}: {exc}")
        return []
    if tree.root_node.has_error:
        warnings.append(f"tree-sitter found syntax errors in {file_path}; file skipped")
        return []
    try:
        return scan_tree(tree.root_node, language, file_path)
    except RecursionError:
        # The scanner recurses per AST level; minified or generated code
        # can nest deeper than the interpreter stack allows.
        warnings.append(
            f"tree-sitter tree too deep to scan in {file_path}; file skipped"
        )
        return []


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
        Tier 2 (optional): tree-sitter for non-Python files.
        Tier 3 (optional): call-graph severity upgrade.
        """
        result = AnalysisResult()
        code = context.get_file_content(file_path)
        if not code:
            return result

        # Tier 1 only applies to Python source. Other languages go to
        # Tier 2, which no-ops when tree-sitter is missing.
        if file_path.endswith(".py"):
            try:
                result.issues.extend(_python_findings(file_path, code))
            except SyntaxError as exc:
                result.warnings.append(f"AST parse failed for {file_path}: {exc}")
                return result

        result.issues.extend(self._tier2_findings(file_path, code, result.warnings))
        result.issues = self._tier3_findings(
            context, result.issues, file_path, result.warnings
        )
        return result

    # ---- Tier 2: tree-sitter ---------------------------------------

    def _tier2_findings(
        self,
        file_path: str,
        code: str,
        warnings: list[str] | None = None,
    ) -> list[ReviewFinding]:
        """Multi-language detection for non-Python files.

        Returns [] when tree-sitter is not installed or the file has no
        Tier 2 grammar, Python included. Parse failures are appended to
        ``warnings``.
        """
        return _treesitter_findings(
            file_path, code, warnings if warnings is not None else []
        )

    # ---- Tier 3: gauntlet graph ------------------------------------

    def _tier3_findings(
        self,
        _context: Any,
        existing: list[ReviewFinding],
        file_path: str,
        warnings: list[str] | None = None,
    ) -> list[ReviewFinding]:
        """Return ``existing`` with severities raised for hot callees.

        Unlike ``_tier2_findings``, which returns findings to add, this
        returns a full replacement for ``existing``: the caller assigns it
        to ``result.issues``. A finding whose enclosing function transitively calls another
        function that holds a hotspot moves up one severity step. Returns
        ``existing`` unchanged when GraphStore is missing or no
        ``.gauntlet/graph.db`` is found above the file.
        """
        if _GraphStore is None or not existing:
            return existing
        db_path = _find_graph_db(file_path)
        if db_path is None:
            return existing
        try:
            with _GraphStore(db_path) as graph:
                return self._upgrade_with_graph(
                    graph, existing, file_path, db_path.parent.parent
                )
        except sqlite3.Error as exc:
            if warnings is not None:
                warnings.append(f"gauntlet graph unreadable at {db_path}: {exc}")
            return existing

    def _upgrade_with_graph(
        self,
        graph: Any,
        existing: list[ReviewFinding],
        file_path: str,
        project_root: Path,
    ) -> list[ReviewFinding]:
        source = str(Path(file_path).resolve())
        functions = [
            node
            for node in graph.get_nodes_in_file(source)
            if str(node.kind) in _FUNCTION_KINDS
        ]
        hotspot_cache: dict[str, list[int]] = {}
        upgraded: list[ReviewFinding] = []
        for finding in existing:
            row = finding.line - 1
            enclosing = [n for n in functions if n.line_start <= row <= n.line_end]
            seed = min(enclosing, key=lambda n: n.line_end - n.line_start, default=None)
            callee = (
                self._first_hot_callee(graph, seed, hotspot_cache, project_root)
                if seed
                else None
            )
            if callee is None:
                upgraded.append(finding)
                continue
            name = callee.qualified_name.rsplit("::", 1)[-1]
            upgraded.append(
                replace(
                    finding,
                    severity=_upgrade_severity(finding.severity),
                    message=(
                        f"{finding.message} Severity raised: it calls "
                        f"'{name}' ({Path(callee.file_path).name}:"
                        f"{callee.line_start + 1}), which holds a hotspot."
                    ),
                )
            )
        return upgraded

    def _first_hot_callee(
        self,
        graph: Any,
        seed: Any,
        hotspot_cache: dict[str, list[int]],
        project_root: Path,
    ) -> Any | None:
        """Nearest function reachable by CALLS edges that holds a hotspot."""
        visited = {seed.qualified_name}
        queue: deque[tuple[str, int]] = deque([(seed.qualified_name, 0)])
        while queue:
            current, depth = queue.popleft()
            if depth >= _MAX_CALL_DEPTH:
                continue
            for edge in graph.get_edges_by_source(current):
                target = edge.target_qn
                if str(edge.kind) != "CALLS" or target in visited:
                    continue
                visited.add(target)
                node = graph.get_node(target)
                if node is None:
                    continue
                lines = self._hotspot_lines(node.file_path, hotspot_cache, project_root)
                if any(node.line_start <= line - 1 <= node.line_end for line in lines):
                    return node
                queue.append((target, depth + 1))
        return None

    def _hotspot_lines(
        self, file_path: str, cache: dict[str, list[int]], project_root: Path
    ) -> list[int]:
        """1-based lines of Tier 1/2 findings in a file, read from disk.

        ``graph.db`` belongs to the reviewed repository, so its paths are
        untrusted: a path outside the project that holds the database is
        never read and counts as holding no hotspot.
        """
        if file_path not in cache:
            inside = project_root in Path(file_path).resolve().parents
            cache[file_path] = self._scan_disk(file_path) if inside else []
        return cache[file_path]

    @staticmethod
    def _scan_disk(file_path: str) -> list[int]:
        try:
            code = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        if file_path.endswith(".py"):
            try:
                findings = _python_findings(file_path, code)
            except SyntaxError:
                return []
        else:
            findings = _treesitter_findings(file_path, code, [])
        return [finding.line for finding in findings]


__all__ = ["PerformanceReviewSkill"]
