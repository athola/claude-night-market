# ADR-0018: Reuse memory-palace's Graph for the Tome Research Engine

**Date**: 2026-07-17
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Source**: War-room gate on the tome graph decision; four-track
research pass across academic, code, discourse, and TRIZ channels
**Companion**: `docs/metrics/tome-research-quality.md`

## Context

Tome aggregated research findings into a flat ranked list. Turning it
into a graph-backed engine raised one question large enough to gate the
build: where does the knowledge graph come from?

Three options were on the table, and the evidence resolved them.

| Option | For | Against | Verdict |
|--------|-----|---------|---------|
| Reuse `memory-palace` `KnowledgeGraph` | Entities, temporal triples, and weighted synapses already exist; `PalaceGraphAnalyzer` already gives PageRank, community detection, and Adamic-Adar link prediction; `tome:export` already targets memory-palace; zero new graph code | Cross-plugin coupling; tome gains a dependency on memory-palace internals | **Chosen** |
| Build a tome-native graph | No cross-plugin coupling | Reinvents a working SQLite triple and synapse store; violates `leyline:additive-bias-defense` and the shared-utility-consumer rule; more surface to maintain | Rejected |
| LLM-constructed graph (GraphRAG-style) | Richest entity and relation extraction | Its most-reported failure mode is hallucinated entities corrupting the graph cyclically; expensive indexing | Rejected for construction; the community and summary *ideas* were still adopted |

## Decision

Reuse the graph, embedding, and decay tooling already in
`memory-palace`, and keep the ground-truth citation edges tome already
fetched and discarded. No new graph database, no LLM-based graph
construction, no heavy ML in the hot path.

Two amendments came out of the war-room review and are binding:

1. memory-palace promotes `KnowledgeGraph` and `PalaceGraphAnalyzer`
   into its public `__all__`, so tome consumes a supported API rather
   than internals. A tome CI contract test pins that surface.
2. memory-palace is a **declared dependency** of tome's graph feature,
   not a runtime silent no-op. Absence is an install-time invariant.
   If it is ever genuinely absent, tome raises an explicit
   capability-unavailable signal. Base research is unaffected because
   the graph layer is additive.

Coupling is contained to one module, `tome/graph/palace_adapter.py`,
rather than scattered imports, so it is a single seam that can be
swapped or mocked.

## Evidence

The four research tracks behind the decision. Saturation was reached
after one round: the load-bearing findings cross-validated across
independent channels.

### Track 1: GraphRAG and knowledge-graph construction

The reference architecture is settled. Microsoft GraphRAG
([2404.16130][gr]) extracts an entity and relation graph with an LLM,
partitions it with Leiden community detection, and answers global
queries from community summaries. LightRAG ([2410.05779][lr]) adds
incremental updates, so a growing arXiv corpus needs no full re-index.
HippoRAG ([2405.14831][hr], NeurIPS 2024) runs Personalized PageRank
seeded by query entities for single-shot multi-hop retrieval.

Graph structure is not always worth its cost. GraphRAG-Bench
([2506.02404][grb]) and "When to use Graphs in RAG"
([2506.05690][wtg]) both find the graph wins on multi-hop and complex
reasoning while adding overhead with little gain on simple fact
lookups. Practitioners are blunter: an HN thread on KAG
([230 points][kag]) calls graph RAG "incrementally" better and warns
that LLM-based construction hallucinates entities and "cyclically"
corrupts the graph.

The historical cost objection has collapsed. Indexing a 5GB corpus
fell from roughly $33,000 in early 2024 to roughly $33 by mid-2025,
about 1000x, through model price cuts and LazyGraphRAG deferring
summarization to query time ([Cost Cliff][cc], [TianPan][tp]). The
live objection is accuracy, not 2024 cost lore. This is why the design
keeps ground-truth citation edges and rejects LLM construction.

### Track 2: retrieval and RAG evaluation

Deterministic label-based IR metrics (nDCG@k, MRR, MAP, recall@k) are
the trustworthy yardstick. BEIR ([2104.08663][beir]) standardizes
nDCG@10 and includes the SciFact and SciDocs subsets, the closest
public proxy for tome. TREC Deep Learning ([2003.07820][trec]) defines
the protocols.

