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

## Workflow Example

**User shares**: "Check out this article on structured concurrency"

```yaml
intake:
  source: "https://example.com/structured-concurrency"

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
