# Tome Research-Quality Metrics Framework

**Date**: 2026-07-17
**Companion to**: `research-report.md`, `design-spec.md`

## Thesis

Measure research quality as a **five-dimension vector, not a single
score.** The research is unambiguous that collapsing citation-derived
signals into one number is how bibliometrics went wrong (the disruption
index is biased and gameable). Each dimension gets deterministic,
inspectable proxies grounded in signals tome already computes or in
tooling that already exists in this repo. LLM-judged signals are
included only where structural proxies cannot reach, and always
labeled as directional.

Legend for the "status" column below:

- **exists**: already computed in tome today
- **wire-up**: computed but dormant, or present in `memory-palace` and
  callable
- **new**: requires new code

## Dimension 1: Relevancy

How on-topic and authoritative the retrieved set is. This is the one
dimension tome measures today, and the one with the most trustworthy
external metrics.

| Metric | Formula / source | Status |
|--------|------------------|--------|
| nDCG@k, MRR, recall@k | standard IR, vs. a labeled gold set | new (harness) |
| Adjusted relevance | `compute_relevance_score` (relevance + authority + recency) | exists (`ranker.py:68`) |
| Triangulation-weighted relevance | fold dormant `compute_triangulation_bonus` into the rank | wire-up (`ranker.py:27`) |
| Query-embedding cosine | `EmbeddingIndex` cosine(finding, query) | wire-up (memory-palace) |
| Faithfulness (optional) | RAGAS-style claim grounding | new, optional, labeled |

**Guardrail.** nDCG/MRR/recall against hand-labeled relevance are the
headline. The 0.55 human correlation of LLM-judge metrics keeps
faithfulness a secondary, opt-in signal.

## Dimension 2: Insight

Depth beyond the abstract, and whether synthesized claims are grounded.
Tome scores 0 here today because ingestion is abstract-only.

| Metric | Formula / source | Status |
|--------|------------------|--------|
| Section-coverage ratio | ingested sections / total sections per paper | new (paper model) |
| Citation-supported claim ratio | claims with a backing citation edge / total claims | new |
| Sub-question closure | answered planned sub-questions / total | wire-up (upgrade `identify_gaps`) |
| Full-text depth flag | abstract-only vs. full-text ingested | new |

**Guardrail.** Prefer the structural claim-support ratio (deterministic,
uses the citation graph) over an LLM faithfulness judge for the headline
insight number.

## Dimension 3: Creativity

Novelty, diversity, and non-obvious cross-domain connection. The trap
here is rewarding noise: a random retriever scores high on novelty and
is useless. Every creativity metric is therefore paired with relevance.

| Metric | Formula / source | Status |
|--------|------------------|--------|
| Source/domain diversity | `1 - Herfindahl` over channels | exists (`quality.py:96`) |
| TRIZ bridge count | cross-domain analogies found | exists (triz channel) |
| Corpus novelty | mean embedding distance of new findings from the prior-session corpus | wire-up (`EmbeddingIndex` + `memory.py`) |
| Reference atypicality | z-scored reference co-occurrence (Uzzi 2013) | new (needs references) |
| Link-prediction surprise | `predict_links` (Adamic-Adar) edges bridging distant communities | wire-up (`graph_analyzer.py:153`) |

**Guardrail.** Score novelty only jointly with relevance (a bandit
exploit/explore split), and apply an exploration-saturation stop so
speculative "further research paths" stay bounded, not a flood.

## Dimension 4: Performance

Speed, cost, and efficiency of the pipeline. Cheapest to measure, and
the dimension the tiered/on-condition design most directly moves.

| Metric | Formula / source | Status |
|--------|------------------|--------|
| Wall-clock per session | timer around the research run | new (timers) |
| Token budget adherence | tokens spent vs. `research_planner` tier (2000/4000/6000/8000) | exists (`research_planner.py:22`) |
| Findings per 1k tokens | unique findings / tokens | new |
| Dedup ratio | removed / total pre-dedup | exists (`merger.py`) |
| Graph-escalation rate | fraction of queries that hit the expensive graph path | new |
| Retrieval latency p50/p95 | per-query timing | new |

**Guardrail.** Report cost-per-quality (tokens per unit nDCG gain), not
raw speed, so a fast-but-useless run does not look good.

## Dimension 5: Impact

Downstream influence and structural importance. Powerful and cheap to
compute from the graph, but the most bias-prone. Normalization is
mandatory, not optional.

| Metric | Formula / source | Status |
|--------|------------------|--------|
| Graph centrality | PageRank / betweenness | wire-up (`graph_analyzer.py:51`) |
| Citation count | from `metadata` (Semantic Scholar / OpenAlex) | exists |
| Disruption (CD) index | Funk and Owen-Smith 2017, **field- and cohort-normalized, fixed window** | new (guarded) |
| Bridge / keystone finding | `find_bridges` / `find_keystones` | wire-up (`graph_analyzer.py:96`) |
| Cross-session reuse rate | times a finding is re-imported across sessions | exists (`memory.py:61`) |
| Decay-adjusted importance | `decay_model` half-life weighting | wire-up (`decay_model.py`) |

**Guardrail (evidence-backed, non-negotiable).** The disruption index is
biased by citation inflation, depends on the chosen citation-window
length, and barely overlaps with other novelty constructs. So: compare
only within field and publication-year cohort; fix and disclose the
citation window; never present a single collapsed "impact" number.

## Composite index

Report the five dimensions as a **radar/vector dashboard**. A scalar
Research Quality Index is offered only as a transparent, reweightable
convenience:

```
RQI = w_rel * Relevancy + w_ins * Insight + w_cre * Creativity
    + w_perf * Performance + w_imp * Impact
```

Default weights emphasize the trustworthy dimensions
(`w_rel = w_ins = 0.25`, `w_cre = w_imp = 0.2`, `w_perf = 0.1`), are
config-exposed, and every component score is stored alongside the
scalar so the vector is always recoverable. This mirrors tome's
existing `compute_quality_score` blend but widens it from three terms
to five.

## Benchmark and instrumentation

- **Gold set.** A fixed panel of arXiv topics with hand-labeled
  relevant papers (seeded from BEIR SciFact/SciDocs plus a small
  in-repo set), committed under `tests/fixtures/`, so nDCG/MRR/recall
  are reproducible offline with no network and no LLM.
- **Before/after protocol.** Run the same topics through the current
  pipeline and the upgraded one; report the per-dimension delta. A
  metric that does not move on the benchmark does not justify its code.
- **Persistence.** Computed scores are ephemeral today (recomputed each
  run, never stored). Persist them on `Finding.metadata` and in the
  session record so trends are measurable across runs. This is a
  prerequisite for measuring impact (cross-session reuse) at all.
- **Make target.** `make metrics` runs the harness on the gold set and
  prints the five-dimension table plus the RQI.

## Exit criteria

- [ ] Each of the five dimensions has at least one deterministic
      (non-LLM) proxy that runs offline on the gold set.
- [ ] `make metrics` prints the five-dimension table and RQI for a
      committed fixture with no network access.
- [ ] Impact metrics refuse to emit a cross-cohort comparison (field +
      year normalization enforced in code, not just documented).
- [ ] Every LLM-judge metric is labeled directional and is opt-in.
- [ ] Computed scores persist across sessions (reuse rate is non-zero
      on a second run over overlapping topics).
