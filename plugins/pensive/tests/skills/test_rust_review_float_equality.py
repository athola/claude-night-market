"""BDD tests for the rust-review float-equality dimension.

Feature: Rust Review Flags Exact Float Comparison
  As a Rust code reviewer
  I want the skill to flag `==`/`!=` against a floating-point literal
  So that authors compare with a tolerance `(a - b).abs() < EPSILON`
    instead of testing IEEE-754 values for bit-exact equality, which
    rounding makes unreliable.

Research basis: the Rust Reference describes `f32`/`f64` as IEEE-754
floating-point types whose arithmetic rounds
(rust-lang/reference src/types/numeric.md). clippy::float_cmp. See
modules/float-equality.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pensive.skills.rust_review import RustReviewSkill

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
MODULE_NAME = "float-equality"


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


@pytest.mark.unit
class TestFloatEqualityDetector:
    """Detector: analyze_float_equality flags exact float comparison."""

    def setup_method(self) -> None:
        self.skill = RustReviewSkill()

    def test_flags_eq_against_float_literal(self, mock_skill_context) -> None:
        """`ratio == 1.5` tests an IEEE value for bit-exact equality."""
        code = "if ratio == 1.5 { adjust(); }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_float_equality(mock_skill_context, "f.rs")[
            "float_cmp_issues"
        ]
        assert len(issues) >= 1
        assert issues[0]["line"] == 1
        assert issues[0]["clippy_lint"] == "clippy::float_cmp"

    def test_flags_ne_against_float_literal(self, mock_skill_context) -> None:
        """`!=` against a float literal is the same hazard."""
        code = "while total != 0.0 { step(); }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_float_equality(mock_skill_context, "f.rs")[
            "float_cmp_issues"
        ]
        assert len(issues) >= 1

    def test_flags_literal_on_left(self, mock_skill_context) -> None:
        """The literal may sit on either side of the operator."""
        code = "if 3.14 == angle { snap(); }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_float_equality(mock_skill_context, "f.rs")[
            "float_cmp_issues"
        ]
        assert len(issues) >= 1

    def test_flags_suffixed_float_literal(self, mock_skill_context) -> None:
        """A type-suffixed literal `2.0f32` is still a float compare."""
        code = "let same = x == 2.0f32;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_float_equality(mock_skill_context, "f.rs")[
            "float_cmp_issues"
        ]
        assert len(issues) >= 1

    def test_recommends_tolerance(self, mock_skill_context) -> None:
        """The recommendation points at an epsilon tolerance."""
        code = "if ratio == 1.5 { adjust(); }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_float_equality(mock_skill_context, "f.rs")[
            "float_cmp_issues"
        ]
        rec = issues[0]["recommendation"].lower()
        assert "epsilon" in rec or "tolerance" in rec or "abs()" in rec

    def test_integer_comparison_not_flagged(self, mock_skill_context) -> None:
        """`count == 5` is an integer compare and is exact and fine."""
        code = "if count == 5 { done(); }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_float_equality(mock_skill_context, "i.rs")[
            "float_cmp_issues"
        ]
        assert issues == []

    def test_range_literal_not_flagged(self, mock_skill_context) -> None:
        """A range `0.0..1.0` uses `..`, not an equality operator."""
        code = "for t in 0.0..1.0 { tick(t); }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_float_equality(mock_skill_context, "r.rs")[
            "float_cmp_issues"
        ]
        assert issues == []

    def test_comment_not_flagged(self, mock_skill_context) -> None:
        """A comparison shown in a comment is not code."""
        code = "// avoid ratio == 1.5 in float code\nlet x = 1;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_float_equality(mock_skill_context, "c.rs")[
            "float_cmp_issues"
        ]
        assert issues == []

    def test_wired_into_analyze(self, mock_skill_context) -> None:
        """The aggregate analyze() surfaces float_equality info."""
        mock_skill_context.get_file_content.return_value = "let b = x == 1.5;\n"
        result = self.skill.analyze(mock_skill_context, "f.rs")
        assert "float_equality" in result.info


@pytest.mark.unit
class TestFloatEqualityModuleDoc:
    """The float-equality.md module documents the paradigm."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / f"{MODULE_NAME}.md").read_text()

    def test_module_file_exists(self) -> None:
        assert (MODULES_DIR / f"{MODULE_NAME}.md").exists()

    def test_frontmatter_declares_module_name(self, text: str) -> None:
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == MODULE_NAME

    def test_cites_float_cmp(self, text: str) -> None:
        assert "float_cmp" in text

    def test_documents_tolerance(self, text: str) -> None:
        low = text.lower()
        assert "epsilon" in low or "tolerance" in low

    def test_has_exit_criteria(self, text: str) -> None:
        assert "## Exit Criteria" in text


@pytest.mark.unit
class TestSkillMdWiresFloatEquality:
    """SKILL.md references the new module."""

    def test_frontmatter_lists_module(self) -> None:
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert f"{MODULE_NAME}.md" in modules or MODULE_NAME in modules
