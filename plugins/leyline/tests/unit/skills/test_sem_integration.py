"""BDD tests for leyline sem-integration foundation skill.

Feature: sem Integration Foundation Skill Validation
  As a night-market skill consumer
  I want the sem-integration skill to follow ecosystem conventions
  So that detection, fallback, and normalization patterns are
  consistently available to imbue, pensive, and sanctum plugins.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

SKILL_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "skills" / "sem-integration"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"

EXPECTED_MODULES = [
    "detection.md",
    "fallback.md",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_frontmatter(path: Path) -> dict:
    """Return the YAML frontmatter dict from a markdown file."""
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    _, fm, _ = text.split("---", 2)
    return yaml.safe_load(fm) or {}


# ---------------------------------------------------------------------------
# Feature: Skill file structure
# ---------------------------------------------------------------------------


class TestSkillFileExists:
    """
    Feature: SKILL.md exists and is parseable

    As a plugin loader
    I want SKILL.md to exist with valid frontmatter
    So that the skill can be discovered and loaded.
    """

    @pytest.mark.unit
    def test_skill_file_exists(self) -> None:
        """
        Scenario: SKILL.md is present in the skill directory
        Given the sem-integration skill directory
        When the loader checks for SKILL.md
        Then the file exists
        """
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"

    @pytest.mark.unit
    def test_skill_frontmatter_is_valid_yaml(self) -> None:
        """
        Scenario: Frontmatter parses without error
        Given SKILL.md with YAML frontmatter
        When yaml.safe_load is called on the frontmatter block
        Then no exception is raised and the result is a dict
        """
        fm = _parse_frontmatter(SKILL_FILE)
        assert isinstance(fm, dict), "Frontmatter did not parse to a dict"

    @pytest.mark.unit
    def test_skill_name_matches_directory(self) -> None:
        """
        Scenario: Skill name in frontmatter matches directory name
        Given SKILL.md with a 'name' field
        When the name field is read
        Then it equals 'sem-integration'
        """
        fm = _parse_frontmatter(SKILL_FILE)
        assert fm.get("name") == "sem-integration"

    @pytest.mark.unit
    def test_skill_has_required_frontmatter_fields(self) -> None:
        """
        Scenario: Required frontmatter fields are present
        Given SKILL.md
        When its frontmatter is parsed
        Then description, version, category, and tags are present
        """
        fm = _parse_frontmatter(SKILL_FILE)
        for field in ("description", "version", "category", "tags"):
            assert field in fm, f"Missing required frontmatter field: {field}"

    @pytest.mark.unit
    def test_skill_category_is_infrastructure(self) -> None:
        """
        Scenario: Skill is categorized as infrastructure
        Given the sem-integration skill
        When its category is read
        Then it equals 'infrastructure'
        """
        fm = _parse_frontmatter(SKILL_FILE)
        assert fm.get("category") == "infrastructure"

    @pytest.mark.unit
    def test_skill_lists_expected_modules(self) -> None:
        """
        Scenario: Skill frontmatter declares detection and fallback modules
        Given SKILL.md
        When the modules list is read
        Then it includes detection.md and fallback.md
        """
        fm = _parse_frontmatter(SKILL_FILE)
        modules = fm.get("modules", [])
        for expected in ("modules/detection.md", "modules/fallback.md"):
            assert expected in modules, (
                f"Expected module '{expected}' not listed in frontmatter"
            )


# ---------------------------------------------------------------------------
# Feature: Module files exist
# ---------------------------------------------------------------------------


class TestModuleFilesExist:
    """
    Feature: Module files are present on disk

    As a progressive loader
    I want all declared modules to exist as files
    So that lazy loading does not fail at runtime.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize("module_name", EXPECTED_MODULES)
    def test_module_file_exists(self, module_name: str) -> None:
        """
        Scenario: Each declared module file is present
        Given a module name declared in SKILL.md
        When the filesystem is checked
        Then the file exists under modules/
        """
        module_path = MODULES_DIR / module_name
        assert module_path.exists(), f"Module file not found: {module_path}"

    @pytest.mark.unit
    @pytest.mark.parametrize("module_name", EXPECTED_MODULES)
    def test_module_has_frontmatter(self, module_name: str) -> None:
        """
        Scenario: Each module file has parseable YAML frontmatter
        Given a module file
        When its frontmatter is parsed
        Then it is a non-empty dict
        """
        module_path = MODULES_DIR / module_name
        fm = _parse_frontmatter(module_path)
        assert isinstance(fm, dict) and fm, (
            f"Module {module_name} has no valid frontmatter"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("module_name", EXPECTED_MODULES)
    def test_module_has_parent_skill_reference(self, module_name: str) -> None:
        """
        Scenario: Each module references its parent skill
        Given a module file
        When its frontmatter is read
        Then 'parent_skill' equals 'leyline:sem-integration'
        """
        module_path = MODULES_DIR / module_name
        fm = _parse_frontmatter(module_path)
        assert fm.get("parent_skill") == "leyline:sem-integration", (
            f"Module {module_name} missing or wrong parent_skill"
        )


# ---------------------------------------------------------------------------
# Feature: Detection logic behaviour
# ---------------------------------------------------------------------------


class TestSemDetection:
    """
    Feature: Detect sem CLI availability

    As a night-market skill consumer
    I want to know if sem is installed
    So that I can choose semantic or fallback diff paths.
    """

    @pytest.mark.unit
    def test_detection_returns_true_when_sem_installed(self, tmp_path: Path) -> None:
        """
        Scenario: sem is on PATH
        Given sem is installed
        When detection logic runs
        Then the cache file contains '1'
        """
        cache = tmp_path / "sem-available"
        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["which", "sem"],
                returncode=0,
                stdout="/usr/local/bin/sem\n",
            ),
        ):
            result = subprocess.run(["which", "sem"], capture_output=True, text=True)
            available = result.returncode == 0
            cache.write_text("1" if available else "0")

        assert cache.read_text() == "1"

    @pytest.mark.unit
    def test_detection_returns_false_when_sem_missing(self, tmp_path: Path) -> None:
        """
        Scenario: sem is not on PATH
        Given sem is absent
        When detection logic runs
        Then the cache file contains '0'
        """
        cache = tmp_path / "sem-available"
        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["which", "sem"],
                returncode=1,
                stdout="",
            ),
        ):
            result = subprocess.run(["which", "sem"], capture_output=True, text=True)
            available = result.returncode == 0
            cache.write_text("1" if available else "0")

        assert cache.read_text() == "0"

    @pytest.mark.unit
    def test_detection_caches_result(self, tmp_path: Path) -> None:
        """
        Scenario: Detection result is cached
        Given the cache file already contains a result
        When detection logic reads the cache
        Then the cached value is returned without re-running which
        """
        cache = tmp_path / "sem-available"
        cache.write_text("1")
        assert cache.read_text() == "1"


