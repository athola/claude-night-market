# Tome Research Plugin -- Specification v0.1.0

**Date**: 2026-03-20
**Status**: Draft
**Input**: docs/tome-project-brief.md

## Overview

**Purpose**: Systematic multi-source research plugin for
Claude Code that triangulates findings across code
repositories, community discourse, academic literature,
and cross-domain analogical reasoning (TRIZ).

**Scope**:

- IN: Autonomous research sessions, interactive refinement,
  4 research channels (code, discourse, academic, TRIZ),
  domain-adaptive TRIZ depth, multi-format output,
  memory-palace compatible export, visualization
- OUT: Real-time topic monitoring, full-text paper
  indexing, collaborative sessions, browser-based journal
  auth, custom TRIZ matrix editing

**Users**: Developers researching implementation approaches,
technical leads evaluating architecture options,
researchers surveying prior art across domains.

## Functional Requirements

### Core Pipeline

#### FR-001: Research Session Orchestration

**Description**: The `/tome:research "topic"` command starts
an autonomous research session that classifies the domain,
selects channels, dispatches parallel agents, synthesizes
findings, and presents results.

**Acceptance Criteria**:

- [ ] Given a topic string, when `/tome:research` is
      invoked, then a ResearchSession object is created
      with a unique ID and persisted to
      `.tome/sessions/{id}.json`
- [ ] Given a new session, when the pipeline starts, then
      the domain classifier runs before any channel agents
      are dispatched
- [ ] Given classified domain and selected channels, when
      agents are dispatched, then they run in parallel via
      the Agent tool
- [ ] Given all agents complete, when synthesis runs, then
      findings are deduplicated by URL and ranked by
      relevance
- [ ] Given synthesis complete, when the report is
      generated, then it uses the format matching the
      domain classification

**Priority**: High
**Dependencies**: FR-002, FR-003
**Effort**: L

#### FR-002: Domain Classification

**Description**: Classify the research topic into a domain
category that determines TRIZ depth, visualization style,
and channel weighting.

**Acceptance Criteria**:

- [ ] Given a topic string, when classified, then one of
      these domains is assigned: ui-ux, algorithm,
      architecture, data-structure, scientific, financial,
      devops, security, general
- [ ] Given a classified domain, when TRIZ depth is
      determined, then it follows the mapping: ui-ux=light,
      algorithm=medium, architecture=medium,
      data-structure=deep, scientific=deep, financial=medium,
      devops=light, security=medium, general=light
- [ ] Given ambiguous input, when classification confidence
      is below 0.6, then the user is asked to confirm or
      override the domain
- [ ] Given a user override, when provided, then
      classification and TRIZ depth update accordingly

**Priority**: High
**Dependencies**: None
**Effort**: M

#### FR-003: Research Planner

**Description**: Select which research channels to activate
and how to weight their results based on domain and topic.

**Acceptance Criteria**:

- [ ] Given domain "algorithm", when planning, then all 4
      channels are activated with academic and TRIZ weighted
      higher
- [ ] Given domain "ui-ux", when planning, then code and
      discourse channels are weighted higher, TRIZ depth is
      light
- [ ] Given any domain, when planning, then at minimum code
      and discourse channels are always activated
- [ ] Given a plan, when output is produced, then it
      includes: channels list, weights dict, triz_depth
      string, and estimated token budget

**Priority**: High
**Dependencies**: FR-002
**Effort**: S

### Code Search Channel

#### FR-010: GitHub Code Search

**Description**: Search GitHub for existing implementations
of the research topic using the GitHub Search API and
WebSearch fallback.

**Acceptance Criteria**:

- [ ] Given a topic, when searching GitHub, then the agent
      queries GitHub code search API with relevant keywords
- [ ] Given API results, when processing, then each result
      includes: repo name, stars, last updated, language,
      relevant file paths
- [ ] Given a repository match, when analyzing, then the
      agent reads key files (README, main module) to extract
      implementation patterns
- [ ] Given GitHub API is rate-limited, when fallback
      triggers, then WebSearch with "site:github.com" query
      is used
- [ ] Given results, when ranked, then ordering considers:
      stars, recency, language match, README quality

**Priority**: High
**Dependencies**: None
**Effort**: M

#### FR-011: Pattern Extraction

**Description**: Extract implementation patterns from
discovered repositories, not just links.

**Acceptance Criteria**:

