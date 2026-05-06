"""Tests for leyline.frontmatter -- canonical YAML frontmatter parser.

Feature: Frontmatter parsing

As a plugin developer
I want a single canonical frontmatter parser
So that all plugins parse YAML frontmatter consistently
"""

from __future__ import annotations

import pytest

import leyline.frontmatter as fm
from leyline.frontmatter import (
    _fallback_parse,
    parse_frontmatter,
    parse_frontmatter_with_body,
)


class TestParseFrontmatter:
    """Scenarios for parse_frontmatter()."""

    @pytest.mark.unit
    def test_returns_none_when_no_frontmatter_block(self):
        """Given content without a --- delimiter,
        When parse_frontmatter is called,
        Then it returns None.
        """
        assert parse_frontmatter("# Just a heading\nSome text.") is None

    @pytest.mark.unit
    def test_returns_none_when_no_closing_delimiter(self):
        """Given content with an opening --- but no closing ---,
        When parse_frontmatter is called,
        Then it returns None.
        """
        assert parse_frontmatter("---\ntitle: Hello\nNo closing") is None

    @pytest.mark.unit
    def test_parses_simple_key_value_frontmatter(self):
        """Given valid frontmatter with key-value pairs,
        When parse_frontmatter is called,
        Then it returns a dict with parsed values.
        """
        content = "---\ntitle: My Doc\nauthor: Alice\n---\n# Body"
        result = parse_frontmatter(content)
        assert result is not None
        assert result["title"] == "My Doc"
        assert result["author"] == "Alice"

    @pytest.mark.unit
    def test_returns_empty_dict_for_empty_frontmatter(self):
        """Given frontmatter delimiters with no content between,
        When parse_frontmatter is called,
        Then it returns an empty dict.
        """
        result = parse_frontmatter("---\n---\nBody text")
        assert result == {}

    @pytest.mark.unit
    def test_handles_leading_whitespace(self):
        """Given content with leading whitespace before ---,
        When parse_frontmatter is called,
        Then it still parses the frontmatter.
        """
        content = "  \n---\nkey: value\n---\nBody"
        result = parse_frontmatter(content)
        assert result is not None
        assert result["key"] == "value"

    @pytest.mark.unit
    def test_returns_none_for_invalid_yaml(self):
        """Given frontmatter containing invalid YAML,
        When parse_frontmatter is called,
        Then it returns None.
        """
        content = "---\n: :\n  - [\n---\nBody"
        result = parse_frontmatter(content)
        assert result is None

    @pytest.mark.unit
    def test_parses_list_values(self):
        """Given frontmatter with a YAML list,
        When parse_frontmatter is called,
        Then the list is preserved in the result dict.
        """
        content = "---\ntags:\n  - python\n  - testing\n---\nBody"
        result = parse_frontmatter(content)
        assert result is not None
        assert result["tags"] == ["python", "testing"]

    @pytest.mark.unit
    def test_parses_nested_dict(self):
        """Given frontmatter with nested keys,
        When parse_frontmatter is called,
        Then nested structure is preserved.
        """
        content = "---\nmeta:\n  version: 1\n  draft: true\n---\n"
        result = parse_frontmatter(content)
        assert result is not None
        assert result["meta"]["version"] == 1
        assert result["meta"]["draft"] is True

    @pytest.mark.unit
    def test_ignores_content_after_closing_delimiter(self):
        """Given content with --- appearing in the body,
        When parse_frontmatter is called,
        Then only the first frontmatter block is parsed.
        """
        content = "---\ntitle: Doc\n---\nBody with ---\nmore text"
        result = parse_frontmatter(content)
        assert result is not None
        assert result["title"] == "Doc"
        assert len(result) == 1


