"""Score the frontier verdict against the labeled corpus (``make frontier-matrix``).

Replays recorded agent envelopes through ``frontier_verdict`` as a pure
function and prints three things: the confusion matrix of human label
against verdict, the false-THIN rate on the adversarial class, and a
sweep of the sparsity threshold. No network, no model, no LLM, so the
numbers are reproducible and trend-able.

The middle number is the one that matters. ``covered-obscure`` topics
are abundantly published under vocabulary the obvious query misses, and
nothing in the design detects vocabulary mismatch, so some of them will
read THIN. ``labels.yaml`` calls that rate "the bound on the signal's
value". It is the honest headline, and it is a rate this tool cannot
improve by trying harder.

The sweep is what "calibrated" can honestly mean here. ``_F_THIN``
changes a verdict only when exactly two of three retrieval channels are
controlled-empty and the third holds few findings. Outside that band it
is inert. Reporting how many verdicts move across a range of thresholds
says more than any single tuned integer, and a flat sweep is a finding
rather than a failure.

Written before the corpus was recorded, deliberately. A scorer built
while looking at results is a scorer shaped by the results its author
wanted, and this corpus was labeled by the same model that wrote the
signal being scored.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from tome.models import Finding, ResearchSession
from tome.synthesis.frontier import (
    COVERED,
    INCONCLUSIVE,
    MISMATCH_SUSPECTED,
    THIN_CANDIDATE,
    frontier_verdict,
)
from tome.synthesis.quality import parse_envelope

__all__ = [
    "MatrixReport",
    "RecordedTopic",
    "load_corpus",
    "main",
    "score_corpus",
    "sweep_threshold",
]

_FIXTURES = Path(__file__).parents[3] / "tests" / "fixtures" / "frontier"
_LABELS = _FIXTURES / "labels.yaml"

# The adversarial class: abundant work published under vocabulary the
# obvious query misses.
_ADVERSARIAL = "covered-obscure"

_VERDICTS = (COVERED, THIN_CANDIDATE, MISMATCH_SUSPECTED, INCONCLUSIVE)
_LABELS_ORDER = ("covered", _ADVERSARIAL, "thin")


@dataclass(frozen=True)
class RecordedTopic:
    """One topic's human label and its recorded agent envelopes."""

    slug: str
    topic: str
    label: str
    envelopes: list[dict[str, Any]]

    def session(self) -> ResearchSession:
        """Rebuild the session this topic's envelopes describe.

        Findings come from the recorded ``findings`` array and from
        nowhere else. Synthesizing them from ``result_count`` would make
        the sparsity test and the outcome test functions of one input,
        so they would agree by construction rather than by evidence and
        the matrix would score a tautology.
        """
        session = ResearchSession(
            topic=self.topic,
            domain="software",
            triz_depth="none",
            channels=[e["channel"] for e in self.envelopes],
        )
        for envelope in self.envelopes:
            session.query_log.extend(parse_envelope(envelope))
            session.findings.extend(
                Finding.from_dict(f) for f in envelope.get("findings") or []
            )
        return session


