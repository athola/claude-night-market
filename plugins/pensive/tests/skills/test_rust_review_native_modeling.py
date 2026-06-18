"""BDD tests for the rust-review native-type-modeling dimension.

Feature: Rust Review Suggests Porting To Native Type Primitives
  As a Rust code reviewer
  I want the rust-review skill to flag stringly-typed comparisons
    and boolean-blind signatures
  So that authors model state with enums the compiler checks
    instead of bare strings and boolean flags.

Research basis: corrode.dev "Using Enums to Represent State",
thoughtbot "Booleans and Enums", clippy::match_like_matches_macro,
and the "make invalid states unrepresentable" lineage
(Minsky/Wlaschin/King). See modules/native-type-modeling.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pensive.skills.rust_review import RustReviewSkill

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
MODULE_NAME = "native-type-modeling"


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


@pytest.mark.unit
class TestNativeTypeModelingDetector:
    """Detector: analyze_native_type_modeling flags porting opportunities."""

    def setup_method(self) -> None:
        self.skill = RustReviewSkill()

    def test_flags_stringly_typed_equality(self, mock_skill_context) -> None:
        """Given an identifier compared to a string literal,
        the skill suggests an enum + matches!."""
        code = """
        fn is_active(status: &str) -> bool {
            status == "active"
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_native_type_modeling(
            mock_skill_context, "status.rs"
        )
        assert "native_type_modeling_issues" in result
        issues = result["native_type_modeling_issues"]
        kinds = {i["type"] for i in issues}
        assert "stringly_typed_comparison" in kinds
        # Recommendation must steer toward enums.
        rec = " ".join(i.get("recommendation", "") for i in issues).lower()
        assert "enum" in rec

    def test_flags_stringly_typed_inequality(self, mock_skill_context) -> None:
        """Given a `!=` string-literal comparison, the skill flags it."""
        code = 'fn f(mode: &str) -> bool { mode != "fast" }\n'
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_native_type_modeling(mock_skill_context, "m.rs")[
            "native_type_modeling_issues"
        ]
        assert any(i["type"] == "stringly_typed_comparison" for i in issues)

    def test_empty_string_comparison_not_flagged(self, mock_skill_context) -> None:
        """Comparison to "" is an emptiness check, not a stringly-typed
        enum candidate; it must not be flagged here."""
        code = 'fn f(s: &str) -> bool { s == "" }\n'
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_native_type_modeling(mock_skill_context, "e.rs")[
            "native_type_modeling_issues"
        ]
        assert all(i["type"] != "stringly_typed_comparison" for i in issues)

    def test_flags_boolean_blindness_two_bool_params(self, mock_skill_context) -> None:
        """Given a fn with two bool params, the skill flags boolean
        blindness and recommends enums."""
        code = "fn paint(immediate: bool, antialias: bool) {}\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_native_type_modeling(mock_skill_context, "draw.rs")[
            "native_type_modeling_issues"
        ]
        bb = [i for i in issues if i["type"] == "boolean_blindness"]
        assert len(bb) >= 1
        assert "enum" in bb[0].get("recommendation", "").lower()

    def test_single_bool_param_not_flagged(self, mock_skill_context) -> None:
        """A single, self-evident bool param is idiomatic and must not
        be flagged as boolean blindness."""
        code = "fn set_visible(visible: bool) {}\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_native_type_modeling(mock_skill_context, "ui.rs")[
            "native_type_modeling_issues"
        ]
        assert all(i["type"] != "boolean_blindness" for i in issues)

    def test_clean_code_yields_no_issues(self, mock_skill_context) -> None:
        """Idiomatic enum-based code produces no native-modeling issues."""
        code = """
        enum Status { Active, Suspended }
        fn is_active(s: Status) -> bool { matches!(s, Status::Active) }
        """
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_native_type_modeling(mock_skill_context, "ok.rs")[
            "native_type_modeling_issues"
        ]
        assert issues == []

    def test_wired_into_analyze(self, mock_skill_context) -> None:
        """The aggregate analyze() surfaces native_type_modeling info."""
        mock_skill_context.get_file_content.return_value = (
            'fn f(s: &str) -> bool { s == "on" }\n'
        )
        result = self.skill.analyze(mock_skill_context, "f.rs")
        assert "native_type_modeling" in result.info

    def test_flags_integer_state_constant(self, mock_skill_context) -> None:
        """Given a named integer state constant, the skill suggests an
        enum (C-style integer discriminants are a missing enum)."""
        code = "const STATUS_ACTIVE: u8 = 0;\nconst STATUS_CLOSED: u8 = 1;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_native_type_modeling(mock_skill_context, "s.rs")[
            "native_type_modeling_issues"
        ]
        mc = [i for i in issues if i["type"] == "magic_number_state_constant"]
        assert len(mc) >= 2
        assert "enum" in mc[0].get("recommendation", "").lower()

    def test_flags_mode_constant_signed(self, mock_skill_context) -> None:
        """A signed integer mode constant is flagged too."""
        code = "const MODE_FAST: i32 = 2;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_native_type_modeling(mock_skill_context, "m.rs")[
            "native_type_modeling_issues"
        ]
        assert any(i["type"] == "magic_number_state_constant" for i in issues)

    def test_non_state_constant_not_flagged(self, mock_skill_context) -> None:
        """A plain config constant (no state stem) is not a missing enum."""
        code = "const MAX_RETRIES: u32 = 5;\nconst BUFFER_SIZE: usize = 4096;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_native_type_modeling(mock_skill_context, "c.rs")[
            "native_type_modeling_issues"
        ]
        assert all(i["type"] != "magic_number_state_constant" for i in issues)

    def test_bitflag_shift_constant_not_flagged(self, mock_skill_context) -> None:
        """A bitmask using a shift is a `bitflags` candidate, not an enum;
        it must not be flagged as a magic-number state constant."""
        code = "const STATE_MASK: u32 = 1 << 2;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_native_type_modeling(mock_skill_context, "b.rs")[
            "native_type_modeling_issues"
        ]
        assert all(i["type"] != "magic_number_state_constant" for i in issues)