- [ ] Given a repository, when analyzed, then the agent
      identifies: architecture pattern, key libraries used,
      data structures, and API design choices
- [ ] Given multiple repositories, when patterns are
      compared, then common approaches are identified and
      counted (e.g., "3 of 5 repos use event sourcing")
- [ ] Given extracted patterns, when presented, then each
      includes a 2-3 sentence summary and a code snippet
      reference

**Priority**: Medium
**Dependencies**: FR-010
**Effort**: M

### Community Discourse Channel

#### FR-020: Hacker News Search

**Description**: Search Hacker News via the Algolia API for
discussions, experience reports, and community opinions.

**Acceptance Criteria**:

- [ ] Given a topic, when searching HN, then the Algolia
      HN Search API is queried at
      `hn.algolia.com/api/v1/search`
- [ ] Given results, when filtering, then only stories and
      comments with score > 5 are included
- [ ] Given a high-scoring story, when processing, then
      top comments (by points) are extracted for context
- [ ] Given results, when presented, then each includes:
      title, score, comment count, date, and key quotes
      from top comments

**Priority**: High
**Dependencies**: None
**Effort**: S

#### FR-021: Lobsters Search

**Description**: Search Lobsters for tagged discussions
with typically higher signal-to-noise ratio.

**Acceptance Criteria**:

- [ ] Given a topic, when searching Lobsters, then the
      JSON API at `lobste.rs/search.json` or tag-based
      browsing is used
- [ ] Given results, when processing, then each includes:
      title, score, tags, commenter expertise indicators
- [ ] Given Lobsters is unavailable, when fallback
      triggers, then WebSearch with "site:lobste.rs" is used

**Priority**: Medium
**Dependencies**: None
**Effort**: S

#### FR-022: Reddit Search

**Description**: Search relevant Reddit communities for
technical discussions and experience reports.

**Acceptance Criteria**:

- [ ] Given a topic, when searching Reddit, then relevant
      subreddits are identified (r/programming, r/compsci,
      domain-specific subs) and queried via JSON API
      (append `.json` to URLs)
- [ ] Given results, when filtering, then only posts with
      score > 10 and substantive self-text or top comments
      are included
- [ ] Given Reddit API limits, when throttled, then backoff
      with exponential delay is applied

**Priority**: Medium
**Dependencies**: None
**Effort**: S

#### FR-023: Tech Blog Discovery

**Description**: Find relevant technical blog posts and
articles via targeted web search.

**Acceptance Criteria**:

- [ ] Given a topic, when searching blogs, then WebSearch
      queries target known high-quality domains (e.g.,
      martinfowler.com, blog.pragmaticengineer.com,
      danluu.com, jvns.ca, and domain-relevant sites)
- [ ] Given results, when processing, then WebFetch
      retrieves article content for summarization
- [ ] Given a blog post, when summarized, then the key
      takeaway, author credentials (if available), and
      publication date are included

**Priority**: Medium
**Dependencies**: None
**Effort**: S

### Academic Literature Channel

#### FR-030: arXiv Search

**Description**: Search arXiv for preprints and papers
using the arXiv API.

**Acceptance Criteria**:

- [ ] Given a topic, when searching arXiv, then the arXiv
      API (`export.arxiv.org/api/query`) is queried with
      relevant search terms
- [ ] Given results, when processing, then each includes:
      title, authors, abstract, categories, PDF link,
      submission date
- [ ] Given a relevant paper, when the user requests it,
      then the PDF is fetched via WebFetch and read via
      the Read tool with page-range chunking for papers
      over 20 pages

**Priority**: High
**Dependencies**: FR-033
**Effort**: M

#### FR-031: Semantic Scholar Integration

**Description**: Use Semantic Scholar API for citation
graphs, influence metrics, and open-access PDF discovery.

**Acceptance Criteria**:

- [ ] Given a topic, when searching Semantic Scholar, then
      the API at `api.semanticscholar.org/graph/v1` is
      queried with fields: title, abstract, year, citationCount,
      influentialCitationCount, isOpenAccess, openAccessPdf
- [ ] Given results, when ranked, then citation count and
      influential citation count are primary ranking factors
- [ ] Given rate limiting (100 req/5min), when approaching
      limit, then requests are batched with appropriate
      delays
- [ ] Given a paper with `isOpenAccess: true`, when
      accessing, then the `openAccessPdf.url` is used
      directly

**Priority**: High
**Dependencies**: None
**Effort**: M

