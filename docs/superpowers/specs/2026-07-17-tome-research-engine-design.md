# Tome Research Engine: Design Specification

**Date**: 2026-07-17
**Companion to**: [metrics framework](../../metrics/tome-research-quality.md)
**Status**: Draft for plan-review + war-room gate before build
**Method**: Dogfooded `tome` across four channels (academic, code,
discourse, TRIZ) over four tracks. Saturation was reached after one
round: the load-bearing findings cross-validated across independent
channels, so no `dig` rounds ran. The evidence is recorded in
[Evidence base](#evidence-base) below.

## Thesis

Turn tome from a flat-list aggregator into a graph-backed research
engine by **reusing the graph, embedding, and decay tooling that
already exists in `memory-palace`, and by keeping the ground-truth
citation edges tome already fetches and discards.** No new graph
database, no LLM-based graph construction, no heavy ML in the hot path.

## The graph decision: reuse, not build

The single largest design choice is where the knowledge graph lives.
The evidence resolves it.

| Option | For | Against | Verdict |
|--------|-----|---------|---------|
| **Reuse `memory-palace` `KnowledgeGraph`** | Entities + temporal triples + weighted synapses already exist; `PalaceGraphAnalyzer` already gives PageRank, community detection, and Adamic-Adar link prediction; `tome:export` already targets memory-palace; zero new graph code | Cross-plugin coupling; tome gains a dependency on memory-palace internals | **Chosen** |
| Build tome-native graph | No cross-plugin coupling | Reinvents a working SQLite triple/synapse store; violates additive-bias-defense and shared-utility rules; more surface to maintain | Rejected |
| LLM-constructed graph (GraphRAG-style) | Richest entity/relation extraction | The #1 reported failure mode: hallucinated entities corrupt the graph "cyclically"; expensive indexing | Rejected for construction; the community/summary *ideas* are still adopted |

**Coupling containment.** Tome talks to memory-palace through a single
thin adapter module (`tome/graph/palace_adapter.py`), not scattered
imports, so the coupling is one seam that can be swapped or mocked. Two
amendments from the war-room review (`docs/plans/2026-07-17-war-room-tome-graph-decision.md`):

1. memory-palace must promote `KnowledgeGraph` and `PalaceGraphAnalyzer`
   into its public `__all__` so tome consumes a supported API, not
   internals; a tome CI contract test pins that surface.
2. memory-palace is a **declared dependency** of tome's graph feature,
   not a runtime silent no-op. Absence is an install-time invariant; if
   ever genuinely absent, tome surfaces an explicit
   capability-unavailable signal. Base (non-graph) research is
   unaffected because the graph layer is additive.

## Architecture

```
arXiv / S2 / OpenAlex          existing channels (academic.py)
        |
        v
  [ ingest ]  thin API clients (arxiv.py / pyalex / semanticscholar)
        |     + optional GROBID sidecar for full text
        v
  Paper model  sections + references + citation edges   <-- NEW, edges KEPT
        |
        v
  [ palace_adapter ]  write entities + triples + synapses  <-- reuse KnowledgeGraph
        |
        +--> detect_communities   -> "common threads"      <-- reuse graph_analyzer
        +--> predict_links (A-A)   -> "further research paths"
        +--> pagerank/betweenness  -> impact centrality
        |
        v
  [ retrieval ]  EmbeddingIndex (hash fallback) + on-condition graph escalation
        |
        v
  [ metrics harness ]  five-dimension vector + RQI, persisted   <-- NEW
        |
        v
  report / export (existing output layer, now graph-aware)
```

## Reused memory-palace interfaces

The build calls these existing APIs (no reimplementation):

- `KnowledgeGraph.upsert_entity` / `bulk_upsert_entities` (papers,
  authors, concepts as nodes)
- `KnowledgeGraph.add_triple` (citation and authorship edges as
  temporal triples)
- `KnowledgeGraph.create_synapse` / `strengthen_synapse` (weighted
  co-citation / co-read associations that decay)
- `PalaceGraphAnalyzer.pagerank`, `detect_communities`,
  `find_bridges`, `find_keystones`, `predict_links`
- `corpus.embedding_index.EmbeddingIndex` (semantic retrieval, hash
  fallback so no hard dependency)
- `corpus.semantic_deduplicator.SemanticDeduplicator` (near-duplicate
  removal across arXiv/S2/OpenAlex)
- `corpus.decay_model` (importance half-lives for pruning)

## Changes inside tome

| Area | Change | Reuses / basis |
|------|--------|----------------|
| `models.py` | Add `Paper` (sections, references, citation edges) alongside `Finding` | new; ceremony justified by the citation-edge need |
| `channels/academic.py` | Stop discarding citation-chain edges; populate `Paper.references`; optional GROBID full-text | wire-up (`academic.py:520`) |
| `synthesis/ranker.py` | Fold `compute_triangulation_bonus` into the ranked score | wire-up (`ranker.py:27`) |
| `synthesis/quality.py` | Upgrade `identify_gaps` to emit next-query suggestions (sub-question closure) | wire-up (`quality.py:19`) |
| `graph/palace_adapter.py` | New thin seam to memory-palace; no-op if absent | reuse |
| `graph/threads.py` | `detect_communities` -> threads; `predict_links` -> paths, with exploit/explore split + saturation stop | reuse |
| `retrieval/` | `EmbeddingIndex` semantic search; on-condition graph escalation for multi-hop queries | reuse |
| `metrics/` | Five-dimension harness + RQI + persistence; `make metrics` | new |
| `output/export.py` | Emit graph entities/edges, not only markdown | wire-up (`export.py:9`) |
| `README.md` | Fix the "parses PDFs" claim to match reality | doc fix |

## Dependency policy

- **Hard deps stay minimal.** Core spine is `networkx` (already a
  memory-palace dependency), plus thin `requests`-only API clients
  (`arxiv`, `pyalex`, `semanticscholar`). Metrics use a hand-rolled
  nDCG or `pytrec_eval`; no LLM required for the headline numbers.
- **Heavy tier is optional and isolated.** GROBID runs as a Docker
  sidecar behind an HTTP client; `sentence-transformers` / `faiss`
  stay optional extras (the hash-vector fallback covers the default);
  `microsoft/graphrag` and PyTorch Geometric are out of scope for v1.
- **Supply-chain gates.** OpenAlex needs an API key (Feb 2026);
  Nougat's weights are CC-BY-NC (excluded); every new dependency runs
  through `leyline:supply-chain-advisory`.

## Build increments (each a TDD slice, own PR)

1. **Keep the edges.** `Paper` model + citation-edge capture in
   `academic.py`; unit tests assert edges survive parsing. No graph
   write yet.
2. **Graph seam.** Promote `KnowledgeGraph` / `PalaceGraphAnalyzer` to
   memory-palace's public `__all__`; `palace_adapter` writes
   papers/edges into `KnowledgeGraph`; CI contract test pins the
   public surface; explicit capability gate (not silent no-op) when
   the feature is disabled.
3. **Threads and paths.** `detect_communities` + `predict_links`
   wired; triangulation bonus folded into rank; `identify_gaps`
   suggests next queries.
4. **Semantic retrieval.** `EmbeddingIndex` search + on-condition graph
   escalation; `SemanticDeduplicator` for near-dups.
5. **Metrics harness.** Five-dimension vector + RQI, persisted; gold-set
   fixture; `make metrics`; README fix.

Increments 1 to 3 carry most of the value (the graph the user asked
for) at the least new code. Increment 4 to 5 are tunable in depth.

## Evidence base

The four research tracks behind the decisions above.

**Track 1: GraphRAG and knowledge-graph construction.** The reference
architecture is settled: Microsoft GraphRAG ([2404.16130][gr]) extracts
an entity/relation graph with an LLM, partitions it with Leiden
community detection, and answers global queries from community
summaries. LightRAG ([2410.05779][lr]) adds incremental updates, so a
growing arXiv corpus needs no full re-index. HippoRAG
([2405.14831][hr], NeurIPS 2024) runs Personalized PageRank seeded by
query entities for single-shot multi-hop retrieval. But graph structure
is not always worth its cost: GraphRAG-Bench ([2506.02404][grb]) and
"When to use Graphs in RAG" ([2506.05690][wtg]) find the graph wins on
multi-hop and complex reasoning while adding overhead with little gain
on simple fact lookups. Practitioners are blunter still: an HN thread
on KAG ([230 points][kag]) calls graph RAG "incrementally" better and
warns that LLM-based construction hallucinates entities and
"cyclically" corrupts the graph. The historical cost objection has
collapsed (indexing a 5GB corpus fell from roughly $33,000 in early
2024 to roughly $33 by mid-2025, about 1000x, via model price cuts and
LazyGraphRAG deferring summarization to query time; [Cost Cliff][cc],
[TianPan][tp]), so the live objection is accuracy, not 2024 cost lore.
This is why the spec keeps ground-truth citation edges and rejects LLM
construction.

**Track 2: retrieval and RAG evaluation.** Deterministic label-based IR
metrics (nDCG@k, MRR, MAP, recall@k) are the trustworthy yardstick;
BEIR ([2104.08663][beir]) standardizes nDCG@10 and includes the
SciFact and SciDocs subsets, the closest public proxy for tome. TREC
Deep Learning ([2003.07820][trec]) defines the protocols. Reference-free
LLM-judged metrics (RAGAS [2309.15217][ragas]; ARES [2311.09476][ares])
measure faithfulness without gold labels but cost trust: RAGAS
correlates with human judgment at only about 0.55 harmonic mean
([getmaxim][gm]), and the CALM framework catalogs 12 distinct judge
biases including position, verbosity, self-enhancement, and authority
([Evidently][ev]). Hence the metrics framework's rule that judges are
directional only.

**Track 3: scientific full-text ingestion.** GROBID
([kermitt2/grobid][grobid]) parses PDFs to TEI XML at about 10 PDFs/sec
(roughly 400x Nougat) and leads reference extraction (F1 about 0.79 to
0.90 with the deep-learning citation model) ([Meuschke 2023][meu]).
Nougat ([2308.13418][nougat], ICLR 2024) preserves math and tables that
GROBID's text-layer approach loses, but is slow and, by its authors'
own disclosure, "skips or hallucinates" reference numbers in
bibliographies. The pattern that holds up in production is hybrid,
one tool primary and the other as fallback (reported splits near
94/6). A pre-built corpus removes most of the burden anyway:
unarXive 2022 ([2303.14957][unarxive]) ships 1.9M arXiv papers with a
resolved in-text citation network, and S2ORC ([1911.02782][s2orc])
offers 81M papers with inline citation spans. This is why GROBID is a
sidecar, not a dependency.

**Track 4: novelty, insight, and impact.** Graph-native impact signals
are cheap to compute: the CD/disruption index ([Funk and Owen-Smith
2017][funk], validated at scale by [Wu, Wang, Evans 2019][wu]) labels a
paper disruptive versus consolidating from citation structure alone;
Uzzi et al. ([2013][uzzi]) score atypicality from z-scored reference
co-occurrence; node2vec ([1607.00653][n2v]) and Adamic-Adar ([aa][aa])
predict missing edges. But raw citation metrics are biased and must be
normalized, the strongest cross-channel warning in the study: the
disruption index is biased by citation inflation and unsuitable for
cross-time comparison ([Petersen 2023][pet], [QSS/MIT][qss]), depends
on the analyst-chosen citation window so it is tunable and gameable
([window][win]), barely overlaps with novelty as a construct
([Triadic Novelty][triadic]), and the famous small-teams-disrupt
finding partly dissolves once inflation is corrected
([re-analysis][reana]). Impact metrics therefore ship only
field-normalized and cohort-restricted, with the window fixed and
disclosed, never collapsed to one number.

## Adoption risks

- **Over-building the graph.** Graph value is real but bounded to
  multi-hop. Guard: escalate on condition, measure the before/after
  delta on a multi-hop benchmark ([MultiHop-RAG][mhr]), and drop the
  graph path if it does not beat vector retrieval.
- **Trusting LLM-judge metrics.** 0.55 human correlation, 12 known
  biases. Guard: deterministic metrics are the headline; judges are
  labeled "directional."
- **Shipping biased impact numbers.** Citation metrics are confounded
  and gameable. Guard: normalize by field and cohort, fix and disclose
  the citation window, never collapse to one number.
- **Supply-chain surface.** Nougat weights are CC-BY-NC
  (non-commercial), OpenAlex mandates an API key as of Feb 2026, and
  nano-graphrag and Nougat are both stale. Guard: keep the heavy tier
  optional and isolated.
- **Tool-coverage gaps in the study itself.** Reddit and Lobsters
  returned no usable primary discourse (fetch blocks) and Semantic
  Scholar rate-limited citation counts. The academic and HN/blog
  channels triangulated the key claims, but community breadth is
  thinner than ideal.

[gr]: https://arxiv.org/abs/2404.16130
[lr]: https://arxiv.org/abs/2410.05779
[hr]: https://arxiv.org/abs/2405.14831
[grb]: https://arxiv.org/abs/2506.02404
[wtg]: https://arxiv.org/abs/2506.05690
[kag]: https://news.ycombinator.com/item?id=42545986
[cc]: https://medium.com/graph-praxis/the-graphrag-cost-cliff-how-33-000-became-33-in-eighteen-months-be1b0fbe37e4
[tp]: https://tianpan.co/blog/2026-04-19-graphrag-vs-vector-rag-architecture-decision
[beir]: https://arxiv.org/abs/2104.08663
[trec]: https://arxiv.org/abs/2003.07820
[ragas]: https://arxiv.org/abs/2309.15217
[ares]: https://arxiv.org/abs/2311.09476
[gm]: https://www.getmaxim.ai/articles/complete-guide-to-rag-evaluation-metrics-methods-and-best-practices-for-2025/
[ev]: https://www.evidentlyai.com/llm-guide/llm-as-a-judge
[grobid]: https://github.com/kermitt2/grobid
[meu]: https://gipplab.uni-goettingen.de/wp-content/papercite-data/pdf/meuschke2023.pdf
[nougat]: https://arxiv.org/abs/2308.13418
[unarxive]: https://arxiv.org/abs/2303.14957
[s2orc]: https://arxiv.org/abs/1911.02782
[funk]: https://www.nature.com/articles/s41586-019-0941-9
[wu]: https://www.nature.com/articles/s41586-019-0941-9
[uzzi]: https://www.science.org/doi/10.1126/science.1240474
[n2v]: https://arxiv.org/abs/1607.00653
[aa]: https://www.sciencedirect.com/science/article/abs/pii/S0378873303000091
[pet]: https://arxiv.org/abs/2306.01949
[qss]: https://direct.mit.edu/qss/article/5/4/936/124788/The-disruption-index-is-biased-by-citation
[win]: https://www.researchgate.net/publication/345473456_Disruption_index_depends_on_length_of_citation_window
[triadic]: https://arxiv.org/pdf/2506.17851
[reana]: https://www.sciencedirect.com/science/article/pii/S1751157724001172
[mhr]: https://arxiv.org/abs/2401.15391

## Non-goals (v1)

- LLM-based entity/relation graph construction (rejected: hallucination
  risk).
- A bundled vector database or GPU parser (optional extras only).
- A single collapsed "research value" score (the metrics framework
  forbids it).

## Exit criteria

- [ ] The graph decision is recorded with tradeoffs and passes the
      war-room gate before any build.
- [ ] `palace_adapter` is the only module importing memory-palace
      internals (one swappable seam).
- [ ] Base (non-graph) research runs unchanged; the graph feature is
      gated by an explicit capability check, not a silent fallback, and
      memory-palace's graph API is public and contract-tested.
- [ ] Each build increment lands as its own reviewable PR on a fresh
      branch, not on the current RED-zone branch.
- [ ] No new hard dependency ships without a supply-chain-advisory note.
