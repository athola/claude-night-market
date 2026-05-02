"""Extended tests for abstract.utils module.

Targets uncovered paths in utils.py to raise coverage toward 85%.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from abstract.config import AbstractConfig, SkillValidationConfig
from abstract.utils import (
    check_meta_skill_indicators,
    count_sections,
    extract_dependencies,
    extract_frontmatter,
    extract_section,
    find_dependency_file,
    find_project_root,
    find_skill_files,
    format_score,
    get_config_dir,
    get_log_directory,
    get_skill_name,
    load_config_with_defaults,
    load_skill_file,
    parse_frontmatter_fields,
    parse_yaml_frontmatter,
    safe_json_load,
    validate_skill_frontmatter,
)

# ---------------------------------------------------------------------------
# find_project_root
# ---------------------------------------------------------------------------


class TestFindProjectRoot:
    """find_project_root walks up to locate a project marker."""

    @pytest.mark.unit
    def test_finds_directory_with_config(self, tmp_path):
        """Given a 'config' subdirectory, returns that directory."""
        (tmp_path / "config").mkdir()
        sub = tmp_path / "src" / "module"
        sub.mkdir(parents=True)
        result = find_project_root(sub)
        assert result == tmp_path

    @pytest.mark.unit
    def test_finds_directory_with_pyproject_toml(self, tmp_path):
        """Given a pyproject.toml, returns that directory."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        sub = tmp_path / "src"
        sub.mkdir()
        result = find_project_root(sub)
        assert result == tmp_path

    @pytest.mark.unit
    def test_returns_cwd_when_no_marker_found(self, tmp_path):
        """Given no project marker anywhere, returns Path.cwd()."""
        # Use a path with no markers all the way to root
        isolated = tmp_path / "a" / "b" / "c"
        isolated.mkdir(parents=True)
        result = find_project_root(isolated)
        # Should return cwd since no marker found
        assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# get_log_directory
# ---------------------------------------------------------------------------


