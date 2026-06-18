"""BDD tests for the rust-review transmute-audit dimension.

Feature: Rust Review Flags `mem::transmute`
  As a Rust code reviewer
  I want the skill to flag `transmute` and `transmute_copy` calls
  So that authors reach for a typed, checked conversion (`from_*_bytes`,
    `as` for pointer casts, `bytemuck`, `From`/`TryFrom`) instead of
    reinterpreting bytes, which is undefined behavior when the source
    and target layouts disagree.

Research basis: the Rust Reference lists invalid-value reinterpretation
under behavior considered undefined
(rust-lang/reference src/behavior-considered-undefined.md), and the
std::mem::transmute docs call it "incredibly unsafe". clippy::transmute_*
family. See modules/transmute-audit.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pensive.skills.rust_review import RustReviewSkill

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
MODULE_NAME = "transmute-audit"


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


@pytest.mark.unit
class TestTransmuteDetector:
    """Detector: analyze_transmute_safety flags transmute calls."""

    def setup_method(self) -> None:
        self.skill = RustReviewSkill()

    def test_flags_mem_transmute(self, mock_skill_context) -> None:
        """`mem::transmute` reinterprets bytes and is flagged."""
        code = "let f: f32 = unsafe { mem::transmute(bits) };\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_transmute_safety(mock_skill_context, "t.rs")[
            "transmute_issues"
        ]
        tm = [i for i in issues if i["type"] == "transmute"]
        assert len(tm) >= 1
        assert tm[0]["line"] == 1
        assert tm[0]["clippy_lint"].startswith("clippy::")

    def test_flags_turbofish_transmute(self, mock_skill_context) -> None:
        """A turbofished `transmute::<A, B>(x)` is the same call."""
        code = "let b = unsafe { transmute::<u32, [u8; 4]>(n) };\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_transmute_safety(mock_skill_context, "t.rs")[
            "transmute_issues"
        ]
        assert any(i["type"] == "transmute" for i in issues)

    def test_flags_transmute_copy(self, mock_skill_context) -> None:
        """`transmute_copy` is the even-less-checked sibling."""
        code = "let v = unsafe { mem::transmute_copy(&src) };\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_transmute_safety(mock_skill_context, "t.rs")[
            "transmute_issues"
        ]
        assert any(i["type"] == "transmute_copy" for i in issues)

    def test_recommends_typed_alternative(self, mock_skill_context) -> None:
        """The recommendation names a checked alternative."""
        code = "let f = unsafe { mem::transmute(bits) };\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_transmute_safety(mock_skill_context, "t.rs")[
            "transmute_issues"
        ]
        rec = issues[0]["recommendation"].lower()
        assert "from_" in rec or "bytemuck" in rec or "try_from" in rec

    def test_identifier_containing_transmute_not_flagged(
        self, mock_skill_context
    ) -> None:
        """A method like `x.transmuter()` is not the std function."""
        code = "let y = pipeline.transmuter(input);\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_transmute_safety(mock_skill_context, "t.rs")[
            "transmute_issues"
        ]
        assert issues == []

    def test_comment_not_flagged(self, mock_skill_context) -> None:
        """A transmute mentioned in a comment is not code."""
        code = "// never use mem::transmute here\nlet x = 1;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_transmute_safety(mock_skill_context, "t.rs")[
            "transmute_issues"
        ]
        assert issues == []

    def test_wired_into_analyze(self, mock_skill_context) -> None:
        """The aggregate analyze() surfaces transmute info."""
        mock_skill_context.get_file_content.return_value = (
            "let f = unsafe { mem::transmute(bits) };\n"
        )
        result = self.skill.analyze(mock_skill_context, "t.rs")
        assert "transmute" in result.info


@pytest.mark.unit
class TestTransmuteModuleDoc:
    """The transmute-audit.md module documents the paradigm."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / f"{MODULE_NAME}.md").read_text()

    def test_module_file_exists(self) -> None:
        assert (MODULES_DIR / f"{MODULE_NAME}.md").exists()

    def test_frontmatter_declares_module_name(self, text: str) -> None:
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == MODULE_NAME

    def test_cites_undefined_behavior(self, text: str) -> None:
        low = text.lower()
        assert "undefined behavior" in low or "behavior-considered-undefined" in low

    def test_documents_alternative(self, text: str) -> None:
        low = text.lower()
        assert "from_" in low or "bytemuck" in low or "try_from" in low

    def test_has_exit_criteria(self, text: str) -> None:
        assert "## Exit Criteria" in text


@pytest.mark.unit
class TestSkillMdWiresTransmute:
    """SKILL.md references the new module."""

    def test_frontmatter_lists_module(self) -> None:
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert f"{MODULE_NAME}.md" in modules or MODULE_NAME in modules
