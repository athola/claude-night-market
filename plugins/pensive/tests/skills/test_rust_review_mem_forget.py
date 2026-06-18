"""BDD tests for the rust-review mem-forget-audit dimension.

Feature: Rust Review Flags Skipped and No-op Destructors
  As a Rust code reviewer
  I want the skill to flag `mem::forget(x)` (which skips a destructor and
    leaks the resource) and `drop(&x)` (which drops a reference and is a
    no-op, so the value still lives)
  So that authors use `ManuallyDrop`, a real owning `drop`, or scope
    instead of silently leaking or no-op'ing cleanup.

Research basis: the Rust Reference destructors chapter
(rust-lang/reference src/destructors.md) explains that `mem::forget`
skips the destructor and that dropping runs on the owned value, not a
borrow. clippy::mem_forget, clippy::drop_ref. See
modules/mem-forget-audit.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pensive.skills.rust_review import RustReviewSkill

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
MODULE_NAME = "mem-forget-audit"


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


@pytest.mark.unit
class TestMemForgetDetector:
    """Detector: analyze_mem_forget flags forget and no-op drops."""

    def setup_method(self) -> None:
        self.skill = RustReviewSkill()

    def test_flags_mem_forget(self, mock_skill_context) -> None:
        """`mem::forget(guard)` skips the destructor and leaks."""
        code = "mem::forget(guard);\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_mem_forget(mock_skill_context, "m.rs")[
            "mem_forget_issues"
        ]
        fg = [i for i in issues if i["type"] == "mem_forget"]
        assert len(fg) >= 1
        assert fg[0]["line"] == 1
        assert fg[0]["clippy_lint"] == "clippy::mem_forget"

    def test_flags_imported_forget(self, mock_skill_context) -> None:
        """An unqualified `forget(x)` (imported) is the same call."""
        code = "forget(handle);\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_mem_forget(mock_skill_context, "m.rs")[
            "mem_forget_issues"
        ]
        assert any(i["type"] == "mem_forget" for i in issues)

    def test_flags_drop_of_reference(self, mock_skill_context) -> None:
        """`drop(&x)` drops a borrow: a no-op, the value still lives."""
        code = "drop(&resource);\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_mem_forget(mock_skill_context, "d.rs")[
            "mem_forget_issues"
        ]
        nr = [i for i in issues if i["type"] == "drop_ref"]
        assert len(nr) >= 1
        assert nr[0]["clippy_lint"] == "clippy::drop_ref"

    def test_method_forget_not_flagged(self, mock_skill_context) -> None:
        """A method `cache.forget(key)` is not `mem::forget`."""
        code = "cache.forget(key);\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_mem_forget(mock_skill_context, "m.rs")[
            "mem_forget_issues"
        ]
        assert issues == []

    def test_owning_drop_not_flagged(self, mock_skill_context) -> None:
        """`drop(value)` on an owned value is the correct idiom."""
        code = "drop(value);\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_mem_forget(mock_skill_context, "d.rs")[
            "mem_forget_issues"
        ]
        assert [i for i in issues if i["type"] == "drop_ref"] == []

    def test_comment_not_flagged(self, mock_skill_context) -> None:
        """A forget shown in a comment is not code."""
        code = "// do not mem::forget(guard) here\nlet x = 1;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_mem_forget(mock_skill_context, "m.rs")[
            "mem_forget_issues"
        ]
        assert issues == []

    def test_wired_into_analyze(self, mock_skill_context) -> None:
        """The aggregate analyze() surfaces mem_forget info."""
        mock_skill_context.get_file_content.return_value = "mem::forget(g);\n"
        result = self.skill.analyze(mock_skill_context, "m.rs")
        assert "mem_forget" in result.info


@pytest.mark.unit
class TestMemForgetModuleDoc:
    """The mem-forget-audit.md module documents the paradigm."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / f"{MODULE_NAME}.md").read_text()

    def test_module_file_exists(self) -> None:
        assert (MODULES_DIR / f"{MODULE_NAME}.md").exists()

    def test_frontmatter_declares_module_name(self, text: str) -> None:
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == MODULE_NAME

    def test_cites_destructor(self, text: str) -> None:
        low = text.lower()
        assert "destructor" in low or "drop" in low

    def test_documents_alternative(self, text: str) -> None:
        assert "ManuallyDrop" in text

    def test_has_exit_criteria(self, text: str) -> None:
        assert "## Exit Criteria" in text


@pytest.mark.unit
class TestSkillMdWiresMemForget:
    """SKILL.md references the new module."""

    def test_frontmatter_lists_module(self) -> None:
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert f"{MODULE_NAME}.md" in modules or MODULE_NAME in modules