class TestGetLogDirectory:
    """get_log_directory returns the skill log path."""

    @pytest.mark.unit
    def test_default_path_ends_with_skills_logs(self):
        """Given no CLAUDE_HOME env var, returns ~/.claude/skills/logs."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAUDE_HOME", None)
            result = get_log_directory()
        assert result.parts[-1] == "logs"
        assert "skills" in result.parts

    @pytest.mark.unit
    def test_respects_claude_home_env(self, tmp_path):
        """Given CLAUDE_HOME set, uses that directory."""
        with patch.dict(os.environ, {"CLAUDE_HOME": str(tmp_path)}):
            result = get_log_directory()
        assert str(tmp_path) in str(result)

    @pytest.mark.unit
    def test_create_true_creates_directory(self, tmp_path):
        """Given create=True, the directory is created."""
        with patch.dict(os.environ, {"CLAUDE_HOME": str(tmp_path)}):
            result = get_log_directory(create=True)
        assert result.exists()


# ---------------------------------------------------------------------------
# get_config_dir
# ---------------------------------------------------------------------------


class TestGetConfigDir:
    """get_config_dir returns the discussions config directory."""

    @pytest.mark.unit
    def test_returns_path_with_discussions(self):
        """Given default settings, path includes 'discussions'."""
        result = get_config_dir()
        assert "discussions" in str(result)

    @pytest.mark.unit
    def test_create_true_creates_directory(self, tmp_path, monkeypatch):
        """Given create=True, the directory is created under tmp_path home."""
        monkeypatch.setenv("HOME", str(tmp_path))
        # Override Path.home() by monkeypatching
        with patch("abstract.utils.Path.home", return_value=tmp_path):
            result = get_config_dir(create=True)
        assert result.exists()


# ---------------------------------------------------------------------------
# load_config_with_defaults
# ---------------------------------------------------------------------------


class TestLoadConfigWithDefaults:
    """load_config_with_defaults returns an AbstractConfig."""

    @pytest.mark.unit
    def test_returns_abstract_config_when_no_file(self, tmp_path):
        """Given no config file, returns default AbstractConfig."""
        result = load_config_with_defaults(project_root=tmp_path)
        assert isinstance(result, AbstractConfig)

    @pytest.mark.unit
    def test_uses_auto_detection_when_no_project_root(self):
        """Given project_root=None, auto-detection is used."""
        result = load_config_with_defaults(project_root=None)
        assert isinstance(result, AbstractConfig)


# ---------------------------------------------------------------------------
# extract_frontmatter
# ---------------------------------------------------------------------------


class TestExtractFrontmatter:
    """extract_frontmatter separates YAML header from body."""

    @pytest.mark.unit
    def test_extracts_frontmatter_and_body(self):
        """Given content with frontmatter, returns (frontmatter, body) tuple."""
        content = "---\nname: test\n---\n\nBody text."
        fm, body = extract_frontmatter(content)
        assert "name: test" in fm
        assert "Body text" in body

    @pytest.mark.unit
    def test_no_frontmatter_returns_empty_and_full_body(self):
        """Given content without frontmatter, frontmatter is empty."""
        content = "Just plain text."
        fm, body = extract_frontmatter(content)
        assert fm == ""
        assert "Just plain text" in body


# ---------------------------------------------------------------------------
# parse_frontmatter_fields
# ---------------------------------------------------------------------------


class TestParseFrontmatterFields:
    """parse_frontmatter_fields parses simple YAML key:value pairs."""

    @pytest.mark.unit
    def test_parses_key_value_pairs(self):
        """Given frontmatter with key:value lines, returns correct dict."""
        fm = "---\nname: my-skill\ncategory: testing\n---"
        result = parse_frontmatter_fields(fm)
        assert result["name"] == "my-skill"
        assert result["category"] == "testing"

    @pytest.mark.unit
    def test_skips_list_items(self):
        """Given list items starting with '-', they are not parsed as keys."""
        fm = "---\ntags:\n- alpha\n- beta\n---"
        result = parse_frontmatter_fields(fm)
        assert "alpha" not in result

    @pytest.mark.unit
    def test_empty_frontmatter_returns_empty_dict(self):
        """Given empty frontmatter, returns empty dict."""
        result = parse_frontmatter_fields("---\n---")
        assert result == {}

    @pytest.mark.unit
    def test_value_with_colon_preserved(self):
        """Given a value containing a colon, only first colon is used as separator."""
        fm = "---\nurl: http://example.com\n---"
        result = parse_frontmatter_fields(fm)
        assert result["url"] == "http://example.com"


# ---------------------------------------------------------------------------
# validate_skill_frontmatter
# ---------------------------------------------------------------------------


class TestValidateSkillFrontmatter:
    """validate_skill_frontmatter returns list of validation issues."""

    def _config(self):
        return SkillValidationConfig()

    @pytest.mark.unit
    def test_valid_content_returns_no_issues(self):
        """Given valid frontmatter with required fields, no issues returned."""
        content = "---\nname: test\ndescription: A test skill\ncategory: testing\n---\n\nBody."
        result = validate_skill_frontmatter(content, self._config())
        # May return info-level recommendations but no ERROR issues
        error_issues = [i for i in result if i.startswith("ERROR")]
        assert error_issues == []

    @pytest.mark.unit
    def test_missing_frontmatter_returns_error(self):
        """Given content without frontmatter, returns an ERROR issue."""
        result = validate_skill_frontmatter("Just plain text.", self._config())
        assert any("ERROR" in i for i in result)

    @pytest.mark.unit
    def test_returns_list(self):
        """Given any content, returns a list."""
        result = validate_skill_frontmatter("---\nname: test\n---\n", self._config())
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# check_meta_skill_indicators
# ---------------------------------------------------------------------------


class TestCheckMetaSkillIndicators:
    """check_meta_skill_indicators checks for meta-skill keywords."""

    def _config_with_indicators(self):
        cfg = SkillValidationConfig()
        cfg.META_INDICATORS = ["orchestrate", "workflow"]
        cfg.META_SKILL_EXCEPTIONS = ["excluded-skill"]
        return cfg

    @pytest.mark.unit
    def test_returns_none_when_indicator_found(self):
        """Given content containing a meta indicator word exactly, returns None."""
        cfg = self._config_with_indicators()
        # Use exact word "orchestrate" to match the \b word boundary regex
        result = check_meta_skill_indicators(
            "This will orchestrate tasks.", cfg, "my-skill"
        )
        assert result is None

    @pytest.mark.unit
    def test_returns_warning_when_no_indicator(self):
        """Given content without meta indicator, returns warning string."""
        cfg = self._config_with_indicators()
        result = check_meta_skill_indicators("Just a simple skill.", cfg, "my-skill")
        assert result is not None
        assert "WARNING" in result

    @pytest.mark.unit
    def test_exception_skill_returns_none(self):
        """Given skill name in exceptions, returns None regardless of content."""
        cfg = self._config_with_indicators()
        result = check_meta_skill_indicators(
            "No indicators here.", cfg, "excluded-skill"
        )
        assert result is None

    @pytest.mark.unit
    def test_empty_indicators_always_warns(self):
        """Given empty indicators list, non-excepted skill always gets warning."""
        cfg = SkillValidationConfig()
        cfg.META_INDICATORS = []
        cfg.META_SKILL_EXCEPTIONS = []
        result = check_meta_skill_indicators("Some content.", cfg, "my-skill")
        assert result is not None


# ---------------------------------------------------------------------------
# find_skill_files
# ---------------------------------------------------------------------------


class TestFindSkillFiles:
    """find_skill_files finds SKILL.md files recursively."""

    @pytest.mark.unit
    def test_returns_empty_for_nonexistent_directory(self, tmp_path):
        """Given a path that doesn't exist, returns empty list."""
        result = find_skill_files(tmp_path / "nonexistent")
        assert result == []

    @pytest.mark.unit
    def test_finds_skill_md_recursively(self, tmp_path):
        """Given nested SKILL.md files, all are found."""
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "SKILL.md").write_text("content")
        (tmp_path / "b").mkdir()
        (tmp_path / "b" / "SKILL.md").write_text("content")
        result = find_skill_files(tmp_path)
        assert len(result) == 2

    @pytest.mark.unit
    def test_ignores_non_skill_md_files(self, tmp_path):
        """Given other .md files, only SKILL.md is returned."""
        (tmp_path / "README.md").write_text("# readme")
        (tmp_path / "SKILL.md").write_text("# skill")
        result = find_skill_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "SKILL.md"

    @pytest.mark.unit
    def test_result_sorted(self, tmp_path):
        """Given multiple skills, result is sorted by path."""
        for name in ["z-skill", "a-skill"]:
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text("")
        result = find_skill_files(tmp_path)
        paths = [str(p) for p in result]
        assert paths == sorted(paths)


