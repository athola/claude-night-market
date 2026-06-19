"""British -> American spelling normalization for slop detection.

The slop workflow normalizes British spellings to American by default.
This module provides three functions (the loader memoizes the map in a
module-level cache; the detection and rewrite functions are pure given the
loaded data):

- :func:`load_spelling_map` loads the curated British -> American mapping.
- :func:`find_british_spellings` reports occurrences with line/column and a
  suggested American replacement (for flag-only reporting).
- :func:`to_american` rewrites text, converting British spellings while
  preserving case and leaving code, inline code, and URLs untouched.

Both detection functions accept an ``allowlist`` of British words to leave
alone (proper nouns such as "Labour Party", or documents that intentionally
use British spelling).

The mapping is an explicit word list, never a suffix rule: "-ise -> -ize"
would corrupt words that are -ise in both dialects (surprise, exercise) and
nouns that are -ysis in both (analysis). See ``data/spelling/`` for the data
and its design rules.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised via ImportError branch
    yaml = None

# Data file lives alongside the language packs, as a sibling of ``src``.
DATA_FILE = (
    Path(__file__).parent.parent.parent / "data" / "spelling" / "british_american.yaml"
)

# Spans of text that must never be rewritten: fenced code blocks, inline code,
# and URLs. A CSS ``color``, a variable named ``behaviour_flag``, or a link
# path are not prose and must survive normalization untouched.
_FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]*`")
_URL = re.compile(r"https?://\S+")

_MAP_CACHE: dict[str, str] | None = None
_REGEX_CACHE: re.Pattern[str] | None = None


def load_spelling_map() -> dict[str, str]:
    """Load and cache the curated British -> American spelling map.

    Returns:
        Mapping of lowercase British spelling to its American replacement.

    Raises:
        ImportError: If pyyaml is not installed.
        FileNotFoundError: If the data file is missing.
        ValueError: If the data file is empty, unparseable, or carries no
            entries. An empty map silently turns normalization into a
            no-op, so it is treated as a packaging bug (issue #569).
    """
    global _MAP_CACHE
    if _MAP_CACHE is not None:
        return _MAP_CACHE

    if yaml is None:
        raise ImportError(
            "pyyaml is required to load the spelling map. "
            "Install it with: pip install pyyaml"
        )
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Spelling data file not found: {DATA_FILE}")

    with open(DATA_FILE, encoding="utf-8") as f:
        raw: dict[str, Any] | None = yaml.safe_load(f)

    if not raw:
        raise ValueError(f"Spelling map is empty or unparseable: {DATA_FILE}")

    mappings = raw.get("mappings", raw)
    if not mappings:
        raise ValueError(f"Spelling map has no entries: {DATA_FILE}")

    _MAP_CACHE = {str(k).lower(): str(v) for k, v in mappings.items()}
    return _MAP_CACHE


def _build_regex() -> re.Pattern[str]:
    """Compile a single word-boundary regex matching every British key.

    Keys are sorted longest-first so the alternation prefers the most specific
    match. The result is cached because the map is static per process.
    """
    global _REGEX_CACHE
    if _REGEX_CACHE is not None:
        return _REGEX_CACHE

    keys = sorted(load_spelling_map(), key=len, reverse=True)
    if not keys:
        # A pattern that can never match, so callers degrade to no-ops.
        _REGEX_CACHE = re.compile(r"(?!x)x")
        return _REGEX_CACHE

    alternation = "|".join(re.escape(k) for k in keys)
    _REGEX_CACHE = re.compile(rf"\b({alternation})\b", re.IGNORECASE)
    return _REGEX_CACHE


def _protected_spans(text: str) -> list[tuple[int, int]]:
    """Return character spans (code, inline code, URLs) to leave untouched."""
    spans: list[tuple[int, int]] = []
    for pattern in (_FENCED_CODE, _INLINE_CODE, _URL):
        spans.extend((m.start(), m.end()) for m in pattern.finditer(text))
    return spans


def _in_protected(pos: int, spans: Iterable[tuple[int, int]]) -> bool:
    return any(start <= pos < end for start, end in spans)


def _match_case(source: str, replacement: str) -> str:
    """Map ``replacement`` onto the case pattern of the matched ``source``."""
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def find_british_spellings(
    text: str,
    allowlist: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Find British spellings in ``text`` without modifying it.

    Args:
        text: The document text to scan.
        allowlist: British words to ignore (case-insensitive). Use for proper
            nouns or intentionally British terms.

    Returns:
        One dict per occurrence with keys ``line`` (1-based), ``column``
        (1-based), ``british`` (lowercase matched key), ``matched`` (the text
        as it appeared), and ``american`` (suggested replacement). Matches
        inside code, inline code, or URLs are skipped.
    """
    mapping = load_spelling_map()
    allow = {w.lower() for w in (allowlist or ())}
    spans = _protected_spans(text)
    regex = _build_regex()

    findings: list[dict[str, Any]] = []
    for match in regex.finditer(text):
        start = match.start()
        if _in_protected(start, spans):
            continue
        matched = match.group(0)
        key = matched.lower()
        if key in allow:
            continue
        american = mapping.get(key)
        if american is None:
            continue
        line = text.count("\n", 0, start) + 1
        column = start - (text.rfind("\n", 0, start) + 1) + 1
        findings.append(
            {
                "line": line,
                "column": column,
                "british": key,
                "matched": matched,
                "american": american,
            }
        )
    return findings


def to_american(text: str, allowlist: Iterable[str] | None = None) -> str:
    """Rewrite British spellings to American, preserving case.

    Code blocks, inline code, URLs, and allowlisted words are left untouched.
    Conversion is idempotent: no American value is also a British key, so a
    second pass changes nothing.

    Args:
        text: The document text to convert.
        allowlist: British words to leave unchanged (case-insensitive).

    Returns:
        The converted text.
    """
    mapping = load_spelling_map()
    allow = {w.lower() for w in (allowlist or ())}
    spans = _protected_spans(text)
    regex = _build_regex()

    def replace(match: re.Match[str]) -> str:
        if _in_protected(match.start(), spans):
            return match.group(0)
        matched = match.group(0)
        key = matched.lower()
        if key in allow:
            return matched
        american = mapping.get(key)
        if american is None:
            return matched
        return _match_case(matched, american)

    return regex.sub(replace, text)