#### FR-032: Open Access Discovery Chain

**Description**: For papers not freely available, attempt
multiple access strategies in priority order.

**Acceptance Criteria**:

- [ ] Given a DOI, when checking access, then the
      following chain is tried in order:
      1. Unpaywall API (`api.unpaywall.org/v2/{doi}`)
      2. CORE.ac.uk API search
      3. PubMed Central (if biomedical)
      4. OpenAlex metadata
      5. Author's personal/institutional page (WebSearch)
      6. ResearchGate full-text link
      7. Google Scholar cached version
- [ ] Given all automated access fails, when generating
      fallback guidance, then the report includes:
      public library access instructions (JSTOR via
      library card), DeepDyve rental link, ILL request
      template, author email request template, and
      physical library catalog search guidance
- [ ] Given a successfully accessed paper, when recording,
      then the access method is logged for analytics

**Priority**: High
**Dependencies**: FR-031
**Effort**: L

#### FR-033: PDF Processing Pipeline

**Description**: Fetch, parse, and extract structured
information from academic PDFs.

**Acceptance Criteria**:

- [ ] Given a PDF URL, when fetching, then WebFetch
      downloads the file to a temporary location
- [ ] Given a PDF under 20 pages, when reading, then
      the Claude Read tool processes it in a single pass
- [ ] Given a PDF over 20 pages, when reading, then
      page-range chunking is used (pages 1-20, 21-40,
      etc.) with a synthesis step that merges extracted
      information
- [ ] Given a parsed paper, when extracting, then the
      output includes: title, authors, abstract, key
      findings (3-5 bullets), methodology summary,
      limitations, and cited references relevant to the
      research topic
- [ ] Given a PDF with complex tables, when optional
      pdfplumber extra is installed, then table data is
      extracted as structured dicts

**Priority**: High
**Dependencies**: None
**Effort**: M

### TRIZ Cross-Domain Channel

#### FR-040: Problem Abstraction

**Description**: Abstract the research topic into TRIZ
problem formulation: identify the system, contradictions,
and ideal final result.

**Acceptance Criteria**:

- [ ] Given a topic and domain, when abstracting, then the
      output includes: system description, technical
      contradiction (improving X worsens Y), and ideal
      final result statement
- [ ] Given TRIZ depth "light", when abstracting, then
      only the contradiction is identified without full
      matrix analysis
- [ ] Given TRIZ depth "deep" or "maximum", when
      abstracting, then the full 39-parameter contradiction
      matrix is consulted to suggest inventive principles

**Priority**: Medium
**Dependencies**: FR-002
**Effort**: M

#### FR-041: Adjacent Field Mapping

**Description**: Identify 2-3 fields outside the problem's
primary domain where analogous problems have been solved.

**Acceptance Criteria**:

- [ ] Given a problem abstraction, when mapping fields,
      then Semantic Scholar's "fields of study" taxonomy
      is used to identify 2-3 adjacent fields
- [ ] Given adjacent fields, when searching, then the
      academic channel (FR-030/031) is reused with
      field-specific queries
- [ ] Given cross-domain findings, when presenting, then
      each includes an explicit bridge statement: "In
      [field], [problem] was solved by [approach], which
      maps to your domain as [application]"
- [ ] Given TRIZ depth "light", when mapping, then only
      1 adjacent field is explored
- [ ] Given TRIZ depth "maximum", when mapping, then 3-5
      fields are explored including deliberately distant
      ones (biology for software, materials science for
      data, etc.)

**Priority**: Medium
**Dependencies**: FR-030, FR-031, FR-040
**Effort**: L

#### FR-042: Inventive Principles Application

**Description**: For deep/maximum TRIZ depth, map
Altshuller's 40 inventive principles to the problem domain
and suggest concrete approaches.

**Acceptance Criteria**:

- [ ] Given a technical contradiction, when consulting the
      matrix, then the top 3-5 inventive principles are
      identified
- [ ] Given inventive principles, when applying, then each
      is translated into a domain-specific suggestion with
      a concrete example
- [ ] Given TRIZ depth below "deep", when invoked, then
      this step is skipped entirely

**Priority**: Low (Phase 3)
**Dependencies**: FR-040
**Effort**: M

### Synthesis and Output

#### FR-050: Finding Synthesis

**Description**: Merge findings from all channels into a
coherent, deduplicated, ranked result set.