@dataclass
class MatrixReport:
    """The scored corpus, with every number traceable to its topics."""

    n_recorded: int
    n_labeled: int
    matrix: dict[tuple[str, str], int] = field(default_factory=dict)
    false_thin_rate: float | None = None
    sweep: dict[int, dict[str, str]] = field(default_factory=dict)
    _cells: dict[tuple[str, str], list[str]] = field(default_factory=dict)

    def topics_in(self, cell: tuple[str, str]) -> list[str]:
        """The slugs behind one cell.

        A rate with no route back to the runs behind it cannot be
        disagreed with, which is the property this whole feature exists
        to keep out of the verdict.
        """
        return list(self._cells.get(cell, []))

    def render(self) -> str:
        lines = [
            "Frontier verdict vs human label",
            "=" * 60,
            f"Recorded: {self.n_recorded}/{self.n_labeled} topics",
            "",
        ]
        if not self.n_recorded:
            lines += [
                "Nothing recorded yet, so nothing is scored. This is not a",
                "result of zero error; it is the absence of a measurement.",
                "",
                "Record envelopes into tests/fixtures/frontier/<slug>.json,",
                "three per topic (academic, code, discourse). triz is",
                "excluded from the verdict, so recording it reads nothing.",
            ]
            return "\n".join(lines)

        header = f"{'label':<18}" + "".join(f"{v[:11]:>13}" for v in _VERDICTS)
        lines += [header, "-" * len(header)]
        for label in _LABELS_ORDER:
            row = f"{label:<18}"
            for verdict in _VERDICTS:
                row += f"{self.matrix.get((label, verdict), 0):>13}"
            lines.append(row)

        lines += ["", "False-THIN rate on the adversarial class"]
        if self.false_thin_rate is None:
            lines.append(
                f"  no {_ADVERSARIAL} topics recorded, so the bound is unmeasured "
                "(not zero)"
            )
        else:
            offenders = self.topics_in((_ADVERSARIAL, THIN_CANDIDATE))
            lines.append(f"  {self.false_thin_rate:.1%}")
            lines.append(
                "  These are fields published under other words that the verdict"
            )
            lines.append(
                "  read as thin. No mechanism here detects vocabulary mismatch,"
            )
            lines.append(
                "  so this rate is the bound on the signal's value, not a bug to fix."
            )
            if offenders:
                lines.append(f"  topics: {', '.join(sorted(offenders))}")

        lines += ["", "Sparsity threshold sweep"]
        baseline = self.sweep.get(min(self.sweep, default=0), {})
        moved = {
            slug
            for verdicts in self.sweep.values()
            for slug, v in verdicts.items()
            if v != baseline.get(slug)
        }
        for threshold in sorted(self.sweep):
            counts = Counter(self.sweep[threshold].values())
            summary = ", ".join(f"{v}={counts.get(v, 0)}" for v in _VERDICTS)
            lines.append(f"  _F_THIN={threshold:<3} {summary}")
        lines += [
            "",
            f"  {len(moved)} of {self.n_recorded} topic(s) change verdict "
            "anywhere in this range.",
            "  The threshold discriminates only when exactly two retrieval",
            "  channels are controlled-empty and the third holds few findings.",
            "  At three empty it is inert, and at one it is unreachable. A flat",
            "  sweep therefore means the corpus sits outside that band, not that",
            "  any threshold is as good as another.",
            "",
            "Caveats",
            "  Each topic is one recorded run from a nondeterministic,",
            "  rate-limited pipeline, so this measures the pipeline and the",
            "  verdict jointly. It is not a repeatable accuracy figure and no",
            "  test asserts against it.",
            "  The threshold counts findings the agents chose to report, which",
            "  their own instructions cap ('at most 10', 'top 2-3 posts'), not",
            "  the number of results retrieved.",
        ]
        return "\n".join(lines)


def score_corpus(topics: list[RecordedTopic], *, n_labeled: int) -> MatrixReport:
    """Build the label-by-verdict matrix and the adversarial-class rate."""
    matrix: dict[tuple[str, str], int] = {}
    cells: dict[tuple[str, str], list[str]] = {}
    for topic in topics:
        cell = (topic.label, frontier_verdict(topic.session()).verdict)
        matrix[cell] = matrix.get(cell, 0) + 1
        cells.setdefault(cell, []).append(topic.slug)

    adversarial = [t for t in topics if t.label == _ADVERSARIAL]
    # None, not 0.0, when the class is unrecorded. A zero would read as
    # "the signal never fails on the adversarial class", which is the
    # opposite of "the adversarial class was never tested".
    rate: float | None = None
    if adversarial:
        false_thin = len(cells.get((_ADVERSARIAL, THIN_CANDIDATE), []))
        rate = false_thin / len(adversarial)

    return MatrixReport(
        n_recorded=len(topics),
        n_labeled=n_labeled,
        matrix=matrix,
        false_thin_rate=rate,
        sweep=sweep_threshold(topics) if topics else {},
        _cells=cells,
    )


def sweep_threshold(
    topics: list[RecordedTopic], thresholds: range = range(0, 11)
) -> dict[int, dict[str, str]]:
    """Per threshold: the verdict each topic receives under it.

    Returns the full per-topic mapping rather than a count of changes,
    so a reader can see which topics moved and where, instead of a
    single number that hides whether one topic flipped ten times or ten
    topics flipped once.
    """
    sessions = [(t.slug, t.session()) for t in topics]
    return {
        threshold: {
            slug: frontier_verdict(session, f_thin=threshold).verdict
            for slug, session in sessions
        }
        for threshold in thresholds
    }


def load_corpus() -> tuple[list[RecordedTopic], int]:
    """Read the labels and whatever envelopes have been recorded.

    Returns the recorded topics and the total labeled count, so the
    report can say 4/23 rather than implying 4 was the target.
    """
    labels = yaml.safe_load(_LABELS.read_text(encoding="utf-8"))
    entries = labels["topics"]
    recorded: list[RecordedTopic] = []
    for entry in entries:
        path = _FIXTURES / f"{entry['slug']}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        recorded.append(
            RecordedTopic(
                slug=entry["slug"],
                topic=entry["topic"],
                label=entry["label"],
                envelopes=data["envelopes"],
            )
        )
    return recorded, len(entries)


def main() -> None:
    topics, n_labeled = load_corpus()
    print(score_corpus(topics, n_labeled=n_labeled).render())


if __name__ == "__main__":
    main()