# ---------------------------------------------------------------------------
# parse_yaml_frontmatter
# ---------------------------------------------------------------------------


class TestParseYamlFrontmatter:
    """parse_yaml_frontmatter parses YAML frontmatter into a dict."""

    @pytest.mark.unit
    def test_parses_fields_correctly(self):
        """Given valid YAML frontmatter, returns correct dict."""
        content = "---\nname: test\ncategory: testing\n---\nBody."
        result = parse_yaml_frontmatter(content)
        assert result["name"] == "test"
        assert result["category"] == "testing"

    @pytest.mark.unit
    def test_no_frontmatter_returns_empty_dict(self):
        """Given content without frontmatter, returns empty dict."""
        result = parse_yaml_frontmatter("Just text.")
        assert result == {}


# ---------------------------------------------------------------------------
# load_skill_file
# ---------------------------------------------------------------------------


class TestLoadSkillFile:
    """load_skill_file reads and parses a skill file."""

    @pytest.mark.unit
    def test_loads_file_and_parses_frontmatter(self, tmp_path):
        """Given a valid skill file, returns (content, frontmatter) tuple."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: test\n---\nBody.")
        content, fm = load_skill_file(skill_file)
        assert "Body." in content
        assert fm.get("name") == "test"

    @pytest.mark.unit
    def test_raises_file_not_found(self, tmp_path):
        """Given a nonexistent path, raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_skill_file(tmp_path / "missing.md")


# ---------------------------------------------------------------------------
# get_skill_name
# ---------------------------------------------------------------------------


