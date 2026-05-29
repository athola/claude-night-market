# Capture-Index Methods: Research Findings

**Date**: 2026-05-27
**Mission**: Incorporate, analyze, and learn from
`plugins/memory-palace/hooks/memory-palace-index.yaml`
**Channels**: GitHub code search, community discourse, academic literature
(three parallel `tome` agents)

## Summary

Three findings shape the implementation, and they agree across channels.

First, **draining a capture inbox is a state-machine problem, not a
machine-learning problem**. Real personal-knowledge-management (PKM)
tools track maturity with explicit frontmatter fields and cheap signals
(word count, link count, frontmatter completeness), and reserve any
LLM or embedding call for *suggesting* where a note belongs, never for
the promote/archive decision itself. The dominant practitioner
experience is that capture inboxes become "graveyards": intake far
outpaces processing, and the promotion that actually fires is driven by
*use* (linking, citing, revisiting), not by ceremony. The corollary
matters for our 484 inert entries: a note that is never reused is a
signal to archive, not to promote.

Second, **at 500 to 5000 documents, keyword search (BM25) is the
workhorse and embeddings are an optional additive stage**. Every hybrid
implementation runs BM25 as the base layer and fuses optional vector
results with Reciprocal Rank Fusion. Practitioners report that local
embeddings earn their cost only for vocabulary-mismatch discovery, and
that the real cost is operational (RAM, GPU, index upkeep), not poor
relevance. The memory-palace plugin already ships an *optional*
`embedding_index`, so the right default is keyword-first with embeddings
left off until a concrete recall failure appears.

Third, **the existing 14/30/90-day exponential decay half-lives are a
defensible engineering heuristic, not an empirically privileged
constant**. The strongest memory-science evidence favors a power law
over a single exponential, and modern spaced-repetition systems use
exponential decay only with a *learned per-item* half-life. For
near-duplicate detection at this scale, a SHA-256 exact-match first pass
(already present) followed by MinHash with shingling is the
best-grounded and cheapest choice; embeddings-based semantic dedup is
reserved for paraphrase detection at far larger scale.

## Findings

### 1. Promotion lifecycle and inbox draining

Real tools encode maturity explicitly and derive it from cheap signals:

- `karx/kaaroGarden` uses a four-stage enum (STUB, SEED, BUDDING,
  EVERGREEN) keyed off word count, plus a composite readiness score
  (name quality, frontmatter completeness, maturity) and a
  `published: true` approval gate.
- `twaugh/logsqueak` tracks promotion provenance with paired backlink
  markers so the transition stays non-destructive and auditable, using
  embeddings only for semantic placement suggestions.

Practitioners report that the canonical digital-garden frameworks
describe stages but specify no concrete promotion trigger. The trigger
that fires in practice is linking, citing, or revisiting a note in real
work. Notes never reused are the graveyard, and the honest fix is "build
a drain, not a bigger funnel": auto-archive or snooze stale items rather
than let them accumulate.

**Implication for this mission**: the promotion engine must classify
entries into promote, hold, and archive paths. Word count and recency
drive promotion; orphaned and never-revisited entries drive archival.
The transition stays deterministic, and any model call is advisory only.

### 2. Local-corpus retrieval

- `xhluca/bm25s` is a pure-Python, NumPy-only BM25 that indexes a small
  corpus in milliseconds with `.save()` / `.load()` persistence: the
  strongest keyword-first option at our scale.
- `flowing-abyss/obsidian-hybrid-search` and
  `liamca/sqlite-hybrid-search` both run BM25 plus optional vector KNN
  fused with Reciprocal Rank Fusion (`score += 1 / (k + rank + 1)`,
  k=60). SQLite FTS5 yields BM25 "for free" alongside `sqlite-vec`.

The community debate (Doug Turnbull, several HN threads) converges on:
start with keyword search, reach for embeddings only when balancing many
relevance signals or solving vocabulary mismatch.

**Implication**: reuse the plugin's existing `cache_lookup` /
`keyword_index` for retrieval. Do not add an embedding dependency for
the index-surfacing hook.

### 3. Decay form and importance scoring

- Murre & Dros (2015) confirm a decelerating forgetting curve; Wixted &
  Ebbesen (1991, 1997) argue forgetting follows a power law, beating a
  single exponential.
