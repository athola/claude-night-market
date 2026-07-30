"""Tests for British -> American spelling normalization.

The slop workflow normalizes British spellings to American by default
(with a config opt-out and per-word allowlist for intentional British
text). These tests pin the correctness traps that make naive
implementations wrong:

- Words that are ``-ise``/``-our``/``-re`` in form but identical in both
  dialects (surprise, exercise, analysis, four, your) must NOT change.
- Code blocks, inline code, and URLs must be left untouched.
- Case must be preserved (Colour -> Color, COLOUR -> COLOR).
- The allowlist suppresses conversion (Labour Party stays British).
- Conversion is idempotent.
"""

from __future__ import annotations

import pytest

from scribe import spelling
from scribe.spelling import (
    find_british_spellings,
    load_spelling_map,
    to_american,
)

# ---------------------------------------------------------------------------
# load_spelling_map
# ---------------------------------------------------------------------------


def test_map_loads_known_pairs() -> None:
    mapping = load_spelling_map()
    assert mapping["colour"] == "color"
    assert mapping["organise"] == "organize"
    assert mapping["centre"] == "center"
    assert mapping["artefact"] == "artifact"


def test_map_keys_are_lowercase_and_distinct() -> None:
    mapping = load_spelling_map()
    for british, american in mapping.items():
        assert british == british.lower(), f"key not lowercase: {british}"
        assert british != american, f"no-op mapping: {british}"


def test_map_is_not_circular() -> None:
    """An American value must never also be a British key (would oscillate)."""
    mapping = load_spelling_map()
    keys = set(mapping)
    for american in mapping.values():
        assert american not in keys, f"value {american!r} is also a key"


# ---------------------------------------------------------------------------
# load_spelling_map: error branches (issue #569)
# ---------------------------------------------------------------------------


def test_load_raises_on_empty_data(monkeypatch) -> None:
    """An empty or typo'd data file must fail loudly, not silently disable.

    Treating an empty map as valid quietly turns the whole normalization
    feature into a no-op; a missing/empty bundled file is a packaging bug.
    """
    monkeypatch.setattr(spelling, "_MAP_CACHE", None)
    monkeypatch.setattr(spelling, "_REGEX_CACHE", None)
    monkeypatch.setattr(spelling.yaml, "safe_load", lambda *_a, **_k: None)
    with pytest.raises(ValueError, match="empty|unparseable"):
        spelling.load_spelling_map()


def test_load_raises_when_mappings_empty(monkeypatch) -> None:
    """A file that parses but carries no entries is equally unusable."""
    monkeypatch.setattr(spelling, "_MAP_CACHE", None)
    monkeypatch.setattr(spelling, "_REGEX_CACHE", None)
    monkeypatch.setattr(spelling.yaml, "safe_load", lambda *_a, **_k: {"mappings": {}})
    with pytest.raises(ValueError, match="no entries|empty"):
        spelling.load_spelling_map()


def test_load_raises_when_file_missing(monkeypatch, tmp_path) -> None:
    """A missing data file surfaces FileNotFoundError (loader error branch)."""
    monkeypatch.setattr(spelling, "_MAP_CACHE", None)
    monkeypatch.setattr(spelling, "_REGEX_CACHE", None)
    monkeypatch.setattr(spelling, "DATA_FILE", tmp_path / "does_not_exist.yaml")
    with pytest.raises(FileNotFoundError):
        spelling.load_spelling_map()


def test_load_raises_without_pyyaml(monkeypatch) -> None:
    """When pyyaml is unavailable the loader raises a clear ImportError."""
    monkeypatch.setattr(spelling, "_MAP_CACHE", None)
    monkeypatch.setattr(spelling, "_REGEX_CACHE", None)
    monkeypatch.setattr(spelling, "yaml", None)
    with pytest.raises(ImportError, match="pyyaml"):
        spelling.load_spelling_map()


def test_find_reports_column_for_midline_match() -> None:
    """The 1-based column points at the match start, not the line start."""
    # "The colour" -> 'colour' starts at index 4, so column is 5 (1-based).
    findings = find_british_spellings("The colour scheme.")
    assert len(findings) == 1
    assert findings[0]["column"] == 5
    assert findings[0]["line"] == 1


