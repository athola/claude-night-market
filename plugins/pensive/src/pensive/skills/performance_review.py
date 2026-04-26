"""Performance review skill: time and space complexity hotspots.

Detects O(n^2) and unbounded-allocation patterns in source code via
Python AST (Tier 1, always available). Optionally enriches with
gauntlet's tree-sitter parser (Tier 2) and code knowledge graph
(Tier 3) when those are importable; falls back gracefully when not.

The fallback contract follows the precedent in
`plugins/leyline/src/leyline/tokens.py:25-32` and
`plugins/gauntlet/hooks/pr_blast_radius.py:52-56`: try-import to
sentinels at module scope, then early-return on None inside each
tier helper.
"""

from __future__ import annotations

import ast
from typing import Any, ClassVar

from .base import AnalysisResult, BaseReviewSkill, ReviewFinding

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


_MEMOIZATION_DECORATORS: frozenset[str] = frozenset(
    {
        "lru_cache",
        "cache",
        "functools.lru_cache",
        "functools.cache",
        "memoize",
    }
)

_REDUCER_FUNCTIONS: frozenset[str] = frozenset(
    {"sum", "max", "min", "any", "all", "sorted", "set", "frozenset"}
)


def _decorator_name(decorator: ast.expr) -> str:
    """Return a string form of a decorator expression for matching."""
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        parts: list[str] = []
        node: ast.expr = decorator
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))
    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator.func)
    return ""