class TestGetSkillName:
    """get_skill_name extracts the skill name from frontmatter or path."""

    @pytest.mark.unit
    def test_returns_name_from_frontmatter(self, tmp_path):
        """Given frontmatter with 'name', returns that name."""
        skill_path = tmp_path / "SKILL.md"
        result = get_skill_name({"name": "my-skill"}, skill_path)
        assert result == "my-skill"

    @pytest.mark.unit
    def test_falls_back_to_stem_when_no_name(self, tmp_path):
        """Given frontmatter without 'name', returns file stem."""
        skill_path = tmp_path / "my-skill.md"
        result = get_skill_name({}, skill_path)
        assert result == "my-skill"


# ---------------------------------------------------------------------------
# format_score
# ---------------------------------------------------------------------------


class TestFormatScore:
    """format_score formats a score as 'value/max'."""

    @pytest.mark.unit
    def test_default_max_score(self):
        """Given score=85, returns '85.0/100'."""
        result = format_score(85.0)
        assert result == "85.0/100"

    @pytest.mark.unit
    def test_custom_max_score(self):
        """Given score=7 and max_score=10, returns '7.0/10'."""
        result = format_score(7.0, max_score=10)
        assert result == "7.0/10"

    @pytest.mark.unit
    def test_zero_score(self):
        """Given score=0, returns '0.0/100'."""
        assert format_score(0) == "0.0/100"


# ---------------------------------------------------------------------------
# count_sections
# ---------------------------------------------------------------------------


class TestCountSections:
    """count_sections counts heading levels in markdown."""

    @pytest.mark.unit
    def test_counts_h1_sections(self):
        """Given two H1 headings, returns 2."""
        content = "# One\n\ntext\n\n# Two\n\nmore"
        assert count_sections(content, level=1) == 2

    @pytest.mark.unit
    def test_counts_h2_sections(self):
        """Given three H2 headings, returns 3."""
        content = "## A\n\n## B\n\n## C\n"
        assert count_sections(content, level=2) == 3

    @pytest.mark.unit
    def test_no_headings_returns_zero(self):
        """Given no headings of the specified level, returns 0."""
        content = "Just plain text without any headings."
        assert count_sections(content, level=1) == 0

    @pytest.mark.unit
    def test_level_specific(self):
        """Given H2 headings only, count at H1 level returns 0."""
        content = "## Heading\n\nText\n"
        assert count_sections(content, level=1) == 0
        assert count_sections(content, level=2) == 1


# ---------------------------------------------------------------------------
# extract_dependencies
# ---------------------------------------------------------------------------


class TestExtractDependencies:
    """extract_dependencies parses the 'dependencies' frontmatter field."""

    @pytest.mark.unit
    def test_extracts_list_dependencies(self):
        """Given a list of deps, returns that list."""
        fm = {"dependencies": ["dep-a", "dep-b"]}
        result = extract_dependencies(fm)
        assert result == ["dep-a", "dep-b"]

    @pytest.mark.unit
    def test_extracts_string_dependencies(self):
        """Given comma-separated string, returns parsed list."""
        fm = {"dependencies": "dep-a, dep-b, dep-c"}
        result = extract_dependencies(fm)
        assert result == ["dep-a", "dep-b", "dep-c"]

    @pytest.mark.unit
    def test_missing_key_returns_empty(self):
        """Given no 'dependencies' key, returns empty list."""
        result = extract_dependencies({})
        assert result == []

    @pytest.mark.unit
    def test_unexpected_type_returns_empty(self):
        """Given unexpected type for dependencies, returns empty list."""
        result = extract_dependencies({"dependencies": 42})
        assert result == []


# ---------------------------------------------------------------------------
# find_dependency_file
# ---------------------------------------------------------------------------


