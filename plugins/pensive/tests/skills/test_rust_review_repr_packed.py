"""BDD tests for the rust-review repr-packed-audit dimension.

Feature: Rust Review Flags `#[repr(packed)]`
  As a Rust code reviewer
  I want the skill to flag `#[repr(packed)]` struct attributes
  So that authors know a borrow of a packed field produces an unaligned
    reference, which is undefined behavior; the field must be copied out
    first (or the `packed` layout reconsidered).

Research basis: the Rust Reference type-layout chapter
(rust-lang/reference src/type-layout.md) defines the `packed`
representation and warns that references to under-aligned fields are
invalid. The `unaligned_references` lint is a hard error. See
modules/repr-packed-audit.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pensive.skills.rust_review import RustReviewSkill

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
MODULE_NAME = "repr-packed-audit"


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


@pytest.mark.unit
class TestReprPackedDetector:
    """Detector: analyze_repr_packed flags packed representations."""

    def setup_method(self) -> None:
        self.skill = RustReviewSkill()

    def test_flags_repr_packed(self, mock_skill_context) -> None:
        """`#[repr(packed)]` removes field alignment padding."""
        code = "#[repr(packed)]\nstruct Header { tag: u8, len: u32 }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_repr_packed(mock_skill_context, "r.rs")[
            "repr_packed_issues"
        ]
        assert len(issues) >= 1
        assert issues[0]["line"] == 1
        assert issues[0]["clippy_lint"] == "unaligned_references"

    def test_flags_repr_c_packed(self, mock_skill_context) -> None:
        """`#[repr(C, packed)]` is still a packed layout."""
        code = "#[repr(C, packed)]\nstruct Wire { a: u8, b: u64 }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_repr_packed(mock_skill_context, "r.rs")[
            "repr_packed_issues"
        ]
        assert len(issues) >= 1

    def test_flags_repr_packed_n(self, mock_skill_context) -> None:
        """`#[repr(packed(2))]` sets a packed alignment of 2."""
        code = "#[repr(packed(2))]\nstruct P { a: u8, b: u32 }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_repr_packed(mock_skill_context, "r.rs")[
            "repr_packed_issues"
        ]
        assert len(issues) >= 1

    def test_recommends_copy_out(self, mock_skill_context) -> None:
        """The recommendation explains copying the field out first."""
        code = "#[repr(packed)]\nstruct H { a: u8, b: u32 }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_repr_packed(mock_skill_context, "r.rs")[
            "repr_packed_issues"
        ]
        rec = issues[0]["recommendation"].lower()
        assert "unaligned" in rec or "copy" in rec or "align" in rec

    def test_repr_c_only_not_flagged(self, mock_skill_context) -> None:
        """`#[repr(C)]` keeps natural alignment and is not packed."""
        code = "#[repr(C)]\nstruct Aligned { a: u8, b: u32 }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_repr_packed(mock_skill_context, "c.rs")[
            "repr_packed_issues"
        ]
        assert issues == []

    def test_repr_transparent_not_flagged(self, mock_skill_context) -> None:
        """`#[repr(transparent)]` is a single-field wrapper, not packed."""
        code = "#[repr(transparent)]\nstruct Wrap(u32);\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_repr_packed(mock_skill_context, "t.rs")[
            "repr_packed_issues"
        ]
        assert issues == []

    def test_comment_not_flagged(self, mock_skill_context) -> None:
        """A repr shown in a comment is not an attribute."""
        code = "// avoid #[repr(packed)] on this struct\nlet x = 1;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_repr_packed(mock_skill_context, "k.rs")[
            "repr_packed_issues"
        ]
        assert issues == []

    def test_wired_into_analyze(self, mock_skill_context) -> None:
        """The aggregate analyze() surfaces repr_packed info."""
        mock_skill_context.get_file_content.return_value = "#[repr(packed)]\n"
        result = self.skill.analyze(mock_skill_context, "r.rs")
        assert "repr_packed" in result.info


@pytest.mark.unit
class TestReprPackedModuleDoc:
    """The repr-packed-audit.md module documents the paradigm."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / f"{MODULE_NAME}.md").read_text()

    def test_module_file_exists(self) -> None:
        assert (MODULES_DIR / f"{MODULE_NAME}.md").exists()

    def test_frontmatter_declares_module_name(self, text: str) -> None:
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == MODULE_NAME

    def test_cites_alignment(self, text: str) -> None:
        low = text.lower()
        assert "align" in low and "unaligned" in low

    def test_documents_alternative(self, text: str) -> None:
        low = text.lower()
        assert "copy" in low

    def test_has_exit_criteria(self, text: str) -> None:
        assert "## Exit Criteria" in text


@pytest.mark.unit
class TestSkillMdWiresReprPacked:
    """SKILL.md references the new module."""

    def test_frontmatter_lists_module(self) -> None:
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert f"{MODULE_NAME}.md" in modules or MODULE_NAME in modules
