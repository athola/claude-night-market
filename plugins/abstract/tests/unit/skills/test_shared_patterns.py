"""BDD contract tests for abstract:shared-patterns skill.

Feature: shared-patterns SKILL.md declares a complete and consistent
module list.

As a skill developer referencing shared-patterns
I want frontmatter modules to match the content modules on disk
So that progressive loading includes all documented patterns.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parents[3] / "skills" / "shared-patterns"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"

# Modules the body prose describes as the core content of this skill.
CONTENT_MODULES = {
    "validation-patterns.md",
    "error-handling.md",
    "testing-templates.md",
    "workflow-patterns.md",
}


def _frontmatter_modules() -> list[str]:
    text = SKILL_FILE.read_text(encoding="utf-8")
    fm_end = text.find("\n---\n", 4)
    fm = text[4:fm_end] + "\n"  # ensure trailing newline for last-line regex match
    block = re.search(r"^modules:\n((?:- .+\n)+)", fm, re.MULTILINE)
    if not block:
        return []
    return re.findall(r"- modules/(.+)", block.group(0))


class TestSharedPatternsModuleConsistency:
    """SKILL.md frontmatter modules must be consistent with modules on disk."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self) -> None:
        """shared-patterns SKILL.md must exist."""
        assert SKILL_FILE.is_file(), f"SKILL.md missing at {SKILL_FILE}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_frontmatter_modules_exist_on_disk(self) -> None:
        """Every module declared in frontmatter must be present on disk."""
        fm_modules = _frontmatter_modules()
        assert fm_modules, "Frontmatter must declare at least one module"
        missing = [m for m in fm_modules if not (MODULES_DIR / m).is_file()]
        assert not missing, (
            f"Frontmatter declares modules that do not exist on disk: {missing}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_includes_content_modules(self) -> None:
        """Frontmatter modules must include the 4 core content modules.

        The SKILL.md body documents validation-patterns, error-handling,
        testing-templates, and workflow-patterns as the primary content.
        These must be in the frontmatter modules list so progressive loading
        includes them.
        """
        fm_set = set(_frontmatter_modules())
        missing = CONTENT_MODULES - fm_set
        assert not missing, (
            f"Frontmatter modules is missing core content modules: {sorted(missing)}\n"
            f"Currently declared: {sorted(fm_set)}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_modules_dir_files_are_declared(self) -> None:
        """All .md files in modules/ must be declared in frontmatter.

        Undeclared modules are silently skipped by progressive loading.
        """
        fm_set = set(_frontmatter_modules())
        disk_modules = {f.name for f in MODULES_DIR.glob("*.md")}
        undeclared = disk_modules - fm_set
        assert not undeclared, (
            f"Module files on disk not declared in frontmatter: {sorted(undeclared)}"
        )
