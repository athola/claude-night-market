"""Tests for cursor_lean_export script."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from cursor_lean_export import generate_cursor_mdc, parse_frontmatter, trim_body


class TestTrimBody:
    """
    Feature: Strip non-essential sections from skill body

    As a plugin developer
    I want lean skill exports for Cursor
    So that token costs are reduced by removing noise
    """

    @pytest.mark.unit
    def test_preserves_troubleshooting_section(self):
        """
        Scenario: Body contains Troubleshooting section
        Given a skill body with a ## Troubleshooting heading
        When trimmed
        Then that section is preserved (has task-relevant content)
        """
        body = "# Main\n\nContent here.\n\n## Troubleshooting\n\nFix stuff.\n"
        result = trim_body(body)
        assert "Troubleshooting" in result
        assert "Content here." in result

    @pytest.mark.unit
    def test_strips_see_also_section(self):
        body = "# Main\n\nContent.\n\n## See Also\n\n- Link\n- Link2\n"
        result = trim_body(body)
        assert "See Also" not in result
        assert "Content." in result

    @pytest.mark.unit
    def test_strips_module_references(self):
        body = "# Main\n\n- [Output templates](modules/output-templates.md) - formats\n\nOther content.\n"
        result = trim_body(body)
        assert "modules/" not in result
        assert "Other content." in result

    @pytest.mark.unit
    def test_preserves_essential_content(self):
        body = "# Steps\n\n1. Do this\n2. Do that\n\n## Rules\n\nNever do X.\n"
        result = trim_body(body)
        assert "Do this" in result
        assert "Never do X." in result

    @pytest.mark.unit
    def test_collapses_excessive_blank_lines(self):
        body = "Line 1\n\n\n\n\nLine 2\n"
        result = trim_body(body)
        assert "\n\n\n" not in result


class TestParseFrontmatter:
    """
    Feature: Parse YAML frontmatter from SKILL.md files
    """

    @pytest.mark.unit
    def test_extracts_name(self):
        content = "---\nname: my-skill\ndescription: A skill\n---\n\n# Body\n"
        fm, body = parse_frontmatter(content)
        assert fm["name"] == "my-skill"
        assert "# Body" in body

    @pytest.mark.unit
    def test_handles_no_frontmatter(self):
        content = "# Just a body\n"
        fm, body = parse_frontmatter(content)
        assert fm == {}
        assert "Just a body" in body


class TestGenerateCursorMdc:
    """
    Feature: Generate Cursor .mdc format from skill data
    """

    @pytest.mark.unit
    def test_includes_description_and_model_hint(self):
        fm = {
            "description": "Generate commit messages. Use when committing.",
            "model_hint": "fast",
            "alwaysApply": False,
        }
        result = generate_cursor_mdc(fm, "# Body", "sanctum", "commit-messages")
        assert "Generate commit messages." in result
        assert "model_hint: fast" in result
        assert "sanctum:commit-messages" in result

    @pytest.mark.unit
    def test_strips_use_when_from_description(self):
        fm = {
            "description": "Do X. Use when Y happens. Do not use when Z.",
            "model_hint": "standard",
        }
        result = generate_cursor_mdc(fm, "# Body", "test", "test-skill")
        assert "Use when" not in result.split("---")[1]  # in frontmatter
        assert "Do X." in result