@pytest.mark.unit
class TestNativeTypeModelingModuleDoc:
    """The native-type-modeling.md module documents the paradigms."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / f"{MODULE_NAME}.md").read_text()

    def test_module_file_exists(self) -> None:
        assert (MODULES_DIR / f"{MODULE_NAME}.md").exists()

    def test_frontmatter_declares_module_name(self, text: str) -> None:
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == MODULE_NAME

    def test_covers_enums_for_comparison(self, text: str) -> None:
        low = text.lower()
        assert "stringly" in low or "boolean blindness" in low
        assert "matches!" in text

    def test_covers_newtype_and_typestate(self, text: str) -> None:
        low = text.lower()
        assert "newtype" in low
        assert "type-state" in low or "typestate" in low

    def test_covers_derived_ordering(self, text: str) -> None:
        assert "comparison_chain" in text or "Ordering" in text

    def test_covers_integer_state_constants(self, text: str) -> None:
        """Module must document the integer-state-constant port and the
        bitflags exclusion that keeps it conservative."""
        low = text.lower()
        assert "const" in low and "discriminant" in low
        assert "bitflags" in low

    def test_credits_invariant_lineage(self, text: str) -> None:
        """Term attribution: the principle predates Rust (Minsky/Wlaschin)."""
        low = text.lower()
        assert "unrepresentable" in low
        assert "wlaschin" in low or "minsky" in low or "parse, don't validate" in low

    def test_documents_exclusions(self, text: str) -> None:
        """Module must carry the don't-over-apply guardrails."""
        low = text.lower()
        assert "exclusion" in low or "not flag" in low or "do not flag" in low
        # Storage/boundary caveat is the strongest cross-source exclusion.
        assert "boundary" in low or "storage" in low or "serializ" in low


@pytest.mark.unit
class TestSkillMdWiresNativeModeling:
    """SKILL.md references the new module."""

    def test_frontmatter_lists_module(self) -> None:
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert f"{MODULE_NAME}.md" in modules or MODULE_NAME in modules