def _is_memoized(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True if the function carries a known memoization decorator."""
    for dec in func.decorator_list:
        name = _decorator_name(dec)
        if name in _MEMOIZATION_DECORATORS:
            return True
    return False


def _has_self_call(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True if the function body contains a Call to its own name."""
    target = func.name
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            callee = node.func
            if isinstance(callee, ast.Name) and callee.id == target:
                return True
    return False


def _iter_name(for_node: ast.For) -> str | None:
    """Return the iterable's Name id when `for x in <Name>:`, else None."""
    if isinstance(for_node.iter, ast.Name):
        return for_node.iter.id
    return None


def _classify_rhs(value: ast.expr) -> str | None:
    """Classify an Assign RHS as 'dict', 'set', 'string', or None.

    Used to suppress T2 false positives where the membership test
    target is provably not a list. Conservative: returns None for
    anything indeterminate (Name reference, attribute access, etc.).
    """
    if isinstance(value, (ast.Dict, ast.DictComp)):
        return "dict"
    if isinstance(value, (ast.Set, ast.SetComp)):
        return "set"
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return "string"
    if isinstance(value, ast.JoinedStr):
        return "string"
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
        if value.func.id == "dict":
            return "dict"
        if value.func.id in {"set", "frozenset"}:
            return "set"
        if value.func.id == "str":
            return "string"
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
        # Common string-returning methods. Conservative list: only
        # methods whose return type is unambiguously str across the
        # stdlib (str, pathlib, io.IOBase). Not included: split (list),
        # splitlines (list), partition (tuple), readlines (list).
        if value.func.attr in {
            "lower",
            "upper",
            "strip",
            "lstrip",
            "rstrip",
            "title",
            "casefold",
            "swapcase",
            "capitalize",
            "replace",
            "format",
            "join",
            "encode",
            "decode",
            "read",
            "readline",
            "read_text",
        }:
            return "string"
    return None


_STRING_ITER_METHODS: frozenset[str] = frozenset({"split", "splitlines", "rsplit"})


def _classify_string_iter(value: ast.expr) -> bool:
    """True iff value is provably an iterable of string elements."""
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
        if value.func.attr in _STRING_ITER_METHODS:
            return True
    if isinstance(value, (ast.SetComp, ast.ListComp, ast.GeneratorExp)):
        return _classify_rhs(value.elt) == "string"
    return False


def _iter_yields_string(
    iter_expr: ast.expr,
    string_names: set[str],
    string_iter_names: set[str],
) -> bool:
    """True if iter_expr yields elements that are provably strings.

    Covers: inline `.split()`/`.splitlines()` results; comprehensions
    whose `elt` classifies as string; iteration over a Name that was
    classified as string (iter over a string yields chars) or as
    string-iter (the loop var is each string element).
    """
    if _classify_string_iter(iter_expr):
        return True
    if isinstance(iter_expr, ast.Name):
        if iter_expr.id in string_names:
            return True
        if iter_expr.id in string_iter_names:
            return True
    return False


def _collect_non_list_names(tree: ast.AST) -> set[str]:
    """Pre-pass: gather Names provably bound to non-list values.

    Sources, processed iteratively to a fixed point:
    - Assignments whose RHS classifies as dict/set/string.
    - Function args annotated `str` or `bytes`.
    - For-loop / async-for loop iter vars whose `iter` expression
      yields string elements (e.g. `lines = s.split(); for line in
      lines:` adds `line`).

    Scope is intentionally coarse (module-wide). False-positive cost
    dominates the rare cross-scope reassignment case.
    """
    names: set[str] = set()
    # Names whose VALUE is iterable of strings (e.g. `.split()` result).
    # Tracked separately because they ARE lists (so don't suppress T2
    # when the RHS in a Compare IS this name) but iterating over them
    # yields strings (so iter-vars get classified).
    string_iter_names: set[str] = set()

    def _add(name: str) -> bool:
        if name in names:
            return False
        names.add(name)
        return True

    def _add_iter(name: str) -> bool:
        if name in string_iter_names:
            return False
        string_iter_names.add(name)
        return True

    # Iterate to a fixed point so chains pick up correctly:
    # `lines = s.split(); for line in lines: ...` -> line classified as str.
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Three independent classifications, each may apply:
                # (1) RHS literal/call -> non_list_names
                # (2) RHS provably yields strings -> string_iter_names
                # (3) RHS is a Name already classified -> propagate
                cat = _classify_rhs(node.value)
                yields_strings = _classify_string_iter(node.value)
                propagate_non_list = (
                    isinstance(node.value, ast.Name) and node.value.id in names
                )
                propagate_string_iter = (
                    isinstance(node.value, ast.Name)
                    and node.value.id in string_iter_names
                )
                if cat is not None or propagate_non_list:
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name) and _add(tgt.id):
                            changed = True
                if yields_strings or propagate_string_iter:
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name) and _add_iter(tgt.id):
                            changed = True
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                cat = _classify_rhs(node.value)
                yields_strings = _classify_string_iter(node.value)
                propagate_non_list = (
                    isinstance(node.value, ast.Name) and node.value.id in names
                )
                propagate_string_iter = (
                    isinstance(node.value, ast.Name)
                    and node.value.id in string_iter_names
                )
                if cat is not None or propagate_non_list:
                    if isinstance(node.target, ast.Name) and _add(node.target.id):
                        changed = True
                if yields_strings or propagate_string_iter:
                    if isinstance(node.target, ast.Name) and _add_iter(node.target.id):
                        changed = True
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg in node.args.args + node.args.kwonlyargs:
                    if (
                        isinstance(arg.annotation, ast.Name)
                        and arg.annotation.id in {"str", "bytes"}
                        and _add(arg.arg)
                    ):
                        changed = True
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                if (
                    _iter_yields_string(node.iter, names, string_iter_names)
                    and isinstance(node.target, ast.Name)
                    and _add(node.target.id)
                ):
                    changed = True
            elif isinstance(node, ast.comprehension):
                # `for X in Y` clause inside a SetComp/ListComp/DictComp/
                # GeneratorExp. Same iter-var classification as a regular
                # For: if Y yields strings, X is a string.
                if (
                    _iter_yields_string(node.iter, names, string_iter_names)
                    and isinstance(node.target, ast.Name)
                    and _add(node.target.id)
                ):
                    changed = True
    return names


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

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802 - ast.NodeVisitor uppercase visit_X convention
        self._enter_func(node)
        self.generic_visit(node)
        self._exit_func()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802 - ast.NodeVisitor uppercase visit_X convention
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
            if (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "list"
                and not value.args
                and not value.keywords
            ):
                return True
            return False

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

    def visit_For(self, node: ast.For) -> None:  # noqa: N802 - ast.NodeVisitor uppercase visit_X convention
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

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:  # noqa: N802 - ast.NodeVisitor uppercase visit_X convention
        cur_iter = node.iter.id if isinstance(node.iter, ast.Name) else None
        self._loop_stack.append(cur_iter)
        self.generic_visit(node)
        self._loop_stack.pop()

    # ---- T2: `x in <Name>` inside a loop ---------------------------

    def visit_Compare(self, node: ast.Compare) -> None:  # noqa: N802 - ast.NodeVisitor uppercase visit_X convention
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
            for op, right in zip(node.ops, node.comparators, strict=False):
                if isinstance(op, ast.In) and isinstance(right, ast.Name):
                    if right.id in self._non_list_names:
                        # RHS is provably a dict, set, or string —
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

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 - ast.NodeVisitor uppercase visit_X convention
        # T3: re.compile inside a loop.
        if self._loop_stack and self._is_re_compile(node):
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

        # T6: list/dict/set comp passed to a reducer (sum, max, ...).
        # S2: list(...) or dict(...) or tuple(...) wrapping a generator
        #     inside a reducer call.
        if isinstance(node.func, ast.Name) and node.func.id in _REDUCER_FUNCTIONS:
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

        # S1: .append() inside a loop. We surface it as a hot-path
        # accumulator hint rather than a hard error.
        if (
            self._loop_stack
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "append"
        ):
            # Suppress canonical accumulator pattern: target is a Name
            # initialized to `[]` in the same function. Real S1 hotspots
            # are appends to external state (params, class attrs).
            target = node.func.value
            is_local_accumulator = (
                isinstance(target, ast.Name)
                and bool(self._local_accumulators_stack)
                and target.id in self._local_accumulators_stack[-1]
            )
            # Suppress when the loop has only one iteration source AND
            # is not nested: single-loop accumulators are usually fine.
            if len(self._loop_stack) >= 2 and not is_local_accumulator:
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

        # S3: .copy() / dict() / list() / tuple() inside a loop body
        # that allocate per iteration.
        if self._loop_stack:
            allocates = False
            if isinstance(node.func, ast.Attribute) and node.func.attr == "copy":
                allocates = True
            elif (
                isinstance(node.func, ast.Name)
                and node.func.id in {"dict", "list", "tuple"}
                and node.args
            ):
                # dict(other) / list(other) / tuple(other) with a single arg
                # is a copy. Skip when the only arg is a literal builder
                # like a comprehension — those are expected.
                first = node.args[0]
                if not isinstance(
                    first, (ast.ListComp, ast.GeneratorExp, ast.DictComp)
                ):
                    allocates = True
            if allocates:
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

        self.generic_visit(node)

    # ---- T4: string += inside a loop -------------------------------

    def visit_AugAssign(self, node: ast.AugAssign) -> None:  # noqa: N802 - ast.NodeVisitor uppercase visit_X convention
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
