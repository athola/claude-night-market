"""Impact metrics over the citation graph.

Two families. ``disruption_index`` computes the CD index (Funk and
Owen-Smith 2017): does a paper's citing works ignore its intellectual
predecessors (disruptive, toward +1) or cite them too (consolidating,
toward -1)? ``rank_by_centrality`` orders papers by PageRank produced by
memory-palace's analyzer.

The disruption index is biased by citation inflation, field size, and
citation-window length (Petersen 2023; QSS 2024). So a raw score is
never comparable across cohorts: ``assert_comparable`` enforces that in
code, not just in prose.
"""

from __future__ import annotations

from dataclasses import dataclass


def disruption_index(citing_focal: set[str], citing_references: set[str]) -> float:
    """CD index in ``[-1.0, 1.0]`` from two citing-paper sets.

    Args:
        citing_focal: IDs of papers that cite the focal paper.
        citing_references: IDs of papers that cite the focal paper's
            references (its intellectual predecessors).

    Returns:
        ``(n_i - n_j) / (n_i + n_j + n_k)`` where ``n_i`` cite only the
        focal (disruptive), ``n_j`` cite both (consolidating), and
        ``n_k`` cite only the references. ``0.0`` when no citing papers.
    """
    n_i = len(citing_focal - citing_references)
    n_j = len(citing_focal & citing_references)
    n_k = len(citing_references - citing_focal)
    denominator = n_i + n_j + n_k
    if denominator == 0:
        return 0.0
    return (n_i - n_j) / denominator


@dataclass(frozen=True)
class Cohort:
    """A comparison cohort: same field and publication year."""

    field: str
    year: int


@dataclass(frozen=True)
class DisruptionScore:
    """A disruption score tagged with the cohort it was measured in."""

    paper_id: str
    score: float
    cohort: Cohort


def assert_comparable(a: DisruptionScore, b: DisruptionScore) -> None:
    """Raise unless two disruption scores share a cohort.

    Cross-cohort comparison of raw disruption is invalid: the index is
    confounded by citation inflation and field size. Comparing only
    within a field-and-year cohort is the documented correction.

    Raises:
        ValueError: When the two scores are from different cohorts.
    """
    if a.cohort != b.cohort:
        raise ValueError(
            f"disruption scores are not comparable across cohorts: "
            f"{a.cohort} vs {b.cohort}"
        )


def rank_by_centrality(pagerank: dict[str, float]) -> list[tuple[str, float]]:
    """Rank paper IDs by PageRank centrality, most central first."""
    return sorted(pagerank.items(), key=lambda item: item[1], reverse=True)
