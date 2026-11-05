"""BDD contract tests for shell review, folded into unified-review.

Feature: shell review is a unified-review module, reachable by its old names

As a Claude Code user invoking /shell-review
I want the shell audit to run from unified-review's shell module
So that the verdict scaffold has one owner (ADR-0014, #615) and the
old command and skill name keep working for one release.

These tests pin:

- The shell-review module and its four sub-modules exist under
  unified-review and are non-empty.
- The module carries the workflow sections the skill used to carry.
- unified-review lists the module and dispatches shell review to it,
  not to the old skill.
- The old skill is a redirect stub, and /shell-review routes to
  unified-review's shell focus.
- The ruleset reference scripts exist in scripts/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
PENSIVE = REPO_ROOT / "plugins" / "pensive"
UNIFIED_DIR = PENSIVE / "skills" / "unified-review"
UNIFIED_FILE = UNIFIED_DIR / "SKILL.md"
MODULES_DIR = UNIFIED_DIR / "modules"
MODULE_FILE = MODULES_DIR / "shell-review.md"
STUB_FILE = PENSIVE / "skills" / "shell-review" / "SKILL.md"
COMMAND_FILE = PENSIVE / "commands" / "shell-review.md"


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


class TestUnifiedReviewOwnsShellReview:
    """unified-review lists the module and dispatches shell review to it."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_lists_the_shell_modules(self) -> None:
        """Given unified-review's frontmatter, every shell module is listed."""
        fm = _read_frontmatter(_read(UNIFIED_FILE))
        for name in (
            "shell-review.md",
            "shell-exit-codes.md",
            "shell-portability.md",
            "shell-safety-patterns.md",
            "shell-structure-patterns.md",
        ):
            assert f"modules/{name}" in fm, f"unified-review does not list {name}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dispatch_loads_the_module_not_the_old_skill(self) -> None:
        """Shell review is dispatched to the module, not Skill(pensive:shell-review)."""
        body = _read(UNIFIED_FILE)
        assert "Skill(pensive:shell-review)" not in body
        assert "modules/shell-review.md" in body

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shell_focus_is_selectable(self) -> None:
        """Focused mode offers a shell selector for the /shell-review alias."""
        assert "/full-review shell" in _read(UNIFIED_FILE)
        assert "/full-review shell" in _read(PENSIVE / "commands" / "full-review.md")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_declares_the_dependency_the_module_invokes(self) -> None:
        """The module runs review-core's citation verifier, so it is declared."""
        assert "Skill(imbue:review-core)" in _read(MODULE_FILE)
        assert "- imbue:review-core" in _read_frontmatter(_read(UNIFIED_FILE))


class TestOldNamesRedirect:
    """The old skill and command keep working by routing to unified-review."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_stub_is_marked_deprecated_and_redirects(self) -> None:
        """Given the old skill, it names its replacement and carries no workflow."""
        text = _read(STUB_FILE)
        assert "Deprecated" in text
        assert "Skill(pensive:unified-review)" in text
        assert "modules/shell-review.md" in text
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
        """/shell-review invokes unified-review's shell focus."""
        text = _read(COMMAND_FILE)
        assert "Skill(pensive:unified-review)" in text
        assert "Skill(pensive:shell-review)" not in text
        assert "modules/shell-review.md" in text


