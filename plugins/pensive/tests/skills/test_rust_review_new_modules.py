"""BDD tests for new rust-review modules added per AI Slop Playbook.

Feature: Rust Review Covers Model-Specific Tells, Iterator/Allocation
  Slop, Test Slop, Async Slop
  As a Rust code reviewer
  I want the rust-review skill to enforce the playbook's §4 anti-patterns
  So that AI-generated Rust slop is caught alongside safety/concurrency.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"

NEW_MODULES = [
    "model-specific-tells",
    "iterator-and-allocation-slop",
    "test-slop",
    "async-slop",
]


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestNewRustReviewModulesExist:
    """Feature: All four new modules exist on disk."""

    @pytest.mark.unit
    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_module_file_exists(self, module: str) -> None:
        """Each new module must exist as a .md file."""
        path = MODULES_DIR / f"{module}.md"
        assert path.exists(), f"Expected module at {path}"

    @pytest.mark.unit
    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_module_has_frontmatter(self, module: str) -> None:
        """Each new module must begin with YAML frontmatter."""
        text = (MODULES_DIR / f"{module}.md").read_text()
        assert text.startswith("---"), f"{module}.md must begin with YAML frontmatter"

    @pytest.mark.unit
    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_frontmatter_lists_module_name(self, module: str) -> None:
        """Frontmatter must declare the module name."""
        text = (MODULES_DIR / f"{module}.md").read_text()
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == module, f"Frontmatter `module:` must be '{module}'"


class TestSkillMdWiresInNewModules:
    """Feature: SKILL.md frontmatter references the new modules."""

    @pytest.fixture
    def skill_text(self) -> str:
        return SKILL_FILE.read_text()

    @pytest.mark.unit
    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_frontmatter_lists_new_module(self, skill_text: str, module: str) -> None:
        """Each new module must appear in frontmatter `modules:` list."""
        fm = _parse_frontmatter(skill_text)
        modules = fm.get("modules", [])
        # Modules in pensive frontmatter use .md suffix
        assert f"{module}.md" in modules or module in modules, (
            f"rust-review frontmatter must list '{module}'"
        )


class TestModelSpecificTellsModule:
    """Feature: model-specific-tells covers GPT vs Claude vs Gemini."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / "model-specific-tells.md").read_text()

    @pytest.mark.unit
    def test_covers_gpt_fabrication(self, text: str) -> None:
        """Module must address GPT's fabrication tendency."""
        text_lower = text.lower()
        assert "gpt" in text_lower
        assert "fabricate" in text_lower or "fabrication" in text_lower

    @pytest.mark.unit
    def test_covers_claude_omission(self, text: str) -> None:
        """Module must address Claude's omission tendency."""
        text_lower = text.lower()
        assert "claude" in text_lower
        assert "omit" in text_lower or "omission" in text_lower

    @pytest.mark.unit
    def test_covers_gemini_control_flow(self, text: str) -> None:
        """Module must address Gemini's control-flow tendency."""
        text_lower = text.lower()
        assert "gemini" in text_lower
        assert "control" in text_lower or "off-by-one" in text_lower

    @pytest.mark.unit
    def test_covers_reasoning_mode_verbosity(self, text: str) -> None:
        """Module must address reasoning-mode verbosity scaling."""
        text_lower = text.lower()
        assert "thinking" in text_lower or "reasoning" in text_lower
        assert "verbose" in text_lower or "verbosity" in text_lower


class TestIteratorAndAllocationModule:
    """Feature: iterator-and-allocation-slop covers AI-frequent patterns."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / "iterator-and-allocation-slop.md").read_text()

    @pytest.mark.unit
    def test_covers_clone_borrow_checker(self, text: str) -> None:
        """Module must cover .clone() to satisfy borrow checker."""
        text_lower = text.lower()
        assert "clone" in text_lower
        assert "borrow checker" in text_lower or ("borrow-checker" in text_lower)

    @pytest.mark.unit
    def test_covers_index_loops(self, text: str) -> None:
        """Module must cover index-based loops vs iterators."""
        text_lower = text.lower()
        assert "needless_range_loop" in text_lower or "0..vec.len()" in text

    @pytest.mark.unit
    def test_covers_clippy_lints(self, text: str) -> None:
        """Module must reference specific clippy lints."""
        for lint in [
            "redundant_clone",
            "ptr_arg",
            "needless_collect",
        ]:
            assert lint in text, f"Module must reference clippy::{lint}"


class TestTestSlopModule:
    """Feature: test-slop covers AI-generated test failure modes."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / "test-slop.md").read_text()

    @pytest.mark.unit
    def test_covers_it_works_default(self, text: str) -> None:
        """Module must cover the it_works cargo-new default."""
        text_lower = text.lower()
        assert "it_works" in text_lower

    @pytest.mark.unit
    def test_covers_tautological_tests(self, text: str) -> None:
        """Module must cover tautological assertions."""
        text_lower = text.lower()
        assert "tautolog" in text_lower

    @pytest.mark.unit
    def test_covers_mock_everything(self, text: str) -> None:
        """Module must cover mock-everything tests."""
        text_lower = text.lower()
        assert "mock" in text_lower

    @pytest.mark.unit
    def test_recommends_mutation_testing(self, text: str) -> None:
        """Module must recommend cargo-mutants."""
        text_lower = text.lower()
        assert "mutant" in text_lower or "mutation" in text_lower


class TestAsyncSlopModule:
    """Feature: async-slop covers async/tokio anti-patterns."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / "async-slop.md").read_text()

    @pytest.mark.unit
    def test_covers_async_fn_without_await(self, text: str) -> None:
        """Module must cover async fn that doesn't await."""
        text_lower = text.lower()
        assert "async fn" in text_lower
        assert ".await" in text_lower or "no .await" in text_lower

    @pytest.mark.unit
    def test_covers_blocking_in_async(self, text: str) -> None:
        """Module must cover blocking I/O in async runtime."""
        text_lower = text.lower()
        assert "blocking" in text_lower
        assert "spawn_blocking" in text_lower or "tokio::fs" in text_lower

    @pytest.mark.unit
    def test_covers_mutexguard_across_await(self, text: str) -> None:
        """Module must cover MutexGuard held across .await."""
        text_lower = text.lower()
        assert "mutexguard" in text_lower or (
            "mutex" in text_lower and "await" in text_lower
        )

    @pytest.mark.unit
    def test_marks_mutexguard_as_high_severity(self, text: str) -> None:
        """The MutexGuard-across-await pattern must be flagged high-risk."""
        text_lower = text.lower()
        assert "deadlock" in text_lower or "high" in text_lower
