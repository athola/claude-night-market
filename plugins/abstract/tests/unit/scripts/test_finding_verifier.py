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
    _count_lines,
    main,
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

    @pytest.mark.unit
    def test_punctuation_only_tokens_are_skipped(self) -> None:
        """Tokens that strip down to nothing (``...``, ``()``) are
        dropped, leaving only the real path. Guards the tokenizer
        against the trailing-punctuation noise Insight-Engine
        ``Where:`` strings often carry.
        """
        refs = parse_where_refs("src/app.py ... () , ;")
        assert refs == [FileRef("src/app.py")]


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

    @pytest.mark.unit
    @pytest.mark.parametrize("malformed", [":no-plugin", "no-name:", ":"])
    def test_malformed_skill_id_returns_empty(
        self, malformed: str, tmp_path: Path
    ) -> None:
        """A colon with an empty half (``:foo`` / ``foo:`` / ``:``) has
        nothing reliable to resolve, so no candidate path is built --
        the gate then treats it as ``no_refs`` and never blocks.
        """
        assert resolve_skill_refs(malformed, repo_root=tmp_path) == []


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
    def test_present_plus_drifted_lines_stays_present_medium(
        self, tmp_path: Path
    ) -> None:
        """One file with in-bounds lines and another whose cited range
        drifted past EOF: the surviving in-bounds reference keeps the
        verdict ``present`` (so promotion is allowed), but confidence
        drops to ``medium`` to flag the drift for human review.
        """
        (tmp_path / "good.md").write_text("\n".join(f"l{i}" for i in range(1, 51)))
        (tmp_path / "short.md").write_text("only\ntwo\n")  # 2 lines
        result = verify_refs(
            [FileRef("good.md", 10, 20), FileRef("short.md", 40, 47)],
            repo_root=tmp_path,
        )
        assert result.status == "present"
        assert result.confidence == "medium"
        assert result.missing == []
        assert not should_skip_promotion(result)

    @pytest.mark.unit
    def test_no_refs_returns_no_refs_status(self, tmp_path: Path) -> None:
        result = verify_refs([], repo_root=tmp_path)
        assert result.status == "no_refs"


class TestCountLines:
    """_count_lines() returns a line count, or None when the path
    cannot be read as a file.
    """

    @pytest.mark.unit
    def test_counts_lines_of_a_file(self, tmp_path: Path) -> None:
        f = tmp_path / "three.md"
        f.write_text("a\nb\nc\n")
        assert _count_lines(f) == 3

    @pytest.mark.unit
    def test_unreadable_path_returns_none(self, tmp_path: Path) -> None:
        """Opening a directory raises OSError; the helper swallows it
        and returns None so verify_refs degrades to a plain existence
        check instead of crashing.
        """
        assert _count_lines(tmp_path) is None


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


class TestMainCli:
    """The thin CLI wrapper exercises the same parse/verify/gate core
    against a real repo root, so the verifier has a runnable surface
    (and a live dogfood demo) rather than being library-only.
    """

    @staticmethod
    def _repo(tmp_path: Path) -> Path:
        """A minimal tree that ``repo_root_is_valid`` trusts."""
        (tmp_path / ".git").mkdir()
        return tmp_path

    @pytest.mark.unit
    def test_present_location_exits_zero_and_does_not_skip(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A finding whose file exists verifies present and is not skipped."""
        repo = self._repo(tmp_path)
        (repo / "plugins").mkdir()
        (repo / "plugins" / "x.md").write_text("a\nb\n", encoding="utf-8")

        code = main(["--where", "plugins/x.md", "--repo-root", str(repo)])

        out = capsys.readouterr().out
        assert code == 0
        assert "present" in out
        assert "skip_promotion: False" in out

    @pytest.mark.unit
    def test_missing_location_flags_skip(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A finding whose only file is gone is flagged skip (high)."""
        repo = self._repo(tmp_path)

        code = main(["--where", "plugins/gone.md", "--repo-root", str(repo)])

        out = capsys.readouterr().out
        assert code == 0
        assert "missing" in out
        assert "skip_promotion: True" in out

    @pytest.mark.unit
    def test_skill_id_resolves_to_directory(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A ``plugin:name`` id resolving to a real skill dir is present."""
        repo = self._repo(tmp_path)
        (repo / "plugins" / "demo" / "skills" / "thing").mkdir(parents=True)

        code = main(["--skill", "demo:thing", "--repo-root", str(repo)])

        out = capsys.readouterr().out
        assert code == 0
        assert "present" in out

    @pytest.mark.unit
    def test_requires_where_or_skill(self, tmp_path: Path) -> None:
        """Invoking with neither --where nor --skill is a usage error."""
        repo = self._repo(tmp_path)
        with pytest.raises(SystemExit):
            main(["--repo-root", str(repo)])

    @pytest.mark.unit
    def test_untrusted_repo_root_returns_2(self, tmp_path: Path) -> None:
        """An untrusted root disables the gate (returns 2) rather than
        reporting every location missing and skipping live findings.
        """
        bogus = tmp_path / "not-a-repo"
        code = main(["--where", "x.md", "--repo-root", str(bogus)])
        assert code == 2
