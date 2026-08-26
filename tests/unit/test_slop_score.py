"""The CI slop gate scores from the YAML, not from a copy of it.

`slop-check.yml` carried its own inline `TIER1=`/`TIER2=` grep
alternations. `data/languages/en.yaml` is documented as the single
pattern source that `Skill(scribe:slop-detector)` loads at runtime, so
the gate was enforcing a snapshot of it: every Tier 5 category added
since -- spatial copula, negative parallelism, performative honesty and
the rest -- was invisible to CI, and a new one would be too.

These tests pin the property that fixes it. The scorer reads the YAML,
so adding a category to the YAML changes what CI catches with no
workflow edit.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "slop_score.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "plugins" / "scribe" / "src"))

from slop_score import (  # noqa: E402 - scripts/ must join sys.path above before this resolves
    load_allowlist,
    score_text,
)


class TestScoringSourcesFromTheYaml:
    """Feature: the gate and the skill read one pattern source."""

    @pytest.mark.unit
    def test_a_tier1_word_scores(self) -> None:
        """Scenario: the vocabulary tiers still count."""
        assert score_text("This is a comprehensive guide. " * 5).score > 0

    @pytest.mark.unit
    def test_a_tier5_category_scores(self) -> None:
        """Scenario: a structural category the old grep could not see.

        The inline alternation held single words. A regex category like
        litotes cannot be expressed that way, which is why the gate
        never saw one.
        """
        clean = "The parser accepts flat blocks. " * 10
        slopped = clean + "This failure is not uncommon."
        assert score_text(slopped).score > score_text(clean).score

    @pytest.mark.unit
    def test_the_new_negation_categories_reach_the_gate(self) -> None:
        """Scenario: both high-confidence negation categories count."""
        base = "The exporter emits JSON. " * 10
        for phrase in ("This is not uncommon.", "Its value cannot be overstated."):
            assert score_text(base + phrase).score > score_text(base).score

    @pytest.mark.unit
    def test_clean_prose_scores_zero(self) -> None:
        """Scenario: plain technical prose is not penalized."""
        text = "The cache stores one entry per transcript path. " * 8
        assert score_text(text).score == 0

    @pytest.mark.unit
    def test_findings_name_their_category(self) -> None:
        """Scenario: the report says which rule fired, not just a number."""
        result = score_text("This failure is not uncommon. " * 10)
        assert "litotes" in {finding.category for finding in result.findings}

    @pytest.mark.unit
    def test_empty_text_is_zero_rather_than_a_division_error(self) -> None:
        """Guard: a file with no words has no score."""
        assert score_text("").score == 0


class TestCodeIsExcluded:
    """Feature: patterns inside code blocks are syntax, not prose."""

    @pytest.mark.unit
    def test_fenced_code_does_not_score(self) -> None:
        """Scenario: a fence mentioning a slop word is not slop."""
        text = "The parser accepts flat blocks. " * 10
        fenced = text + "\n```python\n# comprehensive not uncommon\n```\n"
        assert score_text(fenced).score == score_text(text).score


class TestCommandLine:
    """Feature: the workflow can call it and read a threshold verdict."""

    @pytest.mark.integration
    def test_exits_zero_on_clean_input(self, tmp_path: Path) -> None:
        """Scenario: a clean file passes the gate."""
        doc = tmp_path / "clean.md"
        doc.write_text("The cache stores one entry per transcript path.\n" * 8)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--threshold", "3.0", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    @pytest.mark.integration
    def test_exits_nonzero_when_a_file_is_over_threshold(self, tmp_path: Path) -> None:
        """Scenario: a slopped file fails the gate and is named."""
        doc = tmp_path / "slop.md"
        doc.write_text(
            "This comprehensive tapestry cannot be overstated. "
            "It is not uncommon to delve into the intricate.\n"
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--threshold", "3.0", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 1
        assert "slop.md" in result.stdout


class TestLowConfidenceDoesNotGate:
    """Feature: a merge fails only on findings the repo calls actionable.

    `.claude/rules/slop-scan-for-docs.md` says a `confidence: low`
    finding is surfaced for human decision and never auto-applied.
    Gating on one contradicts that. Measured on this repository, six
    files under `docs/` and `book/src/` sit above the threshold on
    low-confidence categories alone.
    """

    @pytest.mark.unit
    def test_a_low_confidence_category_adds_no_score(self) -> None:
        """Scenario: a semicolon splice is reported and costs nothing."""
        clean = "The exporter emits JSON. " * 10
        spliced = clean + "The system is fast; it scales."
        assert score_text(spliced).score == score_text(clean).score

    @pytest.mark.unit
    def test_a_low_confidence_category_is_still_reported(self) -> None:
        """Scenario: not scoring it is not the same as hiding it."""
        spliced = "The exporter emits JSON. " * 10 + "The system is fast; it scales."
        categories = {finding.category for finding in score_text(spliced).findings}
        assert "semicolon_splice" in categories

    @pytest.mark.unit
    def test_a_high_confidence_category_still_gates(self) -> None:
        """Guard: the exemption is scoped to low confidence only."""
        clean = "The exporter emits JSON. " * 10
        assert (
            score_text(clean + "This is not uncommon.").score > score_text(clean).score
        )


class TestProjectAllowlist:
    """Feature: a word used correctly in this domain can be exempted.

    `Skill(scribe:slop-detector)` module `config-file.md` documents
    `.slop-config.yaml` with an `allowlist` field, for the case its own
    example names: a marker word that is a term of art here. The
    archetypes plugin is built around the word "paradigm", which tier 2
    carries for "paradigm shift".

    Only `allowlist` is read. The rest of the documented schema is not
    implemented by this scorer, and a config that sets it gets no error
    and no effect, which is worth knowing before relying on it.
    """

    @pytest.mark.unit
    def test_an_allowlisted_word_stops_scoring(self, tmp_path: Path) -> None:
        """Scenario: the exempted word costs nothing."""
        config = tmp_path / ".slop-config.yaml"
        config.write_text("allowlist:\n  - paradigm\n")
        allow = load_allowlist(config)
        text = "The paradigm selector runs first. " * 8
        assert score_text(text, allowlist=allow).score < score_text(text).score

    @pytest.mark.unit
    def test_a_missing_config_is_an_empty_allowlist(self, tmp_path: Path) -> None:
        """Guard: no config file is not an error."""
        assert load_allowlist(tmp_path / "absent.yaml") == frozenset()

    @pytest.mark.unit
    def test_allowlisting_does_not_exempt_other_words(self, tmp_path: Path) -> None:
        """Guard: the exemption is per word, not a blanket off switch."""
        config = tmp_path / ".slop-config.yaml"
        config.write_text("allowlist:\n  - paradigm\n")
        allow = load_allowlist(config)
        assert score_text("This comprehensive guide. " * 8, allowlist=allow).score > 0

    @pytest.mark.unit
    def test_the_repository_config_documents_every_exemption(self) -> None:
        """Scenario: each allowlisted word carries a written reason.

        An allowlist without reasons becomes a place to silence
        findings. A trailing comment per entry keeps the next reader
        able to challenge one.
        """
        config = REPO_ROOT / ".slop-config.yaml"
        assert config.is_file()
        entries = [
            line
            for line in config.read_text().splitlines()
            if line.strip().startswith("- ")
        ]
        assert entries
        for line in entries:
            assert "#" in line, f"allowlist entry has no reason: {line.strip()!r}"
