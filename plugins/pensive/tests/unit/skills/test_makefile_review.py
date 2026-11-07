"""BDD contract tests for Makefile review, folded into unified-review.

Feature: Makefile review is a unified-review module, reachable by its old names

As a Claude Code user invoking /makefile-review
I want the Makefile audit to run from unified-review's makefile module
So that the verdict scaffold has one owner (ADR-0014, #616) and the
old command and skill name keep working for one release.

These tests pin:

- The makefile-review module and its five sub-modules exist under
  unified-review and are non-empty.
- The module carries the workflow sections the skill used to carry.
- unified-review lists the module and dispatches Makefile review to it,
  not to the old skill.
- The old skill is a redirect stub, and /makefile-review routes to
  unified-review's makefile focus.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
PENSIVE = REPO_ROOT / "plugins" / "pensive"
UNIFIED_DIR = PENSIVE / "skills" / "unified-review"
UNIFIED_FILE = UNIFIED_DIR / "SKILL.md"
MODULES_DIR = UNIFIED_DIR / "modules"
MODULE_FILE = MODULES_DIR / "makefile-review.md"
STUB_FILE = PENSIVE / "skills" / "makefile-review" / "SKILL.md"
COMMAND_FILE = PENSIVE / "commands" / "makefile-review.md"

MAKEFILE_MODULES = (
    "makefile-review.md",
    "makefile-dependency-graph.md",
    "makefile-deduplication-patterns.md",
    "makefile-portability-checks.md",
    "makefile-best-practices.md",
    "makefile-plugin-dogfood-checks.md",
)


def _read(path: Path) -> str:
    if not path.exists():
        pytest.fail(f"missing: {path}")
    return path.read_text(encoding="utf-8")


def _read_frontmatter(content: str) -> str:
    if not content.startswith("---\n"):
        pytest.fail("SKILL.md must begin with `---` YAML frontmatter")
    end = content.find("\n---\n", 4)
    if end == -1:
        pytest.fail("SKILL.md frontmatter has no closing `---`")
    return content[4:end]


class TestUnifiedReviewOwnsMakefileReview:
    """unified-review lists the module and dispatches Makefile review to it."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_lists_the_makefile_modules(self) -> None:
        """Given unified-review's frontmatter, every makefile module is listed."""
        fm = _read_frontmatter(_read(UNIFIED_FILE))
        for name in MAKEFILE_MODULES:
            assert f"modules/{name}" in fm, f"unified-review does not list {name}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dispatch_loads_the_module_not_the_old_skill(self) -> None:
        """Makefile review goes to the module, not Skill(pensive:makefile-review)."""
        text = _read(UNIFIED_FILE)
        assert "Skill(pensive:makefile-review)" not in text
        assert "- pensive:makefile-review" not in _read_frontmatter(text)
        assert 'schedule_module("makefile-review")' in text
        assert "modules/makefile-review.md" in text

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_makefile_focus_is_selectable(self) -> None:
        """Focused mode offers a makefile selector for the /makefile-review alias."""
        assert "/full-review makefile" in _read(UNIFIED_FILE)
        full_review = _read(PENSIVE / "commands" / "full-review.md")
        assert "/full-review makefile" in full_review
        assert "Skill(pensive:makefile-review)" not in full_review


class TestOldNamesRedirect:
    """The old skill and command keep working by routing to unified-review."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_stub_is_marked_deprecated_and_redirects(self) -> None:
        """Given the old skill, it names its replacement and carries no workflow."""
        text = _read(STUB_FILE)
        assert "Deprecated" in text
        assert "Skill(pensive:unified-review)" in text
        assert "modules/makefile-review.md" in text
        assert "## Workflow" not in text
        assert not (STUB_FILE.parent / "modules").exists()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_stub_keeps_exit_criteria(self) -> None:
        """Every SKILL.md needs Exit Criteria, the stub included."""
        text = _read(STUB_FILE)
        assert "## Exit Criteria" in text
        assert "- [ ]" in text[text.index("## Exit Criteria") :]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_routes_to_unified_review(self) -> None:
        """/makefile-review invokes unified-review's makefile focus."""
        text = _read(COMMAND_FILE)
        assert "Skill(pensive:unified-review)" in text
        assert "Skill(pensive:makefile-review)" not in text
        assert "modules/makefile-review.md" in text


class TestMakefileReviewModules:
    """Every makefile module exists under unified-review and is wired."""

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize("module_name", MAKEFILE_MODULES)
    def test_module_file_exists(self, module_name: str) -> None:
        """Given a makefile module listed in unified-review, it exists on disk."""
        module_path = MODULES_DIR / module_name
        assert module_path.is_file(), (
            f"Module {module_name} listed in unified-review but missing at {module_path}"
        )
        assert module_path.stat().st_size > 0, (
            f"Module {module_name} exists but is empty"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize("module_name", MAKEFILE_MODULES[1:])
    def test_workflow_includes_each_rule_module(self, module_name: str) -> None:
        """The workflow loads every rule module by its new name."""
        assert f"@include modules/{module_name}" in _read(MODULE_FILE)


class TestMakefileReviewModuleContract:
    """The module must carry the workflow sections the skill used to."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_required_sections_present(self) -> None:
        """The module must include all required workflow sections."""
        body = _read(MODULE_FILE)
        for heading in (
            "## When To Use",
            "## When NOT To Use",
            "## Required Progress Items",
            "## Workflow",
            "## Output Format",
            "## Exit Criteria",
        ):
            assert heading in body, f"module missing required heading: {heading}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_declares_the_dependency_the_module_invokes(self) -> None:
        """The module runs review-core's citation verifier, so it is declared."""
        assert "Skill(imbue:review-core)" in _read(MODULE_FILE)
        assert "- imbue:review-core" in _read_frontmatter(_read(UNIFIED_FILE))

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_exit_criteria_are_concrete(self) -> None:
        """Exit Criteria section must list checkboxes."""
        body = _read(MODULE_FILE)
        section = body[body.index("## Exit Criteria") :]
        assert section.count("- [ ]") >= 4, (
            "Exit Criteria must list at least four concrete checkboxes"
        )
