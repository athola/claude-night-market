---
name: knowledge-intake
description: Processes external resources into stored knowledge with quality scoring and routing. Use when ingesting articles, papers, or docs into a memory palace.
alwaysApply: false
category: governance
tags:
- knowledge-management
- intake
- evaluation
- curation
- external-resources
dependencies:
- memory-palace-architect
- digital-garden-cultivator
- leyline:evaluation-framework
- leyline:storage-templates
- leyline:document-conversion
- scribe:slop-detector
scripts: []
usage_patterns:
- resource-intake
- knowledge-evaluation
- application-routing
complexity: intermediate
model_hint: standard
estimated_tokens: 950
---

# Knowledge Intake

Process external resources into the knowledge store. When a user links an article, blog post, or paper, this skill guides evaluation, storage decisions, and application routing.


## When To Use

- Capturing and organizing knowledge from sessions
- Ingesting information into structured memory palaces

## When NOT To Use

- Temporary notes that do not need long-term storage
- Code-only changes without knowledge capture needs

## What It Is

A knowledge governance framework that answers three questions for every external resource:
1. **Is it worth storing?** - Evaluate signal-to-noise and relevance
2. **Where does it apply?** - Route to local codebase or meta-infrastructure
3. **What does it displace?** - Identify outdated knowledge to prune

## The Intake Signal

> When a user links an external resource, it is a signal of importance.

The act of sharing indicates the resource passed the user's own filter. Our job is to:
- Extract the essential patterns and insights
- Determine appropriate storage location and format
- Connect to existing knowledge structures
- Identify application opportunities

## Quick Start

When a user shares a link:

```
1. FETCH    → Detect format, retrieve and convert content
2. EVALUATE → Apply importance criteria
3. DECIDE   → Storage location and application type
4. STORE    → Create structured knowledge entry
5. VALIDATE → Scribe verification (slop scan + doc verify)
6. CONNECT  → Link to existing palace structures
7. PROMOTE  → Offer Discussion promotion (score 80+)
8. APPLY    → Route to codebase or infrastructure updates
9. PRUNE    → Identify displaced/outdated knowledge
```

### Step 1: FETCH with Format Detection

Before retrieving content, detect the source format from
the URL or file path to choose the right retrieval method.

**Web articles and blog posts** (default path):
Use WebFetch to retrieve HTML content directly.
No conversion needed.

**Document URLs** (PDF, DOCX, PPTX, XLSX):
Apply the `leyline:document-conversion` protocol.
This tries the markitdown MCP tool first for high-quality
markdown, then falls back to native Claude Code tools
(Read for PDFs, etc.), then informs the user if the
format is unsupported without markitdown.

**Local files** (user shares a file path):
Construct a `file://` URI from the absolute path and
apply the `leyline:document-conversion` protocol.

**Format detection heuristics:**

| URL Pattern | Format | Retrieval |
|-------------|--------|-----------|
| `*.pdf`, `arxiv.org/pdf/*` | PDF | document-conversion |
| `*.docx`, `*.doc` | Word | document-conversion |
| `*.pptx`, `*.ppt` | PowerPoint | document-conversion |
| `*.xlsx`, `*.xls` | Excel | document-conversion |
| `*.epub` | E-book | document-conversion |
| `drive.google.com/*` | Various | document-conversion |
| Everything else | HTML/web | WebFetch (existing) |

After retrieval (regardless of method), wrap the content
in external content boundary markers per
`leyline:content-sanitization` before proceeding to
Step 2 (EVALUATE).

### Step 5: Scribe Validation (Required)

**All knowledge corpus entries MUST pass scribe validation before finalizing.**

Run `Skill(scribe:slop-detector)` on the new entry:
- Score must be < 2.5 (Clean to Light)
- No Tier 1 markers (delve, tapestry, comprehensive, leveraging, etc.)
- Hedge word density < 15 per 1000 words

Use `Agent(scribe:doc-verifier)` to validate:
- All file paths and URLs exist
- All cross-references valid
- Source attributions accurate

```bash
# Quick validation for knowledge corpus entry
/slop-scan docs/knowledge-corpus/[entry-name].md
# Doc verification is now agent-only:
Agent(scribe:doc-verifier) "Verify docs/knowledge-corpus/[entry-name].md"
```

**DO NOT finalize entries with slop score > 2.5** - rewrite with concrete specifics.
**Verification:** Run the command with `--help` flag to verify availability.

### Step 7: Discussion Promotion (Score 80+ Only)

When the evaluation score is 80-100 (evergreen), you
MUST execute the Discussion promotion workflow. If the
score is below 80, skip this step entirely.

**Execute these steps in order:**

