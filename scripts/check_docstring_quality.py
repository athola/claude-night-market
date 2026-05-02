#!/usr/bin/env python3
"""Pre-commit hook: flag docstrings that merely restate the function name.

A docstring that restates the function name (e.g. ``def get_user():
\"\"\"Get user.\"\"\"``) costs reader attention without paying for it.
Either delete it (the name is the documentation) or rewrite it to add
information the name does not already convey.

Skip rules:
- Dunder methods (``__init__`` etc.) — Python convention permits stub
  docstrings.
- Private helpers (``_name``) — implementation detail; full docstrings
  are encouraged but minimal ones are acceptable.
- Empty docstrings — not in scope for this rule.

Exit codes:
    0 - no restating docstrings found
    1 - one or more restating docstrings detected (commit blocked)
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

_STOPWORDS = {
    "a",
    "an",
    "the",
    "this",
    "that",
    "to",
    "for",
    "of",
    "in",
    "on",
    "with",
    "from",
    "by",
    "and",
    "or",
}

_VERB_SUFFIXES = ("s", "es", "ed", "ing")


def _normalize(text: str) -> set[str]:
    """Lower-case, strip punctuation, drop stopwords and verb suffixes."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    out: set[str] = set()
    for tok in tokens:
        if tok in _STOPWORDS:
            continue
        for suf in _VERB_SUFFIXES:
            if len(tok) > len(suf) + 1 and tok.endswith(suf):
                tok = tok[: -len(suf)]
                break
        out.add(tok)
    return out


def is_restating_docstring(func_name: str, docstring: str) -> bool:
    """Return True when ``docstring`` adds no information over ``func_name``.

    Out of scope: dunder methods, private helpers, empty docstrings.
    """
    if func_name.startswith("__") and func_name.endswith("__"):
        return False
    if func_name.startswith("_"):
        return False
    text = docstring.strip()
    if not text:
        return False

    first_line = text.splitlines()[0].strip().rstrip(".")
    if len(first_line) > 80:
        return False

    name_tokens = _normalize(func_name.replace("_", " "))
    doc_tokens = _normalize(first_line)

    if not name_tokens or not doc_tokens:
        return False

    extra = doc_tokens - name_tokens
    return not extra


def check_file(path: Path) -> list[str]:
    """Return ``file:line: message`` strings for each restating docstring."""
    try:
        source = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        doc = ast.get_docstring(node) or ""
        if is_restating_docstring(node.name, doc):
            hits.append(
                f"{path}:{node.lineno}: docstring for `{node.name}` "
                f"restates the function name; delete it or add information"
            )
    return hits


def main(argv: list[str]) -> int:
    """Entry point. Accepts file paths from pre-commit."""
    paths = [Path(p) for p in argv[1:] if p.endswith(".py")]
    all_hits: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        all_hits.extend(check_file(path))
    if all_hits:
        for hit in all_hits:
            print(hit)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
