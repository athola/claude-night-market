# Tome Research Plugin -- Implementation Plan v1.0

**Date**: 2026-03-20
**Input**: docs/tome-specification.md
**Delivery**: 5 phases, incremental

## Architecture

### System Overview

Pipeline-hybrid architecture: a skill orchestrates
the research session, dispatches parallel agents for
each channel, and merges results in the main thread
for interactive refinement.

```
┌──────────────────────────────────────────────┐
│            /tome:research "topic"            │
│                  (command)                    │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│         research skill (orchestrator)        │
│  ┌────────────┐  ┌───────────────────────┐   │
│  │  domain    │  │   research planner    │   │
│  │ classifier │─▶│ (channels, weights,   │   │
│  │            │  │  triz depth)          │   │
│  └────────────┘  └───────────┬───────────┘   │
└──────────────────────────────┼───────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
  ┌───────────────┐ ┌──────────────┐ ┌──────────────┐
  │ code-searcher │ │  discourse-  │ │  literature-  │
  │    (agent)    │ │   scanner    │ │   reviewer    │
  │               │ │   (agent)    │ │   (agent)     │
  │ GitHub API    │ │ HN/lobsters/ │ │ arXiv/S2/     │
  │ WebSearch     │ │ reddit/blogs │ │ Unpaywall     │
  └───────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
              ┌───────────────────────┐
              │   synthesize skill    │
              │  merge, rank, format  │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   output formatter    │
              │  report/brief/xscript │
              │  + domain viz         │
              └───────────────────────┘
```

### Components

#### Component: Domain Classifier (`scripts/domain_classifier.py`)

**Responsibility**: Classify topic into domain category,
determine TRIZ depth and channel weights.

**Interface**:
```python
def classify(topic: str) -> DomainClassification:
    """Return domain, triz_depth, channel_weights."""
```

**Logic**: Keyword matching against domain vocabularies
with confidence scoring. Falls back to "general" if
confidence < 0.6 and no user override.

#### Component: Session Manager (`src/tome/session.py`)

**Responsibility**: Create, persist, load, and list
research sessions. Filesystem-backed via
`.tome/sessions/`.

**Interface**:
```python
class SessionManager:
    def create(topic, domain, triz_depth) -> Session
    def save(session) -> None
    def load(session_id) -> Session
    def load_latest() -> Session | None
    def list_all() -> list[SessionSummary]
```

#### Component: Channel Agents (4 agent .md files)

**Responsibility**: Each agent autonomously searches one
channel, extracts findings, and returns structured
results. Agents use WebFetch, WebSearch, Read, and Bash.

**Shared output contract**:
```python
{
    "channel": str,          # code/discourse/academic/triz
    "findings": list[dict],  # Finding-compatible dicts
    "errors": list[str],     # any failures
    "metadata": dict         # channel-specific stats
}
```

#### Component: Synthesizer (`src/tome/synthesis/`)

**Responsibility**: Merge findings from all channels,
deduplicate by URL/DOI, rank by composite score, group
by theme.

#### Component: Output Formatter (`src/tome/output/`)

**Responsibility**: Generate report, brief, or transcript
from synthesized findings. Handle domain-specific
visualization.

### Data Flow

1. User invokes `/tome:research "topic"`
2. Command loads research skill
3. Skill runs domain classifier on topic
4. Research planner selects channels and weights
5. Session is created and persisted
6. Parallel agents dispatched (up to 3 concurrent)
7. Each agent returns findings in shared contract
8. Synthesizer merges, deduplicates, ranks
9. Formatter generates output in selected format
10. Report saved, session marked complete
11. User can invoke `/tome:dig` for refinement

## Task Breakdown

### Phase 1: Foundation + Code + Discourse

#### T-001: Initialize Plugin Structure

**Type**: Implementation
**Priority**: P0
**Effort**: S
**Dependencies**: None

Create the `plugins/tome/` directory tree matching the
specification's plugin structure. Include pyproject.toml,
plugin.json, metadata.json, openpackage.yml, README.md,
conftest.py.

**Acceptance**:

- [ ] `plugins/tome/.claude-plugin/plugin.json` valid
- [ ] `pyproject.toml` with hatchling build, Python 3.9+
- [ ] Empty `__init__.py` files in all packages
- [ ] `make test` passes (0 tests, 0 errors)

#### T-002: Data Models

**Type**: Implementation
**Priority**: P0
**Effort**: S
**Dependencies**: T-001

Implement `src/tome/models.py` with dataclasses:
ResearchSession, Finding, DomainClassification,
ResearchReport, SessionSummary, Citation.

**Acceptance**:

- [ ] All dataclasses serializable to/from JSON
- [ ] Finding has: source, channel, title, url, relevance,
      summary, metadata
- [ ] Session has: id, topic, domain, triz_depth, channels,
      findings, status, timestamps
- [ ] Tests cover serialization round-trip

#### T-003: Session Manager

**Type**: Implementation
**Priority**: P0
**Effort**: S
**Dependencies**: T-002

Implement `src/tome/session.py` with create, save, load,
load_latest, list_all. Storage in `.tome/sessions/`.

**Acceptance**:

- [ ] `create()` generates UUID-based ID and timestamp
- [ ] `save()` writes JSON to `.tome/sessions/{id}.json`
- [ ] `load()` reads and deserializes session
- [ ] `list_all()` returns summaries sorted by date
- [ ] Tests cover create-save-load round-trip

#### T-004: Domain Classifier

**Type**: Implementation
**Priority**: P0
**Effort**: M
**Dependencies**: T-002

Implement `scripts/domain_classifier.py` with keyword
vocabularies for each domain. Return domain, triz_depth,
channel_weights, confidence.

**Acceptance**:

- [ ] Classifies "async python patterns" as algorithm/medium
- [ ] Classifies "react component library" as ui-ux/light
- [ ] Classifies "raft consensus" as algorithm/medium
- [ ] Classifies "cache eviction policy" as
      data-structure/deep
- [ ] Returns confidence score, falls back to "general"
      below 0.6
- [ ] Tests cover all 9 domain categories

#### T-005: Research Planner

**Type**: Implementation
**Priority**: P0
**Effort**: S
**Dependencies**: T-004

Implement `scripts/research_planner.py` that takes a
DomainClassification and returns a ResearchPlan:
channels, weights, triz_depth, estimated_budget.

**Acceptance**:

- [ ] All plans include code + discourse channels minimum
- [ ] Academic channel included for medium+ TRIZ depth
- [ ] TRIZ channel included for deep+ TRIZ depth
- [ ] Weights sum to 1.0
- [ ] Tests cover each domain's expected plan

#### T-006: GitHub Code Search Agent

**Type**: Implementation
**Priority**: P0
**Effort**: M
**Dependencies**: T-002

Create `agents/code-searcher.md` agent definition.
Implement `src/tome/channels/github.py` with search
logic using WebSearch (site:github.com queries) and
optional GitHub API via Bash curl.

**Acceptance**:

- [ ] Agent definition has proper frontmatter (name,
      description, tools)
- [ ] Searches GitHub with topic-derived queries
- [ ] Returns findings with: repo name, URL, stars,
      language, pattern summary
- [ ] Handles rate limits gracefully
- [ ] Tests mock WebSearch responses

#### T-007: HN Search

**Type**: Implementation
**Priority**: P0
**Effort**: S
**Dependencies**: T-002

Implement HN channel in `src/tome/channels/discourse.py`
using Algolia HN API via WebFetch.

**Acceptance**:

- [ ] Queries `hn.algolia.com/api/v1/search` with topic
- [ ] Filters results by score > 5
- [ ] Extracts top comments from high-scoring stories
- [ ] Returns Finding objects with title, score, URL, quotes
- [ ] Tests mock API responses

#### T-008: Lobsters Search

**Type**: Implementation
**Priority**: P1
**Effort**: S
**Dependencies**: T-007

Add Lobsters channel to `src/tome/channels/discourse.py`
using lobste.rs JSON API or WebSearch fallback.

**Acceptance**:

