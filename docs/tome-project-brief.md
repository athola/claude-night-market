# Tome — Research Plugin Project Brief

## Problem Statement

Developers research problems across multiple disconnected
sources: GitHub for implementations, HN/Reddit for community
wisdom, arXiv for papers, journals for deep science. Each
source requires different access patterns, and findings are
never synthesized. Cross-domain insight (applying solutions
from adjacent fields) happens by accident rather than by
method.

Tome brings systematic, multi-source research into the
Claude Code workflow as a night-market plugin.

## Goals

1. Run autonomous multi-source research sessions that
   triangulate findings across code, discourse, and
   literature
2. Apply TRIZ-inspired cross-domain analogical reasoning
   with depth scaled to problem complexity
3. Access academic literature through every available
   channel, with graceful fallbacks when paywalled
4. Present findings in domain-appropriate formats (charts,
   diagrams, tables, citations)
5. Output research in formats compatible with memory-palace
   ingestion

## Success Criteria

- [ ] `/tome:research "topic"` produces a multi-source
      report within a single session
- [ ] At least 4 research channels operational: code,
      discourse, academic, TRIZ
- [ ] PDF papers fetched and parsed via arXiv/open-access
- [ ] TRIZ depth adapts based on domain classifier output
- [ ] Interactive refinement ("dig deeper into X") works
      after autonomous pass
- [ ] Output selectable: report, brief, transcript
- [ ] Simple visualizations inline, complex delegated to
      scry

## Constraints

- **Python**: 3.9+ (ecosystem standard)
- **Dependencies**: Core must be lightweight; heavy deps
  (matplotlib, pdfplumber) as optional extras
- **Available tools**: WebFetch, WebSearch, Read (PDF),
  Bash, Glob, Grep
- **Rate limits**: GitHub API 5000/hr, Semantic Scholar
  100/5min, respect robots.txt everywhere
- **PDF parsing**: Claude Read tool handles PDFs natively
  (max 20 pages per request)
- **Ecosystem integration**: Follow leyline patterns,
  output memory-palace compatible format
- **Scope**: Incremental delivery, not monolithic

## Research Channels

### 1. Code Archaeology (GitHub)

- Search GitHub for implementations via API
- Analyze repository structure, stars, recency
- Extract patterns, not just links
- Fallback: WebSearch for "site:github.com {query}"

### 2. Community Discourse

- **Hacker News**: Algolia HN Search API (free, fast)
- **Lobsters**: RSS/JSON feed + tag search
- **Reddit**: Old Reddit JSON API (append .json to URLs)
- **Tech blogs**: WebSearch with site-specific queries
- Extract: upvoted takes, contrarian views, experience
  reports, war stories

### 3. Academic Literature

**Open access (always available):**
- arXiv API (free, unlimited for metadata, PDF links)
- Semantic Scholar API (100 req/5min, rich metadata,
  citation graphs, open access PDFs)
- PubMed Central / Europe PMC (biomedical, free)
- DOAJ (Directory of Open Access Journals)
- OpenAlex (free, comprehensive metadata)
- Unpaywall API (finds legal free versions)

**Resourceful access:**
- Author preprint pages (personal sites, university repos)
- ResearchGate full-text requests
- Google Scholar cached/HTML versions
- Public library digital access (JSTOR via library cards,
  ProQuest, OverDrive/Libby partnerships)
- Institutional repository searches (DSpace, EPrints)
- CORE.ac.uk (aggregates open-access research)

**Maximum reach fallbacks:**
- DeepDyve (article rental, $0.99-3.99 per article)
- Inter-library loan guidance (free via public libraries)
- Document delivery services (British Library, SUBITO)
- Physical library recommendations with call numbers
- Direct author email templates for requesting copies
  (authors almost always share when asked politely)

**PDF Processing Pipeline:**
1. Fetch PDF via URL (arXiv, open access)
2. Read via Claude Read tool (20 pages max per request)
3. For longer papers: page-range chunking with synthesis
4. Extract: abstract, key findings, methodology, citations
5. Optional: pdfplumber/PyMuPDF for table extraction

### 4. TRIZ Cross-Domain Bridge

