# Tome Research Engine: Design Specification

**Date**: 2026-07-17
**Companion to**: [research report](../../research/2026-07-17-tome-research-engine.md),
[metrics framework](../../metrics/tome-research-quality.md)
**Status**: Draft for plan-review + war-room gate before build

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
