# Tome-Enriched Feature Review -- Specification v0.1.0

**Author**: Alex T
**Date**: 2026-04-01
**Status**: Draft

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-04-01 | Alex T | Initial draft |

## Overview

**Purpose**: Integrate tome plugin's multi-source research
capabilities into `imbue:feature-review` so that Reach, Impact,
and Business Value scores are grounded in external evidence
(code search, community discourse, academic papers, TRIZ
analysis) rather than pure intuition.

**Scope**:

- **IN**: New research enrichment phase, scoring adjustment
  logic, new module (research-enrichment.md), SKILL.md updates,
  configuration updates, tests, graceful degradation
- **OUT**: Changes to tome plugin itself, new agents, new
  commands, changes to scoring formula structure

**Stakeholders**:

- Plugin maintainers running `/feature-review --research`
- Product-minded developers evaluating feature roadmaps
- Community contributors seeking evidence-based prioritization

## Problem Statement

The current `/feature-review` scoring relies on the reviewer's
subjective assessment of Reach, Impact, Business Value, and
Time Criticality. The scoring-framework explicitly flags features
with confidence < 0.5 for "research before commitment," but
provides no mechanism to actually perform that research.

Tome plugin has five research channels (code-search, discourse,
papers, triz, synthesize) that can provide external evidence
for these scoring factors.

## Solution Design

### Integration Point

Add a new phase between Phase 4 (tradeoff analysis) and Phase 5
(gap analysis):

```
Phase 1: Inventory
Phase 2: Classification
Phase 3: Scoring (initial)
Phase 4: Tradeoff Analysis
Phase 4.5: Research Enrichment (NEW, optional)
Phase 5: Gap Analysis & Suggestions
Phase 6: GitHub Integration
```

Phase 4.5 is triggered by the `--research` flag. When active, it
dispatches tome research channels and uses findings to adjust
initial scores.

### Research Channel to Scoring Factor Mapping

| Channel | Primary Factor | Secondary Factor | Evidence Type |
|---------|---------------|-----------------|---------------|
| code-search | Reach | Complexity | Competitor count, star counts |
| discourse | Impact | Business Value | Community sentiment, request volume |
| papers | Impact | Risk | Academic validation, novelty |
| triz | Business Value | Impact | Cross-domain analogies |

### Score Adjustment Formula

Research findings produce adjustment deltas, not replacement
scores. The initial human assessment is preserved.

```
adjusted_score = initial_score + research_delta * evidence_weight

Where:
  research_delta = delta from research findings (-2 to +2)
  evidence_weight = confidence of research findings (0.0 to 1.0)
  evidence_weight < 0.3: discard delta (insufficient evidence)
```

**Constraints**:
- Adjusted scores clamp to the Fibonacci scale (1, 2, 3, 5, 8, 13)
- Maximum adjustment: +/- 2 scale points per factor
- If research fails or tome is unavailable, initial scores stand

### Graceful Degradation

When tome is not installed:

1. `--research` flag prints a warning: "Tome plugin not
   installed. Running without research enrichment."
2. Feature-review proceeds with initial scores unchanged
3. No error, no abort -- purely additive capability

### Configuration

New section in `.feature-review.yaml`:

```yaml
research:
  enabled: true
  channels:
    code_search: true
    discourse: true
    papers: false       # Disabled by default (slow)
    triz: false          # Disabled by default (niche)
  evidence_threshold: 0.3  # Minimum confidence to apply delta
  max_delta: 2            # Maximum score adjustment per factor
  timeout_seconds: 120    # Research phase timeout
```

### Output Enhancement

When research enrichment runs, the output table gains columns:

```markdown
| Feature | Type | Data | Score | Adjusted | Priority | Evidence |
|---------|------|------|-------|----------|----------|----------|
| Auth    | R    | D    | 2.8   | 3.1      | High     | 3 sources |
```

A new "Research Evidence" section appears before suggestions:

```markdown
## Research Evidence

### Code Search (GitHub)
- Found 12 similar implementations, avg 340 stars
- **Reach adjustment**: +1 (broad ecosystem adoption)

### Discourse (HN/Reddit)
- 47 mentions in last 90 days, 78% positive sentiment
- **Impact adjustment**: +1 (strong community demand)
```

## Files Changed

| File | Change | Description |
|------|--------|-------------|
| `plugins/imbue/skills/feature-review/SKILL.md` | Modify | Add Phase 4.5, --research flag, output format |
| `plugins/imbue/skills/feature-review/modules/research-enrichment.md` | Create | New module: channel mapping, delta logic, degradation |
| `plugins/imbue/skills/feature-review/modules/configuration.md` | Modify | Add research config section |
| `plugins/imbue/.claude-plugin/plugin.json` | Modify | Add tome to optional dependencies |
| `.feature-review.yaml` | Modify | Add research config section |
| `plugins/imbue/tests/unit/skills/test_feature_review.py` | Modify | Add research enrichment tests |

## Acceptance Criteria

1. `--research` flag triggers Phase 4.5 between tradeoff analysis
   and gap analysis
2. Research findings produce score deltas with evidence weights
3. Adjusted scores clamp to Fibonacci scale
4. Graceful degradation when tome is not installed
5. Output includes evidence summary when research runs
6. Existing tests continue to pass unchanged
7. New tests cover: delta calculation, clamping, degradation,
   channel mapping

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Tome research takes too long | Medium | Configurable timeout, default 120s |
| Research contradicts human assessment | High | Deltas are additive, not replacement |
| Tome API failures | Medium | Continue with initial scores |
| Scope creep into tome internals | Low | Only use tome's public skill interfaces |