def test_find_reports_column_on_later_line() -> None:
    """Column arithmetic is relative to the current line, not the document."""
    findings = find_british_spellings("first line\n  colour here\n")
    assert len(findings) == 1
    # 'colour' is preceded by two spaces on line 2 -> column 3.
    assert findings[0]["line"] == 2
    assert findings[0]["column"] == 3


# ---------------------------------------------------------------------------
# find_british_spellings
# ---------------------------------------------------------------------------


def test_find_reports_line_and_suggestion() -> None:
    text = "Intro line.\nThe colour scheme is nice.\n"
    findings = find_british_spellings(text)
    assert len(findings) == 1
    f = findings[0]
    assert f["british"] == "colour"
    assert f["american"] == "color"
    assert f["line"] == 2


def test_find_is_case_insensitive() -> None:
    findings = find_british_spellings("Colour and COLOUR and colour.")
    assert len(findings) == 3


def test_find_respects_allowlist() -> None:
    findings = find_british_spellings("The Labour party.", allowlist=["labour"])
    assert findings == []


def test_find_skips_code_and_urls() -> None:
    text = (
        "Prose colour here.\n"
        "Inline `colour` token.\n"
        "See https://example.com/colour/page\n"
        "```\ncolour = 1\n```\n"
    )
    findings = find_british_spellings(text)
    # Only the first, prose occurrence counts.
    assert len(findings) == 1
    assert findings[0]["line"] == 1


# ---------------------------------------------------------------------------
# to_american: conversion + case preservation
# ---------------------------------------------------------------------------


def test_convert_basic() -> None:
    assert to_american("The colour is bold.") == "The color is bold."


def test_convert_preserves_case() -> None:
    assert to_american("Colour") == "Color"
    assert to_american("COLOUR") == "COLOR"
    assert to_american("colour") == "color"


@pytest.mark.parametrize(
    ("british", "american"),
    [
        ("organise", "organize"),
        ("organisation", "organization"),
        ("centre", "center"),
        ("behaviour", "behavior"),
        ("licence", "license"),
        ("catalogue", "catalog"),
        ("travelling", "traveling"),
        ("grey", "gray"),
        ("analyse", "analyze"),
        ("artefact", "artifact"),
    ],
)
def test_convert_families(british: str, american: str) -> None:
    assert to_american(british) == american


# ---------------------------------------------------------------------------
# to_american: false-positive guards (the load-bearing tests)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "unchanged",
    [
        "surprise",  # -ise in both dialects
        "exercise",
        "advertise",
        "comprise",
        "analysis",  # noun is -ysis in both
        "four hours",  # 'our' substring must not trigger
        "your colourless",  # 'your' unchanged; colourless may convert separately
        "the meter reading",  # American already
    ],
)
def test_does_not_corrupt_both_dialect_words(unchanged: str) -> None:
    result = to_american(unchanged)
    for token in ("surprize", "exercize", "advertize", "comprize", "analyzis"):
        assert token not in result
    # 'your' and 'four' must survive intact
    assert "four hours" not in unchanged or "four hours" in result
    assert "your" not in unchanged or "your" in result


def test_convert_skips_code_and_urls() -> None:
    text = (
        "Prose colour.\n"
        "Inline `var colour = 1`.\n"
        "URL https://x.test/colour.\n"
        "```python\ncolour = 2  # behaviour\n```\n"
    )
    out = to_american(text)
    assert "Prose color." in out
    assert "`var colour = 1`" in out  # inline code untouched
    assert "https://x.test/colour" in out  # url untouched
    assert "colour = 2  # behaviour" in out  # fenced code untouched


def test_convert_respects_allowlist() -> None:
    out = to_american("The Labour Party met.", allowlist=["labour"])
    assert out == "The Labour Party met."


def test_convert_is_idempotent() -> None:
    text = "Colour the centre with favourite behaviour while travelling."
    once = to_american(text)
    twice = to_american(once)
    assert once == twice
    assert "colour" not in once.lower()
