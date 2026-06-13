"""BDD tests for the rust-review mutable-static-audit dimension.

Feature: Rust Review Flags Mutable Global State
  As a Rust code reviewer
  I want the skill to flag `static mut` declarations
  So that authors replace shared mutable globals with `OnceLock`,
    `LazyLock`, atomics, or a `Mutex` instead of unsafe global state.

Research basis: the Rust Reference static items chapter
(rust-lang/reference src/items/static-items.md): "an `unsafe` block is
required when either reading or writing a mutable static variable" and
mutable statics are "a very large source of race conditions or other
bugs". Reading or writing through a `static mut` reference is the
deny-by-default `static_mut_refs` lint (Rust 2024).
See modules/mutable-static-audit.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pensive.skills.rust_review import RustReviewSkill

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
MODULE_NAME = "mutable-static-audit"


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


@pytest.mark.unit
class TestMutableStaticDetector:
    """Detector: analyze_mutable_statics flags `static mut`."""

    def setup_method(self) -> None:
        self.skill = RustReviewSkill()

    def test_flags_static_mut_declaration(self, mock_skill_context) -> None:
        """A `static mut` global is flagged with an alternative."""
        code = "static mut COUNTER: u64 = 0;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_mutable_statics(mock_skill_context, "g.rs")[
            "mutable_static_issues"
        ]
        ms = [i for i in issues if i["type"] == "mutable_static"]
        assert len(ms) == 1
        assert ms[0]["line"] == 1
        rec = ms[0]["recommendation"].lower()
        assert "oncelock" in rec or "atomic" in rec or "mutex" in rec
        assert ms[0]["clippy_lint"] == "static_mut_refs"

    def test_flags_pub_static_mut(self, mock_skill_context) -> None:
        """Visibility modifiers before `static mut` still match."""
        code = "pub static mut REGISTRY: *mut u8 = core::ptr::null_mut();\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_mutable_statics(mock_skill_context, "p.rs")[
            "mutable_static_issues"
        ]
        assert any(i["type"] == "mutable_static" for i in issues)

    def test_immutable_static_not_flagged(self, mock_skill_context) -> None:
        """A plain immutable `static` is safe and is not flagged."""
        code = "static MAX: u64 = 100;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_mutable_statics(mock_skill_context, "i.rs")[
            "mutable_static_issues"
        ]
        assert issues == []

    def test_const_not_flagged(self, mock_skill_context) -> None:
        """A `const` is not a static and is not flagged."""
        code = "const MAX: u64 = 100;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_mutable_statics(mock_skill_context, "c.rs")[
            "mutable_static_issues"
        ]
        assert issues == []

    def test_comment_not_flagged(self, mock_skill_context) -> None:
        """`static mut` mentioned in a comment is not a declaration."""
        code = "// never use static mut COUNTER here\nstatic MAX: u8 = 1;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_mutable_statics(mock_skill_context, "k.rs")[
            "mutable_static_issues"
        ]
        assert issues == []

    def test_wired_into_analyze(self, mock_skill_context) -> None:
        """The aggregate analyze() surfaces mutable_statics info."""
        mock_skill_context.get_file_content.return_value = (
            "static mut COUNTER: u64 = 0;\n"
        )
        result = self.skill.analyze(mock_skill_context, "g.rs")
        assert "mutable_statics" in result.info


@pytest.mark.unit
class TestMutableStaticModuleDoc:
    """The mutable-static-audit.md module documents the paradigm."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / f"{MODULE_NAME}.md").read_text()

    def test_module_file_exists(self) -> None:
        assert (MODULES_DIR / f"{MODULE_NAME}.md").exists()

    def test_frontmatter_declares_module_name(self, text: str) -> None:
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == MODULE_NAME

    def test_cites_unsafe_and_race(self, text: str) -> None:
        low = text.lower()
        assert "unsafe" in low
        assert "race" in low

    def test_documents_alternatives(self, text: str) -> None:
        low = text.lower()
        assert "oncelock" in low or "lazylock" in low
        assert "atomic" in low

    def test_cites_static_mut_refs_lint(self, text: str) -> None:
        assert "static_mut_refs" in text

    def test_has_exit_criteria(self, text: str) -> None:
        assert "## Exit Criteria" in text


@pytest.mark.unit
class TestSkillMdWiresMutableStatic:
    """SKILL.md references the new module."""

    def test_frontmatter_lists_module(self) -> None:
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert f"{MODULE_NAME}.md" in modules or MODULE_NAME in modules