Reference-free LLM-judged metrics (RAGAS [2309.15217][ragas]; ARES
[2311.09476][ares]) measure faithfulness without gold labels but cost
trust. RAGAS correlates with human judgment at only about 0.55
harmonic mean ([getmaxim][gm]), and the CALM framework catalogs 12
distinct judge biases including position, verbosity, self-enhancement,
and authority ([Evidently][ev]). This is why the metrics framework
treats judges as directional only.

### Track 3: scientific full-text ingestion

GROBID ([kermitt2/grobid][grobid]) parses PDFs to TEI XML at about 10
PDFs per second, roughly 400x Nougat, and leads reference extraction
at F1 about 0.79 to 0.90 with the deep-learning citation model
([Meuschke 2023][meu]). Nougat ([2308.13418][nougat], ICLR 2024)
preserves math and tables that GROBID's text-layer approach loses, but
it is slow and, by its authors' own disclosure, "skips or
hallucinates" reference numbers in bibliographies. Production setups
run hybrid, one tool primary and the other as fallback, at reported
splits near 94/6.

A pre-built corpus removes most of the burden anyway. unarXive 2022
([2303.14957][unarxive]) ships 1.9M arXiv papers with a resolved
in-text citation network, and S2ORC ([1911.02782][s2orc]) offers 81M
papers with inline citation spans. This is why GROBID is a sidecar,
not a dependency.

### Track 4: novelty, insight, and impact

Graph-native impact signals are cheap to compute. The CD or disruption
index ([Funk and Owen-Smith 2017][funk], validated at scale by
[Wu, Wang, Evans 2019][wu]) labels a paper disruptive or consolidating
from citation structure alone. Uzzi et al. ([2013][uzzi]) score
atypicality from z-scored reference co-occurrence. node2vec
([1607.00653][n2v]) and Adamic-Adar ([aa][aa]) predict missing edges.

Raw citation metrics are biased and must be normalized, the strongest
cross-channel warning in the study. The disruption index is biased by
citation inflation and unsuitable for cross-time comparison
([Petersen 2023][pet], [QSS/MIT][qss]). It depends on the
analyst-chosen citation window, so it is tunable and gameable
([window][win]). It barely overlaps with novelty as a construct
([Triadic Novelty][triadic]). The famous small-teams-disrupt finding
partly dissolves once inflation is corrected ([re-analysis][reana]).
Impact metrics therefore ship field-normalized and cohort-restricted,
with the window fixed and disclosed, never collapsed to one number.

## Consequences

Guards that the decision obliges, each tied to the risk it answers:

| Risk | Guard |
|------|-------|
| Over-building the graph. Graph value is real but bounded to multi-hop | Escalate to the graph on condition; measure the before and after delta on a multi-hop benchmark ([MultiHop-RAG][mhr]); drop the graph path if it does not beat vector retrieval |
| Trusting LLM-judge metrics. 0.55 human correlation, 12 known biases | Deterministic metrics are the headline; judges are labeled "directional" |
| Shipping biased impact numbers | Normalize by field and cohort, fix and disclose the citation window, never collapse to one number |
| Supply-chain surface. Nougat weights are CC-BY-NC, OpenAlex mandates an API key as of Feb 2026, and nano-graphrag and Nougat are both stale | Keep the heavy tier optional and isolated; every new dependency runs through `Skill(leyline:supply-chain-advisory)` |

Dependency policy that follows: the core spine is `networkx` (already
a memory-palace dependency) plus thin `requests`-only API clients
(`arxiv`, `pyalex`, `semanticscholar`). GROBID runs as a Docker
sidecar behind an HTTP client. `sentence-transformers` and `faiss`
stay optional extras, with a hash-vector fallback covering the
default. `microsoft/graphrag` and PyTorch Geometric are out of scope.

Explicitly not adopted: LLM-based entity and relation graph
construction, a bundled vector database or GPU parser, and any single
collapsed "research value" score.

**Evidence gap in the study itself.** Reddit and Lobsters returned no
usable primary discourse (fetch blocks) and Semantic Scholar
rate-limited citation counts. The academic and HN/blog channels
triangulated the key claims, but community breadth is thinner than
ideal.

## Status of implementation

Shipped in `plugins/tome/src/tome/` as `graph/`, `retrieval/`, and
`metrics/`. The five-dimension metric vector and its composite index
are specified in `docs/metrics/tome-research-quality.md`.

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
