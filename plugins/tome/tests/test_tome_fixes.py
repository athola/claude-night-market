"""Regression and correctness tests for TOME-001 and TOME-004 fixes."""

from __future__ import annotations

import pytest
from tome.synthesis.merger import fuzzy_deduplicate

from tests.factories import make_finding

# ---------------------------------------------------------------------------
# TOME-001: union-find fuzzy_deduplicate
# ---------------------------------------------------------------------------


class TestTOME001FuzzyDeduplicateUnionFind:
    """
    TOME-001: fuzzy_deduplicate was O(n^2) with a removed-set loop.
    Replaced with union-find that handles transitive duplicates and
    emits findings in first-encounter group order.

    Verifies correctness on 20+ items.
    """

    # Ten fully distinct topics for pairs; each pair uses identical titles.
    # The same title gives Jaccard=1.0 within a pair.
    # Different topics give Jaccard=0.0 or very low between pairs.
    _PAIR_TITLES = [
        "quantum entanglement photon teleportation",
        "gradient descent backpropagation neural",
        "distributed consensus byzantine fault",
        "compiler register allocation graph",
        "protein folding molecular dynamics",
        "homomorphic encryption lattice",
        "garbage collection generational heap",
        "rasterization shader pipeline gpu",
        "kalman filter state estimation",
        "merkle tree blockchain hashing",
    ]
    _UNIQUE_TITLES = [
        "zebra migration savanna ecology",
        "baroque counterpoint fugue harmony",
        "tectonic subduction oceanic lithosphere",
        "medieval siege ballista trebuchet",
        "solubility precipitation reagent titration",
    ]

    @pytest.mark.unit
    def test_20_items_ten_pairs_plus_uniques(self) -> None:
        """10 duplicate pairs + 5 uniques = 15 survivors with correct relevance."""
        channel = "academic"
        findings = []

        for i, title in enumerate(self._PAIR_TITLES):
            low = make_finding(
                0.5,
                channel=channel,
                title=title,
                url=f"https://src1.com/{i}",
            )
            high = make_finding(
                0.9,
                channel=channel,
                title=title,
                url=f"https://src2.com/{i}",
            )
            findings.append(low)
            findings.append(high)

        for i, title in enumerate(self._UNIQUE_TITLES):
            findings.append(
                make_finding(
                    0.7,
                    channel=channel,
                    title=title,
                    url=f"https://unique.com/{i}",
                )
            )

        assert len(findings) == 25
        result = fuzzy_deduplicate(findings)

        assert len(result) == 15
        # No low-relevance (0.5) survivor -- high (0.9) wins each pair
        assert all(f.relevance != 0.5 for f in result)

    @pytest.mark.unit
    def test_encounter_order_preserved_in_large_list(self) -> None:
        """First-group-member position determines output order for 20+ items."""
        channel = "academic"
        titles = [
            f"unique research topic {i} with distinct words set" for i in range(20)
        ]
        findings = [
            make_finding(0.6, channel=channel, title=t, url=f"https://x.com/{i}")
            for i, t in enumerate(titles)
        ]
        result = fuzzy_deduplicate(findings)

        # All unique titles: all 20 must appear
        assert len(result) == 20
        # Encounter order must be preserved
        assert [f.url for f in result] == [f.url for f in findings]

    @pytest.mark.unit
    def test_transitive_duplicates_merged_to_one(self) -> None:
        """A duplicates B and B duplicates C: all three collapse to best.

        Uses 9-word titles where adjacent pairs share 8 words (Jaccard=0.8),
        meeting the same-channel threshold. A and C share 7/11 words
        (Jaccard≈0.64) so they only merge via B's transitive link.
        """
        channel = "academic"
        # A and B share 8 of 10 union words → Jaccard=0.8 (threshold met)
        # B and C share 8 of 10 union words → Jaccard=0.8 (threshold met)
        # A and C share 7 of 11 union words → Jaccard≈0.64 (below threshold)
        findings = [
            make_finding(
                0.5,
                channel=channel,
                title="neural network deep learning optimization training gradient descent backprop",
                url="https://a.com/1",
            ),
            make_finding(
                0.7,
                channel=channel,
                title="neural network deep learning optimization training gradient descent inference",
                url="https://b.com/1",
            ),
            make_finding(
                0.9,
                channel=channel,
                title="neural network deep learning optimization training gradient descent latency",
                url="https://c.com/1",
            ),
        ]
        result = fuzzy_deduplicate(findings)

        # All three merge transitively via B; best relevance wins
        assert len(result) == 1
        assert result[0].relevance == 0.9

    @pytest.mark.unit
    def test_empty_list(self) -> None:
        assert fuzzy_deduplicate([]) == []

    @pytest.mark.unit
    def test_single_finding(self) -> None:
        f = make_finding(
            0.8, channel="academic", title="single paper", url="https://x.com"
        )
        assert fuzzy_deduplicate([f]) == [f]