1. Read `modules/discussion-promotion.md` for the
   full GraphQL workflow
2. Tell the user: "This entry has reached evergreen
   maturity. Publishing to GitHub Discussions. [Y/n]"
3. If the user says "n", skip to Step 8 (APPLY)
4. Run the `gh api graphql` commands from the module
   to create or update a Discussion in the "Knowledge"
   category
5. Update the local corpus entry with `discussion_url`

- If the entry already has a `discussion_url` field,
  update the existing Discussion instead of creating
  a new one
- If `gh` is unavailable or promotion fails, warn
  the user and continue to Step 8 (APPLY)

Publishing is the default for qualifying entries. It
never blocks the intake workflow.

## Evaluation Framework

### Importance Criteria

| Criterion | Weight | Questions |
|-----------|--------|-----------|
| **Novelty** | 25% | Does this introduce new patterns or concepts? |
| **Applicability** | 30% | Can we apply this to current work? |
| **Durability** | 20% | Will this remain relevant in 6+ months? |
| **Connectivity** | 15% | Does it connect to multiple existing concepts? |
| **Authority** | 10% | Is the source credible and well-reasoned? |

### Scoring Guide

- **80-100**: Evergreen knowledge, store prominently, apply immediately
- **60-79**: Valuable insight, store in corpus, schedule application
- **40-59**: Useful reference, store as seedling, revisit later
- **Below 40**: Low priority, capture key quote only or skip

## Application Routing

### Local Codebase Application
Apply when knowledge directly improves current project:
- Bug fix patterns
- Performance optimizations
- Architecture decisions for this codebase
- Tool/library recommendations

**Action**: Update code, add comments, create ADR

### Meta-Infrastructure Application
Apply when knowledge improves our plugin ecosystem:
- Skill design patterns
- Agent behavior improvements
- Workflow optimizations
- Learning/evaluation methods (like Franklin Protocol)

**Action**: Update skills, create modules, enhance agents

### Routing Decision Tree

```
**Verification:** Run the command with `--help` flag to verify availability.
Is the knowledge...
├── About HOW we build things? → Meta-infrastructure
│   ├── Skill patterns → Update abstract/memory-palace skills
│   ├── Learning methods → Add to knowledge-corpus
│   └── Tool techniques → Create new skill module
│
└── About WHAT we're building? → Local codebase
    ├── Domain knowledge → Store in project docs
    ├── Implementation patterns → Update code/architecture
    └── Bug/issue solutions → Apply fix, document
```
**Verification:** Run the command with `--help` flag to verify availability.

## Storage Locations

| Knowledge Type | Location | Format |
|----------------|----------|--------|
| Meta-learning patterns | `docs/knowledge-corpus/` | Full memory palace entry |
| Skill design insights | `skills/*/modules/` | Technique module |
| Tool/library knowledge | `docs/references/` | Quick reference |
| Temporary insights | Digital garden seedling | Lightweight note |

## The Tidying Imperative (KonMari-Inspired)

> "A cluttered palace is a cluttered mind."

New knowledge often displaces old, but **time is not the criterion**.
Relevance and aspirational alignment are.

### The Master Curator
The human in the loop defines what stays. Before major tidying:
1. **Who are you becoming?** - Your aspirations as a developer
2. **What excites you now?** - Genuine enthusiasm, not "should"
3. **What have you outgrown?** - Past interests consciously left behind

### The Two Questions
For each piece of knowledge, both must be yes:
- **Does it spark joy?** - Genuine enthusiasm, not obligation
- **Does it serve your aspirations?** - Aligned with who you're becoming

### Tidying Actions

| Finding | Action |
|---------|--------|
| Supersedes | Archive old with gratitude, link as context |
| Contradicts | Evaluate both, keep what sparks joy |
| No longer aligned | Release with gratitude |
| Complements | Create bidirectional links |

**"I might need this someday"** is fear, not joy. Release it.

## Marginal Value Filtering and Quality Scoring

Before storing anything, run the marginal value filter: an entry that
cannot teach something the corpus does not already teach is skipped.
After storage, RL usage signals, quality decay, source lineage and the
anchor-question clarity gate keep each entry's score current. The
three-step filter, its API, the autonomy levels and the scoring model
are in `modules/quality-scoring.md`.

## Workflow Example

**User shares**: "Check out this article on structured concurrency"