class TestShellReviewSkillModules:
    """Each module listed in frontmatter must exist on disk and be non-empty."""

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "module_name",
        [
            "shell-review.md",
            "shell-exit-codes.md",
            "shell-portability.md",
            "shell-safety-patterns.md",
            "shell-structure-patterns.md",
        ],
    )
    def test_module_file_exists(self, module_name: str) -> None:
        """Given a shell module listed in unified-review, it must exist on disk."""
        module_path = MODULES_DIR / module_name
        assert module_path.is_file(), (
            f"Module {module_name} listed in unified-review but missing at {module_path}"
        )
        assert module_path.stat().st_size > 0, (
            f"Module {module_name} exists but is empty"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_safety_patterns_documents_no_echo_rule(self) -> None:
        """safety-patterns.md must document the no-echo rule."""
        text = (
            (MODULES_DIR / "shell-safety-patterns.md")
            .read_text(encoding="utf-8")
            .lower()
        )
        assert "echo" in text and "log()" in text, (
            "safety-patterns.md must document that echo is banned and log() is required"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_safety_patterns_documents_braced_vars(self) -> None:
        """safety-patterns.md must document the braced-variable rule."""
        text = (
            (MODULES_DIR / "shell-safety-patterns.md")
            .read_text(encoding="utf-8")
            .lower()
        )
        assert "brace" in text or "${var}" in text.lower(), (
            "safety-patterns.md must document braced variable references"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_structure_patterns_documents_main_rule(self) -> None:
        """structure-patterns.md must document the main() and last-line rule."""
        text = (MODULES_DIR / "shell-structure-patterns.md").read_text(encoding="utf-8")
        assert 'main "$@"' in text, (
            'structure-patterns.md must document `main "$@"` as the required last line'
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "module_name", ["shell-structure-patterns.md", "shell-safety-patterns.md"]
    )
    def test_no_module_recommends_braced_at(self, module_name: str) -> None:
        """Under `set -u`, bash 3.2 reports `"${@}"` with no arguments as unbound.

        Only the bare `"$@"` form is exempt, which is why every executable
        in this repository ends with `main "$@"` and
        `tests/test_shell_portability.py` asserts it. A review that
        recommends the braced form would flag correct scripts and suggest
        a fix that breaks stock macOS `/bin/sh`.
        """
        text = (MODULES_DIR / module_name).read_text(encoding="utf-8")
        assert 'main "${@}"' not in text
        assert '→ `"${@}"`' not in text

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_structure_patterns_documents_depcheck(self) -> None:
        """structure-patterns.md must document depcheck()."""
        text = (MODULES_DIR / "shell-structure-patterns.md").read_text(encoding="utf-8")
        assert "depcheck()" in text, (
            "structure-patterns.md must document the depcheck() pattern"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_structure_patterns_documents_library_guard(self) -> None:
        """structure-patterns.md must document the __loading_loaded guard form."""
        text = (MODULES_DIR / "shell-structure-patterns.md").read_text(encoding="utf-8")
        assert "__logging_loaded" in text, (
            "structure-patterns.md must document the __logging_loaded library guard"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_structure_patterns_documents_shfmt(self) -> None:
        """structure-patterns.md must document the shfmt -p -i 2 -ci command."""
        text = (MODULES_DIR / "shell-structure-patterns.md").read_text(encoding="utf-8")
        assert "shfmt -p -i 2 -ci" in text, (
            "structure-patterns.md must document the required shfmt invocation"
        )


class TestShellReviewModuleContract:
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
    def test_structure_step_wired_in_workflow(self) -> None:
        """Workflow must include a structure/preamble check step."""
        body = _read(MODULE_FILE).lower()
        assert "structure" in body or "preamble" in body, (
            "Workflow must include a structure check step for the new ruleset"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_exit_criteria_are_concrete(self) -> None:
        """Exit Criteria section must list checkboxes."""
        body = _read(MODULE_FILE)
        idx = body.find("## Exit Criteria")
        assert idx != -1
        section = body[idx:]
        assert "- [ ]" in section or "- [x]" in section, (
            "Exit Criteria must contain checkbox items"
        )


class TestReferenceScriptsReferenced:
    """The skill must reference the canonical scripts that demonstrate the rules."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_logging_sh_exists(self) -> None:
        """scripts/logging.sh must exist as the logging library."""
        assert (REPO_ROOT / "scripts" / "logging.sh").is_file(), (
            "scripts/logging.sh not found — skill depends on it"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shellcheck_sh_exists(self) -> None:
        """scripts/shellcheck.sh must exist as the runner / canonical example."""
        assert (REPO_ROOT / "scripts" / "shellcheck.sh").is_file(), (
            "scripts/shellcheck.sh not found — skill references it as canonical example"
        )