**Core method** (Altshuller's inventive problem solving):
- Classify the problem using TRIZ contradiction matrix
- Identify analogous problems in different fields
- Search for solutions in those adjacent fields
- Map solutions back to the original domain

**Dynamic depth based on domain:**

| Domain | TRIZ Depth | Rationale |
|--------|-----------|-----------|
| UI/UX | Light | Analogies useful but not critical |
| Algorithm | Medium | Cross-field algorithms are gold |
| Architecture | Medium | Patterns transfer across domains |
| Novel data structures | Deep | Adjacent-field solutions essential |
| Scientific computing | Deep | Mathematics crosses all fields |
| Stuck/blocked problems | Maximum | Full contradiction analysis |

**Tangential field selection:**
- Use Semantic Scholar's "fields of study" taxonomy
- Map problem keywords to 2-3 adjacent fields
- Search those fields for solved analogues
- Present bridges with explicit mapping rationale

## Architecture

### Pipeline + Agent Hybrid

```
/tome:research "topic"
  -> DomainClassifier (determines type, TRIZ depth)
  -> ResearchPlanner (selects channels, allocates effort)
  -> Parallel Agent Dispatch:
     | Agent: code-searcher
     | Agent: discourse-scanner
     | Agent: literature-reviewer
     | Agent: triz-analyst (if depth > light)
  -> Synthesizer (merge, deduplicate, rank)
  -> Formatter (domain-appropriate output)
  -> InteractiveShell (refinement commands)
```

### Plugin Components

**Skills:**
- `research` — main orchestration skill (hub)
- `code-search` — GitHub implementation search
- `discourse` — HN/lobsters/reddit scanning
- `papers` — academic literature search and parsing
- `triz` — cross-domain analogical reasoning
- `synthesize` — merge and format findings

**Agents:**
- `code-searcher` — autonomous code research
- `discourse-scanner` — autonomous community search
- `literature-reviewer` — autonomous paper search
- `triz-analyst` — autonomous cross-domain analysis

**Commands:**
- `/tome:research` — full research session
- `/tome:dig` — interactive refinement ("dig deeper")
- `/tome:cite` — generate citations from session
- `/tome:export` — export to memory-palace format

**Hooks:**
- `SessionStart` — load active research session if any
- `PreCompact` — checkpoint research state before compact

### Data Model

```python
@dataclass
class ResearchSession:
    id: str
    topic: str
    domain: str           # classified domain
    triz_depth: str       # light/medium/deep/maximum
    channels: list[str]   # active research channels
    findings: list[Finding]
    status: str           # active/paused/complete
    created_at: datetime

@dataclass
class Finding:
    source: str           # github/hn/arxiv/etc.
    channel: str          # code/discourse/academic/triz
    title: str
    url: str
    relevance: float      # 0.0-1.0
    summary: str
    raw_content: str      # cached for refinement
    metadata: dict        # source-specific data

@dataclass
class ResearchReport:
    session: ResearchSession
    sections: list[Section]
    citations: list[Citation]
    visualizations: list[Visualization]
    triz_bridges: list[TRIZBridge]  # cross-domain maps
```

### Output Formats

| Format | Use Case | Content |
|--------|----------|---------|
| Report | Default | Full markdown with sections |
| Brief | Pre-implementation | Key findings + recommendations |
| Transcript | Audit trail | Raw session with bookmarks |

### Domain-Specific Presentation

| Domain | Visualization |
|--------|--------------|
| Financial | Price charts, risk matrices (matplotlib) |
| Architecture | System diagrams (mermaid via scry) |
| Algorithm | Complexity comparisons, flow diagrams |
| Scientific | Data plots, equation rendering |
| General | Tables, ranked lists |

## Integration Points

- **memory-palace**: Export findings via `/tome:export`
  using `knowledge-intake` compatible format
- **scry**: Delegate complex visualizations (mermaid
  diagrams, browser-captured charts)
- **leyline**: Use shared patterns (error-patterns,
  content-sanitization, storage-templates)
- **pensive**: Research can feed into code reviews
  ("here's how others solved this")

## Approach Rationale

Pipeline architecture with agent dispatch for the
autonomous pass, individual skills for interactive
refinement. This mirrors how egregore handles parallel
work items while keeping research agents lightweight
and scoped. Each agent fetches, parses, and ranks its
source — synthesis happens in the main thread where the
user can interact.

TRIZ depth is dynamic, not fixed, because a UI color
palette decision needs a different research posture than
a novel consensus algorithm.

## Trade-offs Accepted

- **Token cost vs. depth**: Parallel agents burn tokens;
  mitigated by scoping agents tightly
- **API access vs. rate limits**: Aggressive sourcing may
  hit limits; mitigated by caching and backoff
- **PDF quality vs. parsing**: Claude Read tool is good
  but not perfect on complex layouts; mitigated by
  optional pdfplumber fallback
- **Journal access vs. legality**: All access methods are
  legal; Sci-Hub explicitly excluded

## Out of Scope (v1)

- Real-time monitoring of topics (use `/loop` for that)
- Full-text indexing of downloaded papers
- Collaborative research sessions
- Browser-based journal authentication flows
- Custom TRIZ contradiction matrix editing

## Incremental Delivery Plan

1. **Phase 1**: Core pipeline + code search + discourse
2. **Phase 2**: Academic literature + PDF parsing
3. **Phase 3**: TRIZ cross-domain analysis
4. **Phase 4**: Visualization + scry integration
5. **Phase 5**: Memory-palace export + interactive
   refinement polish

## Next Steps

1. `/attune:specify` — detailed specification with
   acceptance criteria per phase
2. `/attune:blueprint` — architecture design with
   dependency-ordered tasks
3. Create `plugins/tome/` directory structure
