"""BDD tests for the dora-metrics SKILL contract.

Feature: minister:dora-metrics skill is loadable and consistent.

As a Claude Code user
I want the dora-metrics skill SKILL.md to be well-formed and to wire
back to the working Python module
So that invoking the skill triggers reliable activation and points at
real code.
"""

from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = PLUGIN_ROOT / "skills" / "dora-metrics"
SKILL_FILE = SKILL_DIR / "SKILL.md"


def _read_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    raw = text[4:end]
    out: dict[str, str] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if line and not line.startswith(" ") and ":" in line:
            key, _, value = line.partition(":")
            current_key = key.strip()
            out[current_key] = value.strip()
        elif current_key and line.startswith(" "):
            out[current_key] += "\n" + line.strip()
    return out


class TestSkillFile:
    """Feature: SKILL.md exists with proper frontmatter."""

    def test_skill_md_exists(self) -> None:
        """Scenario: SKILL.md is present at the expected path.

        Given the dora-metrics skill directory
        When I look for SKILL.md
        Then it exists.
        """
        assert SKILL_FILE.exists()

    def test_skill_has_required_frontmatter_fields(self) -> None:
        """Scenario: frontmatter declares name, description, alwaysApply.

        Given the dora-metrics SKILL.md
        When I parse the frontmatter
        Then name, description, and alwaysApply are present.
        """
        fm = _read_frontmatter(SKILL_FILE)
        assert fm.get("name") == "dora-metrics"
        assert fm.get("description"), "description must not be empty"
        assert "alwaysApply" in fm

    def test_description_under_listing_budget(self) -> None:
        """Scenario: description fits the listing-budget guideline.

        Given the dora-metrics description
        When I count its characters
        Then the description is at most 150 chars.
        """
        fm = _read_frontmatter(SKILL_FILE)
        description = fm.get("description", "").strip("'\"")
        assert len(description) <= 150, (
            f"description too long: {len(description)} chars"
        )


class TestModuleWiring:
    """Feature: the skill points at a real Python module."""

    def test_referenced_module_imports(self) -> None:
        """Scenario: the underlying minister.dora_metrics module imports cleanly.

        Given the SKILL.md mentions ``python3 -m minister.dora_metrics``
        When I import that module
        Then it succeeds and exposes ``compute_metrics``.
        """
        from minister import dora_metrics

        assert hasattr(dora_metrics, "compute_metrics")
        assert hasattr(dora_metrics, "DORAMetrics")


class TestExitCriteria:
    """Feature: the SKILL.md follows project rule skill-exit-criteria."""

    def test_exit_criteria_section_present(self) -> None:
        """Scenario: every new SKILL.md must include Exit Criteria.

        Given the dora-metrics SKILL.md
        When I scan for an Exit Criteria heading
        Then it is present.
        """
        text = SKILL_FILE.read_text(encoding="utf-8")
        assert "## Exit Criteria" in text
