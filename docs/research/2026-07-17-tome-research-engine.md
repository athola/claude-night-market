# Tome Research Engine: Deep-Research Report

**Date**: 2026-07-17
**Method**: Dogfooded `tome` across four channels (academic, code,
discourse, TRIZ) over four tracks (GraphRAG/KG construction, retrieval
and RAG evaluation, scientific full-text ingestion, novelty/impact
measurement). Saturation reached after one round: the load-bearing
findings cross-validated across independent channels, so no `dig`
rounds were run (per the exploration-saturation stop rule the research
itself surfaced).

## Thesis

Tome should become best-in-class not by ingesting more, but by
**keeping the citation edges it already discards, linking them into
the knowledge graph that already exists in `memory-palace`, and
serving the graph only when a query needs it.** The external evidence
converges on three disciplines: build a real entity/citation graph
(GraphRAG), but escalate to it on condition, not always; measure
retrieval with deterministic labeled metrics (nDCG/MRR) and treat
LLM-judge scores as directional only; and compute impact/novelty from
graph structure while normalizing away the well-documented biases that
make raw citation metrics misleading. Every heavy dependency (LLM
graph construction, GPU parsers, vector frameworks) is optional and
isolated. The minimal-dependency spine (`networkx`, thin API clients,
a hand-rolled nDCG) already covers the core.

## Track 1: GraphRAG and knowledge-graph construction

**The reference architecture is settled.** Microsoft GraphRAG
([2404.16130][gr]) is the canonical pattern: an LLM extracts an
entity/relation graph, Leiden community detection partitions it, and
community summaries answer global queries. LightRAG
([2410.05779][lr]) adds incremental graph updates (no full re-index
when new papers arrive, which fits a growing arXiv corpus). HippoRAG
([2405.14831][hr], NeurIPS 2024) runs Personalized PageRank seeded by
query entities for single-shot multi-hop retrieval.

**But graph structure is not always worth its cost.** Two 2025
studies isolate where it helps: GraphRAG-Bench ([2506.02404][grb]) and
"When to use Graphs in RAG" ([2506.05690][wtg]) find the graph wins on
multi-hop and complex reasoning, and adds overhead with little gain on
simple fact lookups. Practitioners confirm this bluntly: an HN thread
([KAG][kag], 230 pts) calls graph RAG "incrementally" better, not
transformational, and warns that LLM-based graph construction
hallucinates entities and "cyclically" corrupts the graph.

**The historical dealbreaker was cost, and it collapsed.** Indexing a
5GB corpus fell from roughly $33,000 in early 2024 to roughly $33 by
mid-2025 (about 1000x), driven by model price cuts and LazyGraphRAG
deferring summarization to query time ([Cost Cliff][cc];
[TianPan][tp]). One reported 4M-doc deployment paid about 1.6x infra
for citation accuracy 87 to 96 percent and multi-hop correctness 41 to
78 percent ([TianPan][tp]). The objection to re-evaluate on today is
accuracy, not 2024 cost lore.

**Implication for tome.** Tome already fetches Semantic Scholar
references and citations, then throws the edges away. Keeping those
edges is a graph built from ground-truth citation data, not from
error-prone LLM extraction. That sidesteps the single biggest reported
failure mode (hallucinated graph construction) while capturing most of
the multi-hop value. Serve the graph on condition (multi-hop queries),
not on every lookup.

## Track 2: Retrieval and RAG evaluation

**Two metric families, with a clear trust ordering.** Deterministic,
label-based IR metrics (nDCG@k, MRR, MAP, recall@k) are the trustworthy
yardstick; BEIR ([2104.08663][beir]) standardizes nDCG@10 and includes
the scientific subsets SciFact and SciDocs, the closest public proxy
for tome. TREC Deep Learning ([2003.07820][trec]) defines the metric
protocols. LLM-judged, reference-free metrics (RAGAS
[2309.15217][ragas]; ARES [2311.09476][ares], which adds
prediction-powered confidence intervals) measure faithfulness and
answer/context relevance without gold labels, but at a cost to trust.

**LLM-judge scores are directional, not ground truth.** RAGAS
correlates with human judgment at only about 0.55 harmonic mean
([getmaxim][gm]), and the CALM framework catalogs 12 distinct judge
biases (position, verbosity, self-enhancement, authority)
([Evidently][ev]). The deeper problem, from practitioners: "correct
context does not equal correct answer" ([HN][rag-ready]), so retrieval
success does not imply answer correctness.