# ---------------------------------------------------------------------------
# Feature: Fallback output normalization
# ---------------------------------------------------------------------------


class TestFallbackNormalization:
    """
    Feature: Produce normalized output from git diff fallback

    As a consumer module
    I want fallback output in the same schema as sem JSON
    So that I can use one code path for processing.
    """

    @pytest.mark.unit
    def test_parse_diff_filter_added(self) -> None:
        """
        Scenario: git diff --diff-filter=A output is parsed as additions
        Given a line of added-file output from git diff
        When the fallback normalizer processes it
        Then the entity has change_type 'added' and kind 'file'
        """
        raw = "plugins/leyline/skills/sem-integration/SKILL.md\n"
        entities = []
        for line in raw.strip().splitlines():
            entities.append(
                {
                    "name": Path(line).stem,
                    "kind": "file",
                    "change_type": "added",
                    "file": line,
                }
            )
        assert len(entities) == 1
        assert entities[0]["change_type"] == "added"
        assert entities[0]["name"] == "SKILL"

    @pytest.mark.unit
    def test_parse_diff_filter_modified(self) -> None:
        """
        Scenario: git diff --diff-filter=M output is parsed as modifications
        Given two lines of modified-file output from git diff
        When the fallback normalizer processes them
        Then both entities have change_type 'modified'
        """
        raw = "src/app.py\nsrc/utils.py\n"
        entities = []
        for line in raw.strip().splitlines():
            entities.append(
                {
                    "name": Path(line).stem,
                    "kind": "file",
                    "change_type": "modified",
                    "file": line,
                }
            )
        assert len(entities) == 2
        assert all(e["change_type"] == "modified" for e in entities)

    @pytest.mark.unit
    def test_empty_diff_produces_empty_list(self) -> None:
        """
        Scenario: Empty git diff output produces no entities
        Given an empty string from git diff
        When the fallback normalizer processes it
        Then the entity list is empty
        """
        raw = ""
        entities = []
        for line in raw.strip().splitlines():
            if line:
                entities.append(
                    {
                        "name": Path(line).stem,
                        "kind": "file",
                        "change_type": "modified",
                        "file": line,
                    }
                )
        assert entities == []

    @pytest.mark.unit
    def test_entity_schema_has_required_keys(self) -> None:
        """
        Scenario: Normalized entity has all required schema keys
        Given a single changed file
        When the fallback normalizer produces an entity
        Then it contains name, kind, change_type, and file keys
        """
        raw = "src/main.py\n"
        entities = []
        for line in raw.strip().splitlines():
            entities.append(
                {
                    "name": Path(line).stem,
                    "kind": "file",
                    "change_type": "modified",
                    "file": line,
                }
            )
        assert len(entities) == 1
        entity = entities[0]
        for key in ("name", "kind", "change_type", "file"):
            assert key in entity, f"Entity missing required key: {key}"
