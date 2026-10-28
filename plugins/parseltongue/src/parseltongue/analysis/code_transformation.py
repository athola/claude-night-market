"""Code transformation skill for parseltongue."""

from __future__ import annotations

import ast
import re
from typing import Any


class CodeTransformationSkill:
    """Skill for transforming and optimizing Python code using AST."""

    async def transform_code(
        self, code: str, target_pattern: str = ""
    ) -> dict[str, Any]:
        transformations: list[dict[str, Any]] = []
        transformed = code
        improvements: list[dict[str, Any]] = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "transformed_code": code,
                "transformations": [],
                "improvements": [],
                "error": "Invalid syntax",
            }

        if target_pattern == "optimize_performance":
            transformed, new_transforms = self._optimize_performance(transformed, tree)
            transformations.extend(new_transforms)
            for t in new_transforms:
                improvements.append(
                    {
                        "type": t["type"],
                        "description": t["description"],
                    }
                )
        elif not target_pattern or target_pattern == "modernize":
            transformed, new_transforms = self._apply_all(transformed, tree)
            transformations.extend(new_transforms)
            try:
                ast.parse(transformed)
            except SyntaxError:
                return {
                    "transformed_code": code,
                    "transformations": [],
                    "improvements": [],
                    "error": "Transformation produced invalid syntax",
                }
        elif target_pattern == "refactor":
            # Refactor pattern: no transformations applied currently
            pass

        return {
            "transformed_code": transformed,
            "transformations": transformations,
            "improvements": improvements,
        }

    def _optimize_performance(
        self, code: str, tree: ast.Module
    ) -> tuple[str, list[dict[str, Any]]]:
        transforms: list[dict[str, Any]] = []

        # Detect for loops that could be optimized
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                transforms.append(
                    {
                        "type": "optimization",
                        "description": "Loop detected: consider "
                        "list comprehension or vectorized operation",
                    }
                )
                break  # Report once

        return code, transforms

    def _apply_all(
        self, code: str, tree: ast.Module
    ) -> tuple[str, list[dict[str, Any]]]:
        """Rewrite modernizable expressions in place, leaving other text as is."""
        edits: list[_Edit] = []
        transforms: list[dict[str, Any]] = []
        seen_types: set[str] = set()

        for node in ast.walk(tree):
            edit = _rewrite(node, code)
            if edit is None:
                continue
            edits.append(edit)
            if edit.kind not in seen_types:
                seen_types.add(edit.kind)
                transforms.append({"type": edit.kind, "description": edit.description})

        return _apply_edits(code, edits), transforms


class _Edit:
    """A source-range replacement derived from one AST node."""

    def __init__(
        self,
        node: ast.expr,
        replacement: str,
        kind: str,
        description: str,
    ) -> None:
        self.start = (node.lineno, node.col_offset)
        self.end = (node.end_lineno or node.lineno, node.end_col_offset or 0)
        self.replacement = replacement
        self.kind = kind
        self.description = description


def _segment(code: str, node: ast.expr) -> str:
    segment = ast.get_source_segment(code, node)
    if segment is None:
        raise ValueError(f"no source position for {type(node).__name__}")
    return segment


def _rewrite(node: ast.AST, code: str) -> _Edit | None:
    if isinstance(node, ast.Call):
        return _dict_call(node) or _format_call(node) or _generator_call(node, code)
    if isinstance(node, ast.BinOp):
        return _percent_s(node)
    return None


def _dict_call(node: ast.Call) -> _Edit | None:
    if (
        isinstance(node.func, ast.Name)
        and node.func.id == "dict"
        and not node.args
        and not node.keywords
    ):
        return _Edit(node, "{}", "dict_literal", "Converted dict() to {}")
    return None


_PLAIN_TEXT = re.compile(r'[^"\\\n{}]*')


def _format_call(node: ast.Call) -> _Edit | None:
    """Turn "a {} b".format(x) into f"a {x} b" when placeholders match args."""
    func = node.func
    if not (
        isinstance(func, ast.Attribute)
        and func.attr == "format"
        and isinstance(func.value, ast.Constant)
        and isinstance(func.value.value, str)
        and not node.keywords
        and node.args
        and all(isinstance(arg, ast.Name) for arg in node.args)
    ):
        return None
    pieces = func.value.value.split("{}")
    if len(pieces) - 1 != len(node.args):
        return None
    if not all(_PLAIN_TEXT.fullmatch(piece) for piece in pieces):
        return None
    names = [arg.id for arg in node.args if isinstance(arg, ast.Name)]
    body = pieces[0] + "".join(
        f"{{{name}}}{piece}" for name, piece in zip(names, pieces[1:])
    )
    return _Edit(node, f'f"{body}"', "fstring", "Converted .format() to f-string")


def _percent_s(node: ast.BinOp) -> _Edit | None:
    if (
        isinstance(node.op, ast.Mod)
        and isinstance(node.left, ast.Constant)
        and node.left.value == "%s"
        and isinstance(node.right, ast.Name)
    ):
        return _Edit(
            node,
            f"f'{{{node.right.id}}}'",
            "fstring",
            "Converted %-formatting to f-string",
        )
    return None


def _generator_call(node: ast.Call, code: str) -> _Edit | None:
    """Turn list(x for x in xs) into a comprehension (tuple([...]) for tuple)."""
    if not (
        isinstance(node.func, ast.Name)
        and node.func.id in ("list", "tuple")
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], ast.GeneratorExp)
    ):
        return None
    generator = node.args[0]
    clause = generator.generators[0]
    if not (
        len(generator.generators) == 1
        and not clause.ifs
        and not clause.is_async
        and isinstance(generator.elt, ast.Name)
        and isinstance(clause.target, ast.Name)
        and generator.elt.id == clause.target.id
    ):
        return None
    comprehension = (
        f"[{generator.elt.id} for {generator.elt.id} in {_segment(code, clause.iter)}]"
    )
    if node.func.id == "list":
        return _Edit(
            node,
            comprehension,
            "list_comprehension",
            "Converted list() generator to comprehension",
        )
    return _Edit(
        node,
        f"tuple({comprehension})",
        "tuple_comprehension",
        "Converted tuple() generator to tuple(comprehension)",
    )


def _apply_edits(code: str, edits: list[_Edit]) -> str:
    """Apply edits outermost-first; an edit nested in an applied one is dropped."""
    raw = code.encode("utf-8")
    offsets = [0]
    for line in raw.split(b"\n"):
        offsets.append(offsets[-1] + len(line) + 1)

    def absolute(position: tuple[int, int]) -> int:
        return offsets[position[0] - 1] + position[1]

    spans = sorted(
        ((absolute(e.start), absolute(e.end), e) for e in edits),
        key=lambda span: (span[0], -span[1]),
    )
    kept: list[tuple[int, int, _Edit]] = []
    last_end = 0
    for start, end, edit in spans:
        if start >= last_end:
            kept.append((start, end, edit))
            last_end = end
    for start, end, edit in reversed(kept):
        raw = raw[:start] + edit.replacement.encode("utf-8") + raw[end:]
    return raw.decode("utf-8")
