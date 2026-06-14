"""BDD tests for the rust-review idiomatic-elision dimension.

Feature: Rust Review Suggests Eliding What The Compiler Infers
  As a Rust code reviewer
  I want the skill to flag needless explicit lifetimes and trailing
    `return` statements
  So that authors lean on lifetime elision and expression-oriented
    blocks instead of writing what the compiler already infers.

Research basis: the Rust Reference lifetime-elision rules
(rust-lang/reference src/lifetime-elision.md) and block tail
expressions (src/expressions/block-expr.md); clippy::needless_lifetimes
and clippy::needless_return. See modules/idiomatic-elision.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pensive.skills.rust_review import RustReviewSkill

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
MODULE_NAME = "idiomatic-elision"


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


@pytest.mark.unit
class TestIdiomaticElisionDetector:
    """Detector: analyze_idiomatic_elision flags inferable annotations."""

    def setup_method(self) -> None:
        self.skill = RustReviewSkill()

    def test_flags_needless_single_input_lifetime(self, mock_skill_context) -> None:
        """One input reference + matching output lifetime is elidable
        (elision rule 2)."""
        code = "fn first<'a>(x: &'a str) -> &'a str { x }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_idiomatic_elision(mock_skill_context, "l.rs")[
            "idiomatic_elision_issues"
        ]
        nl = [i for i in issues if i["type"] == "needless_lifetime"]
        assert len(nl) >= 1
        assert "elid" in nl[0].get("recommendation", "").lower()

    def test_flags_needless_lifetime_on_self_receiver(self, mock_skill_context) -> None:
        """`&'a self` with a matching output lifetime is elidable
        (elision rule 3)."""
        code = "fn name<'a>(&'a self) -> &'a str { self.name }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_idiomatic_elision(mock_skill_context, "s.rs")[
            "idiomatic_elision_issues"
        ]
        assert any(i["type"] == "needless_lifetime" for i in issues)

    def test_two_shared_input_lifetimes_not_flagged(self, mock_skill_context) -> None:
        """Two inputs tied to the same lifetime cannot be elided; the
        explicit annotation is load-bearing and must not be flagged."""
        code = "fn longest<'a>(x: &'a str, y: &'a str) -> &'a str { x }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_idiomatic_elision(mock_skill_context, "g.rs")[
            "idiomatic_elision_issues"
        ]
        assert all(i["type"] != "needless_lifetime" for i in issues)

    def test_already_elided_signature_not_flagged(self, mock_skill_context) -> None:
        """An already-elided signature produces no lifetime finding."""
        code = "fn first(x: &str) -> &str { x }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_idiomatic_elision(mock_skill_context, "e.rs")[
            "idiomatic_elision_issues"
        ]
        assert all(i["type"] != "needless_lifetime" for i in issues)

    def test_type_param_signature_not_flagged(self, mock_skill_context) -> None:
        """A signature with a type param alongside the lifetime is the
        conservative skip case (bounds may force the annotation)."""
        code = "fn f<'a, T>(x: &'a T) -> &'a T { x }\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_idiomatic_elision(mock_skill_context, "t.rs")[
            "idiomatic_elision_issues"
        ]
        assert all(i["type"] != "needless_lifetime" for i in issues)

    def test_flags_trailing_return(self, mock_skill_context) -> None:
        """A `return <expr>;` as the block's last statement is needless."""
        code = "fn add(a: i32, b: i32) -> i32 {\n    return a + b;\n}\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_idiomatic_elision(mock_skill_context, "r.rs")[
            "idiomatic_elision_issues"
        ]
        nr = [i for i in issues if i["type"] == "needless_return"]
        assert len(nr) >= 1
        assert nr[0]["line"] == 2

    def test_early_return_not_flagged(self, mock_skill_context) -> None:
        """An early guard `return` (not the block tail) is control flow,
        not a needless trailing return."""
        code = (
            "fn f(x: i32) -> i32 {\n"
            "    if x < 0 {\n"
            "        return 0;\n"
            "    }\n"
            "    x * 2\n"
            "}\n"
        )
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_idiomatic_elision(mock_skill_context, "f.rs")[
            "idiomatic_elision_issues"
        ]
        assert all(i["type"] != "needless_return" for i in issues)

    def test_trailing_return_flagged_with_following_item(
        self, mock_skill_context
    ) -> None:
        """A tail return is still flagged when another item follows the
        function (the common multi-function-file case)."""
        code = (
            "fn first(x: i32) -> i32 {\n"
            "    return x;\n"
            "}\n"
            "\n"
            "fn second(y: i32) -> i32 {\n"
            "    y\n"
            "}\n"
        )
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_idiomatic_elision(mock_skill_context, "m.rs")[
            "idiomatic_elision_issues"
        ]
        nr = [i for i in issues if i["type"] == "needless_return"]
        assert len(nr) == 1
        assert nr[0]["line"] == 2

    def test_early_return_before_more_statements_not_flagged(
        self, mock_skill_context
    ) -> None:
        """A guard return followed by more body statements, in a file
        with a following function, is still not flagged."""
        code = (
            "fn f(x: i32) -> i32 {\n"
            "    if x < 0 {\n"
            "        return 0;\n"
            "    }\n"
            "    x * 2\n"
            "}\n"
            "\n"
            "fn g() {}\n"
        )
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_idiomatic_elision(mock_skill_context, "f.rs")[
            "idiomatic_elision_issues"
        ]
        assert all(i["type"] != "needless_return" for i in issues)

    def test_guard_return_before_comment_not_flagged(self, mock_skill_context) -> None:
        """A guard `return` whose continuation begins with a comment is still
        an early return, not a needless tail return. The comment precedes the
        happy-path statement, so it must not be read as an item boundary
        (PR #577 finding I1)."""
        code = (
            "fn f(x: i32) -> i32 {\n"
            "    if x < 0 {\n"
            "        return 0;\n"
            "    }\n"
            "    // compute the positive case\n"
            "    x * 2\n"
            "}\n"
        )
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_idiomatic_elision(mock_skill_context, "f.rs")[
            "idiomatic_elision_issues"
        ]
        assert all(i["type"] != "needless_return" for i in issues)

    def test_tail_return_before_doc_comment_and_item_flagged(
        self, mock_skill_context
    ) -> None:
        """Characterization: a tail return before a doc comment stays flagged.

        This pins true-positive detection so the comment-skipping in the I1
        fix cannot silently suppress a real tail return. It is NOT a revert
        test for I1: both the pre- and post-fix code flag this input (the old
        code stops at `///` as a boundary; the new code skips `///` and stops
        at `fn second`). The discriminating revert test for I1 is
        test_guard_return_before_comment_not_flagged above, which fails on
        revert. This one is a forward over-correction guard."""
        code = (
            "fn first(x: i32) -> i32 {\n"
            "    return x;\n"
            "}\n"
            "/// docs for second\n"
            "fn second() {}\n"
        )
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_idiomatic_elision(mock_skill_context, "m.rs")[
            "idiomatic_elision_issues"
        ]
        nr = [i for i in issues if i["type"] == "needless_return"]
        assert len(nr) == 1
        assert nr[0]["line"] == 2

    def test_wired_into_analyze(self, mock_skill_context) -> None:
        """The aggregate analyze() surfaces idiomatic_elision info."""
        mock_skill_context.get_file_content.return_value = (
            "fn first<'a>(x: &'a str) -> &'a str { x }\n"
        )
        result = self.skill.analyze(mock_skill_context, "l.rs")
        assert "idiomatic_elision" in result.info