- [ ] Queries lobsters search or tag API
- [ ] Falls back to WebSearch if API unavailable
- [ ] Returns findings with tags and scores
- [ ] Tests cover both API and fallback paths

#### T-009: Reddit Search

**Type**: Implementation
**Priority**: P1
**Effort**: S
**Dependencies**: T-007

Add Reddit channel to `src/tome/channels/discourse.py`
using old.reddit.com JSON API (append `.json`).

**Acceptance**:

- [ ] Identifies relevant subreddits for the topic
- [ ] Queries with `.json` suffix on search URLs
- [ ] Filters posts by score > 10
- [ ] Respects 2-second delay between requests
- [ ] Tests mock JSON responses

#### T-010: Tech Blog Discovery

**Type**: Implementation
**Priority**: P2
**Effort**: S
**Dependencies**: T-007

Add blog search to `src/tome/channels/discourse.py`
using WebSearch with curated site list.

**Acceptance**:

- [ ] Searches known high-quality blog domains
- [ ] Fetches article content via WebFetch for summary
- [ ] Returns findings with author, date, key takeaway
- [ ] Tests cover search query construction

#### T-011: Discourse Scanner Agent

**Type**: Implementation
**Priority**: P0
**Effort**: S
**Dependencies**: T-007, T-008, T-009, T-010

Create `agents/discourse-scanner.md` that invokes the
discourse channel functions and returns merged findings.

**Acceptance**:

- [ ] Agent frontmatter properly configured
- [ ] Searches HN, lobsters, reddit, blogs in sequence
- [ ] Merges findings with source attribution
- [ ] Handles individual source failures gracefully

#### T-012: Finding Synthesizer

**Type**: Implementation
**Priority**: P0
**Effort**: M
**Dependencies**: T-002

Implement `src/tome/synthesis/merger.py` and
`src/tome/synthesis/ranker.py`.

**Acceptance**:

- [ ] Deduplicates findings by URL
- [ ] Computes composite relevance score from: source
      authority, recency, keyword match
- [ ] Groups findings by theme using keyword clustering
- [ ] Generates 3-5 sentence executive summary
- [ ] Tests cover dedup, ranking, and grouping

#### T-013: Output Formatter -- Report

**Type**: Implementation
**Priority**: P0
**Effort**: M
**Dependencies**: T-012

Implement `src/tome/output/report.py` for full markdown
report generation.

**Acceptance**:

- [ ] Generates sections: Executive Summary, Code
      Implementations, Community Perspectives,
      Recommendations, Citations
- [ ] Saves to `docs/research/{session_id}-{slug}.md`
- [ ] Follows 80-char prose wrapping
- [ ] Tests verify section presence and structure

#### T-014: Output Formatter -- Brief and Transcript

**Type**: Implementation
**Priority**: P1
**Effort**: S
**Dependencies**: T-013

Add brief and transcript formatters.

**Acceptance**:

- [ ] Brief: 1-2 pages with bullets, approach, papers,
      next steps
- [ ] Transcript: raw session log with bookmarks
- [ ] Format selectable via `--format` flag

#### T-015: Research Skill (Orchestrator)

**Type**: Implementation
**Priority**: P0
**Effort**: L
**Dependencies**: T-004, T-005, T-006, T-011, T-012, T-013

Create `skills/research/SKILL.md` as the hub skill that
orchestrates the full pipeline: classify, plan, dispatch
agents, synthesize, format.

**Acceptance**:

- [ ] Invokes domain classifier and planner
- [ ] Dispatches channel agents in parallel via Agent tool
- [ ] Waits for all agents, collects findings
- [ ] Runs synthesizer and formatter
- [ ] Saves session and outputs report
- [ ] Handles partial agent failures gracefully

#### T-016: Research Command

**Type**: Implementation
**Priority**: P0
**Effort**: S
**Dependencies**: T-015

Create `commands/research.md` with frontmatter and usage
docs. Invokes the research skill.

**Acceptance**:

- [ ] `/tome:research "topic"` starts a session
- [ ] `--format report|brief|transcript` selectable
- [ ] `--resume` loads latest session
- [ ] `--list` shows saved sessions

