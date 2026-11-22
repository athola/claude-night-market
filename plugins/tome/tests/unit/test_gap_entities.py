"""Entity coverage in identify_gaps: named options no finding mentions."""

from __future__ import annotations

from typing import Any

import pytest

from tests.factories import make_finding
from tome.synthesis.quality import identify_gaps

_BASE_KEYS = {"empty_channels", "source_diversity_warning", "recency_gap"}


@pytest.mark.unit
class TestEntityCoverage:
    def test_entity_absent_from_every_finding_is_reported(self) -> None:
        findings = [make_finding(title="Meshtastic range test", summary="LoRa")]
        gaps = identify_gaps(findings, ["code"], entities=["Meshtastic", "Beartooth"])
        assert gaps["uncovered_entities"] == ["Beartooth"]

    def test_entity_in_summary_is_covered(self) -> None:
        findings = [make_finding(title="Radios", summary="compares goTenna units")]
        gaps = identify_gaps(findings, ["code"], entities=["gotenna"])
        assert gaps["uncovered_entities"] == []

    def test_match_is_case_insensitive(self) -> None:
        findings = [make_finding(title="BEARTOOTH review", summary="")]
        gaps = identify_gaps(findings, ["code"], entities=["beartooth"])
        assert gaps["uncovered_entities"] == []

    def test_substring_of_a_longer_word_is_not_a_mention(self) -> None:
        findings = [make_finding(title="Meshtastic", summary="")]
        gaps = identify_gaps(findings, ["code"], entities=["Mesh"])
        assert gaps["uncovered_entities"] == ["Mesh"]

    def test_regex_metacharacters_in_entity_are_literal(self) -> None:
        findings = [make_finding(title="Why C++ stays", summary="")]
        gaps = identify_gaps(findings, ["code"], entities=["C++", "C#"])
        assert gaps["uncovered_entities"] == ["C#"]

    def test_coverage_ratio_is_covered_share(self) -> None:
        findings = [make_finding(title="Alpha", summary="")]
        gaps = identify_gaps(findings, ["code"], entities=["Alpha", "Beta"])
        assert gaps["entity_coverage"] == 0.5

    def test_no_findings_means_every_entity_uncovered(self) -> None:
        gaps = identify_gaps([], ["code"], entities=["Alpha"])
        assert gaps["uncovered_entities"] == ["Alpha"]
        assert gaps["entity_coverage"] == 0.0

    def test_no_entities_leaves_result_shape_unchanged(self) -> None:
        gaps = identify_gaps([make_finding()], ["code"])
        assert set(gaps) == _BASE_KEYS

    def test_empty_entity_list_leaves_result_shape_unchanged(self) -> None:
        gaps = identify_gaps([make_finding()], ["code"], entities=[])
        assert set(gaps) == _BASE_KEYS

    def test_blank_entities_are_ignored(self) -> None:
        gaps = identify_gaps([make_finding()], ["code"], entities=["  ", ""])
        assert set(gaps) == _BASE_KEYS

    def test_a_bare_string_or_non_string_entities_are_ignored(self) -> None:
        """The skill passes its own list straight in: "Rust" split into
        letters and a number raised at ``e.strip()``.
        """
        finding = make_finding()
        bare: Any = "Rust"
        mixed: Any = [3, None, " Rust "]
        assert set(identify_gaps([finding], ["code"], entities=bare)) == _BASE_KEYS
        gaps = identify_gaps([finding], ["code"], entities=mixed)
        assert gaps["uncovered_entities"] == ["Rust"]

    def test_entity_named_only_in_url_is_covered(self) -> None:
        # research.js matches title, url and why; the Python rule must agree
        findings = [
            make_finding(
                title="Field radios", summary="", url="https://beartooth.com/x"
            )
        ]
        gaps = identify_gaps(findings, ["code"], entities=["beartooth"])
        assert gaps["uncovered_entities"] == []

    def test_padded_entity_still_matches(self) -> None:
        findings = [make_finding(title="Meshtastic notes", summary="")]
        gaps = identify_gaps(findings, ["code"], entities=[" Meshtastic "])
        assert gaps["uncovered_entities"] == []
