"""Every scribe check strips inline code with the same pattern.

Three of the four sites carried the single-backtick form, which on an
RST double-backtick span matches the two backtick pairs and leaves the
code between them exposed. The spelling normalizer then rewrote
identifiers inside quoted code, and the negation density scored a
``not_found`` enum as a stance.

Two kinds of test here: the behavior each site owes on a double
backtick span, and an identity check that the four sites hold the same
compiled object, so a fifth copy cannot be introduced quietly.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT / "plugins" / "scribe" / "src"))

from scribe import markdown_spans, negation, spelling, ste  # noqa: E402 - path first


def _load_slop_score():
    """Import scripts/slop_score.py, which is a script rather than a package."""
    module_path = _REPO_ROOT / "scripts" / "slop_score.py"
    spec = importlib.util.spec_from_file_location("slop_score", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["slop_score"] = module
    spec.loader.exec_module(module)
    return module


class TestRstCodeSpansAreProtected:
    """Feature: a double-backtick span is code everywhere in scribe.

    As a writer quoting an identifier the RST way
    I want every scribe check to treat the span as code
    So that a checker does not rewrite or score what I quoted.
    """

    @pytest.mark.unit
    def test_spelling_leaves_a_double_backtick_span_alone(self) -> None:
        """
        Scenario: a British spelling inside an RST code span
        Given the text ``Use ``colour`` here``
        When to_american runs
        Then the span is returned unchanged
        """
        source = "Use ``colour`` here"

        assert spelling.to_american(source) == source

    @pytest.mark.unit
    def test_spelling_still_normalizes_prose_outside_the_span(self) -> None:
        """
        Scenario: protecting code does not stop normalizing prose
        Given a British spelling outside the span
        Then it is still rewritten
        """
        assert spelling.to_american("The colour of ``colour``") == (
            "The color of ``colour``"
        )

    @pytest.mark.unit
    def test_negation_density_drops_a_double_backtick_span(self) -> None:
        """
        Scenario: negation words quoted as code
        Given the text ``x ``not no never`` y``
        When _prose_only strips code
        Then no word from inside the span survives
        """
        stripped = negation._prose_only("x ``not no never`` y")

        assert "not" not in stripped
        assert "never" not in stripped
        assert "x" in stripped and "y" in stripped

    @pytest.mark.unit
    def test_ste_counts_a_double_backtick_span_as_one_word(self) -> None:
        """
        Scenario: a quoted identifier is one thing
        Given a sentence whose only code span holds three words
        When the span mask runs
        Then the span collapses to a single token
        """
        masked = ste._mask_spans("The ``one two three`` value")

        assert len(masked.split()) == 3, masked


class TestTheFourSitesShareOnePattern:
    """Feature: the inline-code pattern lives in one place.

    As a maintainer
    I want the four strip sites to hold the same compiled pattern
    So that fixing one cannot leave the other three behind.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "module", [spelling, negation, ste], ids=lambda m: m.__name__
    )
    def test_scribe_modules_import_the_shared_pattern(self, module) -> None:
        """
        Scenario: identity, not equality
        Then the module's _INLINE_CODE is markdown_spans.INLINE_CODE
        """
        assert module._INLINE_CODE is markdown_spans.INLINE_CODE

    @pytest.mark.unit
    def test_slop_score_imports_the_shared_pattern(self) -> None:
        """
        Scenario: the standalone script shares it too
        Then slop_score._INLINE_CODE is markdown_spans.INLINE_CODE
        """
        assert _load_slop_score()._INLINE_CODE is markdown_spans.INLINE_CODE

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "source_path",
        [
            _REPO_ROOT / "plugins" / "scribe" / "src" / "scribe" / "spelling.py",
            _REPO_ROOT / "plugins" / "scribe" / "src" / "scribe" / "negation.py",
            _REPO_ROOT / "plugins" / "scribe" / "src" / "scribe" / "ste.py",
            _REPO_ROOT / "scripts" / "slop_score.py",
        ],
        ids=lambda p: p.name,
    )
    def test_no_site_compiles_its_own_copy(self, source_path: Path) -> None:
        """
        Scenario: a fresh copy would pass the identity check by accident

            ``re.compile`` caches by pattern string, so two identical
            literals return the same object and identity alone cannot
            see a copy. The source is what rules the copy out.

        Then the file carries no inline-code pattern of its own
        """
        source = source_path.read_text(encoding="utf-8")

        assert "_INLINE_CODE = re.compile" not in source, (
            f"{source_path.name} compiles its own inline-code pattern. "
            "Import INLINE_CODE from scribe.markdown_spans instead."
        )


_BACKTICK_FENCE = "Intro.\n\n```python\ncolour = never\n```\n\nOutro.\n"
_TILDE_FENCE = "Intro.\n\n~~~python\ncolour = never\n~~~\n\nOutro.\n"
_HTTP_URL = "See https://example.com/colour-never for details.\n"
_WWW_URL = "See www.colour-never.example for details.\n"


