"""Contract tests for the export skill.

Feature: Export is mechanically linked to its implementation
  commands/export.md described a behavior with no named function, so a
  reader could not tell what actually ran.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from tome.output.export import export_for_memory_palace

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILL = PLUGIN_ROOT / "skills" / "export" / "SKILL.md"
COMMAND = PLUGIN_ROOT / "commands" / "export.md"
MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"


def _frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    return yaml.safe_load(content[3 : content.index("---", 3)])


def test_skill_exists() -> None:
    """Scenario: the skill file is present."""
    assert SKILL.exists(), f"missing {SKILL}"


def test_frontmatter_names_the_skill() -> None:
    """Scenario: frontmatter parses and is named export."""
    assert _frontmatter(SKILL.read_text()).get("name") == "export"


def test_skill_names_the_real_function() -> None:
    """Scenario: the skill names the function that does the work."""
    assert "export_for_memory_palace" in SKILL.read_text()


def test_function_actually_exists() -> None:
    """Scenario: the named function is importable, not aspirational.

    The import sits at module scope, so a missing function fails
    collection rather than this one assertion.
    """
    assert callable(export_for_memory_palace)


def test_command_points_at_the_skill() -> None:
    """Scenario: the command delegates rather than re-describing."""
    assert "export" in COMMAND.read_text()
    assert "export_for_memory_palace" in COMMAND.read_text()


def test_skill_registered_in_manifest() -> None:
    """Scenario: the skill is discoverable."""
    skills = json.loads(MANIFEST.read_text()).get("skills", [])
    assert any(s.rstrip("/").endswith("skills/export") for s in skills), skills


def test_handoff_target_is_named() -> None:
    """Scenario: the skill says which consumer reads its output."""
    assert "knowledge-intake" in SKILL.read_text()


def test_exit_criteria_present() -> None:
    """Scenario: the skill states when it is done."""
    content = SKILL.read_text()
    assert "## Exit Criteria" in content
    assert content.split("## Exit Criteria", 1)[1].count("- [ ]") >= 3