class TestFindDependencyFile:
    """find_dependency_file locates a dependency SKILL.md."""

    @pytest.mark.unit
    def test_finds_sibling_md_file(self, tmp_path):
        """Given a sibling .md file matching the dep name, returns it."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("")
        dep_file = tmp_path / "my-dep.md"
        dep_file.write_text("")
        result = find_dependency_file(skill_file, "my-dep")
        assert result == dep_file

    @pytest.mark.unit
    def test_finds_nested_skill_md(self, tmp_path):
        """Given a nested my-dep/SKILL.md, returns it."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("")
        dep_dir = tmp_path / "my-dep"
        dep_dir.mkdir()
        dep_skill = dep_dir / "SKILL.md"
        dep_skill.write_text("")
        result = find_dependency_file(skill_file, "my-dep")
        assert result == dep_skill

    @pytest.mark.unit
    def test_returns_none_when_not_found(self, tmp_path):
        """Given no matching dependency file, returns None."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("")
        result = find_dependency_file(skill_file, "nonexistent-dep")
        assert result is None


# ---------------------------------------------------------------------------
# safe_json_load
# ---------------------------------------------------------------------------


class TestSafeJsonLoad:
    """safe_json_load loads JSON from a path with a fallback default."""

    @pytest.mark.unit
    def test_loads_valid_json_file(self, tmp_path):
        """Given a valid JSON file, returns parsed data."""
        p = tmp_path / "data.json"
        p.write_text('{"key": "value", "num": 42}')
        result = safe_json_load(p)
        assert result == {"key": "value", "num": 42}

    @pytest.mark.unit
    def test_returns_none_for_missing_file(self, tmp_path):
        """Given a path that does not exist, returns None by default."""
        result = safe_json_load(tmp_path / "missing.json")
        assert result is None

    @pytest.mark.unit
    def test_returns_custom_default_for_missing_file(self, tmp_path):
        """Given a missing file and a custom default, returns that default."""
        result = safe_json_load(tmp_path / "missing.json", default={})
        assert result == {}

    @pytest.mark.unit
    def test_returns_default_for_malformed_json(self, tmp_path):
        """Given a file with invalid JSON, returns default."""
        p = tmp_path / "bad.json"
        p.write_text("{ not valid json }")
        result = safe_json_load(p, default={"fallback": True})
        assert result == {"fallback": True}

    @pytest.mark.unit
    def test_loads_json_list(self, tmp_path):
        """Given a JSON file containing a list, returns that list."""
        p = tmp_path / "list.json"
        p.write_text("[1, 2, 3]")
        result = safe_json_load(p)
        assert result == [1, 2, 3]

    @pytest.mark.unit
    def test_returns_none_default_for_empty_file(self, tmp_path):
        """Given an empty file, returns default (empty file is invalid JSON)."""
        p = tmp_path / "empty.json"
        p.write_text("")
        result = safe_json_load(p)
        assert result is None


# ---------------------------------------------------------------------------
# extract_section (D-03)
# ---------------------------------------------------------------------------


class TestExtractSection:
    """extract_section pulls the body of a named markdown ## section.

    Feature: shared markdown-section extraction (D-03).

    The three abstract scripts (discussion_enrichment,
    auto_promote_learnings, post_learnings_to_discussions) used
    a byte-identical helper. Promoting it to abstract.utils gives
    one definition consumed by all three.
    """

    @pytest.mark.unit
    def test_extracts_body_of_named_section(self):
        """Given a doc with a matching '## High-Impact Issues' heading,
        When extract_section is called with that heading,
        Then it returns the body up to the next ## or --- boundary.
        """
        content = (
            "# Title\n\n## High-Impact Issues\n- Issue A\n- Issue B\n\n## Other\nRest"
        )
        result = extract_section(content, "## High-Impact Issues")
        assert result == "- Issue A\n- Issue B"

    @pytest.mark.unit
    def test_returns_none_when_heading_absent(self):
        """Given content without the heading,
        When extract_section is called,
        Then it returns None.
        """
        assert extract_section("# Doc\nNo headings here", "## Missing") is None

    @pytest.mark.unit
    def test_terminates_at_horizontal_rule(self):
        """Given a section terminated by --- rather than another heading,
        When extract_section is called,
        Then it stops at ---.
        """
        content = "## Slow Execution\n- skill A\n- skill B\n\n---\nfooter"
        result = extract_section(content, "## Slow Execution")
        assert result == "- skill A\n- skill B"

    @pytest.mark.unit
    def test_terminates_at_end_of_file(self):
        """Given the named section at the end of the document,
        When extract_section is called,
        Then it returns the remaining body without trailing whitespace.
        """
        content = "## Low User Ratings\n- entry\n"
        result = extract_section(content, "## Low User Ratings")
        assert result == "- entry"
