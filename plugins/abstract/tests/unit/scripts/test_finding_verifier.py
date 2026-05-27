"""Tests for finding_verifier.py.

Feature: verify that an auto-promoted finding's referenced
locations still exist at the current HEAD, so the Insight
Engine does not create (or keep) issues for findings the
codebase has already moved past.

The verifier answers "do the referenced locations still
exist?" -- NOT "is the concern resolved?". File existence is
an honest, low-false-positive signal; concern-resolution
requires reading content and stays a human/`/do-issue`
decision.

Origin: Discussion-promoted learning (verify-then-close sweep
found 8 of 11 auto-promoted issues already resolved).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path for import
sys.path.insert(0, str(Path(__file__).parents[3] / "scripts"))

from finding_verifier import (
    FileRef,
    VerificationResult,
    parse_where_refs,
    resolve_skill_refs,
    should_skip_promotion,
    verify_refs,
)


class TestParseWhereRefs:
    """parse_where_refs() extracts file references from the varied
    free-text ``Where:`` strings the Insight Engine emits.
    """

    @pytest.mark.unit
    def test_backticked_path_with_colon_range(self) -> None:
        """`path:20-22` -> one FileRef with the line range."""
        refs = parse_where_refs(
            "`plugins/leyline/skills/additive-bias-defense/SKILL.md:20-22`"
        )
        assert refs == [
            FileRef(
                "plugins/leyline/skills/additive-bias-defense/SKILL.md",
                20,
                22,
            )
        ]

    @pytest.mark.unit
    def test_l_prefixed_line_range(self) -> None:
        """``CHANGELOG.md L37-47`` -> FileRef with the L-range."""
        refs = parse_where_refs("CHANGELOG.md L37-47")
        assert refs == [FileRef("CHANGELOG.md", 37, 47)]

    @pytest.mark.unit
    def test_multiple_line_markers_same_file(self) -> None:
        """``docs/x.md L45 / L87 / L147`` -> one FileRef per marker."""
        refs = parse_where_refs(
            "docs/karpathy-derivation/project-brief.md L45 / L87 / L147"
        )
        paths = {r.path for r in refs}
        starts = sorted(r.line_start for r in refs if r.line_start)
        assert paths == {"docs/karpathy-derivation/project-brief.md"}
        assert starts == [45, 87, 147]

    @pytest.mark.unit
    def test_path_with_trailing_prose(self) -> None:
        """A path followed by prose keeps just the path token."""
        refs = parse_where_refs(
            "plugins/conserve/hooks/shared/json_utils.sh and 2 siblings"
        )
        assert refs == [FileRef("plugins/conserve/hooks/shared/json_utils.sh")]

    @pytest.mark.unit
    def test_bare_path_no_lines(self) -> None:
        refs = parse_where_refs(
            "plugins/scribe/skills/slop-detector/modules/document-economy.md"
        )
        assert refs == [
            FileRef("plugins/scribe/skills/slop-detector/modules/document-economy.md")
        ]

    @pytest.mark.unit
    def test_no_parseable_path_returns_empty(self) -> None:
        assert parse_where_refs("a vague narrative concern with no path") == []


class TestResolveSkillRefs:
    """resolve_skill_refs() maps a ``plugin:name`` skill id to its
    on-disk location for existence checks.
    """

    @pytest.mark.unit
    def test_existing_skill_resolves_to_existing_dir(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "plugins" / "leyline" / "skills" / "git-platform"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: git-platform\n---\n")
        refs = resolve_skill_refs("leyline:git-platform", repo_root=tmp_path)
        assert any("plugins/leyline/skills/git-platform" in r.path for r in refs)

    @pytest.mark.unit
    def test_bare_skill_name_without_plugin_returns_empty(self, tmp_path: Path) -> None:
        assert resolve_skill_refs("just-a-name", repo_root=tmp_path) == []


class TestVerifyRefs:
    """verify_refs() reports whether referenced locations exist."""

    @pytest.mark.unit
    def test_present_when_file_exists_and_lines_in_bounds(self, tmp_path: Path) -> None:
        f = tmp_path / "a.md"
        f.write_text("\n".join(f"line {i}" for i in range(1, 51)))
        result = verify_refs([FileRef("a.md", 10, 20)], repo_root=tmp_path)
        assert result.status == "present"
        assert result.confidence == "high"
        assert result.missing == []

    @pytest.mark.unit
    def test_missing_when_file_absent(self, tmp_path: Path) -> None:
        result = verify_refs([FileRef("gone.md", 1, 5)], repo_root=tmp_path)
        assert result.status == "missing"
        assert result.confidence == "high"
        assert result.missing == ["gone.md"]

    @pytest.mark.unit
    def test_partial_missing_is_medium_confidence(self, tmp_path: Path) -> None:
        (tmp_path / "here.md").write_text("x\n")
        result = verify_refs(
            [FileRef("here.md"), FileRef("gone.md")],
            repo_root=tmp_path,
        )
        assert result.status == "missing"
        assert result.confidence == "medium"
        assert result.missing == ["gone.md"]

    @pytest.mark.unit
    def test_stale_lines_when_range_out_of_bounds(self, tmp_path: Path) -> None:
        f = tmp_path / "short.md"
        f.write_text("only\ntwo\n")  # 2 lines
        result = verify_refs([FileRef("short.md", 40, 47)], repo_root=tmp_path)
        assert result.status == "stale_lines"

    @pytest.mark.unit
    def test_no_refs_returns_no_refs_status(self, tmp_path: Path) -> None:
        result = verify_refs([], repo_root=tmp_path)
        assert result.status == "no_refs"


class TestShouldSkipPromotion:
    """The promotion gate skips only the clearest stale case:
    every referenced location is gone. Weaker signals
    (stale_lines, no_refs) never block promotion.
    """

    @pytest.mark.unit
    def test_skip_only_on_missing_status(self) -> None:
        assert should_skip_promotion(
            VerificationResult("missing", "high", [], ["gone.md"], "")
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("status", ["present", "stale_lines", "no_refs"])
    def test_do_not_skip_on_weaker_signals(self, status: str) -> None:
        assert not should_skip_promotion(VerificationResult(status, "low", [], [], ""))

    @pytest.mark.unit
    def test_do_not_skip_on_partial_missing(self) -> None:
        """Partial-missing (medium) means some referenced files survive,
        so the concern may still apply -- never block promotion.
        """
        assert not should_skip_promotion(
            VerificationResult("missing", "medium", [], ["gone.md"], "")
        )