#### T-017: Dig Command (Interactive Refinement)

**Type**: Implementation
**Priority**: P1
**Effort**: M
**Dependencies**: T-015, T-003

Create `commands/dig.md` and supporting
`skills/dig/SKILL.md` for interactive refinement.

**Acceptance**:

- [ ] `/tome:dig "subtopic"` runs targeted search on
      active session
- [ ] `--channel code|discourse|academic` limits scope
- [ ] New findings merge into existing session
- [ ] Error if no active session

#### T-018: Session Hooks

**Type**: Implementation
**Priority**: P2
**Effort**: S
**Dependencies**: T-003

Create `hooks/hooks.json`, `hooks/session_start.py`,
`hooks/pre_compact.py`.

**Acceptance**:

- [ ] SessionStart hook checks for active research session
      and prints status
- [ ] PreCompact hook saves session state before context
      is compacted
- [ ] hooks.json properly configured

### Phase 2: Academic Literature

#### T-020: arXiv API Client

**Type**: Implementation
**Priority**: P0
**Effort**: M
**Dependencies**: T-002

Implement `src/tome/channels/academic.py` with arXiv
search using the Atom API via WebFetch.

**Acceptance**:

- [ ] Queries `export.arxiv.org/api/query` with search
      terms
- [ ] Parses Atom XML response for: title, authors,
      abstract, categories, PDF link, date
- [ ] Returns Finding objects with academic metadata
- [ ] Tests mock XML responses

#### T-021: Semantic Scholar Client

**Type**: Implementation
**Priority**: P0
**Effort**: M
**Dependencies**: T-020

Add Semantic Scholar search to academic channel.

**Acceptance**:

- [ ] Queries `api.semanticscholar.org/graph/v1/paper/search`
- [ ] Requests fields: title, abstract, year,
      citationCount, isOpenAccess, openAccessPdf
- [ ] Implements rate limiting (100 req/5min)
- [ ] Ranks by citation count
- [ ] Tests mock API responses

#### T-022: Open Access Discovery Chain

**Type**: Implementation
**Priority**: P1
**Effort**: L
**Dependencies**: T-021

Implement the access chain: Unpaywall, CORE, PubMed
Central, OpenAlex, author pages, ResearchGate, Google
Scholar cached.

**Acceptance**:

- [ ] Given a DOI, tries each source in priority order
- [ ] Stops at first successful access
- [ ] Logs which method succeeded
- [ ] When all fail, generates fallback guidance with:
      library card instructions, DeepDyve link, ILL
      template, author email template

#### T-023: PDF Processing

**Type**: Implementation
**Priority**: P0
**Effort**: M
**Dependencies**: T-020

Implement `scripts/pdf_processor.py` using Claude Read
tool with page-range chunking.

**Acceptance**:

- [ ] Downloads PDF via WebFetch to temp location
- [ ] Reads <= 20 pages in single Read call
- [ ] Chunks longer papers with page ranges
- [ ] Extracts: title, key findings, methodology,
      limitations
- [ ] Tests cover short and long paper paths

#### T-024: Literature Reviewer Agent

**Type**: Implementation
**Priority**: P0
**Effort**: S
**Dependencies**: T-020, T-021, T-022, T-023

Create `agents/literature-reviewer.md` that orchestrates
the academic channel.

**Acceptance**:

- [ ] Searches arXiv and Semantic Scholar
- [ ] Attempts open access for top results
- [ ] Processes accessible PDFs
- [ ] Returns findings with citation metadata

#### T-025: Citation Formatter

**Type**: Implementation
**Priority**: P1
**Effort**: S
**Dependencies**: T-020

Implement `src/tome/output/citations.py` and
`commands/cite.md`.

**Acceptance**:

- [ ] Academic: Author(s), "Title", Venue, Year. DOI/URL
- [ ] GitHub: Author, "Repo", GitHub, Stars. URL
- [ ] Discourse: User, "Title", Platform, Score. URL
- [ ] `/tome:cite` generates standalone bibliography

### Phase 3: TRIZ Cross-Domain

