"""Shared constants and helpers for the testing-guide mixins."""

from __future__ import annotations

import ast

MIN_FUNCTIONS_FOR_PARAMETRIZE = 3
HEAVY_PARAMETRIZE_THRESHOLD = 100


def parse_code(code: str) -> tuple[ast.Module | None, dict | None]:
    """Parse code into an AST, returning an error dict on failure."""
    try:
        return ast.parse(code), None
    except SyntaxError:
        return None, {"error": "Invalid Python syntax"}
