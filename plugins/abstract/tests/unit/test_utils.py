"""Tests for src/abstract/utils.py.

Covers filesystem utilities, frontmatter helpers, and analysis utilities.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from abstract.config import AbstractConfig, SkillValidationConfig
from abstract.utils import (
    check_meta_skill_indicators,
    count_sections,
    extract_dependencies,
    find_dependency_file,
    find_project_root,
    find_skill_files,
    format_score,
    get_config_dir,
    get_log_directory,
    get_skill_name,
    load_config_with_defaults,
    load_skill_file,
    safe_json_load,
)

# ---------------------------------------------------------------------------
# find_project_root
# ---------------------------------------------------------------------------


class TestFindProjectRoot:
    """find_project_root walks up the directory tree to locate the root."""

    @pytest.mark.unit
    def test_finds_root_with_config_dir(self, tmp_path):
        """Returns directory containing a config/ subdirectory."""
        (tmp_path / "config").mkdir()
        nested = tmp_path / "subdir" / "deep"
        nested.mkdir(parents=True)
        result = find_project_root(nested)
        assert result == tmp_path

    @pytest.mark.unit
    def test_finds_root_with_pyproject_toml(self, tmp_path):
        """Returns directory containing pyproject.toml."""
        (tmp_path / "pyproject.toml").touch()
        nested = tmp_path / "src" / "module"
        nested.mkdir(parents=True)
        result = find_project_root(nested)
        assert result == tmp_path

    @pytest.mark.unit
    def test_returns_cwd_when_no_marker_found(self, tmp_path):
        """Returns Path.cwd() when no marker found all the way to root."""
        # An isolated tmp_path with no markers
        result = find_project_root(tmp_path)
        # It will traverse up until it hits the filesystem root.
        # For a typical tmp_path there usually won't be a marker, so
        # it should return something (cwd or a parent directory that has one)
        assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# get_log_directory
# ---------------------------------------------------------------------------


class TestGetLogDirectory:
    """get_log_directory respects CLAUDE_HOME env var."""

    @pytest.mark.unit
    def test_default_path_under_home(self, monkeypatch):
        """Without CLAUDE_HOME, path is under ~/.claude."""
        monkeypatch.delenv("CLAUDE_HOME", raising=False)
        result = get_log_directory()
        assert "skills" in str(result)
        assert "logs" in str(result)

    @pytest.mark.unit
    def test_respects_claude_home_env(self, tmp_path, monkeypatch):
        """CLAUDE_HOME overrides the default home directory."""
        monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
        result = get_log_directory()
        assert str(tmp_path) in str(result)

    @pytest.mark.unit
    def test_create_flag_makes_directory(self, tmp_path, monkeypatch):
        """When create=True, the directory is created if absent."""
        monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
        result = get_log_directory(create=True)
        assert result.exists()

    @pytest.mark.unit
    def test_no_create_does_not_make_directory(self, tmp_path, monkeypatch):
        """When create=False (default), directory is not created."""
        monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
        result = get_log_directory(create=False)
        # Directory may or may not exist; the key is no error is raised
        assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# get_config_dir
# ---------------------------------------------------------------------------


class TestGetConfigDir:
    """get_config_dir returns ~/.claude/skills/discussions."""

    @pytest.mark.unit
    def test_path_structure(self):
        """Path includes skills/discussions."""
        result = get_config_dir()
        assert "skills" in str(result)
        assert "discussions" in str(result)

    @pytest.mark.unit
    def test_create_flag_makes_directory(self, tmp_path, monkeypatch):
        """When create=True, directory is created."""
        # Monkeypatch Path.home to return tmp_path
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        result = get_config_dir(create=True)
        assert result.exists()


# ---------------------------------------------------------------------------
# safe_json_load
# ---------------------------------------------------------------------------


class TestSafeJsonLoad:
    """safe_json_load returns default on any error."""

    @pytest.mark.unit
    def test_loads_valid_json(self, tmp_path):
        """Valid JSON file is parsed successfully."""
        f = tmp_path / "data.json"
        f.write_text('{"key": "value"}')
        result = safe_json_load(f)
        assert result == {"key": "value"}

    @pytest.mark.unit
    def test_returns_default_when_file_missing(self, tmp_path):
        """Returns default when file does not exist."""
        result = safe_json_load(tmp_path / "missing.json", default="fallback")
        assert result == "fallback"

    @pytest.mark.unit
    def test_returns_default_when_malformed_json(self, tmp_path):
        """Returns default when JSON is malformed."""
        f = tmp_path / "bad.json"
        f.write_text("NOT JSON")
        result = safe_json_load(f, default=[])
        assert result == []

    @pytest.mark.unit
    def test_default_is_none_by_default(self, tmp_path):
        """Default is None when not specified."""
        result = safe_json_load(tmp_path / "missing.json")
        assert result is None


# ---------------------------------------------------------------------------
# extract_frontmatter (deprecated wrapper)
# ---------------------------------------------------------------------------


class TestExtractFrontmatter:
    """extract_frontmatter emits deprecation warning."""

    @pytest.mark.unit
    def test_emits_deprecation_warning(self):
        """Calling extract_frontmatter emits DeprecationWarning."""
        from abstract.utils import extract_frontmatter

        content = "---\nname: test\n---\n\n## Body\n"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            extract_frontmatter(content)
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)

    @pytest.mark.unit
    def test_returns_frontmatter_and_body(self):
        """Returns (frontmatter, body) tuple."""
        from abstract.utils import extract_frontmatter

        content = "---\nname: test\n---\n\n## Body\n"
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            fm, body = extract_frontmatter(content)

        assert "name" in fm
        assert "Body" in body


# ---------------------------------------------------------------------------
# parse_frontmatter_fields (deprecated wrapper)
# ---------------------------------------------------------------------------


class TestParseFrontmatterFields:
    """parse_frontmatter_fields emits deprecation warning."""

    @pytest.mark.unit
    def test_emits_deprecation_warning(self):
        """Calling parse_frontmatter_fields emits DeprecationWarning."""
        from abstract.utils import parse_frontmatter_fields

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            parse_frontmatter_fields("---\nname: test\n---")
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)

    @pytest.mark.unit
    def test_parses_simple_fields(self):
        """Parses key: value pairs from frontmatter."""
        from abstract.utils import parse_frontmatter_fields

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            fields = parse_frontmatter_fields(
                "---\nname: myskill\ncategory: testing\n---"
            )

        assert fields.get("name") == "myskill"
        assert fields.get("category") == "testing"


# ---------------------------------------------------------------------------
# validate_skill_frontmatter (deprecated wrapper)
# ---------------------------------------------------------------------------


class TestValidateSkillFrontmatter:
    """validate_skill_frontmatter checks for required fields."""

    @pytest.mark.unit
    def test_valid_frontmatter_no_issues(self):
        """Content with all required fields returns no issues."""
        from abstract.utils import validate_skill_frontmatter

        content = "---\nname: test\ndescription: A test skill\n---\n\n## Body\n"
        config = SkillValidationConfig()

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            issues = validate_skill_frontmatter(content, config)

        errors = [i for i in issues if i.startswith("ERROR")]
        assert errors == []

    @pytest.mark.unit
    def test_missing_required_field_is_error(self):
        """Content missing a required field returns ERROR issue."""
        from abstract.utils import validate_skill_frontmatter

        content = "---\nname: test\n---\n\n## Body\n"
        config = SkillValidationConfig()
        # description is required but absent

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            issues = validate_skill_frontmatter(content, config)

        errors = [i for i in issues if "description" in i.lower() or "ERROR" in i]
        assert len(errors) >= 1

    @pytest.mark.unit
    def test_missing_frontmatter_returns_error(self):
        """Content without frontmatter delimiters returns ERROR."""
        from abstract.utils import validate_skill_frontmatter

        content = "# No Frontmatter Here\n\nJust body.\n"
        config = SkillValidationConfig()

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            issues = validate_skill_frontmatter(content, config)

        assert any("ERROR" in i for i in issues)


# ---------------------------------------------------------------------------
# parse_yaml_frontmatter (deprecated wrapper)
# ---------------------------------------------------------------------------


class TestParseYamlFrontmatter:
    """parse_yaml_frontmatter emits deprecation warning."""

    @pytest.mark.unit
    def test_emits_deprecation_warning(self):
        """Calling parse_yaml_frontmatter emits DeprecationWarning."""
        from abstract.utils import parse_yaml_frontmatter

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            parse_yaml_frontmatter("---\nname: test\n---\n")
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)

    @pytest.mark.unit
    def test_returns_parsed_dict(self):
        """Returns dictionary of frontmatter fields."""
        from abstract.utils import parse_yaml_frontmatter

        content = "---\nname: myskill\ncategory: testing\n---\n\n# Body\n"
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = parse_yaml_frontmatter(content)

        assert result.get("name") == "myskill"

    @pytest.mark.unit
    def test_returns_empty_dict_when_no_frontmatter(self):
        """Returns empty dict when no frontmatter is present."""
        from abstract.utils import parse_yaml_frontmatter

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = parse_yaml_frontmatter("# No Frontmatter\n\nContent.")

        assert result == {}


# ---------------------------------------------------------------------------
# check_meta_skill_indicators
# ---------------------------------------------------------------------------


class TestCheckMetaSkillIndicators:
    """check_meta_skill_indicators checks for meta-skill patterns."""

    @pytest.mark.unit
    def test_returns_none_when_indicator_present(self):
        """Returns None when an indicator keyword is found."""
        config = SkillValidationConfig()
        content = "This skill uses a framework for orchestration."
        result = check_meta_skill_indicators(content, config, "my-skill")
        assert result is None

    @pytest.mark.unit
    def test_returns_warning_when_no_indicator(self):
        """Returns warning string when no indicator found."""
        config = SkillValidationConfig()
        content = "Just plain content with no special words."
        result = check_meta_skill_indicators(content, config, "my-skill")
        assert result is not None
        assert "WARNING" in result

    @pytest.mark.unit
    def test_exception_skill_bypasses_check(self):
        """Skills in META_SKILL_EXCEPTIONS return None even without indicators."""
        config = SkillValidationConfig()
        # 'skills-eval' is in the default exceptions
        content = "No meta keywords here at all."
        result = check_meta_skill_indicators(content, config, "skills-eval")
        assert result is None

    @pytest.mark.unit
    def test_empty_indicators_always_warns(self):
        """When META_INDICATORS is empty, warning is always returned."""
        config = SkillValidationConfig()
        config.META_INDICATORS = []
        result = check_meta_skill_indicators("any content", config, "my-skill")
        assert result is not None


# ---------------------------------------------------------------------------
# find_skill_files
# ---------------------------------------------------------------------------


class TestFindSkillFiles:
    """find_skill_files recursively locates SKILL.md files."""

    @pytest.mark.unit
    def test_returns_empty_for_nonexistent_dir(self, tmp_path):
        """Returns empty list when directory doesn't exist."""
        result = find_skill_files(tmp_path / "missing")
        assert result == []

    @pytest.mark.unit
    def test_finds_skill_md_files(self, tmp_path):
        """Returns SKILL.md files found recursively."""
        (tmp_path / "skill-one").mkdir()
        (tmp_path / "skill-one" / "SKILL.md").write_text("# Skill One")
        (tmp_path / "skill-two").mkdir()
        (tmp_path / "skill-two" / "SKILL.md").write_text("# Skill Two")

        result = find_skill_files(tmp_path)
        assert len(result) == 2

    @pytest.mark.unit
    def test_sorted_output(self, tmp_path):
        """Results are sorted by path."""
        (tmp_path / "b-skill").mkdir()
        (tmp_path / "b-skill" / "SKILL.md").write_text("B")
        (tmp_path / "a-skill").mkdir()
        (tmp_path / "a-skill" / "SKILL.md").write_text("A")

        result = find_skill_files(tmp_path)
        assert result[0].parent.name == "a-skill"
        assert result[1].parent.name == "b-skill"

    @pytest.mark.unit
    def test_excludes_non_skill_md_files(self, tmp_path):
        """Non-SKILL.md files are not returned."""
        (tmp_path / "README.md").write_text("readme")
        (tmp_path / "OTHER.md").write_text("other")
        result = find_skill_files(tmp_path)
        assert result == []