**Acceptance Criteria**:

- [ ] Given findings from multiple channels, when
      synthesizing, then duplicates (same URL or same
      paper by DOI) are merged
- [ ] Given merged findings, when ranking, then a
      composite score is computed from: relevance (0-1),
      source authority (GitHub stars, citation count,
      HN score), and recency
- [ ] Given ranked findings, when grouping, then they
      are organized by theme (not by source channel)
- [ ] Given a synthesis, when summarizing, then a 3-5
      sentence executive summary is generated capturing
      the key takeaway across all sources

**Priority**: High
**Dependencies**: FR-010, FR-020, FR-030, FR-040
**Effort**: M

#### FR-051: Output Format Selection

**Description**: Generate the research output in the
user's chosen format: report, brief, or transcript.

**Acceptance Criteria**:

- [ ] Given format "report" (default), when generating,
      then a full markdown document is produced with
      sections: Executive Summary, Code Implementations,
      Community Perspectives, Academic Literature, Cross-
      Domain Insights, Recommendations, Citations
- [ ] Given format "brief", when generating, then a
      condensed 1-2 page document is produced with: Key
      Findings (bulleted), Recommended Approach,
      Critical Papers, and Next Steps
- [ ] Given format "transcript", when generating, then
      the raw session log with bookmarked key findings is
      produced
- [ ] Given any format, when outputting, then the file is
      saved to `docs/research/{session_id}-{topic_slug}.md`

**Priority**: High
**Dependencies**: FR-050
**Effort**: M

#### FR-052: Domain-Specific Visualization

**Description**: Generate inline visualizations for simple
cases, delegate complex ones to scry.

**Acceptance Criteria**:

- [ ] Given domain "financial" with numeric data, when
      visualizing, then matplotlib generates inline charts
      (requires optional `viz` extra)
- [ ] Given domain "architecture" with system components,
      when visualizing, then mermaid diagram syntax is
      generated inline
- [ ] Given a complex visualization request, when scry
      is available, then `Skill(scry:record-browser)` or
      mermaid rendering is delegated
- [ ] Given no visualization extras installed, when
      visualizing, then markdown tables and ASCII diagrams
      are used as fallback

**Priority**: Medium (Phase 4)
**Dependencies**: FR-051
**Effort**: M

#### FR-053: Citation Generation

**Description**: Generate properly formatted citations for
all findings in the research report.

**Acceptance Criteria**:

- [ ] Given academic papers, when citing, then citations
      follow a consistent format: Author(s), "Title",
      Venue/Journal, Year. DOI/URL
- [ ] Given GitHub repos, when citing, then format is:
      Author/Org, "Repo Name", GitHub, Stars, Last Updated.
      URL
- [ ] Given HN/Reddit posts, when citing, then format is:
      Username, "Title", Platform, Score, Date. URL
- [ ] Given all findings, when `/tome:cite` is invoked,
      then a standalone bibliography is generated

**Priority**: Medium
**Dependencies**: FR-050
**Effort**: S

### Interactive Refinement

#### FR-060: Dig Deeper Command

**Description**: After the autonomous pass completes, the
user can interactively refine results with `/tome:dig`.

**Acceptance Criteria**:

- [ ] Given a completed research session, when
      `/tome:dig "subtopic"` is invoked, then additional
      targeted searches run on the specified subtopic
      using the same channels
- [ ] Given `/tome:dig --channel academic "query"`, when
      invoked, then only the academic channel runs
- [ ] Given dig results, when returning, then new
      findings are merged into the existing session and
      the report is updated
- [ ] Given no active session, when `/tome:dig` is
      invoked, then an error message directs the user
      to start a session with `/tome:research`

**Priority**: High
**Dependencies**: FR-001, FR-050
**Effort**: M

#### FR-061: Session Persistence

**Description**: Research sessions persist across
conversation boundaries via filesystem state.

**Acceptance Criteria**:

- [ ] Given an active session, when the conversation
      ends or is cleared, then session state is saved to
      `.tome/sessions/{id}.json`
- [ ] Given a saved session, when `/tome:research --resume`
      is invoked, then the most recent session is loaded
- [ ] Given multiple saved sessions, when
      `/tome:research --list` is invoked, then sessions
      are listed with topic, date, status, and finding
      count
- [ ] Given a PreCompact hook fires, when the session is
      active, then state is checkpointed automatically

