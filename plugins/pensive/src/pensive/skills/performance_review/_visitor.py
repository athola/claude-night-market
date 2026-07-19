"""AST visitor for performance hotspot detection."""

from __future__ import annotations

import ast

from ..base import ReviewFinding
from ._helpers import (
    _REDUCER_FUNCTIONS,
    _has_self_call,
    _is_memoized,
    _iter_name,
)


class _PerfVisitor(ast.NodeVisitor):
    """Single-pass AST visitor that emits time/space ReviewFindings.

    State machine:
    - `_loop_stack`: stack of for-loop iter Names; nested-loop check
      compares the current iter against outer entries.
    - `_str_locals_stack`: per-function frames of variables assigned a
      string literal: used by T4 to scope the `+=` check.
    - `_func_stack`: tracks whether we are inside a function body so
      module-level recursion checks are skipped.
    - `_non_list_names`: pre-collected Names whose RHS is provably
      a dict, set, or string. Suppresses T2 false positives.
    """

    def __init__(self, file_path: str, non_list_names: set[str] | None = None) -> None:
        self.findings: list[ReviewFinding] = []
        self._file = file_path
        self._loop_stack: list[str | None] = []
        self._str_locals_stack: list[set[str]] = []
        self._func_stack: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        self._non_list_names: set[str] = non_list_names or set()
        # Per-function frames of Names initialized to `[]` in that
        # function's body. S1 suppresses appends to these because they
        # are the canonical accumulator pattern: `out = []; for ...:
        # out.append(...); return out`. Real S1 hotspots are appends
        # to NON-local targets (params, class attrs, module-level lists).
        self._local_accumulators_stack: list[set[str]] = []

    # ---- function tracking (T5, T4 scoping) -------------------------

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_func(node)
        self.generic_visit(node)
        self._exit_func()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter_func(node)
        self.generic_visit(node)
        self._exit_func()

    def _enter_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # T5: recursive without memoization (LOW).
        if _has_self_call(node) and not _is_memoized(node):
            self.findings.append(
                ReviewFinding(
                    file=self._file,
                    line=node.lineno,
                    severity="LOW",
                    category="time",
                    message=(
                        f"Recursive function '{node.name}' has no "
                        f"memoization decorator."
                    ),
                    suggestion=(
                        "Consider @functools.cache / @functools.lru_cache "
                        "to memoize repeat subproblems."
                    ),
                )
            )
        # Build a per-function frame of locals assigned a string literal
        # for T4 scoping.
        str_locals: set[str] = set()
        for body_node in ast.walk(node):
            if isinstance(body_node, ast.Assign):
                for target in body_node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and isinstance(body_node.value, ast.Constant)
                        and isinstance(body_node.value.value, str)
                    ):
                        str_locals.add(target.id)
        self._str_locals_stack.append(str_locals)
        self._func_stack.append(node)
        # Per-function accumulator frame: any Name initialized to an
        # empty list in the function body. Recognized forms:
        # - `out = []`            (Assign + empty List)
        # - `out: list[X] = []`   (AnnAssign + empty List)
        # - `out = list()`        (Assign + Call to bare list)
        # - `out: list[X] = list()` (AnnAssign + Call to bare list)
        accumulators: set[str] = set()

        def _is_empty_list_value(value: ast.expr | None) -> bool:
            if value is None:
                return False
            if isinstance(value, ast.List) and not value.elts:
                return True
            return bool(
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "list"
                and not value.args
                and not value.keywords
            )

        for body_node in ast.walk(node):
            if isinstance(body_node, ast.Assign) and _is_empty_list_value(
                body_node.value
            ):
                for tgt in body_node.targets:
                    if isinstance(tgt, ast.Name):
                        accumulators.add(tgt.id)
            elif isinstance(body_node, ast.AnnAssign) and _is_empty_list_value(
                body_node.value
            ):
                if isinstance(body_node.target, ast.Name):
                    accumulators.add(body_node.target.id)
        self._local_accumulators_stack.append(accumulators)

    def _exit_func(self) -> None:
        self._str_locals_stack.pop()
        self._func_stack.pop()
        self._local_accumulators_stack.pop()

    # ---- loop tracking (T1, T2, T3, T4, S1, S3) --------------------

    def visit_For(self, node: ast.For) -> None:
        # T1: nested for over the same iterable.
        cur_iter = _iter_name(node)
        if cur_iter is not None and cur_iter in self._loop_stack:
            self.findings.append(
                ReviewFinding(
                    file=self._file,
                    line=node.lineno,
                    severity="HIGH",
                    category="time",
                    message=(
                        f"Nested loop over the same iterable "
                        f"'{cur_iter}' — potential O(n^2)."
                    ),
                    suggestion=(
                        "If pairwise work is needed, consider sorting "
                        "+ two pointers or a set-based approach."
                    ),
                )
            )

        self._loop_stack.append(cur_iter)
        self.generic_visit(node)
        self._loop_stack.pop()

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        cur_iter = node.iter.id if isinstance(node.iter, ast.Name) else None
        self._loop_stack.append(cur_iter)
        self.generic_visit(node)
        self._loop_stack.pop()

    # ---- T2: `x in <Name>` inside a loop ---------------------------

    def visit_Compare(self, node: ast.Compare) -> None:
        # T2 suppression rules:
        # - LHS string literal (e.g. `'foo' in s`): always substring
        #   matching, O(m+n) on string length, not list scan.
        # - LHS f-string (JoinedStr): same: produces a string at
        #   runtime so the RHS is necessarily a string container.
        # When suppressed, no finding fires regardless of RHS shape.
        is_string_lhs = (
            isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)
        ) or isinstance(node.left, ast.JoinedStr)

        if self._loop_stack and not is_string_lhs:
            for op, right in zip(node.ops, node.comparators):
                if isinstance(op, ast.In) and isinstance(right, ast.Name):
                    if right.id in self._non_list_names:
                        # RHS is provably a dict, set, or string,
                        # not a list. Skip.
                        continue
                    self.findings.append(
                        ReviewFinding(
                            file=self._file,
                            line=node.lineno,
                            severity="HIGH",
                            category="time",
                            message=(
                                f"Membership test '{ast.unparse(node.left)} "
                                f"in {right.id}' inside a loop: O(n) per "
                                f"iteration if {right.id} is a list."
                            ),
                            suggestion=(
                                f"If '{right.id}' is a list, convert it "
                                f"to a set once outside the loop."
                            ),
                        )
                    )
        self.generic_visit(node)

    # ---- T3, T6, S2, S3: Call patterns -----------------------------

    def _check_recompile_in_loop(self, node: ast.Call) -> None:
        """T3: ``re.compile()`` called inside a loop body."""
        if not (self._loop_stack and self._is_re_compile(node)):
            return
        self.findings.append(
            ReviewFinding(
                file=self._file,
                line=node.lineno,
                severity="MEDIUM",
                category="time",
                message=(
                    "re.compile() called inside a loop — pattern is "
                    "recompiled per iteration."
                ),
                suggestion=(
                    "Hoist re.compile(...) above the loop and reuse "
                    "the compiled pattern."
                ),
            )
        )

    def _check_listcomp_to_reducer(self, node: ast.Call) -> None:
        """T6 + S2: list/dict comp or list(...) wrapper passed to a reducer."""
        if not (isinstance(node.func, ast.Name) and node.func.id in _REDUCER_FUNCTIONS):
            return
        for arg in node.args:
            if isinstance(arg, ast.ListComp):
                self.findings.append(
                    ReviewFinding(
                        file=self._file,
                        line=node.lineno,
                        severity="LOW",
                        category="time",
                        message=(
                            f"List comprehension passed to "
                            f"{node.func.id}() — materializes the "
                            f"full list."
                        ),
                        suggestion=(
                            "Drop the brackets to use a generator "
                            "expression and avoid the intermediate."
                        ),
                    )
                )
            if (
                isinstance(arg, ast.Call)
                and isinstance(arg.func, ast.Name)
                and arg.func.id in {"list", "dict", "tuple", "set"}
                and arg.args
                and isinstance(arg.args[0], ast.GeneratorExp)
            ):
                self.findings.append(
                    ReviewFinding(
                        file=self._file,
                        line=node.lineno,
                        severity="LOW",
                        category="space",
                        message=(
                            f"{arg.func.id}(...) wraps a generator "
                            f"inside {node.func.id}() — "
                            f"the wrapper materializes the entire "
                            f"sequence."
                        ),
                        suggestion=(
                            "Drop the wrapper; reducers accept generators directly."
                        ),
                    )
                )

    def _check_append_in_nested_loop(self, node: ast.Call) -> None:
        """S1: ``.append()`` inside nested loops, not to a local accumulator."""
        if not (
            self._loop_stack
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "append"
        ):
            return
        target = node.func.value
        is_local_accumulator = (
            isinstance(target, ast.Name)
            and bool(self._local_accumulators_stack)
            and target.id in self._local_accumulators_stack[-1]
        )
        if len(self._loop_stack) < 2 or is_local_accumulator:
            return
        self.findings.append(
            ReviewFinding(
                file=self._file,
                line=node.lineno,
                severity="MEDIUM",
                category="space",
                message=(
                    "Unbounded .append() inside nested loops — "
                    "output grows multiplicatively."
                ),
                suggestion=(
                    "Consider yielding from a generator or "
                    "computing on demand instead of materializing "
                    "all combinations."
                ),
            )
        )

    def _check_per_iteration_allocation(self, node: ast.Call) -> None:
        """S3: ``.copy()`` / ``dict(...)`` / ``list(...)`` / ``tuple(...)`` in a loop body."""
        if not self._loop_stack:
            return
        allocates = False
        if isinstance(node.func, ast.Attribute) and node.func.attr == "copy":
            allocates = True
        elif (
            isinstance(node.func, ast.Name)
            and node.func.id in {"dict", "list", "tuple"}
            and node.args
        ):
            first = node.args[0]
            if not isinstance(first, (ast.ListComp, ast.GeneratorExp, ast.DictComp)):
                allocates = True
        if not allocates:
            return
        self.findings.append(
            ReviewFinding(
                file=self._file,
                line=node.lineno,
                severity="MEDIUM",
                category="space",
                message=(
                    "Per-iteration allocation inside a loop "
                    "(.copy() / dict() / list() / tuple())."
                ),
                suggestion=(
                    "If the base is read-only, hoist it; if you "
                    "need a snapshot, build it once outside."
                ),
            )
        )

    def visit_Call(self, node: ast.Call) -> None:
        self._check_recompile_in_loop(node)
        self._check_listcomp_to_reducer(node)
        self._check_append_in_nested_loop(node)
        self._check_per_iteration_allocation(node)
        self.generic_visit(node)

    # ---- T4: string += inside a loop -------------------------------

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if (
            self._loop_stack
            and isinstance(node.op, ast.Add)
            and isinstance(node.target, ast.Name)
            and self._str_locals_stack
            and node.target.id in self._str_locals_stack[-1]
        ):
            self.findings.append(
                ReviewFinding(
                    file=self._file,
                    line=node.lineno,
                    severity="MEDIUM",
                    category="time",
                    message=(
                        f"String accumulation '{node.target.id} += ...' "
                        f"inside a loop — quadratic on long iterations."
                    ),
                    suggestion=(
                        "Append to a list inside the loop and "
                        "''.join(parts) once afterwards."
                    ),
                )
            )
        self.generic_visit(node)

    # ---- helpers ---------------------------------------------------

    @staticmethod
    def _is_re_compile(call: ast.Call) -> bool:
        """True iff call is `re.compile(...)`."""
        func = call.func
        return (
            isinstance(func, ast.Attribute)
            and func.attr == "compile"
            and isinstance(func.value, ast.Name)
            and func.value.id == "re"
        )
