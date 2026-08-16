"""BDD tests for the memory-allocation review lenses (issue #599).

Feature: Performance Review Adds Manual Memory-Allocation Lenses
  As a performance reviewer
  I want three manual review lenses (unbounded external-source
  collections, hot-path recompute, serial blocking I/O over unbounded
  sets) documented and wired into the performance-review skill
  So that patterns which pass unit tests but blow up on large inputs
  are caught by a review lens.

These lenses are documentation, not AST detectors, so no visitor test
applies. Following the precedent in test_rust_review_new_modules.py,
these tests assert the module's existence, frontmatter, SKILL.md
wiring, and content contract.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PENSIVE_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = PENSIVE_ROOT / "skills" / "performance-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
LENSES_MODULE = MODULES_DIR / "memory-allocation-lenses.md"

MODULE_NAME = "memory-allocation-lenses"


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


def _section(content: str, heading: str) -> str:
    """Return one markdown section, whitespace-normalized to one line.

    Slices from ``heading`` to the next heading at the same or a
    shallower depth. Normalizing collapses the 80-column prose wrap so
    assertions can quote a phrase without knowing where it breaks.
    """
    start = content.index(heading)
    depth = len(heading) - len(heading.lstrip("#"))
    rest = content[start + len(heading) :]
    end = len(rest)
    for line_start, line in _line_offsets(rest):
        stripped = line.lstrip("#")
        if line.startswith("#") and len(line) - len(stripped) <= depth:
            end = line_start
            break
    return " ".join((heading + rest[:end]).split())


def _line_offsets(text: str):
    """Yield ``(offset, line)`` for every line in ``text``."""
    offset = 0
    for line in text.splitlines(keepends=True):
        yield offset, line
        offset += len(line)


class TestMemoryLensesModuleExists:
    """Feature: the module exists and declares itself correctly."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_file_exists(self) -> None:
        """The memory-allocation-lenses module must exist on disk."""
        assert LENSES_MODULE.exists(), f"Expected module at {LENSES_MODULE}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_has_frontmatter(self) -> None:
        """The module must begin with YAML frontmatter."""
        assert LENSES_MODULE.read_text().startswith("---")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_declares_module_name(self) -> None:
        """
        Scenario: frontmatter follows the sibling `module:` convention
        Given the module frontmatter
        When it is parsed
        Then `module:` is the module name and parent_skill is set
        """
        fm = _parse_frontmatter(LENSES_MODULE.read_text())
        assert fm.get("module") == MODULE_NAME
        assert fm.get("parent_skill") == "performance-review"


class TestSkillMdWiresInMemoryLenses:
    """Feature: performance-review SKILL.md references the module."""

    @pytest.fixture
    def skill_text(self) -> str:
        return SKILL_FILE.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_lists_module(self, skill_text: str) -> None:
        """
        Scenario: the module appears in SKILL.md frontmatter modules list
        Given performance-review SKILL.md
        When its `modules:` list is read
        Then the memory-allocation-lenses module is present
        """
        fm = _parse_frontmatter(skill_text)
        modules = fm.get("modules", [])
        assert f"modules/{MODULE_NAME}.md" in modules

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_workflow_references_manual_lenses(self, skill_text: str) -> None:
        """
        Scenario: the workflow tells the reviewer to apply the lenses
        Given performance-review SKILL.md
        When the scan step is read
        Then it references applying the manual lenses alongside the scan

        The assertion anchors on the Step-2 instruction sentence rather
        than the bare module name. The module name also appears in the
        frontmatter list and the Supporting Modules table, and the word
        "manual" pre-dates this wiring elsewhere in the file, so an
        assertion on either alone survives deleting the instruction it
        is supposed to guard.
        """
        step_two = _section(skill_text, "### Step 2:")
        assert "modules/memory-allocation-lenses.md" in step_two, (
            "Step 2 no longer tells the reviewer to load the lenses module"
        )
        assert "apply its three" in step_two, (
            "Step 2 no longer instructs applying the three manual lenses"
        )
        for lens in (
            "unbounded external-source collections",
            "hot-path recompute",
            "serial blocking I/O",
        ):
            assert lens in step_two, f"Step 2 no longer names the {lens!r} lens"


class TestMemoryLensesContent:
    """Feature: the module documents all three lenses and the caveat."""

    @pytest.fixture
    def text(self) -> str:
        return LENSES_MODULE.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_unbounded_collection_lens(self, text: str) -> None:
        """Lens 1: unbounded collection fed from an external source."""
        lower = text.lower()
        assert "unbounded collection" in lower
        assert "external" in lower
        # Fix shape names a MAX_* cap constant.
        assert "max_" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_hot_path_recompute_lens(self, text: str) -> None:
        """Lens 2: hot-path recompute memoized behind a generation counter."""
        lower = text.lower()
        assert "recompute" in lower
        assert "generation counter" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_serial_blocking_io_lens(self, text: str) -> None:
        """Lens 3: serial blocking I/O over an unbounded set."""
        lower = text.lower()
        assert "blocking" in lower
        assert "buffer_unordered" in lower
        assert "timeout" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_states_growth_mode_caveat(self, text: str) -> None:
        """
        Scenario: findings must distinguish growth from churn
        Given the caveats section
        When it is read
        Then persistent unbounded growth is distinguished from
        transient per-frame churn
        """
        lower = text.lower()
        assert "persistent" in lower
        assert "churn" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_documents_lenses_not_detectors(self, text: str) -> None:
        """
        Scenario: the module is explicit that these are review lenses
        Given the module
        When it is read
        Then it states the lenses are manual, not AST detectors
        """
        lower = text.lower()
        assert "not" in lower and "detector" in lower
