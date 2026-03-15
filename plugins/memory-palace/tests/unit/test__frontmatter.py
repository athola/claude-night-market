"""Tests for shared frontmatter parsing helpers."""

from __future__ import annotations

import pytest

from memory_palace.corpus._frontmatter import parse_entry_frontmatter, split_entry


class TestParseEntryFrontmatter:
    """Tests for parse_entry_frontmatter()."""

    @pytest.mark.unit
    def test_returns_dict_for_valid_frontmatter(self) -> None:
        """Return parsed dict when entry has valid YAML frontmatter."""
        content = (
            "---\ntitle: Test Entry\ntags:\n  - alpha\n  - beta\n---\nBody text here."
        )
        result = parse_entry_frontmatter(content)

        assert result is not None
        assert result["title"] == "Test Entry"
        assert result["tags"] == ["alpha", "beta"]

    @pytest.mark.unit
    def test_returns_none_when_no_frontmatter(self) -> None:
        """Return None when content does not start with ---."""
        content = "Just plain markdown body text."
        result = parse_entry_frontmatter(content)

        assert result is None

    @pytest.mark.unit
    def test_returns_none_for_incomplete_delimiters(self) -> None:
        """Return None when opening --- has no closing ---."""
        content = "---\ntitle: Broken\n"
        result = parse_entry_frontmatter(content)

        assert result is None

    @pytest.mark.unit
    def test_returns_none_for_invalid_yaml(self) -> None:
        """Return None when frontmatter contains malformed YAML."""
        content = "---\n: [invalid yaml\n---\nBody."
        result = parse_entry_frontmatter(content)

        assert result is None

    @pytest.mark.unit
    def test_returns_none_for_scalar_yaml(self) -> None:
        """Return None when YAML parses to a non-dict scalar."""
        content = "---\njust a string\n---\nBody."
        result = parse_entry_frontmatter(content)

        assert result is None

    @pytest.mark.unit
    def test_returns_none_for_empty_string(self) -> None:
        """Return None for empty content."""
        result = parse_entry_frontmatter("")

        assert result is None

    @pytest.mark.unit
    def test_preserves_nested_metadata(self) -> None:
        """Preserve nested dicts and lists in frontmatter."""
        content = "---\ntitle: Nested\nextra:\n  foo: bar\n  count: 42\n---\nBody."
        result = parse_entry_frontmatter(content)

        assert result is not None
        assert result["extra"] == {"foo": "bar", "count": 42}


class TestSplitEntry:
    """Tests for split_entry()."""

    @pytest.mark.unit
    def test_splits_valid_entry(self) -> None:
        """Return (metadata_dict, body_text) for valid frontmatter."""
        content = "---\ntitle: Hello\n---\nThe body content."
        metadata, body = split_entry(content)

        assert metadata is not None
        assert metadata["title"] == "Hello"
        assert body == "\nThe body content."

    @pytest.mark.unit
    def test_returns_none_and_full_content_when_no_frontmatter(self) -> None:
        """Return (None, original_content) when no --- delimiters present."""
        content = "Plain markdown text."
        metadata, body = split_entry(content)

        assert metadata is None
        assert body == content

    @pytest.mark.unit
    def test_returns_none_and_full_content_for_incomplete_delimiters(self) -> None:
        """Return (None, original_content) when only opening --- exists."""
        content = "---\ntitle: Broken\n"
        metadata, body = split_entry(content)

        assert metadata is None
        assert body == content

    @pytest.mark.unit
    def test_returns_none_and_full_content_for_invalid_yaml(self) -> None:
        """Return (None, original_content) for malformed YAML."""
        content = "---\n: [bad yaml\n---\nBody."
        metadata, body = split_entry(content)

        assert metadata is None
        assert body == content

    @pytest.mark.unit
    def test_returns_none_and_full_content_for_scalar_yaml(self) -> None:
        """Return (None, original_content) when YAML parses to non-dict."""
        content = "---\njust a string\n---\nBody."
        metadata, body = split_entry(content)

        assert metadata is None
        assert body == content

    @pytest.mark.unit
    def test_body_preserves_multiple_sections(self) -> None:
        """Keep --- separators in body when they appear after frontmatter."""
        content = "---\ntitle: Test\n---\nPart 1\n---\nPart 2"
        metadata, body = split_entry(content)

        assert metadata is not None
        assert metadata["title"] == "Test"
        # The body should include the --- that appears in the text
        assert "Part 1" in body
        assert "---" in body
        assert "Part 2" in body