**Implication for tome.** Anchor the metrics harness on deterministic
nDCG/MRR/recall against a small hand-labeled arXiv gold set (tome
already knows the query and the returned findings). Offer LLM-judge
faithfulness as an optional, clearly-labeled signal to guard against
hallucinated citations in synthesized answers, never as the headline
score.

## Track 3: Scientific full-text ingestion

**GROBID and Nougat are complementary, not competing.** GROBID
([kermitt2/grobid][grobid]) parses PDFs to TEI XML with header
metadata, sections, and structured references; it is fast (about 10
PDFs/sec, roughly 400x Nougat) and leads reference extraction (F1
about 0.79 to 0.90 with the deep-learning citation model)
([Meuschke 2023][meu]). Nougat ([2308.13418][nougat], ICLR 2024) is a
visual-transformer OCR that preserves math and tables GROBID's
text-layer approach loses, but it is slow and, by its authors' own
disclosure, "skips or hallucinates" reference numbers in
bibliographies. The robust real-world pattern is hybrid: one tool
primary, the other as fallback (reported splits near 94/6), with
cheap PyMuPDF for clean layouts and an ML parser only for math-heavy
pages ([2410.09871][pdfcmp]). Tables and dense numeric data are where
every tool breaks ([CodeCut][cc2]).

**A pre-built corpus removes most of the parsing burden.** unarXive
2022 ([2303.14957][unarxive], JCDL 2023) ships 1.9M arXiv papers with
structured full text and a resolved in-text citation network; S2ORC
([1911.02782][s2orc], ACL 2020) offers 81M papers with inline citation
spans. Tome can bootstrap its citation graph from these instead of
parsing every PDF.

**Implication for tome.** The README claim that tome "parses PDFs" is
aspirational: parsing is deferred to the LLM via markitdown and
captured in no data model. The honest, low-cost path is a structured
paper model (sections plus references) fed by thin API metadata
(arxiv.py, pyalex, semanticscholar) plus optional GROBID as a sidecar
for real full-text extraction. Fix the README to match.

## Track 4: Novelty, insight, and impact

**Graph-native impact signals are computable and cheap.** The CD /
disruption index ([Funk and Owen-Smith 2017][funk]; validated at scale
by [Wu, Wang, Evans 2019][wu], Nature) labels a paper disruptive
versus consolidating purely from citation-network structure. Uzzi et
al. ([2013 Science][uzzi]) score atypicality from z-scored reference
co-occurrence. node2vec ([1607.00653][n2v]) and Adamic-Adar
([2003][aa]) predict missing edges for "papers you should read next."

**But raw citation metrics are biased and must be normalized.** This
is the strongest cross-channel warning in the entire study. The
disruption index is biased by citation inflation and is unsuitable for
cross-time comparison ([Petersen 2023][pet]; [QSS/MIT][qss]); it
depends on the analyst-chosen citation-window length (so it is
tunable and gameable) ([window][win]); disruption and novelty barely
overlap as constructs ([Triadic Novelty][triadic]); and the famous
small-teams-disrupt finding partly dissolves once inflation is
corrected ([re-analysis][reana]).

**Implication for tome.** Impact and novelty metrics are worth
shipping, but only field-normalized and cohort-restricted (compare
within discipline and publication-year band), with the citation window
fixed and disclosed. Present them as one structural signal among
several, never as a single "value" number. This is an evidence-backed
guardrail, not a nice-to-have.

## Cross-cutting design implications

The TRIZ channel framed the core contradiction (comprehensiveness
versus performance/legibility) and its resolution, which the other
three channels' evidence independently supports:

1. **Reuse over rebuild.** The knowledge graph
   (`memory_palace.knowledge_graph.KnowledgeGraph`: entities,
   temporal triples, weighted synapses), its analytics
   (`PalaceGraphAnalyzer`: `pagerank`, `detect_communities`,
   `predict_links` via Adamic-Adar), embeddings (`EmbeddingIndex` with
   a dependency-free hash fallback), and `decay_model` already exist in
   this repo. Tome's `export.py` stops at markdown and never writes to
   them. Wiring tome into them is the highest-value, lowest-code move.
