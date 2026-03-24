"""Tests for clawhub-export.py — ClawHub/OpenClaw skill exporter.

Feature: Export night-market skills as OpenClaw-compatible packages

As a night-market maintainer
I want to export skills in ClawHub format
So that OpenClaw and NemoClaw users can discover and use them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Add scripts/ to path so we can import the module
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from clawhub_export import (  # noqa: E402
    _clean_description,
    discover_skills,
    export_all,
    extract_triggers,
    parse_frontmatter,
    to_clawhub_slug,
    translate_frontmatter,
    validate_export,
)

# ---------- fixtures ----------


@pytest.fixture()
def sample_skill_md() -> str:
    """A representative Claude Code SKILL.md with full frontmatter."""
    return """\
---
name: bug-review
description: 'Systematic bug hunting with evidence trails. Use when deep bug
  hunting needed, documenting defects. Do not use when test coverage audit.'
category: code-review
tags:
- bugs
- debugging
- evidence
- defects
dependencies:
- imbue:proof-of-work
estimated_tokens: 1500
---

# Bug Review

Hunt bugs systematically with evidence.
"""


@pytest.fixture()
def minimal_skill_md() -> str:
    """A minimal SKILL.md with only required fields."""
    return """\
---
name: simple-skill
description: A simple skill for testing
---

# Simple Skill

Does simple things.
"""


@pytest.fixture()
def skill_with_tools_md() -> str:
    """SKILL.md with tools and model fields."""
    return """\
---
name: code-refinement
description: Analyze and improve living code quality
category: code-review
tags:
- refactoring
- quality
tools: [Read, Write, Edit, Bash, Glob, Grep]
model: sonnet
complexity: medium
estimated_tokens: 4200
---

# Code Refinement

Improve code quality.
"""


@pytest.fixture()
def tmp_plugins(tmp_path: Path) -> Path:
    """Create a temporary plugin structure for testing."""
    # Plugin: pensive
    pensive = tmp_path / "pensive"
    pensive_plugin = pensive / ".claude-plugin"
    pensive_plugin.mkdir(parents=True)
    (pensive_plugin / "plugin.json").write_text(
        json.dumps({"name": "pensive", "version": "1.7.0"})
    )

    skills = pensive / "skills"
    bug_review = skills / "bug-review"
    bug_review.mkdir(parents=True)
    (bug_review / "SKILL.md").write_text(
        """\
---
name: bug-review
description: Systematic bug hunting with evidence trails
category: code-review
tags:
- bugs
- debugging
---

# Bug Review

Content here.
"""
    )

    code_refinement = skills / "code-refinement"
    code_refinement.mkdir(parents=True)
    (code_refinement / "SKILL.md").write_text(
        """\
---
name: code-refinement
description: Analyze and improve living code quality
tags:
- refactoring
---

# Code Refinement

Content here.
"""
    )

    # Plugin: sanctum (with modules)
    sanctum = tmp_path / "sanctum"
    sanctum_plugin = sanctum / ".claude-plugin"
    sanctum_plugin.mkdir(parents=True)
    (sanctum_plugin / "plugin.json").write_text(
        json.dumps({"name": "sanctum", "version": "1.7.0"})
    )

    commit_skill = sanctum / "skills" / "commit-messages"
    commit_skill.mkdir(parents=True)
    (commit_skill / "SKILL.md").write_text(
        """\
---
name: commit-messages
description: Generate conventional commit messages from staged changes
tags:
- git
- commits
---

# Commit Messages

