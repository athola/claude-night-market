"""Tier 2: tree-sitter hotspot detection for non-Python source.

Covers the patterns whose shape is the same across imperative languages:
T1 (nested loop over the same iterable), T2 (list scan inside a loop) and
S1 (append inside nested loops). The Python-only patterns (T3, T4, T5, T6,
S2, S3) have no counterpart here.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from ..base import ReviewFinding

if TYPE_CHECKING:
    from collections.abc import Mapping

_MIN_NESTED_LOOP_DEPTH = 2

# Node types that start a new scope: loops outside them do not count.
_SCOPE_TYPES: frozenset[str] = frozenset(
    {
        "function_declaration",
        "function_expression",
        "function",
        "generator_function",
        "generator_function_declaration",
        "arrow_function",
        "method_definition",
        "func_literal",
        "method_declaration",
        "constructor_declaration",
        "lambda_expression",
        "function_item",
        "closure_expression",
        "function_definition",
    }
)


@dataclass(frozen=True)
class _LangSpec:
    # loop node type -> field holding the iterated expression (None when
    # the loop has no iterable, such as `while` or a C-style `for`).
    loops: Mapping[str, str | None]
    # Callee shapes. A leading "." matches any receiver: ".includes" matches
    # `names.includes`. Anything else must equal the callee text exactly.
    list_scans: tuple[str, ...] = ()
    appends: tuple[str, ...] = ()
    scan_container: str = "an array"
    # What to convert the scanned container to, named in the advice.
    scan_replacement: str = "Set"
    # Child node holding the iterable when the loop has no field for it,
    # such as Go's `for _, x := range xs`.
    range_child: str | None = None


# A C-style loop has no iterable field to compare.
_C_LOOPS: Mapping[str, str | None] = MappingProxyType(
    {"for_statement": None, "while_statement": None, "do_statement": None}
)


_JS = _LangSpec(
    loops=MappingProxyType({"for_in_statement": "right", **_C_LOOPS}),
    list_scans=(".includes", ".indexOf"),
    appends=(".push",),
)

SPECS: dict[str, _LangSpec] = {
    "javascript": _JS,
    "typescript": _JS,
    "tsx": _JS,
    "go": _LangSpec(
        loops=MappingProxyType({"for_statement": None}),
        list_scans=("slices.Contains", "slices.Index"),
        appends=("append",),
        scan_container="a slice",
        scan_replacement="map",
        range_child="range_clause",
    ),
    "rust": _LangSpec(
        loops=MappingProxyType(
            {
                "for_expression": "value",
                "while_expression": None,
                "loop_expression": None,
            }
        ),
        appends=(".push",),
    ),
    # `.add(` is List.add, Set.add and Map-like alike: not reported.
    "java": _LangSpec(
        loops=MappingProxyType({"enhanced_for_statement": "value", **_C_LOOPS}),
    ),
    "c": _LangSpec(
        loops=_C_LOOPS,
    ),
    "cpp": _LangSpec(
        loops=MappingProxyType({"for_range_loop": "right", **_C_LOOPS}),
        appends=(".push_back",),
    ),
}

EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
}


def _text(node: Any) -> str:
    return "".join(node.text.decode("utf-8", errors="replace").split())


def _matches(callee: str, shapes: tuple[str, ...]) -> bool:
    return any(
        callee.endswith(shape) if shape.startswith(".") else callee == shape
        for shape in shapes
    )


def _callee_text(node: Any) -> str | None:
    if node.type == "method_invocation":
        name = node.child_by_field_name("name")
        receiver = node.child_by_field_name("object")
        if name is None:
            return None
        return f"{_text(receiver)}.{_text(name)}" if receiver else _text(name)
    if node.type == "call_expression":
        func = node.child_by_field_name("function")
        return _text(func) if func is not None else None
    return None


class _Scanner:
    def __init__(self, language: str, file_path: str) -> None:
        self._spec = SPECS[language]
        self._file = file_path
        self._loop_stack: list[str | None] = []
        self.findings: list[ReviewFinding] = []

    def _iterable(self, node: Any) -> str | None:
        field = self._spec.loops[node.type]
        target = node.child_by_field_name(field) if field else None
        if target is None and self._spec.range_child is not None:
            for child in node.children:
                if child.type == self._spec.range_child:
                    target = child.child_by_field_name("right")
        return _text(target) if target is not None else None

    def visit(self, node: Any) -> None:
        if node.type in _SCOPE_TYPES:
            outer, self._loop_stack = self._loop_stack, []
            self._children(node)
            self._loop_stack = outer
        elif node.type in self._spec.loops:
            self._enter_loop(node)
        else:
            self._check_call(node)
            self._children(node)

    def _children(self, node: Any) -> None:
        for child in node.children:
            self.visit(child)

    def _enter_loop(self, node: Any) -> None:
        iterable = self._iterable(node)
        if iterable is not None and iterable in self._loop_stack:
            self._add(
                node,
                "HIGH",
                "time",
                f"Nested loop over the same iterable '{iterable}' — potential O(n^2).",
                "If pairwise work is needed, consider sorting "
                "+ two pointers or a set-based approach.",
            )
        self._loop_stack.append(iterable)
        self._children(node)
        self._loop_stack.pop()

    def _check_call(self, node: Any) -> None:
        if not self._loop_stack:
            return
        callee = _callee_text(node)
        if callee is None:
            return
        if _matches(callee, self._spec.list_scans):
            self._add(
                node,
                "HIGH",
                "time",
                f"Membership test '{callee}(...)' inside a loop: O(n) per "
                f"iteration if the receiver is {self._spec.scan_container}.",
                f"If the collection is {self._spec.scan_container}, convert "
                f"it to a {self._spec.scan_replacement} once outside the loop.",
            )
        elif len(self._loop_stack) >= _MIN_NESTED_LOOP_DEPTH and _matches(
            callee, self._spec.appends
        ):
            self._add(
                node,
                "MEDIUM",
                "space",
                "Unbounded append inside nested loops — output grows multiplicatively.",
                "Consider yielding from a generator or "
                "computing on demand instead of materializing "
                "all combinations.",
            )

    def _add(
        self, node: Any, severity: str, category: str, message: str, suggestion: str
    ) -> None:
        self.findings.append(
            ReviewFinding(
                file=self._file,
                line=node.start_point[0] + 1,
                severity=severity,
                category=category,
                message=message,
                suggestion=suggestion,
            )
        )


def scan_tree(root: Any, language: str, file_path: str) -> list[ReviewFinding]:
    """Return Tier 2 findings for a parsed tree of ``language``."""
    scanner = _Scanner(language, file_path)
    scanner.visit(root)
    return scanner.findings