2. **Tiered, on-condition escalation.** Keep a small hot working set
   (summaries, embeddings, recent nodes); reach the full graph and
   full text only when the query is multi-hop. This is TRIZ separation
   in space and on condition, and it matches the GraphRAG "when to use
   graphs" evidence.
3. **Off-line consolidation with decay.** Attach a stability score to
   nodes and edges; let unused ones decay and prune on a schedule, not
   on the read path. `memory_palace.corpus.decay_model` already
   implements the half-life machinery.
4. **Cheap proxies rank, expensive reading is reserved.** Use
   centrality and citation proxies to pick the top-k papers that earn
   full-text loading, so most ranking costs no tokens.
5. **Bandit-style research paths.** Generate "further research paths"
   with an explicit exploit/explore split and an exploration-saturation
   stop rule, so suggestions are novel-and-relevant and bounded, not a
   flood.
6. **Minimal dependency spine.** `networkx` (already a `memory-palace`
   dependency) gives PageRank and Adamic-Adar with zero hard deps;
   `arxiv.py`, `pyalex`, and `semanticscholar` are `requests`-only
   clients; a hand-rolled or `pytrec_eval` nDCG gives deterministic
   metrics with no LLM. Everything heavier (GROBID sidecar,
   microsoft/graphrag, PyTorch Geometric, LLM-judge eval) stays behind
   an optional extra or a service boundary.

## Recommended adoption (prioritized)

| Priority | Move | Basis |
|----------|------|-------|
| 1 | Keep citation edges; write papers as entities and citations as triples/synapses into `memory-palace` `KnowledgeGraph` | reuse; ground-truth edges avoid LLM-construction failure ([KAG][kag]) |
| 2 | `detect_communities` = common threads; `predict_links` (Adamic-Adar) + node2vec = further research paths | [HippoRAG][hr], [n2v][n2v], [aa][aa]; reuse `graph_analyzer` |
| 3 | Deterministic metrics harness (nDCG/MRR/recall@k) on a hand-labeled arXiv gold set; LLM-judge faithfulness optional | [BEIR][beir], [TREC][trec]; distrust of judges ([gm][gm], [ev][ev]) |
| 4 | Structured paper model (sections + references); thin API ingest, GROBID sidecar optional; fix README PDF claim | [GROBID][grobid], [unarXive][unarxive], [Meuschke][meu] |
| 5 | Field-and-cohort-normalized impact/novelty (CD index, atypicality) with fixed citation window | [Funk][funk], [Uzzi][uzzi], with [Petersen][pet]/[QSS][qss] corrections |
| 6 | On-condition graph escalation + decay-based pruning | [when-to-graph][wtg], TRIZ; reuse `decay_model` |

## Adoption risks

- **Over-building the graph.** Evidence says graph value is real but
  bounded to multi-hop. Guard: escalate on condition; measure the
  before/after delta on a multi-hop benchmark ([MultiHop-RAG][mhr]) and
  drop the graph path if it does not beat vector retrieval.
- **Trusting LLM-judge metrics.** 0.55 human correlation, 12 biases.
  Guard: deterministic metrics are the headline; judges are labeled
  "directional."
- **Shipping biased impact numbers.** Citation metrics are confounded
  and gameable. Guard: normalize by field and cohort; fix and disclose
  the citation window; never collapse to one number.
- **Supply-chain surface.** Nougat model weights are CC-BY-NC
  (non-commercial); OpenAlex now mandates an API key (Feb 2026);
  nano-graphrag and Nougat are stale. Guard: keep the heavy tier
  optional and vendored/isolated; run `leyline:supply-chain-advisory`
  on any new dependency.
- **Tool-coverage gaps in this study.** Reddit and Lobsters returned no
  usable primary discourse (fetch blocks); Semantic Scholar
  rate-limited citation counts. The academic and HN/blog channels
  triangulated the key claims, but community breadth is thinner than
  ideal. A rerun with an authenticated Reddit source would strengthen
  the practitioner picture.

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
[rag-ready]: https://news.ycombinator.com/item?id=44701172
[grobid]: https://github.com/kermitt2/grobid
[meu]: https://gipplab.uni-goettingen.de/wp-content/papercite-data/pdf/meuschke2023.pdf
[nougat]: https://arxiv.org/abs/2308.13418
[pdfcmp]: https://arxiv.org/abs/2410.09871
[cc2]: https://codecut.ai/docling-vs-marker-vs-llamaparse/
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
