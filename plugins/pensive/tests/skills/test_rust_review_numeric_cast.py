"""BDD tests for the rust-review numeric-cast-safety dimension.

Feature: Rust Review Flags Lossy `as` Casts
  As a Rust code reviewer
  I want the skill to flag `as` casts that truncate a size/length or
    narrow to a byte, and precision-losing casts to `f32`
  So that authors reach for `TryFrom`/`try_into` (fallible) or
    `From`/`into` (lossless) instead of silently wrapping values.

Research basis: the Rust Reference type-cast rules
(rust-lang/reference src/expressions/operator-expr.md): "Casting from
a larger integer to a smaller integer (e.g. u32 -> u8) will truncate";
float-to-int saturates and `NaN` maps to 0. clippy::cast_possible_truncation
and clippy::cast_precision_loss. See modules/numeric-cast-safety.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pensive.skills.rust_review import RustReviewSkill

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
MODULE_NAME = "numeric-cast-safety"


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


@pytest.mark.unit
class TestNumericCastDetector:
    """Detector: analyze_numeric_cast_safety flags lossy casts."""

    def setup_method(self) -> None:
        self.skill = RustReviewSkill()

    def test_flags_len_cast_to_narrower_int(self, mock_skill_context) -> None:
        """`.len() as u32` truncates a usize length and is flagged."""
        code = "fn n(v: &[u8]) -> u32 { v.len() as u32 }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_numeric_cast_safety(mock_skill_context, "c.rs")[
            "numeric_cast_issues"
        ]
        lt = [i for i in issues if i["type"] == "length_truncation_cast"]
        assert len(lt) >= 1
        assert "try_from" in lt[0]["recommendation"].lower()
        assert lt[0]["clippy_lint"] == "clippy::cast_possible_truncation"

    def test_flags_count_cast_to_i32(self, mock_skill_context) -> None:
        """`.count() as i32` is the same usize-truncation shape."""
        code = "let c = it.count() as i32;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_numeric_cast_safety(mock_skill_context, "c.rs")[
            "numeric_cast_issues"
        ]
        assert any(i["type"] == "length_truncation_cast" for i in issues)

    def test_flags_narrowing_to_byte(self, mock_skill_context) -> None:
        """`as u8` targets the smallest type, so it cannot widen."""
        code = "let b = value as u8;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_numeric_cast_safety(mock_skill_context, "b.rs")[
            "numeric_cast_issues"
        ]
        nb = [i for i in issues if i["type"] == "narrowing_to_byte_cast"]
        assert len(nb) >= 1
        assert nb[0]["line"] == 1

    def test_flags_precision_loss_to_f32(self, mock_skill_context) -> None:
        """`as f32` can lose precision from f64/i64 sources."""
        code = "let r = total as f32;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_numeric_cast_safety(mock_skill_context, "f.rs")[
            "numeric_cast_issues"
        ]
        pl = [i for i in issues if i["type"] == "precision_loss_cast"]
        assert len(pl) >= 1
        assert pl[0]["clippy_lint"] == "clippy::cast_precision_loss"

    def test_widening_to_usize_not_flagged(self, mock_skill_context) -> None:
        """`as usize` is the common widening/index cast and is safe."""
        code = "let i = byte as usize;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_numeric_cast_safety(mock_skill_context, "u.rs")[
            "numeric_cast_issues"
        ]
        assert issues == []

    def test_pointer_cast_not_flagged(self, mock_skill_context) -> None:
        """`as *const T` / `as *mut T` are pointer casts, not numeric."""
        code = "let p = data as *const u8;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_numeric_cast_safety(mock_skill_context, "p.rs")[
            "numeric_cast_issues"
        ]
        assert issues == []

    def test_comment_not_flagged(self, mock_skill_context) -> None:
        """A cast mentioned in a comment is not code."""
        code = "// avoid value as u8 here\nlet x = 1;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_numeric_cast_safety(mock_skill_context, "k.rs")[
            "numeric_cast_issues"
        ]
        assert issues == []

    def test_wired_into_analyze(self, mock_skill_context) -> None:
        """The aggregate analyze() surfaces numeric_cast info."""
        mock_skill_context.get_file_content.return_value = "let b = x as u8;\n"
        result = self.skill.analyze(mock_skill_context, "c.rs")
        assert "numeric_cast" in result.info


@pytest.mark.unit
class TestNumericCastModuleDoc:
    """The numeric-cast-safety.md module documents the paradigm."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / f"{MODULE_NAME}.md").read_text()

    def test_module_file_exists(self) -> None:
        assert (MODULES_DIR / f"{MODULE_NAME}.md").exists()

    def test_frontmatter_declares_module_name(self, text: str) -> None:
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == MODULE_NAME

    def test_cites_truncation(self, text: str) -> None:
        low = text.lower()
        assert "truncat" in low
        assert "cast_possible_truncation" in text

    def test_documents_try_from_alternative(self, text: str) -> None:
        assert "try_from" in text.lower() or "try_into" in text.lower()

    def test_documents_exclusions(self, text: str) -> None:
        low = text.lower()
        assert "usize" in low and ("not flag" in low or "exclu" in low)

    def test_has_exit_criteria(self, text: str) -> None:
        assert "## Exit Criteria" in text


@pytest.mark.unit
class TestSkillMdWiresNumericCast:
    """SKILL.md references the new module."""

    def test_frontmatter_lists_module(self) -> None:
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert f"{MODULE_NAME}.md" in modules or MODULE_NAME in modules
