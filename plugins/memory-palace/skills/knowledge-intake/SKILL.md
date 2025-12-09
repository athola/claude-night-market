---
name: knowledge-intake
description: Process external resources (articles, blog posts, papers) into actionable knowledge with systematic evaluation, storage, and application decisions
category: governance
tags: [knowledge-management, intake, evaluation, curation, external-resources]
dependencies: [memory-palace-architect, digital-garden-cultivator, leyline:evaluation-framework, leyline:storage-templates]
scripts: []
usage_patterns: [resource-intake, knowledge-evaluation, application-routing]
complexity: intermediate
estimated_tokens: 950
---

# Knowledge Intake

Systematically process external resources into actionable knowledge. When a user links an article, blog post, or paper, this skill guides evaluation, storage decisions, and application routing.

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
1. FETCH    → Retrieve and parse the content
2. EVALUATE → Apply importance criteria
3. DECIDE   → Storage location and application type
4. STORE    → Create structured knowledge entry
5. CONNECT  → Link to existing palace structures
6. APPLY    → Route to codebase or infrastructure updates
7. PRUNE    → Identify displaced/outdated knowledge
```

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

## Storage Locations

| Knowledge Type | Location | Format |
|----------------|----------|--------|
| Meta-learning patterns | `docs/knowledge-corpus/` | Full memory palace entry |
| Skill design insights | `skills/*/modules/` | Technique module |
| Tool/library knowledge | `docs/references/` | Quick reference |
| Temporary insights | Digital garden seedling | Lightweight note |

## The Tidying Imperative (KonMari-Inspired)

> "A cluttered palace is a cluttered mind."

New knowledge often displaces old—but **time is not the criterion**. Relevance and aspirational alignment are.

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

## Marginal Value Filtering (Anti-Pollution)

> "If it can't teach something the existing corpus can't already teach → skip it."

Before storing ANY knowledge, run the **marginal value filter** to prevent corpus pollution.

### The Three-Step Filter

**1. Redundancy Check**
- Exact match → REJECT immediately
- 80%+ overlap → REJECT as redundant
- 40-80% overlap → Evaluate delta (Step 2)
- <40% overlap → Likely novel, proceed to store

**2. Delta Analysis** (for partial overlap only)
- **Novel insight/pattern** → High value (0.7-0.9)
- **Different framing only** → Low value (0.2-0.4)
- **More examples** → Marginal value (0.4-0.6)
- **Contradicts existing** → Investigate (0.6-0.8)

**3. Integration Decision**
- **Standalone**: Novel content, no significant overlap
- **Merge**: Enhances existing entry with examples/details
- **Replace**: Supersedes outdated knowledge
- **Skip**: Insufficient marginal value

### Using the Filter

```python
from memory_palace.corpus import MarginalValueFilter

# Initialize filter with corpus and index directories
filter = MarginalValueFilter(
    corpus_dir="docs/knowledge-corpus",
    index_dir="docs/knowledge-corpus/indexes"
)

# Evaluate new content
redundancy, delta, integration = filter.evaluate_content(
    content=article_text,
    title="Structured Concurrency in Python",
    tags=["async", "concurrency", "python"]
)

# Get human-readable explanation
explanation = filter.explain_decision(redundancy, delta, integration)
print(explanation)

# Act on decision
if integration.decision == IntegrationDecision.SKIP:
    print(f"Skipping: {integration.rationale}")
elif integration.decision == IntegrationDecision.STANDALONE:
    # Store as new entry
    store_knowledge(content, title)
elif integration.decision == IntegrationDecision.MERGE:
    # Enhance existing entry
    enhance_entry(integration.target_entries[0], content)
elif integration.decision == IntegrationDecision.REPLACE:
    # Replace outdated entry
    replace_entry(integration.target_entries[0], content)
```

### Filter Output Example

```
=== Marginal Value Assessment ===

Redundancy: partial
Overlap: 65%
Matches: async-patterns, python-concurrency
  - Partial overlap (65%) with 2 entries

Delta Type: novel_insight
Value Score: 75%
Teaching Delta: Introduces 8 new concepts
Novel aspects:
  + New concepts: structured, taskgroup, context-manager
  + New topics: Error Propagation, Resource Cleanup

Decision: STANDALONE
Confidence: 80%
Rationale: Novel insights justify standalone: Introduces 8 new concepts
```

### Progressive Autonomy Integration

The marginal value filter respects autonomy levels (see plan Phase 4):
- **Level 0**: ALL decisions require human approval
- **Level 1**: Auto-approve 85+ scores in known domains
- **Level 2**: Auto-approve 70+ scores in known domains
- **Level 3**: Auto-approve 60+, auto-reject obvious noise

Current implementation: Level 0 (all human-in-the-loop).

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

## Automation

- Run `uv run python skills/knowledge-intake/scripts/intake_cli.py --candidate path/to/intake_candidate.json --auto-accept`
- The CLI runs marginal value filter, creates palace entries (`docs/knowledge-corpus/*.md`),
  developer drafts (`docs/developer-drafts/`), and appends audit rows to `docs/curation-log.md`.
- Use `--output-root` in tests or sandboxes to avoid mutating the main corpus.

## Detailed Resources

- **Evaluation Rubric**: See `modules/evaluation-rubric.md`
- **Storage Patterns**: See `modules/storage-patterns.md`
- **KonMari Tidying Philosophy**: See `modules/konmari-tidying.md`
- **Tidying Workflows**: See `modules/pruning-workflows.md`

## Hook Integration

Memory-palace hooks automatically detect content that may need knowledge intake processing:

### Automatic Triggers

| Hook | Event | When Triggered |
|------|-------|----------------|
| `url_detector` | UserPromptSubmit | User message contains URLs |
| `web_content_processor` | PostToolUse (WebFetch/WebSearch) | After fetching web content |
| `local_doc_processor` | PostToolUse (Read) | Reading files in knowledge paths |

### Hook Signals

When hooks detect potential knowledge content, they add context messages:

```
Memory Palace: New web content fetched from {url}.
Consider running knowledge-intake to evaluate and store if valuable.
```

```
Memory Palace: Reading local knowledge doc '{path}'.
This path is configured for knowledge tracking.
Consider running knowledge-intake if this contains valuable reference material.
```

### Deduplication

Hooks check the `memory-palace-index.yaml` to avoid redundant processing:
- **Known URLs**: "Content already indexed" - skip re-evaluation
- **Changed content**: "Content has changed" - suggest update
- **New content**: Full evaluation recommended

### Safety Checks

Before signaling intake, hooks validate content:
- Size limits (default 500KB)
- Secret detection (API keys, credentials)
- Data bomb prevention (repetition, unicode bombs)
- Prompt injection sanitization

### Index Schema Alignment

The deduplication index stores fields aligned with this skill's evaluation:

```yaml
entries:
  "https://example.com/article":
    content_hash: "xxh:abc123..."
    stored_at: "docs/knowledge-corpus/article.md"
    importance_score: 82           # From evaluation framework
    maturity: "growing"            # seedling, growing, evergreen
    routing_type: "both"           # local, meta, both
    last_updated: "2025-12-06T..."
```

## Integration

- `memory-palace-architect` - Structures stored knowledge spatially
- `digital-garden-cultivator` - Manages knowledge lifecycle
- `knowledge-locator` - Finds and retrieves stored knowledge
- `skills-eval` (abstract) - Evaluates meta-infrastructure updates
