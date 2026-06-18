"""BDD tests for the rust-review match-wildcard dimension.

Feature: Rust Review Flags Wildcard Arms That Defeat Exhaustiveness
  As a Rust code reviewer
  I want the skill to flag catch-all `_ =>` arms that panic or silently
    swallow cases
  So that a new enum variant produces a compile error instead of a
    runtime panic or a silently ignored case.

Research basis: the Rust Reference match chapter
(rust-lang/reference src/expressions/match-expr.md): match arms must be
exhaustive, and a wildcard `_` arm satisfies exhaustiveness by matching
everything left over. clippy::wildcard_enum_match_arm and
clippy::match_wildcard_for_single_variants. See modules/match-wildcard.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pensive.skills.rust_review import RustReviewSkill

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
MODULE_NAME = "match-wildcard"


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


@pytest.mark.unit
class TestMatchWildcardDetector:
    """Detector: analyze_match_exhaustiveness flags catch-all arms."""

    def setup_method(self) -> None:
        self.skill = RustReviewSkill()

    def test_flags_wildcard_unreachable(self, mock_skill_context) -> None:
        """`_ => unreachable!()` turns a new variant into a runtime panic."""
        code = "        _ => unreachable!(),\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_match_exhaustiveness(mock_skill_context, "m.rs")[
            "match_wildcard_issues"
        ]
        wu = [i for i in issues if i["type"] == "wildcard_unreachable"]
        assert len(wu) == 1
        assert wu[0]["line"] == 1
        assert wu[0]["clippy_lint"] == "clippy::wildcard_enum_match_arm"

    def test_flags_wildcard_panic(self, mock_skill_context) -> None:
        """`_ => panic!(...)` is the same exhaustiveness-defeating shape."""
        code = '        _ => panic!("unexpected state"),\n'
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_match_exhaustiveness(mock_skill_context, "m.rs")[
            "match_wildcard_issues"
        ]
        assert any(i["type"] == "wildcard_panic" for i in issues)

    def test_flags_wildcard_todo(self, mock_skill_context) -> None:
        """`_ => todo!()` / `unimplemented!()` are flagged as panics."""
        code = "        _ => todo!(),\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_match_exhaustiveness(mock_skill_context, "m.rs")[
            "match_wildcard_issues"
        ]
        assert any(i["type"] == "wildcard_panic" for i in issues)

    def test_flags_empty_wildcard_arm(self, mock_skill_context) -> None:
        """`_ => {}` silently swallows every other case."""
        code = "        _ => {}\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_match_exhaustiveness(mock_skill_context, "m.rs")[
            "match_wildcard_issues"
        ]
        we = [i for i in issues if i["type"] == "wildcard_empty_arm"]
        assert len(we) == 1

    def test_legitimate_default_value_not_flagged(self, mock_skill_context) -> None:
        """`_ => 0` (a real default over an open set) is not flagged."""
        code = "        _ => 0,\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_match_exhaustiveness(mock_skill_context, "m.rs")[
            "match_wildcard_issues"
        ]
        assert issues == []

    def test_named_binding_arm_not_flagged(self, mock_skill_context) -> None:
        """A named catch-all binding `other =>` is not a bare wildcard."""
        code = "        other => handle(other),\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_match_exhaustiveness(mock_skill_context, "m.rs")[
            "match_wildcard_issues"
        ]
        assert issues == []

    def test_comment_not_flagged(self, mock_skill_context) -> None:
        """A wildcard arm shown in a comment is not code."""
        code = "// avoid _ => unreachable!() in matches\nlet x = 1;\n"
        mock_skill_context.get_file_content.return_value = code
        issues = self.skill.analyze_match_exhaustiveness(mock_skill_context, "k.rs")[
            "match_wildcard_issues"
        ]
        assert issues == []

    def test_wired_into_analyze(self, mock_skill_context) -> None:
        """The aggregate analyze() surfaces match_exhaustiveness info."""
        mock_skill_context.get_file_content.return_value = "    _ => unreachable!(),\n"
        result = self.skill.analyze(mock_skill_context, "m.rs")
        assert "match_exhaustiveness" in result.info


@pytest.mark.unit
class TestMatchWildcardModuleDoc:
    """The match-wildcard.md module documents the paradigm."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / f"{MODULE_NAME}.md").read_text()

    def test_module_file_exists(self) -> None:
        assert (MODULES_DIR / f"{MODULE_NAME}.md").exists()

    def test_frontmatter_declares_module_name(self, text: str) -> None:
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == MODULE_NAME

    def test_cites_exhaustiveness(self, text: str) -> None:
        assert "exhaustive" in text.lower()

    def test_cites_clippy_lint(self, text: str) -> None:
        assert "wildcard_enum_match_arm" in text

    def test_documents_open_set_exclusion(self, text: str) -> None:
        low = text.lower()
        assert "integer" in low or "open set" in low or "open-ended" in low

    def test_has_exit_criteria(self, text: str) -> None:
        assert "## Exit Criteria" in text


@pytest.mark.unit
class TestSkillMdWiresMatchWildcard:
    """SKILL.md references the new module."""

    def test_frontmatter_lists_module(self) -> None:
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert f"{MODULE_NAME}.md" in modules or MODULE_NAME in modules
