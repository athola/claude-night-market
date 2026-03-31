"""AST-based knowledge extraction from Python source files."""

from __future__ import annotations

import ast
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from gauntlet.models import KnowledgeEntry

# ---------------------------------------------------------------------------
# Category keyword mapping
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS = {
    "business_logic": {"business", "rule", "calculate", "validate", "discount"},
    "data_flow": {"pipeline", "transform", "flow"},
    "api_contract": {"endpoint", "route", "handler"},
    "error_handling": {"error", "exception", "retry"},
}

_DEFAULT_CATEGORY = "architecture"

# ---------------------------------------------------------------------------
# Difficulty line-count thresholds
# ---------------------------------------------------------------------------

_DIFFICULTY_THRESHOLDS = [
    (10, 1),
    (30, 2),
    (60, 3),
    (100, 4),
]
_MAX_DIFFICULTY = 5

# ---------------------------------------------------------------------------
# Branch node types that add complexity
# ---------------------------------------------------------------------------

_BRANCH_TYPES = (ast.If, ast.For, ast.While, ast.Try)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_from_file(file_path: Path) -> list[KnowledgeEntry]:
    """Parse a single Python file and return KnowledgeEntry objects.

    Returns an empty list if the file does not exist or contains a
    syntax error.
    """
    if not file_path.exists():
        return []

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    module_name = file_path.stem
    entries: list[KnowledgeEntry] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            # Skip private names except __init__
            if name.startswith("_") and name != "__init__":
                continue

            docstring = ast.get_docstring(node) or ""
            difficulty = _estimate_difficulty(node)
            category = _infer_category(docstring)
            entry_id = _stable_id(module_name, name)
            extracted_at = datetime.now(timezone.utc).isoformat()

            entries.append(
                KnowledgeEntry(
                    id=entry_id,
                    category=category,
                    module=module_name,
                    concept=name,
                    detail=docstring,
                    difficulty=difficulty,
                    extracted_at=extracted_at,
                    source="code",
                    related_files=[str(file_path)],
                    tags=[],
                    consumers=[],
                )
            )

    return entries


def extract_from_directory(
    directory: Path,
    exclude_patterns: list[str] | None = None,
) -> list[KnowledgeEntry]:
    """Recursively extract KnowledgeEntry objects from all .py files.

    Skips files whose names match the pattern ``__*.py`` (dunder modules
    such as ``__init__.py`` and ``__main__.py``).
    """
    entries: list[KnowledgeEntry] = []

    for py_file in sorted(directory.glob("*.py")):
        if py_file.name.startswith("__"):
            continue
        if exclude_patterns and any(py_file.match(pat) for pat in exclude_patterns):
            continue
        entries.extend(extract_from_file(py_file))

    return entries


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _estimate_difficulty(node: ast.AST) -> int:
    """Estimate difficulty from line count and branching complexity."""
    end_lineno = getattr(node, "end_lineno", None)
    lineno = getattr(node, "lineno", None)
    if end_lineno is not None and lineno is not None:
        line_count = end_lineno - lineno
    else:
        line_count = 0

    difficulty = _MAX_DIFFICULTY
    for threshold, level in _DIFFICULTY_THRESHOLDS:
        if line_count < threshold:
            difficulty = level
            break

    # Add 1 for any branch nodes found inside the definition
    has_branch = any(
        isinstance(child, _BRANCH_TYPES)
        for child in ast.walk(node)
        if child is not node
    )
    if has_branch:
        difficulty = min(difficulty + 1, _MAX_DIFFICULTY)

    return difficulty


def _infer_category(docstring: str) -> str:
    """Map docstring keywords to a knowledge category."""
    lower = docstring.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return category
    return _DEFAULT_CATEGORY


def _stable_id(module: str, name: str) -> str:
    """Return a 12-character hex ID derived from module and name."""
    return hashlib.sha256(f"{module}:{name}".encode()).hexdigest()[:12]