def _spelling_unchanged(source: str) -> bool:
    return spelling.to_american(source) == source


def _negation_drops(source: str) -> bool:
    return "colour" not in negation._prose_only(source)


def _ste_masks(source: str) -> bool:
    return "colour" not in ste._mask_spans(source)


def _slop_score_drops(source: str) -> bool:
    stripped = _load_slop_score()._prose_only(source)
    return "colour" not in stripped


class TestFencesAndUrlsAreProtected:
    """Feature: a fence or a URL is not prose in any scribe check.

    As a writer quoting code in a tilde fence or linking a www address
    I want every check that masks the construct to leave it alone
    So that a checker does not rewrite or score what is not prose.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "source", [_BACKTICK_FENCE, _TILDE_FENCE], ids=["backtick", "tilde"]
    )
    @pytest.mark.parametrize(
        "protects",
        [_spelling_unchanged, _negation_drops, _ste_masks, _slop_score_drops],
        ids=["spelling", "negation", "ste", "slop_score"],
    )
    def test_fenced_code_is_protected(self, protects, source: str) -> None:
        """
        Scenario: a British spelling and a negation inside a fence
        Given a fenced block opened with backticks or tildes
        When the check runs
        Then the fence content is not treated as prose
        """
        assert protects(source)

    @pytest.mark.unit
    @pytest.mark.parametrize("source", [_HTTP_URL, _WWW_URL], ids=["http", "www"])
    @pytest.mark.parametrize(
        "protects", [_spelling_unchanged, _ste_masks], ids=["spelling", "ste"]
    )
    def test_url_is_protected(self, protects, source: str) -> None:
        """
        Scenario: a British spelling inside a URL
        Given an http URL or a bare www address
        When a check that masks URLs runs
        Then the URL is not treated as prose
        """
        assert protects(source)

    @pytest.mark.unit
    def test_a_tilde_fence_holding_backticks_closes_on_its_own_marker(self) -> None:
        """
        Scenario: a tilde fence quoting a backtick fence
        Given a ``~~~`` block whose body contains a ``` line
        Then the colour after the inner ``` is still inside the fence
        """
        source = "~~~\n```\ncolour\n~~~\n"

        assert spelling.to_american(source) == source


class TestFenceAndUrlPatternsAreShared:
    """Feature: the fence and URL patterns live in markdown_spans."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "module", [spelling, negation, ste], ids=lambda m: m.__name__
    )
    def test_scribe_modules_import_the_shared_fence(self, module) -> None:
        assert module._FENCED_CODE is markdown_spans.FENCED_CODE

    @pytest.mark.unit
    def test_slop_score_imports_the_shared_fence(self) -> None:
        assert _load_slop_score()._FENCED_CODE is markdown_spans.FENCED_CODE

    @pytest.mark.unit
    @pytest.mark.parametrize("module", [spelling, ste], ids=lambda m: m.__name__)
    def test_url_masking_modules_import_the_shared_url(self, module) -> None:
        assert module._URL is markdown_spans.URL

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "source_path",
        [
            _REPO_ROOT / "plugins" / "scribe" / "src" / "scribe" / "spelling.py",
            _REPO_ROOT / "plugins" / "scribe" / "src" / "scribe" / "negation.py",
            _REPO_ROOT / "plugins" / "scribe" / "src" / "scribe" / "ste.py",
            _REPO_ROOT / "scripts" / "slop_score.py",
        ],
        ids=lambda p: p.name,
    )
    def test_no_site_compiles_its_own_fence_or_url(self, source_path: Path) -> None:
        """``re.compile`` caches by pattern, so identity cannot see a copy."""
        source = source_path.read_text(encoding="utf-8")

        assert "_FENCED_CODE = re.compile" not in source
        assert "_URL = re.compile" not in source


class TestFenceClosingFollowsCommonMark:
    """Any line opening with the same three characters closed a fence (SCR-7)."""

    def test_longer_fence_survives_an_inner_shorter_fence(self) -> None:
        text = "````md\n```py\nx = 1\n```\nstill code\n````\nprose\n"
        (span,) = [m.group(0) for m in markdown_spans.FENCED_CODE.finditer(text)]
        assert "still code" in span and "prose" not in span

    def test_unterminated_fence_runs_to_the_end(self) -> None:
        text = "prose\n```\ncode with no closer\n"
        (span,) = [m.group(0) for m in markdown_spans.FENCED_CODE.finditer(text)]
        assert span.endswith("code with no closer\n")

    def test_a_line_with_an_info_string_does_not_close(self) -> None:
        text = "```\na\n```py\nb\n```\nprose\n"
        (span,) = [m.group(0) for m in markdown_spans.FENCED_CODE.finditer(text)]
        assert "b" in span and "prose" not in span