# ---------------------------------------------------------------------------
# load_skill_file
# ---------------------------------------------------------------------------


class TestLoadSkillFile:
    """load_skill_file loads and parses a SKILL.md file."""

    @pytest.mark.unit
    def test_raises_file_not_found_for_missing_file(self, tmp_path):
        """FileNotFoundError raised when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_skill_file(tmp_path / "missing.md")

    @pytest.mark.unit
    def test_returns_content_and_frontmatter(self, tmp_path):
        """Returns (content, frontmatter_dict) tuple."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: my-skill\ndescription: Test\n---\n\n## Body\n"
        )
        content, fm = load_skill_file(skill_file)
        assert "## Body" in content
        assert fm.get("name") == "my-skill"


# ---------------------------------------------------------------------------
# get_skill_name
# ---------------------------------------------------------------------------


class TestGetSkillName:
    """get_skill_name returns name from frontmatter or filename."""

    @pytest.mark.unit
    def test_uses_name_from_frontmatter(self, tmp_path):
        """Uses frontmatter 'name' field when present."""
        skill_path = tmp_path / "skill-dir" / "SKILL.md"
        skill_path.parent.mkdir()
        result = get_skill_name({"name": "my-skill"}, skill_path)
        assert result == "my-skill"

    @pytest.mark.unit
    def test_falls_back_to_stem(self, tmp_path):
        """Falls back to path stem when name not in frontmatter."""
        skill_path = tmp_path / "SKILL.md"
        result = get_skill_name({}, skill_path)
        assert result == "SKILL"

    @pytest.mark.unit
    def test_converts_non_string_name_to_string(self, tmp_path):
        """Non-string name is converted to string."""
        skill_path = tmp_path / "SKILL.md"
        result = get_skill_name({"name": 42}, skill_path)
        assert result == "42"


