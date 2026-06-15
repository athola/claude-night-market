"""BDD tests for the rust-review conversion-traits dimension.

Feature: Rust Review Prefers From Over Into And Surfaced Conversion Errors
  As a Rust code reviewer
  I want the skill to flag `impl Into<..> for ..` (should be `impl From`)
    and `.try_into().unwrap()` / `try_from(..).unwrap()` (discarding the
    fallible-conversion error)
  So that conversions implement the most general standard trait and the
    error that `TryFrom` exists to surface is not silently panicked away.

Research basis: Rust API Guidelines C-CONV-TRAITS ("never implement
`Into`/`TryInto`; the blanket impl derives them from `From`/`TryFrom`")
and std::convert docs ("always prefer implementing `From<T>`/`TryFrom<T>`
... `Into`/`TryInto` for free"); clippy::from_over_into (since 1.51,
gated on the 1.41 coherence rebalancing). Exclusion: an `impl Into` whose
target is a FOREIGN type cannot be rewritten as `From` (orphan rule;
rust-clippy #9638, #6607). See modules/conversion-traits.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pensive.skills.rust_review import RustReviewSkill

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "rust-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
MODULE_NAME = "conversion-traits"


def _parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


@pytest.mark.unit
class TestConversionTraitsDetector:
    """Detector: analyze_conversion_traits flags Into impls + unwraps."""

    def setup_method(self) -> None:
        self.skill = RustReviewSkill()

    def _issues(self, mock_ctx, code: str) -> list[dict]:
        mock_ctx.get_file_content.return_value = code
        return self.skill.analyze_conversion_traits(mock_ctx, "c.rs")[
            "conversion_traits_issues"
        ]

    def test_flags_impl_into(self, mock_skill_context) -> None:
        """`impl Into<X> for Y` -> recommend `impl From<Y> for X`."""
        issues = self._issues(
            mock_skill_context, "impl Into<Settings> for Config {\n}\n"
        )
        fo = [i for i in issues if i["type"] == "from_over_into"]
        assert len(fo) >= 1
        assert "From" in fo[0]["recommendation"]
        assert fo[0]["clippy_lint"] == "clippy::from_over_into"

    def test_impl_from_not_flagged(self, mock_skill_context) -> None:
        """`impl From<..>` is already the preferred direction."""
        issues = self._issues(
            mock_skill_context, "impl From<Config> for Settings {\n}\n"
        )
        assert all(i["type"] != "from_over_into" for i in issues)

    def test_into_trait_bound_not_flagged(self, mock_skill_context) -> None:
        """A `where`/generic bound `T: Into<U>` is correct and idiomatic;
        only `impl Into` blocks are flagged, never bounds."""
        issues = self._issues(
            mock_skill_context, "fn g<T: Into<u64>>(t: T) -> u64 { t.into() }\n"
        )
        assert all(i["type"] != "from_over_into" for i in issues)

    def test_flags_try_into_unwrap(self, mock_skill_context) -> None:
        """`.try_into().unwrap()` discards the conversion error."""
        issues = self._issues(
            mock_skill_context, "let n: u32 = x.try_into().unwrap();\n"
        )
        assert any(i["type"] == "discarded_conversion_error" for i in issues)

    def test_flags_try_from_unwrap(self, mock_skill_context) -> None:
        """`T::try_from(x).unwrap()` discards the conversion error."""
        issues = self._issues(
            mock_skill_context, "let n = u32::try_from(x).unwrap();\n"
        )
        assert any(i["type"] == "discarded_conversion_error" for i in issues)

    def test_plain_try_into_not_flagged(self, mock_skill_context) -> None:
        """A propagated `try_into()?` keeps the error; not flagged."""
        issues = self._issues(mock_skill_context, "let n: u32 = x.try_into()?;\n")
        assert all(i["type"] != "discarded_conversion_error" for i in issues)

    def test_comment_not_flagged(self, mock_skill_context) -> None:
        issues = self._issues(
            mock_skill_context, "// impl Into<Settings> for Config {}\n"
        )
        assert issues == []

    def test_wired_into_analyze(self, mock_skill_context) -> None:
        """The aggregate analyze() surfaces conversion_traits info."""
        mock_skill_context.get_file_content.return_value = (
            "impl Into<Settings> for Config {\n}\n"
        )
        result = self.skill.analyze(mock_skill_context, "c.rs")
        assert "conversion_traits" in result.info


@pytest.mark.unit
class TestConversionTraitsModuleDoc:
    """The conversion-traits.md module documents the paradigm."""

    @pytest.fixture
    def text(self) -> str:
        return (MODULES_DIR / f"{MODULE_NAME}.md").read_text()

    def test_module_file_exists(self) -> None:
        assert (MODULES_DIR / f"{MODULE_NAME}.md").exists()

    def test_frontmatter_declares_module_name(self, text: str) -> None:
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end])
        assert fm.get("module") == MODULE_NAME

    def test_covers_from_over_into(self, text: str) -> None:
        assert "from_over_into" in text
        assert "TryFrom" in text

    def test_documents_orphan_rule_exclusion(self, text: str) -> None:
        """The foreign-target orphan-rule exclusion must be documented."""
        low = text.lower()
        assert "orphan" in low or "foreign" in low

    def test_has_exit_criteria(self, text: str) -> None:
        assert "## Exit Criteria" in text


@pytest.mark.unit
class TestSkillMdWiresConversionTraits:
    """SKILL.md references the new module."""

    def test_frontmatter_lists_module(self) -> None:
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert f"{MODULE_NAME}.md" in modules or MODULE_NAME in modules
