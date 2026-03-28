"""Tests for cursor_lean_export script."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from cursor_lean_export import (
    _parse_yaml_simple,
    export_lean,
    generate_cursor_mdc,
    parse_frontmatter,
    trim_body,
)


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

    @pytest.mark.unit
    def test_strips_table_of_contents_section(self):
        body = (
            "# Main\n\nContent.\n\n"
            "## Table of Contents\n\n- [A](#a)\n- [B](#b)\n\n"
            "## Real Section\n\nKeep this.\n"
        )
        result = trim_body(body)
        assert "Table of Contents" not in result
        assert "Keep this." in result

    @pytest.mark.unit
    def test_strips_supporting_modules_section(self):
        body = (
            "# Main\n\nContent.\n\n"
            "## Supporting Modules\n\n- module-a\n- module-b\n\n"
            "## Usage\n\nKeep this.\n"
        )
        result = trim_body(body)
        assert "Supporting Modules" not in result
        assert "Keep this." in result


class TestParseYamlSimple:
    """
    Feature: Minimal YAML parsing for frontmatter fields

    Covers boolean, integer, inline list, multi-line list,
    and multiline continuation parsing.
    """

    @pytest.mark.unit
    def test_parses_boolean_true(self):
        result = _parse_yaml_simple("alwaysApply: true")
        assert result["alwaysApply"] is True

    @pytest.mark.unit
    def test_parses_boolean_false(self):
        result = _parse_yaml_simple("alwaysApply: false")
        assert result["alwaysApply"] is False

    @pytest.mark.unit
    def test_parses_integer(self):
        result = _parse_yaml_simple("estimated_tokens: 200")
        assert result["estimated_tokens"] == 200

    @pytest.mark.unit
    def test_parses_inline_list(self):
        result = _parse_yaml_simple("tags: [fast, lean, export]")
        assert result["tags"] == ["fast", "lean", "export"]

    @pytest.mark.unit
    def test_parses_multiline_list(self):
        text = "tools:\n- Read\n- Write\n- Bash"
        result = _parse_yaml_simple(text)
        assert result["tools"] == ["Read", "Write", "Bash"]

    @pytest.mark.unit
    def test_skips_comments(self):
        text = "# comment line\nname: my-skill"
        result = _parse_yaml_simple(text)
        assert result["name"] == "my-skill"
        assert "#" not in result

    @pytest.mark.unit
    def test_multiline_continuation(self):
        text = "description: First part\n  second part"
        result = _parse_yaml_simple(text)
        assert result["description"] == "First part second part"

    @pytest.mark.unit
    def test_empty_value(self):
        result = _parse_yaml_simple("globs:")
        assert result["globs"] == ""


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

    @pytest.mark.unit
    def test_parses_boolean_and_integer_fields(self):
        content = (
            "---\nname: test\nalwaysApply: true\nestimated_tokens: 150\n---\n\nBody\n"
        )
        fm, _ = parse_frontmatter(content)
        assert fm["alwaysApply"] is True
        assert fm["estimated_tokens"] == 150


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

    @pytest.mark.unit
    def test_always_apply_true(self):
        fm = {"description": "Always on.", "alwaysApply": True}
        result = generate_cursor_mdc(fm, "Body", "p", "s")
        assert "alwaysApply: true" in result

    @pytest.mark.unit
    def test_includes_globs_when_present(self):
        fm = {"description": "Lint.", "globs": "*.py"}
        result = generate_cursor_mdc(fm, "Body", "p", "s")
        assert "globs: *.py" in result

    @pytest.mark.unit
    def test_defaults_model_hint_to_standard(self):
        fm = {"description": "No hint set."}
        result = generate_cursor_mdc(fm, "Body", "p", "s")
        assert "model_hint: standard" in result


class TestExportLean:
    """
    Feature: Export skills to lean directory format

    Uses a mock plugins directory with synthetic SKILL.md files
    to test tier filtering, index-only mode, and trimming.
    """

    @pytest.fixture()
    def mock_plugins(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Create a minimal plugins dir with two skills."""
        plugins = tmp_path / "plugins"
        for plugin, skill, complexity in [
            ("sanctum", "commit-messages", "low"),
            ("pensive", "bug-review", "advanced"),
        ]:
            skill_dir = plugins / plugin / "skills" / skill
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {skill}\ndescription: A {skill} skill.\n"
                f"complexity: {complexity}\n---\n\n# {skill}\n\nContent.\n\n"
                f"## See Also\n\n- link\n"
            )
        monkeypatch.setattr("cursor_lean_export.PLUGINS_DIR", plugins)
        return plugins

    @pytest.mark.unit
    def test_exports_all_skills(self, mock_plugins: Path, tmp_path: Path):
        """
        Given a plugins dir with 2 skills
        When exported with tier "all"
        Then both skills are exported
        """
        out = tmp_path / "output"
        result = export_lean(out, tier="all")
        assert result["exported"] == 2
        assert (out / "commit-messages" / "SKILL.md").exists()
        assert (out / "bug-review" / "SKILL.md").exists()

    @pytest.mark.unit
    def test_tier_filters_skills(
        self, mock_plugins: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Given a custom tier with only one skill
        When exported with that tier
        Then only the matching skill is exported
        """
        monkeypatch.setattr(
            "cursor_lean_export.TIERS",
            {"custom": ["sanctum:commit-messages"], "all": None},
        )
        out = tmp_path / "output"
        result = export_lean(out, tier="custom")
        assert result["exported"] == 1
        assert (out / "commit-messages" / "SKILL.md").exists()
        assert not (out / "bug-review").exists()

    @pytest.mark.unit
    def test_index_only_creates_single_file(self, mock_plugins: Path, tmp_path: Path):
        """
        Given index_only=True
        When exported
        Then a single index file is created instead of directories
        """
        out = tmp_path / "output"
        result = export_lean(out, index_only=True)
        assert result["exported"] == 2
        index = out / "night-market-skills-index.md"
        assert index.exists()
        content = index.read_text()
        assert "commit-messages" in content
        assert "bug-review" in content

    @pytest.mark.unit
    def test_trim_removes_see_also(self, mock_plugins: Path, tmp_path: Path):
        """
        Given trim=True (default)
        When exported
        Then See Also sections are stripped from output
        """
        out = tmp_path / "output"
        export_lean(out, trim=True)
        content = (out / "commit-messages" / "SKILL.md").read_text()
        assert "See Also" not in content
        assert "Content." in content