#### T-030: Problem Abstraction Engine

**Type**: Implementation
**Priority**: P1
**Effort**: M
**Dependencies**: T-004

Implement `scripts/triz_engine.py` with problem
abstraction: system, contradiction, ideal final result.

**Acceptance**:

- [ ] Given topic + domain, produces TRIZ abstraction
- [ ] Light depth: contradiction only
- [ ] Deep depth: full matrix consultation
- [ ] Tests cover each depth level

#### T-031: Adjacent Field Mapper

**Type**: Implementation
**Priority**: P1
**Effort**: M
**Dependencies**: T-030, T-021

Map problem to 2-3 adjacent fields using Semantic
Scholar's field taxonomy.

**Acceptance**:

- [ ] Identifies adjacent fields from S2 field taxonomy
- [ ] Light: 1 field, Deep: 3 fields, Maximum: 5 fields
- [ ] Generates bridge mapping rationale
- [ ] Reuses academic channel for cross-field search

#### T-032: TRIZ Analyst Agent

**Type**: Implementation
**Priority**: P1
**Effort**: S
**Dependencies**: T-030, T-031

Create `agents/triz-analyst.md`.

**Acceptance**:

- [ ] Runs problem abstraction
- [ ] Maps adjacent fields
- [ ] Searches for cross-domain solutions
- [ ] Returns findings with bridge statements

#### T-033: Inventive Principles Application

**Type**: Implementation
**Priority**: P2
**Effort**: M
**Dependencies**: T-030

For deep/maximum depth, map contradictions to
Altshuller's 40 principles.

**Acceptance**:

- [ ] Contradiction matrix data embedded or loaded
- [ ] Top 3-5 principles identified per contradiction
- [ ] Each principle translated to domain-specific
      suggestion
- [ ] Skipped for depth < deep

### Phase 4: Visualization

#### T-040: Inline Visualization

**Type**: Implementation
**Priority**: P2
**Effort**: M
**Dependencies**: T-013

Implement `src/tome/output/visualizer.py` for simple
inline visualizations.

**Acceptance**:

- [ ] Mermaid diagrams for architecture topics
- [ ] Markdown tables for comparison data
- [ ] ASCII diagrams as fallback
- [ ] Optional matplotlib charts with `viz` extra
- [ ] Tests verify output format per domain

#### T-041: Scry Delegation

**Type**: Implementation
**Priority**: P3
**Effort**: S
**Dependencies**: T-040

Delegate complex visualizations to scry when available.

**Acceptance**:

- [ ] Detects scry availability
- [ ] Delegates mermaid rendering
- [ ] Falls back to raw syntax if scry absent
- [ ] Embeds generated asset path in report

### Phase 5: Integration + Polish

#### T-050: Memory-Palace Export

**Type**: Implementation
**Priority**: P2
**Effort**: S
**Dependencies**: T-013

Create `commands/export.md` and export logic.

**Acceptance**:

- [ ] `/tome:export` generates knowledge-intake compatible
      markdown
- [ ] Includes source URLs, dates, relevance scores
- [ ] Can be processed by memory-palace without reformatting

#### T-051: Plugin Registration

**Type**: Implementation
**Priority**: P1
**Effort**: S
**Dependencies**: T-016

Add tome entry to `.claude-plugin/marketplace.json`.

**Acceptance**:

- [ ] Marketplace entry with name, description, keywords
- [ ] Description matches plugin capabilities
- [ ] Keywords enable discovery

#### T-052: Documentation

**Type**: Documentation
**Priority**: P1
**Effort**: M
**Dependencies**: T-016, T-017

Write README.md, update CHANGELOG.md, add book chapter
at `book/src/plugins/tome.md`.

**Acceptance**:

- [ ] README covers: overview, commands, skills, examples
- [ ] Book chapter follows existing plugin page format
- [ ] No AI slop (slop-detector passes)

## Dependency Graph