- Half-Life Regression (Settles & Meeder, 2016) and FSRS (Ye, Su & Cao,
  2022) validate exponential decay only with a *learned, per-item*
  half-life that adapts on access.
- PageRank (Page et al., 1998) and temporal-dynamics ranking (Koren,
  2009) ground an importance formula of the form
  `relevance = w1 * centrality + w2 * decay(t) + w3 * usage`.

**Implication**: keep `decay_model.py` (14/30/90-day exponential) as a
reasonable coarse default but document it as a tunable prior, not a
retention constant. Calibrate against reopen logs if usage data
accrues. The plugin already has every term of the importance formula
(`graph_analyzer` PageRank, `decay_model`, `usage_tracker`).

### 4. Near-duplicate detection

- Broder (1997) MinHash with k-shingling estimates Jaccard similarity
  and is the best-grounded syntactic near-duplicate method; trivial
  compute at 500 documents.
- Charikar (2002) and Manku et al. (2007) SimHash is preferable only at
  tens of thousands of documents.
- The `text-dedup` benchmark measured MinHash at 11s versus SimHash at
  626s on the same corpus.

**Implication**: a SHA-256 exact-match first pass (the plugin's existing
`content_hash`) catches byte-identical recaptures; MinHash with
shingling handles near-duplicates. No embedding dependency needed.

## Recommendations (applied to the implementation)

1. **Incorporation engine** classifies each pending entry into promote,
   hold, or archive. Promotion uses recency, domain authority, and topic
   cluster size; archival targets orphans and stale never-revisited
   captures. Transitions are deterministic and dry-run by default.
2. **Retrieval and surfacing** reuse the existing keyword path; no new
   embedding dependency.
3. **Decay** stays on the existing model; this document records that the
   half-lives are tunable priors, with power-law or adaptive decay noted
   as future calibration work.
4. **Dedup** layers SHA-256 exact match (present) then MinHash for
   near-duplicates.

## Evidence

Code search:

- bm25s: https://github.com/xhluca/bm25s
- obsidian-hybrid-search: https://github.com/flowing-abyss/obsidian-hybrid-search
- sqlite-hybrid-search: https://github.com/liamca/sqlite-hybrid-search
- kaaroGarden: https://github.com/karx/kaaroGarden
- logsqueak: https://github.com/twaugh/logsqueak
- datasketch: https://github.com/ekzhu/datasketch
- text-dedup: https://github.com/ChenghaoMou/text-dedup
- reor: https://github.com/reorproject/reor

Discourse:

- Ask HN, read-it-later apps: https://news.ycombinator.com/item?id=46880866
- "Your Notes Are a Graveyard" (Kumar):
  https://anshulkumar.substack.com/p/your-notes-are-a-graveyard-heres
- "Agentic search is having a grep moment" (Turnbull):
  https://softwaredoug.com/blog/2026/04/06/agentic-search-is-having-a-grep-moment
- HN, "The RAG Obituary": https://news.ycombinator.com/item?id=45439997
- Maggie Appleton, "Growing the Evergreens":
  https://maggieappleton.com/evergreens

Literature:

- Murre & Dros (2015), PLOS ONE:
  https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0120644
- Wixted & Ebbesen (1997):
  http://wixtedlab.ucsd.edu/publications/wixted/Wixted_and_Ebbesen_(1997).pdf
- Settles & Meeder (2016), Half-Life Regression, ACL:
  https://aclanthology.org/P16-1174/
- Ye, Su & Cao (2022), SSP-MMC, KDD:
  https://ieeexplore.ieee.org/document/10059206/
- Page et al. (1998), PageRank: http://ilpubs.stanford.edu:8090/422/
- Koren (2009), Temporal Dynamics, KDD:
  https://faculty.cc.gatech.edu/~zha/CSE8801/CF/kdd-fp074-koren.pdf
- Broder (1997), MinHash:
  https://www.cs.princeton.edu/courses/archive/spring13/cos598C/broder97resemblance.pdf
- Charikar (2002), SimHash: https://dl.acm.org/doi/10.1145/509907.509965
- Abbas et al. (2023), SemDeDup: https://arxiv.org/abs/2303.09540
