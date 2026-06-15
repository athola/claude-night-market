"""BDD tests for the rust-review coercion-params dimension.

Feature: Rust Review Suggests Borrowed-Slice Params Over Owned-Type Refs
  As a Rust code reviewer
  I want the skill to flag `&String` / `&Vec<T>` / `&PathBuf` parameters
  So that authors take `&str` / `&[T]` / `&Path` instead, letting deref
    coercion accept either an owned value or a borrowed one at the call
    site (the borrowed-slice form is strictly more general).

Research basis: the Rust Reference type-coercions chapter
(rust-lang/reference src/type-coercions.md) "Coercion types" -- `&T` or
`&mut T` to `&U` when `T: Deref<Target = U>`, with function arguments
listed as a coercion site; std Deref docs (String: Deref<Target=str>,
Vec<T>: Deref<Target=[T]>); and clippy::ptr_arg. Exclusions hardened
from rust-clippy issues #8463/#9067/#8410/#9542/#13489 (Vec/String-only
methods, &mut growth, trait-fixed signatures, unused params). Note:
clippy::ptr_arg does NOT flag `&Box<T>`. See modules/coercion-params.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pensive.skills.rust_review import RustReviewSkill

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
MODULE_NAME = "coercion-params"


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


@pytest.mark.unit
class TestCoercionParamsDetector:
    """Detector: analyze_coercion_params flags owned-type ref params."""

    def setup_method(self) -> None:
        self.skill = RustReviewSkill()

    def _issues(self, mock_ctx, code: str) -> list[dict]:
        mock_ctx.get_file_content.return_value = code
        return self.skill.analyze_coercion_params(mock_ctx, "p.rs")[
            "coercion_params_issues"
        ]

    def test_flags_string_ref_param(self, mock_skill_context) -> None:
        """`&String` parameter -> recommend `&str` (deref coercion)."""
        issues = self._issues(mock_skill_context, "fn g(s: &String) {}\n")
        assert any(i["type"] == "ptr_arg" for i in issues)
        rec = next(i for i in issues if i["type"] == "ptr_arg")["recommendation"]
        assert "&str" in rec

    def test_flags_vec_ref_param(self, mock_skill_context) -> None:
        """`&Vec<T>` parameter -> recommend `&[T]`."""
        issues = self._issues(mock_skill_context, "fn g(v: &Vec<u8>) {}\n")
        assert any("&[" in i["recommendation"] for i in issues)

    def test_flags_pathbuf_ref_param(self, mock_skill_context) -> None:
        """`&PathBuf` parameter -> recommend `&Path`."""
        issues = self._issues(mock_skill_context, "fn g(p: &PathBuf) {}\n")
        assert any("&Path" in i["recommendation"] for i in issues)

    def test_each_finding_cites_ptr_arg_lint(self, mock_skill_context) -> None:
        issues = self._issues(mock_skill_context, "fn g(s: &String) {}\n")
        assert all(i["clippy_lint"] == "clippy::ptr_arg" for i in issues)

    def test_mut_string_ref_not_flagged(self, mock_skill_context) -> None:
        """`&mut String` can grow (push_str); `&mut str` cannot, so the
        owned-type ref is load-bearing (clippy issue #9542)."""
        issues = self._issues(mock_skill_context, "fn g(s: &mut String) {}\n")
        assert issues == []

    def test_mut_vec_ref_not_flagged(self, mock_skill_context) -> None:
        """`&mut Vec<T>` supports push/clear; `&mut [T]` cannot change
        length, so it must not be narrowed (clippy issue #8463)."""
        issues = self._issues(mock_skill_context, "fn g(v: &mut Vec<u8>) {}\n")
        assert issues == []

    def test_box_ref_not_flagged(self, mock_skill_context) -> None:
        """clippy::ptr_arg deliberately does not flag `&Box<T>`; neither
        does this detector (it would invent a rule clippy lacks)."""
        issues = self._issues(mock_skill_context, "fn g(b: &Box<u8>) {}\n")
        assert issues == []

    def test_already_borrowed_param_not_flagged(self, mock_skill_context) -> None:
        """`&str` / `&[T]` parameters are already the general form."""
        issues = self._issues(mock_skill_context, "fn g(s: &str, v: &[u8]) {}\n")
        assert issues == []

    def test_by_value_owned_param_not_flagged(self, mock_skill_context) -> None:
        """A by-value `String` is not a deref-coercion case at all."""
        issues = self._issues(mock_skill_context, "fn g(s: String) {}\n")
        assert issues == []

    def test_comment_not_flagged(self, mock_skill_context) -> None:
        """A signature shown in a comment is not code."""
        issues = self._issues(mock_skill_context, "// fn g(s: &String) {}\n")
        assert issues == []

    def test_reports_line_number(self, mock_skill_context) -> None:
        code = "fn a() {}\nfn g(s: &String) {}\n"
        issues = self._issues(mock_skill_context, code)
        assert any(i["line"] == 2 for i in issues)

    def test_wired_into_analyze(self, mock_skill_context) -> None:
        """The aggregate analyze() surfaces coercion_params info."""
        mock_skill_context.get_file_content.return_value = "fn g(s: &String) {}\n"
        result = self.skill.analyze(mock_skill_context, "p.rs")
        assert "coercion_params" in result.info


@pytest.mark.unit
class TestCoercionParamsModuleDoc:
    """The coercion-params.md module documents the paradigm."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / f"{MODULE_NAME}.md").read_text()

    def test_module_file_exists(self) -> None:
        assert (MODULES_DIR / f"{MODULE_NAME}.md").exists()

    def test_frontmatter_declares_module_name(self, text: str) -> None:
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == MODULE_NAME

    def test_covers_deref_coercion(self, text: str) -> None:
        low = text.lower()
        assert "deref coercion" in low
        assert "ptr_arg" in text

    def test_documents_exclusions(self, text: str) -> None:
        low = text.lower()
        assert "exclusion" in low or "not flag" in low
        # The foreign-to-narrow vetoes must be present.
        assert "&mut" in text

    def test_has_exit_criteria(self, text: str) -> None:
        assert "## Exit Criteria" in text


@pytest.mark.unit
class TestSkillMdWiresCoercionParams:
    """SKILL.md references the new module."""

    def test_frontmatter_lists_module(self) -> None:
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert f"{MODULE_NAME}.md" in modules or MODULE_NAME in modules