```
T-001 (init)
  ├─▶ T-002 (models)
  │     ├─▶ T-003 (session mgr) ──▶ T-017 (dig cmd)
  │     │                         ──▶ T-018 (hooks)
  │     ├─▶ T-004 (domain classifier)
  │     │     ├─▶ T-005 (planner)
  │     │     └─▶ T-030 (TRIZ engine) [Phase 3]
  │     ├─▶ T-006 (GitHub search)
  │     ├─▶ T-007 (HN) ──▶ T-008 (lobsters)
  │     │              ──▶ T-009 (reddit)
  │     │              ──▶ T-010 (blogs)
  │     │              ──▶ T-011 (discourse agent)
  │     ├─▶ T-012 (synthesizer)
  │     │     └─▶ T-013 (report formatter)
  │     │           ├─▶ T-014 (brief/transcript)
  │     │           ├─▶ T-040 (viz) [Phase 4]
  │     │           └─▶ T-050 (export) [Phase 5]
  │     └─▶ T-020 (arXiv) [Phase 2]
  │           ├─▶ T-021 (Semantic Scholar)
  │           │     └─▶ T-022 (open access chain)
  │           ├─▶ T-023 (PDF processing)
  │           └─▶ T-024 (literature agent)
  │
  T-005 + T-006 + T-011 + T-012 + T-013
    └─▶ T-015 (research skill/orchestrator)
          └─▶ T-016 (research command)
                └─▶ T-051 (marketplace) + T-052 (docs)
```

## Parallelization Opportunities

Tasks that can be worked on concurrently:

| Batch | Tasks | Rationale |
|-------|-------|-----------|
| 1 | T-001 | Foundation, must be first |
| 2 | T-002, T-003, T-004, T-005 | Core infra, independent |
| 3 | T-006, T-007, T-012 | Channels + synthesis |
| 4 | T-008, T-009, T-010, T-011 | Remaining discourse |
| 5 | T-013, T-014, T-015 | Output + orchestration |
| 6 | T-016, T-017, T-018 | Commands + hooks |

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API rate limits during research | Med | Med | Caching, backoff, WebSearch fallback |
| PDF parsing quality | Low | Med | Page chunking, optional pdfplumber |
| TRIZ contradiction matrix size | Low | Low | Embed as JSON, load on demand |
| Agent token cost | Med | Med | Scope agents tightly, cap findings |
| Lobsters/Reddit API changes | Low | Low | WebSearch fallback for all discourse |

## Checkpoint Gates

| After Phase | Gate |
|-------------|------|
| Phase 1 | `/tome:research "async patterns"` returns report with GitHub + discourse findings |
| Phase 2 | Same query returns academic papers with PDF content |
| Phase 3 | TRIZ bridge findings appear for deep-domain topics |
| Phase 4 | Domain-appropriate visualizations in reports |
| Phase 5 | `/tome:export` output processable by memory-palace |

## Phase 6: Feature Review Integration (v1.8.0)

Integrates tome research into `imbue:feature-review` so
that Reach, Impact, and Business Value scores can be
adjusted with external evidence from code search,
community discourse, papers, and TRIZ analysis.

### Three-phase execution with six tasks

**Phase A: Foundation (T001, T002, T003) -- parallel.**
Create the `research-enrichment` module defining
channel-to-factor mapping, score delta formulas, and
graceful degradation.
Update the configuration module and `.feature-review.yaml`
with a new `research:` section.
Add `tome` as an optional dependency in
`plugins/imbue/.claude-plugin/plugin.json`.

**Phase B: Skill Integration (T004, T005) -- depends on
Phase A.**
Insert Phase 4.5 (Research Enrichment) into the
`feature-review` SKILL.md between tradeoff analysis and
gap analysis, gated by the `--research` flag.
Update `.feature-review.yaml` output sections and plugin
categories to include research evidence.

**Phase C: Tests (T006) -- depends on T001 and T004.**
Add `TestResearchEnrichment` covering delta calculation,
Fibonacci clamping, max delta constraint, evidence
threshold discard, graceful degradation, and channel-to-
factor mapping.

### Execution order

T001, T002, and T003 run in parallel.
T004 depends on T001; T005 depends on T002.
T006 depends on both T001 and T004.