**Priority**: Medium
**Dependencies**: FR-001
**Effort**: S

### Integration

#### FR-070: Memory-Palace Export

**Description**: Export research findings in a format
compatible with memory-palace's knowledge-intake skill.

**Acceptance Criteria**:

- [ ] Given a completed session, when `/tome:export` is
      invoked, then findings are formatted as a
      knowledge-intake compatible markdown file
- [ ] Given exported findings, when memory-palace
      processes them, then they can be stored in a
      palace room without manual reformatting
- [ ] Given an export, when metadata is included, then
      it contains: source URLs, access dates, relevance
      scores, and domain classification

**Priority**: Medium (Phase 5)
**Dependencies**: FR-051
**Effort**: S

#### FR-071: Scry Visualization Delegation

**Description**: Delegate complex visualization tasks to
the scry plugin when available.

**Acceptance Criteria**:

- [ ] Given a mermaid diagram needed, when scry is
      installed, then `Skill(scry:record-browser)` or
      MCP mermaid tool is used to render
- [ ] Given scry is not installed, when visualization is
      needed, then raw mermaid syntax is included in the
      report with a note to render externally
- [ ] Given delegation, when scry returns, then the
      generated asset path is embedded in the report

**Priority**: Low (Phase 4)
**Dependencies**: FR-052
**Effort**: S

## Non-Functional Requirements

### NFR-001: Performance

- Autonomous research pass completes in under 5 minutes
  for typical topics
- Individual channel agents complete in under 90 seconds
- Session state save/load under 1 second
- PDF processing: under 30 seconds per 20-page paper

### NFR-002: Rate Limit Compliance

- GitHub API: stay under 5000 requests/hour
- Semantic Scholar: stay under 100 requests/5 minutes
  with automatic backoff
- HN Algolia: respect rate limits (undocumented, use
  1-second delays between requests)
- Reddit: respect robots.txt, use 2-second delays
- All external APIs: implement exponential backoff on
  429 responses

### NFR-003: Token Efficiency

- Research agents use targeted reads, not full file dumps
- PDF pages are read in ranges, not entirely
- Findings are summarized before synthesis to reduce
  context size
- Agent prompts are focused and scoped (under 2000 tokens
  each)

### NFR-004: Graceful Degradation

- If any single channel fails, the session continues
  with remaining channels
- If all external APIs are down, WebSearch fallback is
  attempted for each channel
- If no results are found, the report states this
  explicitly rather than hallucinating

### NFR-005: Legal Compliance

- All journal access methods are legal
- Sci-Hub is explicitly excluded
- robots.txt is respected for all web scraping
- API terms of service are followed
- Author email templates include proper academic etiquette

## Technical Constraints

**Stack**:

- Python 3.9+ (match ecosystem)
- No required heavy dependencies in core
- Optional extras: `viz` (matplotlib), `pdf` (pdfplumber),
  `full` (all optional deps)

**Plugin structure**:

```
plugins/tome/
  .claude-plugin/
    plugin.json
    metadata.json
  skills/
    research/SKILL.md          # orchestration hub
    code-search/SKILL.md
    discourse/SKILL.md
    papers/SKILL.md
    triz/SKILL.md
    synthesize/SKILL.md
  agents/
    code-searcher.md
    discourse-scanner.md
    literature-reviewer.md
    triz-analyst.md
  commands/
    research.md
    dig.md
    cite.md
    export.md
  hooks/
    hooks.json
    session_start.py
    pre_compact.py
  scripts/
    domain_classifier.py
    research_planner.py
    finding_ranker.py
    session_manager.py
    api_clients.py
    pdf_processor.py
    triz_engine.py
    citation_formatter.py
  src/tome/
    __init__.py
    models.py               # dataclasses
    session.py               # session management
    channels/
      __init__.py
      github.py
      discourse.py
      academic.py
      triz.py
    synthesis/
      __init__.py
      merger.py
      ranker.py
      formatter.py
    output/
      __init__.py
      report.py
      brief.py
      transcript.py
      visualizer.py
      citations.py
  tests/
    conftest.py
    test_models.py
    test_session.py
    test_domain_classifier.py
    channels/
      test_github.py
      test_discourse.py
      test_academic.py
      test_triz.py
    synthesis/
      test_merger.py
      test_ranker.py
      test_formatter.py
    output/
      test_report.py
      test_citations.py
  pyproject.toml
  README.md
  openpackage.yml
```