Generate commits.
"""
    )
    modules = commit_skill / "modules"
    modules.mkdir()
    (modules / "conventional-format.md").write_text("# Format\n\nDetails.\n")

    return tmp_path


# ---------- frontmatter parsing ----------


class TestParseFrontmatter:
    """
    Feature: Parse YAML frontmatter from SKILL.md files

    As a converter
    I want to parse Claude Code SKILL.md frontmatter
    So that I can translate fields to OpenClaw format.
    """

    @pytest.mark.unit
    def test_parses_basic_frontmatter(self, sample_skill_md: str) -> None:
        """
        Scenario: Parse standard skill frontmatter
        Given a SKILL.md with name, description, category, tags
        When I parse the frontmatter
        Then all fields are extracted correctly.
        """
        fm, body = parse_frontmatter(sample_skill_md)

        assert fm["name"] == "bug-review"
        assert "bug hunting" in fm["description"]
        assert fm["category"] == "code-review"
        assert isinstance(fm["tags"], list)
        assert "bugs" in fm["tags"]
        assert fm["estimated_tokens"] == 1500

    @pytest.mark.unit
    def test_parses_minimal_frontmatter(self, minimal_skill_md: str) -> None:
        """
        Scenario: Parse minimal frontmatter
        Given a SKILL.md with only name and description
        When I parse the frontmatter
        Then name and description are extracted.
        """
        fm, body = parse_frontmatter(minimal_skill_md)

        assert fm["name"] == "simple-skill"
        assert fm["description"] == "A simple skill for testing"

    @pytest.mark.unit
    def test_parses_inline_list(self, skill_with_tools_md: str) -> None:
        """
        Scenario: Parse inline list syntax [a, b, c]
        Given a SKILL.md with tools as inline list
        When I parse the frontmatter
        Then tools is a list of strings.
        """
        fm, _ = parse_frontmatter(skill_with_tools_md)

        assert isinstance(fm["tools"], list)
        assert "Read" in fm["tools"]
        assert "Bash" in fm["tools"]

    @pytest.mark.unit
    def test_separates_body_from_frontmatter(self, sample_skill_md: str) -> None:
        """
        Scenario: Body is separated from frontmatter
        Given a SKILL.md with frontmatter and body
        When I parse the content
        Then the body starts after the closing ---.
        """
        _, body = parse_frontmatter(sample_skill_md)

        assert "# Bug Review" in body
        assert "---" not in body

    @pytest.mark.unit
    def test_handles_no_frontmatter(self) -> None:
        """
        Scenario: File without frontmatter
        Given a markdown file without --- delimiters
        When I parse the content
        Then frontmatter is empty and body is full content.
        """
        content = "# Just a heading\n\nSome content.\n"
        fm, body = parse_frontmatter(content)

        assert fm == {}
        assert body == content

    @pytest.mark.unit
    def test_parses_dependencies_list(self, sample_skill_md: str) -> None:
        """
        Scenario: Parse dependencies as list
        Given a SKILL.md with dependencies
        When I parse the frontmatter
        Then dependencies is a list of plugin:skill strings.
        """
        fm, _ = parse_frontmatter(sample_skill_md)

        assert isinstance(fm["dependencies"], list)
        assert "imbue:proof-of-work" in fm["dependencies"]

    @pytest.mark.unit
    def test_parses_boolean_values(self) -> None:
        """
        Scenario: Parse boolean frontmatter values
        Given frontmatter with true/false values
        When I parse it
        Then booleans are Python bool type.
        """
        content = "---\nname: test\nenabled: true\ndisabled: false\n---\n\nBody\n"
        fm, _ = parse_frontmatter(content)

        assert fm["enabled"] is True
        assert fm["disabled"] is False


# ---------- slug generation ----------


class TestSlugGeneration:
    """
    Feature: Generate valid ClawHub slugs

    As a publisher
    I want slugs that match ClawHub's ^[a-z0-9][a-z0-9-]*$ pattern
    So that skills can be published to the registry.
    """

    @pytest.mark.unit
    def test_generates_prefixed_slug(self) -> None:
        """
        Scenario: Standard plugin:skill name
        Given plugin "pensive" and skill "bug-review"
        When I generate a slug
        Then it is prefixed with "nm-" for namespace.
        """
        slug = to_clawhub_slug("pensive", "bug-review")
        assert slug == "nm-pensive-bug-review"

    @pytest.mark.unit
    def test_lowercases_slug(self) -> None:
        """
        Scenario: Mixed case input
        Given uppercase characters in names
        When I generate a slug
        Then it is all lowercase.
        """
        slug = to_clawhub_slug("Pensive", "Bug-Review")
        assert slug == "nm-pensive-bug-review"

    @pytest.mark.unit
    def test_replaces_underscores(self) -> None:
        """
        Scenario: Underscores in names
        Given names with underscores
        When I generate a slug
        Then underscores become hyphens.
        """
        slug = to_clawhub_slug("my_plugin", "my_skill")
        assert slug == "nm-my-plugin-my-skill"

    @pytest.mark.unit
    def test_removes_invalid_chars(self) -> None:
        """
        Scenario: Special characters in names
        Given names with dots or other chars
        When I generate a slug
        Then invalid characters are removed.
        """
        slug = to_clawhub_slug("plugin.v2", "skill@test")
        assert slug == "nm-pluginv2-skilltest"


# ---------- trigger extraction ----------


class TestTriggerExtraction:
    """
    Feature: Extract semantic triggers from Claude Code metadata

    As a converter
    I want to generate OpenClaw triggers from tags and descriptions
    So that OpenClaw's intent matching works well.
    """

    @pytest.mark.unit
    def test_extracts_tags_as_triggers(self) -> None:
        """
        Scenario: Tags become triggers
        Given frontmatter with tags
        When I extract triggers
        Then tags appear in the trigger list.
        """
        fm: dict[str, Any] = {"tags": ["bugs", "debugging", "evidence"]}
        triggers = extract_triggers(fm)

        assert "bugs" in triggers
        assert "debugging" in triggers

    @pytest.mark.unit
    def test_extracts_use_when_phrases(self) -> None:
        """
        Scenario: Description "Use when" phrases become triggers
        Given a description with "Use when" guidance
        When I extract triggers
        Then key phrases are included.
        """
        fm: dict[str, Any] = {
            "tags": [],
            "description": (
                "Review code quality. Use when: deep bug hunting needed, "
                "documenting defects. Do not use when test coverage audit."
            ),
        }
        triggers = extract_triggers(fm)

        assert any("bug hunting" in t for t in triggers)

    @pytest.mark.unit
    def test_limits_triggers_to_15(self) -> None:
        """
        Scenario: Too many potential triggers
        Given frontmatter with 20+ tags
        When I extract triggers
        Then the list is capped at 15.
        """
        fm: dict[str, Any] = {"tags": [f"tag-{i}" for i in range(25)]}
        triggers = extract_triggers(fm)

        assert len(triggers) <= 15


# ---------- frontmatter translation ----------


class TestTranslateFrontmatter:
    """
    Feature: Translate Claude Code frontmatter to OpenClaw format

    As a converter
    I want to map Claude Code fields to OpenClaw equivalents
    So that exported skills load correctly in OpenClaw.
    """

    @pytest.mark.unit
    def test_preserves_name_and_description(self) -> None:
        """
        Scenario: Core fields pass through
        Given Claude Code frontmatter with name and description
        When I translate to OpenClaw format
        Then name and description are preserved.
        """
        fm: dict[str, Any] = {
            "name": "bug-review",
            "description": "Hunt bugs systematically",
            "category": "code-review",
            "tags": ["bugs"],
        }
        result = translate_frontmatter(fm, "pensive")

        assert result["name"] == "bug-review"
        assert "Hunt bugs" in result["description"]

    @pytest.mark.unit
    def test_adds_version(self) -> None:
        """
        Scenario: Version is added from plugin
        Given Claude Code frontmatter without version
        When I translate with plugin version
        Then version field is present.
        """
        fm: dict[str, Any] = {"name": "test", "description": "test"}
        result = translate_frontmatter(fm, "pensive", "1.7.0")

        assert result["version"] == "1.7.0"

    @pytest.mark.unit
    def test_generates_metadata_openclaw(self) -> None:
        """
        Scenario: metadata.openclaw block is generated
        Given Claude Code frontmatter
        When I translate to OpenClaw format
        Then metadata contains openclaw homepage and emoji.
        """
        fm: dict[str, Any] = {
            "name": "test",
            "description": "test",
            "category": "code-review",
        }
        result = translate_frontmatter(fm, "pensive")

        metadata = json.loads(result["metadata"])
        assert "openclaw" in metadata
        assert "pensive" in metadata["openclaw"]["homepage"]

    @pytest.mark.unit
    def test_cleans_description_of_usage_hints(self) -> None:
        """
        Scenario: Remove Claude Code-specific usage hints
        Given a description with "Use when" / "Do not use" guidance
        When I clean the description
        Then only the core description remains.
        """
        desc = (
            "Review code quality and find bugs. "
            "Use when deep hunting needed. "
            "Do not use when simple lint."
        )
        cleaned = _clean_description(desc)

        assert "Review code quality" in cleaned
        assert "Use when" not in cleaned
        assert "Do not use" not in cleaned


# ---------- skill discovery ----------


class TestSkillDiscovery:
    """
    Feature: Discover all SKILL.md files across plugins

    As a converter
    I want to find all exportable skills
    So that no skill is missed in the export.
    """

    @pytest.mark.unit
    def test_discovers_skills_across_plugins(self, tmp_plugins: Path) -> None:
        """
        Scenario: Multiple plugins with skills
        Given a plugins directory with pensive and sanctum
        When I discover skills
        Then all skills from both plugins are found.
        """
        skills = discover_skills(tmp_plugins)

        names = [(p, s) for p, s, _ in skills]
        assert ("pensive", "bug-review") in names
        assert ("pensive", "code-refinement") in names
        assert ("sanctum", "commit-messages") in names
        assert len(skills) == 3

    @pytest.mark.unit
    def test_returns_correct_paths(self, tmp_plugins: Path) -> None:
        """
        Scenario: Returned paths point to actual files
        Given discovered skills
        When I check each path
        Then all paths exist and are SKILL.md files.
        """
        skills = discover_skills(tmp_plugins)

        for _, _, path in skills:
            assert path.exists()
            assert path.name == "SKILL.md"


# ---------- full export ----------


class TestExportAll:
    """
    Feature: Export all skills to ClawHub format

    As a maintainer
    I want to batch export all skills
    So that I can publish the full night-market to ClawHub.
    """

    @pytest.mark.unit
    def test_exports_all_skills(self, tmp_plugins: Path, tmp_path: Path) -> None:
        """
        Scenario: Full export of all skills
        Given a plugins directory with 3 skills
        When I export all
        Then 3 skill directories are created with SKILL.md files.
        """
        output = tmp_path / "clawhub-out"
        manifest = export_all(output, plugins_dir=tmp_plugins)

        assert manifest["total_exported"] == 3
        assert manifest["total_errors"] == 0
        assert (output / "manifest.json").exists()

    @pytest.mark.unit
    def test_exported_skills_have_valid_structure(
        self, tmp_plugins: Path, tmp_path: Path
    ) -> None:
        """
        Scenario: Each exported skill has required files
        Given an export has completed
        When I check each skill directory
        Then each contains a valid SKILL.md with OpenClaw frontmatter.
        """
        output = tmp_path / "clawhub-out"
        manifest = export_all(output, plugins_dir=tmp_plugins)

        for skill_info in manifest["skills"]:
            skill_dir = output / skill_info["slug"]
            skill_md = skill_dir / "SKILL.md"
            assert skill_md.exists()

            content = skill_md.read_text()
            fm, _ = parse_frontmatter(content)
            assert fm.get("name")
            assert fm.get("description")
            assert fm.get("version")

    @pytest.mark.unit
    def test_copies_modules(self, tmp_plugins: Path, tmp_path: Path) -> None:
        """
        Scenario: Supporting modules are included in export
        Given a skill with a modules/ directory
        When I export it
        Then modules are copied to the output.
        """
        output = tmp_path / "clawhub-out"
        export_all(output, plugins_dir=tmp_plugins)

        commit_slug = "nm-sanctum-commit-messages"
        modules = output / commit_slug / "modules"
        assert modules.is_dir()
        assert (modules / "conventional-format.md").exists()

    @pytest.mark.unit
    def test_export_adds_provenance_notice(
        self, tmp_plugins: Path, tmp_path: Path
    ) -> None:
        """
        Scenario: Exported skills credit night-market
        Given an exported skill
        When I read its body
        Then it includes a provenance notice with link.
        """
        output = tmp_path / "clawhub-out"
        export_all(output, plugins_dir=tmp_plugins)

        skill_md = output / "nm-pensive-bug-review" / "SKILL.md"
        content = skill_md.read_text()
        assert "Night Market Skill" in content
        assert "claude-night-market" in content


# ---------- validation ----------


class TestValidation:
    """
    Feature: Validate exported ClawHub packages

    As a publisher
    I want to validate exports before submission
    So that ClawHub review doesn't reject them.
    """

    @pytest.mark.unit
    def test_valid_export_passes(self, tmp_plugins: Path, tmp_path: Path) -> None:
        """
        Scenario: Valid export passes validation
        Given a successful export
        When I validate it
        Then no issues are found.
        """
        output = tmp_path / "clawhub-out"
        export_all(output, plugins_dir=tmp_plugins)

        issues = validate_export(output)
        assert issues == []

    @pytest.mark.unit
    def test_missing_directory_fails(self, tmp_path: Path) -> None:
        """
        Scenario: Non-existent output directory
        Given a path that doesn't exist
        When I validate
        Then an error is returned.
        """
        issues = validate_export(tmp_path / "nonexistent")
        assert len(issues) > 0
        assert "does not exist" in issues[0]
