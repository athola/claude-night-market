"""Offline retrieval-metrics benchmark (the ``make metrics`` harness).

Loads a committed gold set (topics, each with a ranked result list and a
relevant set), scores mean nDCG / MRR / recall with the deterministic
functions in :mod:`tome.metrics.retrieval`, and prints a table. No
network, no model, no LLM: the numbers are reproducible and trend-able.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from tome.metrics.retrieval import mrr, ndcg_at_k, recall_at_k

_FIXTURE = Path(__file__).parent / "fixtures" / "gold_set.yaml"


@dataclass(frozen=True)
class GoldItem:
    """A gold-labeled topic: the ranked result IDs and the relevant set."""

    topic: str
    ranked_ids: list[str]
    relevant: frozenset[str]


@dataclass(frozen=True)
class RetrievalReport:
    """Aggregate retrieval metrics over a gold set."""

    k: int
    n_topics: int
    mean_ndcg: float
    mean_mrr: float
    mean_recall: float

    def render(self) -> str:
        """Render the report as a plain-text table."""
        return (
            f"Retrieval metrics (mean over {self.n_topics} topics, k={self.k}):\n"
            f"  nDCG@{self.k}:   {self.mean_ndcg:.3f}\n"
            f"  MRR:        {self.mean_mrr:.3f}\n"
            f"  recall@{self.k}: {self.mean_recall:.3f}\n"
        )


def load_gold_set(path: Path | str = _FIXTURE) -> list[GoldItem]:
    """Load a gold set from a YAML file (defaults to the shipped fixture)."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    items = data.get("items", [])
    return [
        GoldItem(
            topic=str(item["topic"]),
            ranked_ids=[str(i) for i in item["ranked"]],
            relevant=frozenset(str(i) for i in item["relevant"]),
        )
        for item in items
    ]


def evaluate(gold: list[GoldItem], k: int = 10) -> RetrievalReport:
    """Compute mean nDCG / MRR / recall across the gold items."""
    if not gold:
        return RetrievalReport(
            k=k, n_topics=0, mean_ndcg=0.0, mean_mrr=0.0, mean_recall=0.0
        )
    count = len(gold)
    mean_ndcg = sum(ndcg_at_k(g.ranked_ids, set(g.relevant), k) for g in gold) / count
    mean_mrr = sum(mrr(g.ranked_ids, set(g.relevant)) for g in gold) / count
    mean_recall = (
        sum(recall_at_k(g.ranked_ids, set(g.relevant), k) for g in gold) / count
    )
    return RetrievalReport(
        k=k,
        n_topics=count,
        mean_ndcg=mean_ndcg,
        mean_mrr=mean_mrr,
        mean_recall=mean_recall,
    )


def main() -> None:
    """Score the shipped gold set and print the report."""
    report = evaluate(load_gold_set())
    print(report.render())


if __name__ == "__main__":
    main()