**External APIs**:

| API | Auth | Rate Limit | Free |
|-----|------|-----------|------|
| GitHub Search | Token (optional) | 5000/hr (auth), 60/hr (unauth) | Yes |
| HN Algolia | None | Undocumented | Yes |
| Lobsters | None | Respectful | Yes |
| Reddit JSON | None | 60/min | Yes |
| arXiv | None | Unlimited (metadata) | Yes |
| Semantic Scholar | API Key (optional) | 100/5min (unauth) | Yes |
| Unpaywall | Email param | 100K/day | Yes |
| OpenAlex | None | Unlimited | Yes |
| CORE | API Key | 10K/month free | Yes |
| PubMed/Europe PMC | None | 3 req/sec | Yes |

## Phased Delivery

### Phase 1: Core + Code + Discourse

**Requirements**: FR-001, FR-002, FR-003, FR-010, FR-011,
FR-020, FR-021, FR-022, FR-023, FR-050, FR-051, FR-060,
FR-061

**Acceptance**: `/tome:research "async python patterns"`
returns a report with GitHub repos and HN/Reddit
discussions, and `/tome:dig` refines results.

### Phase 2: Academic Literature

**Requirements**: FR-030, FR-031, FR-032, FR-033, FR-053

**Acceptance**: `/tome:research "raft consensus"` returns
academic papers with parsed PDF content and proper
citations, with fallback guidance for paywalled papers.

### Phase 3: TRIZ Cross-Domain

**Requirements**: FR-040, FR-041, FR-042

**Acceptance**: `/tome:research "novel cache eviction"`
identifies adjacent-field solutions (e.g., memory
management in operating systems, inventory management
in logistics) with explicit bridge mappings.

### Phase 4: Visualization

**Requirements**: FR-052, FR-071

**Acceptance**: Financial research includes inline charts,
architecture research includes mermaid diagrams,
complex visuals delegate to scry.

### Phase 5: Integration Polish

**Requirements**: FR-070

**Acceptance**: `/tome:export` produces a file that
memory-palace's `knowledge-intake` skill can process
without manual editing.

## Glossary

- **TRIZ**: Theory of Inventive Problem Solving (Teoriya
  Resheniya Izobretatelskikh Zadatch), developed by
  Genrich Altshuller
- **Adjacent field**: A domain outside the primary problem
  area where analogous problems have been solved
- **Bridge mapping**: An explicit explanation of how a
  solution from one domain applies to another
- **Contradiction matrix**: TRIZ tool mapping 39 engineering
  parameters to 40 inventive principles
- **Open access**: Academic content freely available
  without subscription or payment
- **DOI**: Digital Object Identifier, unique paper ID

## Feature Review Enrichment (v1.8.0)

### Purpose

Integrate tome's multi-source research into
`imbue:feature-review` so that scoring factors (Reach,
Impact, Business Value) are grounded in external evidence
rather than pure intuition.
The `--research` flag activates an optional Phase 4.5
between tradeoff analysis and gap analysis.

### Channel-to-Factor Mapping

| Channel | Primary Factor | Secondary Factor | Evidence Type |
|---------|---------------|-----------------|---------------|
| code-search | Reach | Complexity | Competitor count, star counts |
| discourse | Impact | Business Value | Community sentiment, request volume |
| papers | Impact | Risk | Academic validation, novelty |
| triz | Business Value | Impact | Cross-domain analogies |

### Score Adjustment Formula

Research produces adjustment deltas, not replacements.
The initial human assessment is always preserved.

```
adjusted = initial + research_delta * evidence_weight

research_delta: -2 to +2
evidence_weight: 0.0 to 1.0 (discard if < 0.3)
```

Adjusted scores clamp to the Fibonacci scale
(1, 2, 3, 5, 8, 13).
Maximum adjustment per factor: +/- 2 scale points.

### Graceful Degradation

When tome is not installed, `--research` prints a warning
and feature-review proceeds with initial scores unchanged.
No error, no abort.

### Acceptance Criteria

1. `--research` triggers Phase 4.5 between tradeoff
   analysis and gap analysis
2. Research findings produce score deltas weighted by
   evidence confidence
3. Adjusted scores clamp to the Fibonacci scale
4. Graceful degradation when tome is unavailable
5. Output includes an evidence summary when research runs
6. Existing tests pass unchanged; new tests cover delta
   calculation, clamping, degradation, and channel mapping
