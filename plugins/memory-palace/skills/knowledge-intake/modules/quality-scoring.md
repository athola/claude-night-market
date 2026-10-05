---
name: quality-scoring
description: Marginal value filter and RL-based quality scoring that decide whether intake content is stored and how its score changes with use
category: evaluation
tags: [marginal-value, rl-scoring, quality-decay, lineage, clarity-gate]
dependencies: [knowledge-intake]
complexity: intermediate
estimated_tokens: 2400
---

# Quality Scoring

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
    corpus_dir="docs/knowledge-corpus", index_dir="docs/knowledge-corpus/indexes"
)

# Evaluate new content
redundancy, delta, integration = filter.evaluate_content(
    content=article_text,
    title="Structured Concurrency in Python",
    tags=["async", "concurrency", "python"],
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
**Verification:** Run the command with `--help` flag to verify availability.

### Filter Output Example

```
**Verification:** Run the command with `--help` flag to verify availability.
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
**Verification:** Run the command with `--help` flag to verify availability.

### Progressive Autonomy Integration

The marginal value filter respects autonomy levels (see plan Phase 4):
- **Level 0**: ALL decisions require human approval
- **Level 1**: Auto-approve 85+ scores in known domains
- **Level 2**: Auto-approve 70+ scores in known domains
- **Level 3**: Auto-approve 60+, auto-reject obvious noise

Current implementation: Level 0 (all human-in-the-loop).

## RL-Based Quality Scoring

The knowledge corpus uses reinforcement learning signals to dynamically score entry quality based on actual usage patterns.

### Anchor-Question Clarity Gate

Usage signals score an entry *after* it is stored, from how it gets
accessed. They cannot catch a summary that was never clear enough to
be useful. Before an entry is written, gate it on the MMPO dual-probe
(arXiv:2605.30159), adapted from task state to knowledge value:

1. **Value probe**: what does this knowledge let us *do*? Name a
   concrete capability or decision it enables, not a topic label.
2. **Gap probe**: what does this knowledge *not* answer? List the
   bounded open questions it leaves, not generic "more research".

| Value probe | Gap probe | Decision |
|-------------|-----------|----------|
| Names a concrete use | Bounded, specific gaps | Store at the evaluated score |
| Names a concrete use | "Everything" / empty | Store, but cap at seedling until gaps are named |
| Vague ("useful background") | Any | Do not store as knowledge: capture the key quote only or skip |

This gate is qualitative and complements, does not replace, the
Importance Criteria score: a summary can score well on Applicability
yet still fail the value probe if it cannot name what it enables.
When `memory-palace:memory-clarity-probe` is installed, delegate the
dual-probe evaluation to it and use its `Recommendation` as the gate.

### Usage Signals

| Signal | Weight | Description |
|--------|--------|-------------|
| `ACCESS` | +0.1 | Entry was accessed/read |
| `CITATION` | +0.3 | Entry was cited in another context |
| `POSITIVE_FEEDBACK` | +0.5 | User marked as helpful |
| `NEGATIVE_FEEDBACK` | -0.3 | User marked as unhelpful |
| `CORRECTION` | +0.2 | Entry was corrected/updated |
| `STALE_FLAG` | -0.4 | Entry marked as potentially outdated |

### Quality Decay Model

Knowledge entries decay over time unless validated:

| Maturity | Half-Life | Decay Curve |
|----------|-----------|-------------|
| Seedling | 14 days | Exponential |
| Growing | 30 days | Exponential |
| Evergreen | 90 days | Logarithmic |

Entries are classified by decay status:
- **Fresh**: >70% quality retained
- **Stale**: 40-70% quality retained
- **Critical**: 20-40% quality retained
- **Archived**: <20% quality retained

### Source Lineage Tracking

Hybrid lineage tracking based on source importance:

**Full Lineage** (for important sources):
- Primary source with complete metadata
- Derivation chain (what entries it was derived from)
- Transformation history (summarization, extraction, etc.)
- Validation chain (who validated and when)

**Simple Lineage** (for standard sources):
- Source type and URL
- Retrieval timestamp

Full lineage is used for:
- Research papers
- Documentation
- Entries with importance score >= 0.7

### Knowledge Orchestrator

The `KnowledgeOrchestrator` coordinates all quality systems:

```python
from memory_palace.corpus import KnowledgeOrchestrator, UsageSignal

# Initialize orchestrator
orchestrator = KnowledgeOrchestrator(
    corpus_dir="docs/knowledge-corpus", index_dir="docs/knowledge-corpus/indexes"
)

# Record usage events
orchestrator.record_usage("entry-1", UsageSignal.ACCESS)
orchestrator.record_usage("entry-1", UsageSignal.POSITIVE_FEEDBACK)

# Assess entry quality
entry = {"id": "entry-1", "maturity": "growing"}
assessment = orchestrator.assess_entry(entry)
print(f"Quality: {assessment.overall_score:.0%}")
print(f"Status: {assessment.status}")
print(f"Recommendations: {assessment.recommendations}")

# Get maintenance queue
entries = [...]  # Your entry list
queue = orchestrator.get_maintenance_queue(entries)
for item in queue:
    print(f"{item.entry_id}: {item.status} - {item.recommendations}")

# Ingest new content with lineage
from memory_palace.corpus import SourceReference, SourceType

source = SourceReference(
    source_id="src-1",
    source_type=SourceType.DOCUMENTATION,
    url="https://docs.example.com/api",
    title="API Documentation",
)
entry_id, decision = orchestrator.ingest_with_lineage(
    content="# API Reference\n...", title="API Documentation", source=source
)
```
**Verification:** Run the command with `--help` flag to verify availability.

### RL Integration with Marginal Value Filter

The marginal value filter emits RL signals on integration decisions:

```python
from memory_palace.corpus import MarginalValueFilter

filter = MarginalValueFilter(corpus_dir, index_dir)

# Evaluate with RL signal emission
redundancy, delta, integration, rl_signal = filter.evaluate_with_rl(
    content=article_text, title="New Article", tags=["python", "async"]
)

# RL signal contains:
# - signal_type: UsageSignal to emit
# - weight: Signal weight for scoring
# - action: What happened (new_entry_created, entry_enhanced, etc.)
# - decision: Integration decision made
# - confidence: Decision confidence
print(f"RL Signal: {rl_signal['action']} (weight: {rl_signal['weight']})")
```
**Verification:** Run the command with `--help` flag to verify availability.