```yaml
intake:
  source: "https://example.com/structured-concurrency"

# PHASE 3: Marginal Value Filter
marginal_value:
  redundancy:
    level: partial_overlap
    overlap_score: 0.65
    matching_entries: [async-patterns, python-concurrency]
  delta:
    type: novel_insight
    value_score: 0.75
    novel_aspects: [structured, taskgroup, context-manager]
    teaching_delta: "Introduces structured concurrency pattern"
  integration:
    decision: standalone
    confidence: 0.80
    rationale: "Novel insights justify standalone entry"

# Continue with evaluation if filter passes
evaluation:
  novelty: 75        # New pattern for error handling
  applicability: 90  # Directly relevant to async code
  durability: 85     # Core concept, won't age quickly
  connectivity: 70   # Links to error handling, async patterns
  authority: 80      # Well-known author, cited sources
  total: 82          # Evergreen, store and apply

routing:
  type: both
  local_application:
    - Refactor async error handling in current project
    - Add structured concurrency pattern to codebase
  meta_application:
    - Create module in relevant skill
    - Add to knowledge-corpus as reference

storage:
  location: docs/knowledge-corpus/structured-concurrency.md
  format: memory_palace_entry
  maturity: growing

pruning:
  displaces:
    - Old async error patterns (mark deprecated)
  complements:
    - Existing error handling module
    - Async patterns documentation
```
**Verification:** Run the command with `--help` flag to verify availability.

## Queue Processing

Research sessions and external content are automatically queued for review in `docs/knowledge-corpus/queue/`.

### Processing Queue Entries

```bash
# List pending queue entries
ls -1t docs/knowledge-corpus/queue/*.yaml

# Review specific entry
cat docs/knowledge-corpus/queue/2025-12-31_topic.yaml

# Process approved entry
# 1. Create memory palace entry in docs/knowledge-corpus/
# 2. Update queue entry status to 'processed'
# 3. Archive or delete queue entry
```
**Verification:** Run the command with `--help` flag to verify availability.

### Queue Integration

The `research-queue-integration` hook automatically queues:
- Brainstorming sessions with 3+ WebSearch calls
- Research-focused sessions with substantial findings
- Manual additions via queue entry creation

**Queue entry format**: See `docs/knowledge-corpus/queue/README.md`

### Queue Status Workflow

```
**Verification:** Run the command with `--help` flag to verify availability.
pending_review → [Review] → approved/rejected
approved → [Create Entry] → processed
processed → [Archive] → queue/archive/
```
**Verification:** Run the command with `--help` flag to verify availability.

## Automation

- Run `uv run python scripts/intake_cli.py --candidate path/to/intake_candidate.json --auto-accept`
- The CLI runs marginal value filter, creates palace entries (`docs/knowledge-corpus/*.md`),
  developer drafts (`docs/developer-drafts/`), and appends audit rows to `docs/curation-log.md`.
- Use `--output-root` in tests or sandboxes to avoid mutating the main corpus.
- **Queue Processing**: Use `--process-queue` flag to review and process queued entries interactively.

## Detailed Resources

- **Evaluation Rubric**: See `modules/evaluation-rubric.md`
- **Storage Patterns**: See `modules/storage-patterns.md`
- **KonMari Tidying Philosophy**: See `modules/konmari-tidying.md`
- **Tidying Workflows**: See `modules/pruning-workflows.md`
- **Discussion Promotion**: Invoked in Step 7 (PROMOTE)
  for evergreen entries (score 80+). Publishing is the
  default action.
  See `modules/discussion-promotion.md` for full workflow.
- **Marginal Value Filter and RL Scoring**: See `modules/quality-scoring.md`
- **Hook Integration**: See `modules/hook-integration.md`

## Hook Integration

Memory-palace hooks (`url_detector`, `web_content_processor`,
`local_doc_processor`, `research_queue_integration`) add a context
message when content may need intake. They deduplicate against
`memory-palace-index.yaml` and run safety checks first. Triggers,
signals and the index schema are in `modules/hook-integration.md`.

## Integration

- `memory-palace-architect` - Structures stored knowledge spatially
- `digital-garden-cultivator` - Manages knowledge lifecycle
- `knowledge-locator` - Finds and retrieves stored knowledge
- `skills-eval` (abstract) - Evaluates meta-infrastructure updates
- `memory-clarity-probe` - Dual-probe gate for the clarity check in
  `modules/quality-scoring.md`

## Exit Criteria

- [ ] A non-2xx fetch is dropped, not stored: an HTTP 404/429 body
  produces no index entry (enforced by `web_research_handler`)
- [ ] Every stored entry passed the anchor-question clarity gate: its
  value probe names a concrete capability the knowledge enables
- [ ] Each stored entry has an `importance_score` in `[0, 100]` and a
  routing decision from the Application Routing tree
- [ ] Entries scoring below 40 are captured as a quote or skipped, not
  stored as full knowledge notes
- [ ] The index round-trips through its loader after intake
