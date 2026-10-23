"""Regression tests for API-review findings in sanctum."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sanctum import validators
from sanctum.pr_prep import PRPrepAnalyzer
from sanctum.validators import CommandValidator, PluginValidator, SkillValidator, skill


def test_skill_validator_reports_invalid_frontmatter_for_scalar_yaml() -> None:
    pytest.importorskip("yaml")
    result = SkillValidator.parse_frontmatter("---\nfoo\n---\nbody\n")
    assert not result.is_valid
    assert "Invalid YAML frontmatter" in result.errors


@pytest.mark.parametrize(
    ("key", "ref", "make"),
    [
        ("commands", "./.hidden/c.md", "file"),
        ("skills", "./.hidden/s", "skilldir"),
        ("agents", "./.hidden/a.md", "file"),
    ],
)
def test_plugin_validator_finds_files_under_dot_directories(
    tmp_path: Path, key: str, ref: str, make: str
) -> None:
    target = tmp_path / ref[2:]
    if make == "file":
        target.parent.mkdir(parents=True)
        target.write_text("x", encoding="utf-8")
    else:
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("x", encoding="utf-8")
    manifest = {"name": "p", "version": "1.0.0", "description": "d", key: [ref]}
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    result = PluginValidator.validate_plugin_dir(tmp_path)
    assert not [e for e in result.errors if "not found" in e], result.errors


def test_command_validator_does_not_warn_for_cross_plugin_skill_reference(
    tmp_path: Path,
) -> None:
    result = CommandValidator.validate_skill_references(
        "Skill(imbue:proof-of-work)", tmp_path
    )
    assert result.warnings == []


def test_command_validator_warns_for_missing_own_plugin_skill(tmp_path: Path) -> None:
    own = f"Skill({tmp_path.name}:missing)"
    result = CommandValidator.validate_skill_references(own, tmp_path)
    assert any("missing" in w for w in result.warnings)


def test_private_skill_ref_helper_not_in_public_all() -> None:

    assert "_extract_skill_refs_from_content" not in validators.__all__
    assert "_extract_skill_refs_from_content" not in skill.__all__


def test_pr_prep_accepts_bare_path_strings_everywhere() -> None:
    files = ["a.py", "tests/test_a.py"]
    categories = PRPrepAnalyzer.categorize_changed_files(files)
    assert categories.other == files
    assert PRPrepAnalyzer.suggest_reviewers(files, {"tests/": ["bob"]}) == ["bob"]
    assert not PRPrepAnalyzer.detect_breaking_changes(
        {"changed_files": files}
    ).has_breaking_changes
