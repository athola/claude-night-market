"""BDD contract tests for the pensive:shell-review skill.

Feature: pensive:shell-review skill is loadable, complete, and
references real modules and scripts.

As a Claude Code user invoking /shell-review
I want the skill SKILL.md to declare a complete contract
So that the workflow activates real, verifiable rules rather
than a half-written checklist.

These tests pin the SKILL.md/module contract so a reviewer or
future contributor cannot silently break:

- All frontmatter-declared modules exist on disk and are non-empty.
- Required SKILL.md sections are present (Exit Criteria, etc.).
- The ruleset reference scripts exist in scripts/.
- Each new module (structure-patterns) documents the required
  structural rules.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
SKILL_DIR = REPO_ROOT / "plugins" / "pensive" / "skills" / "shell-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"


def _read_skill() -> str:
    if not SKILL_FILE.exists():
        pytest.fail(f"shell-review SKILL.md missing: {SKILL_FILE}")
    return SKILL_FILE.read_text(encoding="utf-8")


def _read_frontmatter(content: str) -> str:
    if not content.startswith("---\n"):
        pytest.fail("SKILL.md must begin with `---` YAML frontmatter")
    end = content.find("\n---\n", 4)
    if end == -1:
        pytest.fail("SKILL.md frontmatter has no closing `---`")
    return content[4:end]


class TestShellReviewSkillFrontmatter:
    """SKILL.md frontmatter must declare a complete contract."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self) -> None:
        """Given the pensive plugin, shell-review SKILL.md must exist."""
        assert SKILL_FILE.is_file(), f"Expected SKILL.md at {SKILL_FILE}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_declares_required_keys(self) -> None:
        """Frontmatter must declare name, description, modules, and category."""
        fm = _read_frontmatter(_read_skill())
        for key in ("name: shell-review", "modules:", "progressive_loading: true"):
            assert key in fm, f"Frontmatter missing required key: {key}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_estimated_tokens_within_budget(self) -> None:
        """estimated_tokens must not exceed the project cap of 1500."""
        fm = _read_frontmatter(_read_skill())
        for line in fm.splitlines():
            if line.strip().startswith("estimated_tokens:"):
                value = int(line.split(":", 1)[1].strip())
                assert value <= 1500, (
                    f"estimated_tokens {value} exceeds project cap of 1500"
                )
                return
        pytest.fail("Frontmatter must declare estimated_tokens")


class TestShellReviewSkillModules:
    """Each module listed in frontmatter must exist on disk and be non-empty."""

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "module_name",
        [
            "exit-codes.md",
            "portability.md",
            "safety-patterns.md",
            "structure-patterns.md",
        ],
    )
    def test_module_file_exists(self, module_name: str) -> None:
        """Given a module file listed in SKILL.md, it must exist on disk."""
        module_path = MODULES_DIR / module_name
        assert module_path.is_file(), (
            f"Module {module_name} listed in SKILL.md but missing at {module_path}"
        )
        assert module_path.stat().st_size > 0, (
            f"Module {module_name} exists but is empty"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_safety_patterns_documents_no_echo_rule(self) -> None:
        """safety-patterns.md must document the no-echo rule."""
        text = (MODULES_DIR / "safety-patterns.md").read_text(encoding="utf-8").lower()
        assert "echo" in text and "log()" in text, (
            "safety-patterns.md must document that echo is banned and log() is required"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_safety_patterns_documents_braced_vars(self) -> None:
        """safety-patterns.md must document the braced-variable rule."""
        text = (MODULES_DIR / "safety-patterns.md").read_text(encoding="utf-8").lower()
        assert "brace" in text or "${var}" in text.lower(), (
            "safety-patterns.md must document braced variable references"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_structure_patterns_documents_main_rule(self) -> None:
        """structure-patterns.md must document the main() and last-line rule."""
        text = (MODULES_DIR / "structure-patterns.md").read_text(encoding="utf-8")
        assert 'main "${@}"' in text, (
            'structure-patterns.md must document `main "${@}"` as the required last line'
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_structure_patterns_documents_depcheck(self) -> None:
        """structure-patterns.md must document depcheck()."""
        text = (MODULES_DIR / "structure-patterns.md").read_text(encoding="utf-8")
        assert "depcheck()" in text, (
            "structure-patterns.md must document the depcheck() pattern"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_structure_patterns_documents_library_guard(self) -> None:
        """structure-patterns.md must document the __loading_loaded guard form."""
        text = (MODULES_DIR / "structure-patterns.md").read_text(encoding="utf-8")
        assert "__logging_loaded" in text, (
            "structure-patterns.md must document the __logging_loaded library guard"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_structure_patterns_documents_shfmt(self) -> None:
        """structure-patterns.md must document the shfmt -p -i 2 -ci command."""
        text = (MODULES_DIR / "structure-patterns.md").read_text(encoding="utf-8")
        assert "shfmt -p -i 2 -ci" in text, (
            "structure-patterns.md must document the required shfmt invocation"
        )


class TestShellReviewSkillContract:
    """SKILL.md body must include the required sections."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_required_sections_present(self) -> None:
        """SKILL.md must include all required workflow sections."""
        body = _read_skill()
        for heading in (
            "## When To Use",
            "## When NOT To Use",
            "## Required TodoWrite Items",
            "## Workflow",
            "## Output Format",
            "## Exit Criteria",
        ):
            assert heading in body, f"SKILL.md missing required heading: {heading}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_structure_step_wired_in_workflow(self) -> None:
        """Workflow must include a structure/preamble check step."""
        body = _read_skill().lower()
        assert "structure" in body or "preamble" in body, (
            "Workflow must include a structure check step for the new ruleset"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_exit_criteria_are_concrete(self) -> None:
        """Exit Criteria section must list checkboxes."""
        body = _read_skill()
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
