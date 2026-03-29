"""Tests for leyline.frontmatter -- canonical YAML frontmatter parser.

Feature: Frontmatter parsing

As a plugin developer
I want a single canonical frontmatter parser
So that all plugins parse YAML frontmatter consistently
"""

from __future__ import annotations

import pytest

import leyline.frontmatter as fm
from leyline.frontmatter import _fallback_parse, parse_frontmatter


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