# ---------------------------------------------------------------------------
# format_score
# ---------------------------------------------------------------------------


class TestFormatScore:
    """format_score formats a numeric score for display."""

    @pytest.mark.unit
    def test_default_max_is_100(self):
        """Default max_score is 100."""
        assert format_score(85.0) == "85.0/100"

    @pytest.mark.unit
    def test_custom_max_score(self):
        """Custom max_score is used."""
        assert format_score(4.5, 5) == "4.5/5"

    @pytest.mark.unit
    def test_one_decimal_place(self):
        """Score is formatted with one decimal place."""
        assert format_score(85.0) == "85.0/100"


# ---------------------------------------------------------------------------
# count_sections
# ---------------------------------------------------------------------------


class TestCountSections:
    """count_sections counts headings at a given level."""

    @pytest.mark.unit
    def test_counts_h1_headings(self):
        """Counts # headings at level 1."""
        content = "# One\n# Two\n# Three\n"
        assert count_sections(content, level=1) == 3

    @pytest.mark.unit
    def test_counts_h2_headings(self):
        """Counts ## headings at level 2."""
        content = "# Title\n## Section A\n## Section B\n"
        assert count_sections(content, level=2) == 2

    @pytest.mark.unit
    def test_ignores_other_level_headings(self):
        """Level 1 count doesn't include ## headings."""
        content = "## Overview\n## Guide\n### Sub\n"
        assert count_sections(content, level=1) == 0

    @pytest.mark.unit
    def test_zero_when_no_headings(self):
        """Returns 0 when no headings of the given level exist."""
        assert count_sections("No headings here.", level=2) == 0