class TestParseFrontmatterWithBody:
    """Scenarios for parse_frontmatter_with_body() (D-02).

    The helper is added to consolidate the four scripts
    (clawhub_export, a2a_cards, area_agent_registry,
    coordination_workspace) that re-implemented FRONTMATTER_RE
    plus a parser. Each needs the parsed frontmatter dict and
    the body string after the closing ``---``.
    """

    @pytest.mark.unit
    def test_returns_empty_meta_and_full_body_when_no_frontmatter(self):
        """Given content without a frontmatter block,
        When parse_frontmatter_with_body is called,
        Then meta is empty and body is the original content.
        """
        meta, body = parse_frontmatter_with_body("# Just a heading\nText.")
        assert meta == {}
        assert body == "# Just a heading\nText."

    @pytest.mark.unit
    def test_returns_meta_and_body_for_valid_frontmatter(self):
        """Given a valid frontmatter block,
        When parse_frontmatter_with_body is called,
        Then it returns the parsed meta and the body after ---.
        """
        content = "---\ntitle: Hi\n---\n# Body\ntext\n"
        meta, body = parse_frontmatter_with_body(content)
        assert meta == {"title": "Hi"}
        assert body == "# Body\ntext\n"

    @pytest.mark.unit
    def test_preserves_body_when_body_contains_dashes(self):
        """Given body that itself contains --- separators,
        When parse_frontmatter_with_body is called,
        Then those separators are preserved in body.
        """
        content = "---\nkey: v\n---\n# Heading\n---\nrest"
        meta, body = parse_frontmatter_with_body(content)
        assert meta == {"key": "v"}
        assert "---" in body
        assert "rest" in body

    @pytest.mark.unit
    def test_handles_closing_dashes_at_end_of_file(self):
        """Given a document where the closing ``---`` is the last
        characters with no trailing newline,
        When parse_frontmatter_with_body is called,
        Then the meta is parsed and body is empty (parity with
        parse_frontmatter for the same input).

        Regression: F2 from /pensive:full-review. The original
        FRONTMATTER_RE required ``\\n---\\s*\\n`` so a file ending
        in ``---`` without trailing newline silently returned
        ``({}, full_content)`` while parse_frontmatter handled it.
        """
        content = "---\ntitle: foo\n---"
        meta, body = parse_frontmatter_with_body(content)
        assert meta == {"title": "foo"}
        assert body == ""

    @pytest.mark.unit
    def test_returns_empty_meta_when_yaml_invalid(self):
        """Given invalid YAML in the frontmatter block,
        When parse_frontmatter_with_body is called,
        Then meta is empty and body is original content.

        Callers (clawhub_export, a2a_cards) treat unparseable
        frontmatter as 'no frontmatter' rather than fatal.
        """
        content = "---\n: :\n  - [\n---\nBody"
        meta, body = parse_frontmatter_with_body(content)
        assert meta == {}
        assert body == content


class TestFallbackParse:
    """Scenarios for _fallback_parse() when PyYAML is unavailable."""

    @pytest.mark.unit
    def test_fallback_simple_key_value(self):
        """Given raw text with key: value lines,
        When _fallback_parse is called,
        Then it returns a dict of stripped key-value pairs.
        """
        raw = "title: Hello\nauthor: Bob"
        result = _fallback_parse(raw)
        assert result == {"title": "Hello", "author": "Bob"}

    @pytest.mark.unit
    def test_fallback_skips_blank_and_comment_lines(self):
        """Given raw text with blank lines and comments,
        When _fallback_parse is called,
        Then those lines are ignored.
        """
        raw = "# comment\n  \nkey: val\n# another\nother: data"
        result = _fallback_parse(raw)
        assert result == {"key": "val", "other": "data"}

    @pytest.mark.unit
    def test_fallback_skips_lines_without_colon(self):
        """Given raw text with lines missing a colon,
        When _fallback_parse is called,
        Then those lines are skipped.
        """
        raw = "key: val\nno colon here\nanother: one"
        result = _fallback_parse(raw)
        assert result == {"key": "val", "another": "one"}

    @pytest.mark.unit
    def test_fallback_returns_empty_for_empty_input(self):
        """Given an empty string,
        When _fallback_parse is called,
        Then it returns an empty dict.
        """
        assert _fallback_parse("") == {}


class TestParseWithoutYaml:
    """Scenarios for parse_frontmatter when PyYAML is not installed."""

    @pytest.mark.unit
    def test_uses_fallback_when_yaml_is_none(self, monkeypatch):
        """Given yaml module is unavailable,
        When parse_frontmatter is called with valid frontmatter,
        Then it falls back to simple key-value parsing.
        """
        monkeypatch.setattr(fm, "_yaml", None)
        content = "---\ntitle: Hello\nauthor: World\n---\nBody"
        result = fm.parse_frontmatter(content)
        assert result == {"title": "Hello", "author": "World"}

    @pytest.mark.unit
    def test_fallback_returns_empty_for_empty_block(self, monkeypatch):
        """Given yaml module is unavailable and empty frontmatter block,
        When parse_frontmatter is called,
        Then it returns an empty dict.
        """
        monkeypatch.setattr(fm, "_yaml", None)
        result = fm.parse_frontmatter("---\n---\nBody")
        assert result == {}
