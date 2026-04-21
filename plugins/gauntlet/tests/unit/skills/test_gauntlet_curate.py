"""BDD tests for the gauntlet-curate skill.

These tests verify the *behavior* described in SKILL.md:
- The skill has valid frontmatter (name, description, version, model_hint)
- The skill workflow never writes to data/problems/
- The skill produces a report rather than mutating YAML files
- The skill is registered in openpackage.yml

The backing implementation lives in scripts/curate_problems.py, whose
unit tests are in tests/unit/test_curate_problems.py.  These tests focus
on the *skill contract* — what callers of the skill can rely on.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# Absolute paths so tests work regardless of cwd.
_PLUGIN_ROOT = Path(__file__).parents[3]  # plugins/gauntlet/
_SKILL_DIR = _PLUGIN_ROOT / "skills" / "gauntlet-curate"
_SKILL_FILE = _SKILL_DIR / "SKILL.md"
_MANIFEST = _PLUGIN_ROOT / "openpackage.yml"
_SCRIPT = _PLUGIN_ROOT / "scripts" / "curate_problems.py"

# Required frontmatter fields per issue #388 acceptance criteria.
_REQUIRED_FRONTMATTER = {"name", "description", "version"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_skill_frontmatter(skill_file: Path) -> dict:
    """Extract YAML frontmatter between the first two '---' delimiters."""
    text = skill_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = next(
        (i for i, ln in enumerate(lines[1:], start=1) if ln.strip() == "---"),
        None,
    )
    if end is None:
        return {}
    fm_text = "\n".join(lines[1:end])
    return yaml.safe_load(fm_text) or {}


def _load_openpackage() -> dict:
    return yaml.safe_load(_MANIFEST.read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------------------
# Feature: Skill file structure
# ---------------------------------------------------------------------------


class TestGauntletCurateSkillFile:
    """
    Feature: gauntlet-curate skill file exists with valid structure

    As a gauntlet plugin user
    I want the gauntlet-curate skill to have a valid SKILL.md
    So that Claude Code can discover and invoke it
    """

    @pytest.mark.unit
    def test_skill_file_exists(self):
        """
        Scenario: SKILL.md is present in skills/gauntlet-curate/
        Given the gauntlet plugin
        When the skills directory is inspected
        Then skills/gauntlet-curate/SKILL.md exists
        """
        assert _SKILL_FILE.exists(), (
            f"Expected skill file at {_SKILL_FILE} but it was not found."
        )

    @pytest.mark.unit
    def test_skill_frontmatter_has_required_fields(self):
        """
        Scenario: Frontmatter contains name, description, and version
        Given the SKILL.md file
        When frontmatter is parsed
        Then name, description, and version are all present and non-empty
        """
        fm = _parse_skill_frontmatter(_SKILL_FILE)
        missing = _REQUIRED_FRONTMATTER - set(fm.keys())
        assert not missing, f"Frontmatter missing fields: {missing}"
        for field in _REQUIRED_FRONTMATTER:
            assert fm[field], f"Frontmatter field '{field}' is empty."

    @pytest.mark.unit
    def test_skill_name_is_kebab_case(self):
        """
        Scenario: Skill name follows kebab-case convention
        Given the SKILL.md frontmatter
        When the name field is inspected
        Then it equals 'gauntlet-curate' (kebab-case)
        """
        fm = _parse_skill_frontmatter(_SKILL_FILE)
        assert fm.get("name") == "gauntlet-curate"

    @pytest.mark.unit
    def test_skill_version_matches_plugin(self):
        """
        Scenario: Skill version matches the plugin version in openpackage.yml
        Given the SKILL.md and openpackage.yml
        When their versions are compared
        Then they match
        """
        fm = _parse_skill_frontmatter(_SKILL_FILE)
        pkg = _load_openpackage()
        assert fm.get("version") == pkg.get("version"), (
            f"Skill version {fm.get('version')!r} != "
            f"plugin version {pkg.get('version')!r}"
        )

    @pytest.mark.unit
    def test_skill_description_mentions_problem_bank(self):
        """
        Scenario: Skill description is discoverable by /update-plugins routing
        Given the SKILL.md frontmatter description
        When it is inspected for key routing terms
        Then it mentions 'problem' and 'yaml' (case-insensitive)
        """
        fm = _parse_skill_frontmatter(_SKILL_FILE)
        desc = str(fm.get("description", "")).lower()
        assert "problem" in desc, "Description should mention 'problem'."
        assert "yaml" in desc, "Description should mention 'yaml'."

    @pytest.mark.unit
    def test_skill_body_contains_safety_constraint_section(self):
        """
        Scenario: SKILL.md documents the no-overwrite safety constraint
        Given the SKILL.md body text
        When it is scanned for safety language
        Then it explicitly states that data/problems/ files are never modified
        """
        body = _SKILL_FILE.read_text(encoding="utf-8").lower()
        assert "never" in body and "data/problems" in body, (
            "SKILL.md must explicitly state the no-write safety constraint."
        )

    @pytest.mark.unit
    def test_skill_body_references_curate_script(self):
        """
        Scenario: SKILL.md instructs callers to use curate_problems.py
        Given the SKILL.md body text
        When it is scanned for script references
        Then 'curate_problems.py' appears in the text
        """
        body = _SKILL_FILE.read_text(encoding="utf-8")
        assert "curate_problems.py" in body, (
            "SKILL.md must reference the curate_problems.py script."
        )


# ---------------------------------------------------------------------------
# Feature: Plugin registration
# ---------------------------------------------------------------------------


class TestGauntletCurateRegistration:
    """
    Feature: gauntlet-curate is registered in openpackage.yml

    As a gauntlet plugin maintainer
    I want the new skill registered in openpackage.yml
    So that Claude Code discovers it when the plugin loads
    """

    @pytest.mark.unit
    def test_skill_registered_in_openpackage(self):
        """
        Scenario: skills list in openpackage.yml includes gauntlet-curate
        Given the openpackage.yml manifest
        When the skills list is inspected
        Then 'skills/gauntlet-curate' is present
        """
        pkg = _load_openpackage()
        skills = pkg.get("skills", [])
        assert "skills/gauntlet-curate" in skills, (
            f"'skills/gauntlet-curate' not found in openpackage.yml skills: {skills}"
        )


# ---------------------------------------------------------------------------
# Feature: Backing script safety contract
# ---------------------------------------------------------------------------


class TestGauntletCurateScriptSafety:
    """
    Feature: Backing script is read-only

    As a gauntlet problem bank curator
    I want assurance that the skill's script cannot overwrite my files
    So that I can run /gauntlet-curate without risking data loss
    """

    @pytest.mark.unit
    def test_backing_script_exists(self):
        """
        Scenario: curate_problems.py exists in scripts/
        Given the gauntlet plugin
        When the scripts directory is inspected
        Then scripts/curate_problems.py exists
        """
        assert _SCRIPT.exists(), (
            f"Expected backing script at {_SCRIPT} but it was not found."
        )

    @pytest.mark.unit
    def test_backing_script_has_no_write_flag(self):
        """
        Scenario: curate_problems.py source code contains no --write flag
        Given the source of curate_problems.py
        When it is scanned for write-mode flags
        Then neither '--write' nor '--fix' appears as an add_argument call
        """
        source = _SCRIPT.read_text(encoding="utf-8")
        assert '"--write"' not in source and "'--write'" not in source, (
            "curate_problems.py must not define a --write flag."
        )
        assert '"--fix"' not in source and "'--fix'" not in source, (
            "curate_problems.py must not define a --fix flag."
        )