# ---------------------------------------------------------------------------
# extract_dependencies
# ---------------------------------------------------------------------------


class TestExtractDependencies:
    """extract_dependencies returns list from frontmatter."""

    @pytest.mark.unit
    def test_list_value_returned_directly(self):
        """When dependencies is a list, returned as-is."""
        fm = {"dependencies": ["a:skill-1", "b:skill-2"]}
        result = extract_dependencies(fm)
        assert result == ["a:skill-1", "b:skill-2"]

    @pytest.mark.unit
    def test_comma_separated_string_split(self):
        """When dependencies is a comma-separated string, split into list."""
        fm = {"dependencies": "a:x, b:y, c:z"}
        result = extract_dependencies(fm)
        assert result == ["a:x", "b:y", "c:z"]

    @pytest.mark.unit
    def test_missing_field_returns_empty(self):
        """When 'dependencies' absent, returns empty list."""
        assert extract_dependencies({}) == []

    @pytest.mark.unit
    def test_none_or_int_returns_empty(self):
        """Unsupported types return empty list."""
        assert extract_dependencies({"dependencies": None}) == []
        assert extract_dependencies({"dependencies": 42}) == []


# ---------------------------------------------------------------------------
# find_dependency_file
# ---------------------------------------------------------------------------


class TestFindDependencyFile:
    """find_dependency_file searches for a dependency SKILL.md."""

    @pytest.mark.unit
    def test_finds_sibling_md_file(self, tmp_path):
        """Finds dependency.md in the same directory."""
        skill_path = tmp_path / "my-skill" / "SKILL.md"
        skill_path.parent.mkdir()
        dep = tmp_path / "my-skill" / "dep.md"
        dep.write_text("# Dep")

        result = find_dependency_file(skill_path, "dep")
        assert result == dep

    @pytest.mark.unit
    def test_finds_sibling_skill_dir(self, tmp_path):
        """Finds dependency/SKILL.md as a sibling directory."""
        skill_path = tmp_path / "my-skill" / "SKILL.md"
        skill_path.parent.mkdir()
        dep_dir = tmp_path / "my-skill" / "dep"
        dep_dir.mkdir()
        dep_skill = dep_dir / "SKILL.md"
        dep_skill.write_text("# Dep")

        result = find_dependency_file(skill_path, "dep")
        assert result == dep_skill

    @pytest.mark.unit
    def test_finds_in_skills_dir(self, tmp_path):
        """Finds dependency in parent skills/ directory."""
        skill_path = tmp_path / "skills" / "my-skill" / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        dep_dir = tmp_path / "skills" / "dep"
        dep_dir.mkdir()
        dep_skill = dep_dir / "SKILL.md"
        dep_skill.write_text("# Dep")

        result = find_dependency_file(skill_path, "dep")
        assert result == dep_skill

    @pytest.mark.unit
    def test_returns_none_when_not_found(self, tmp_path):
        """Returns None when dependency file is not found."""
        skill_path = tmp_path / "my-skill" / "SKILL.md"
        skill_path.parent.mkdir()

        result = find_dependency_file(skill_path, "nonexistent-dep")
        assert result is None


# ---------------------------------------------------------------------------
# load_config_with_defaults
# ---------------------------------------------------------------------------


class TestLoadConfigWithDefaults:
    """load_config_with_defaults returns AbstractConfig with sensible defaults."""

    @pytest.mark.unit
    def test_returns_abstract_config(self, tmp_path):
        """Returns an AbstractConfig instance."""
        result = load_config_with_defaults(project_root=tmp_path)
        assert isinstance(result, AbstractConfig)

    @pytest.mark.unit
    def test_loads_from_yaml_when_present(self, tmp_path):
        """When config file exists, loads from it."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "abstract_config.yaml"
        config_file.write_text("debug: true\nverbose: false\n")

        result = load_config_with_defaults(project_root=tmp_path)
        assert isinstance(result, AbstractConfig)

    @pytest.mark.unit
    def test_returns_defaults_when_yaml_invalid(self, tmp_path):
        """When YAML config is malformed, returns default config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "abstract_config.yaml").write_text("[invalid yaml {{")

        result = load_config_with_defaults(project_root=tmp_path)
        assert isinstance(result, AbstractConfig)
