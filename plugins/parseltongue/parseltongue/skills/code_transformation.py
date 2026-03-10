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
        transforms: list[dict[str, Any]] = []
        result = code

        result, t = self._convert_dict_calls(result)
        transforms.extend(t)

        result, t = self._convert_format_to_fstring(result)
        transforms.extend(t)

        result, t = self._convert_list_tuple_comprehensions(result)
        transforms.extend(t)

        return result, transforms

    def _convert_dict_calls(self, code: str) -> tuple[str, list[dict[str, Any]]]:
        transforms: list[dict[str, Any]] = []
        pattern = r"\bdict\(\)"
        if re.search(pattern, code):
            code = re.sub(pattern, "{}", code)
            transforms.append(
                {
                    "type": "dict_literal",
                    "description": "Converted dict() to {}",
                }
            )
        return code, transforms

    def _convert_format_to_fstring(self, code: str) -> tuple[str, list[dict[str, Any]]]:
        transforms: list[dict[str, Any]] = []

        # Convert simple "{}".format(x) patterns
        pattern = r'"([^"]*)\{(\}[^"]*)"\.format\((\w+)\)'
        match = re.search(pattern, code)
        if match:
            code = re.sub(
                pattern,
                lambda m: f'f"{m.group(1)}{{{m.group(3)}}}{m.group(2)[1:]}"',
                code,
            )
            transforms.append(
                {
                    "type": "fstring",
                    "description": "Converted .format() to f-string",
                }
            )

        # Convert simple '%s' % x patterns
        pct_pattern = r"'%s'\s*%\s*(\w+)"
        match = re.search(pct_pattern, code)
        if match:
            code = re.sub(pct_pattern, lambda m: f"f'{{{m.group(1)}}}'", code)
            transforms.append(
                {
                    "type": "fstring",
                    "description": "Converted %-formatting to f-string",
                }
            )

        return code, transforms

    def _convert_list_tuple_comprehensions(
        self, code: str
    ) -> tuple[str, list[dict[str, Any]]]:
        transforms: list[dict[str, Any]] = []

        # Convert list(x for x in ...) to [x for x in ...]
        list_pattern = r"\blist\(((\w+)\s+for\s+\2\s+in\s+[^)]+)\)"
        match = re.search(list_pattern, code)
        if match:
            code = re.sub(list_pattern, r"[\1]", code)
            transforms.append(
                {
                    "type": "list_comprehension",
                    "description": "Converted list() generator to comprehension",
                }
            )

        # Convert tuple(x for x in ...) to tuple([x for x in ...])
        tuple_pattern = r"\btuple\(((\w+)\s+for\s+\2\s+in\s+[^)]+)\)"
        match = re.search(tuple_pattern, code)
        if match:
            code = re.sub(tuple_pattern, r"tuple([\1])", code)
            transforms.append(
                {
                    "type": "tuple_comprehension",
                    "description": "Converted tuple() generator "
                    "to tuple(comprehension)",
                }
            )

        return code, transforms