@pytest.mark.unit
class TestIdiomaticElisionModuleDoc:
    """The idiomatic-elision.md module documents the paradigms."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / f"{MODULE_NAME}.md").read_text()

    def test_module_file_exists(self) -> None:
        assert (MODULES_DIR / f"{MODULE_NAME}.md").exists()

    def test_frontmatter_declares_module_name(self, text: str) -> None:
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == MODULE_NAME

    def test_covers_lifetime_elision(self, text: str) -> None:
        low = text.lower()
        assert "lifetime elision" in low
        assert "needless_lifetimes" in text

    def test_covers_needless_return(self, text: str) -> None:
        low = text.lower()
        assert "needless_return" in text
        assert "tail expression" in low or "trailing return" in low

    def test_covers_anonymous_lifetime(self, text: str) -> None:
        """The `'_` placeholder is the reference's preferred form in paths."""
        assert "'_" in text

    def test_documents_exclusions(self, text: str) -> None:
        low = text.lower()
        assert "exclusion" in low or "not flag" in low or "load-bearing" in low


@pytest.mark.unit
class TestSkillMdWiresIdiomaticElision:
    """SKILL.md references the new module."""

    def test_frontmatter_lists_module(self) -> None:
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert f"{MODULE_NAME}.md" in modules or MODULE_NAME in modules
