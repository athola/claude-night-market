# Description Budget Fix Strategy

## Problem

Optimized descriptions too aggressively by removing critical trigger information that Claude uses for skill discovery.

## Requirements (from internal docs)

Per `plugins/abstract/shared-modules/trigger-patterns.md`:
- **Triggers:** Comma-separated keywords for discovery
- **Use when:** Specific scenarios/symptoms
- **DO NOT use when:** Explicit negative triggers with alternatives

These MUST be in the description field (frontmatter) because Claude uses description to choose which skill to read.

## Balanced Solution

Restore trigger information in condensed format while staying under 15,000 char budget.

### Format Template

```yaml
description: |
  [Concise what it does - max 1 sentence]

  Triggers: [5-8 essential keywords only]
  Use when: [brief scenario]
  DO NOT use when: [critical exclusion] - use [alternative].
```

### Optimization Rules

1. **Triggers line**: Keep 5-8 most essential keywords (not 10-15)
2. **Use when**: Single line, most common scenario
3. **DO NOT use when**: Only include if there's a related skill that might overtrigger
4. **NO "Consult this skill when..." endings**

### Target Budget

- Current: 14,745 chars
- After restoration: ~14,900 chars (still under 15,000)
- Per-skill addition: ~6-10 chars average

## Example Transformations

### Before My Optimization (Original)
```yaml
description: |
  CQRS and Event Sourcing for auditability, read/write separation, and temporal queries.

  Triggers: CQRS, event sourcing, audit trail, event replay, read/write separation,
  temporal queries, event store, projections, command handlers, aggregate roots

  Use when: read/write workloads have different scaling needs, complete audit trail
  required, need to rebuild historical state

  DO NOT use when: selecting from multiple paradigms - use architecture-paradigms first.
  DO NOT use when: simple CRUD without audit requirements.
```

### After My Over-Optimization (BROKEN)
```yaml
description: CQRS and Event Sourcing for auditability, read/write separation, and temporal queries. Avoid for simple CRUD.
```
**Problem**: No triggers list, no "Use when" guidance!

### Balanced Fix (CORRECT)
```yaml
description: |
  CQRS and Event Sourcing for auditability, read/write separation, and temporal queries.

  Triggers: CQRS, event sourcing, audit trail, temporal queries
  Use when: read/write scaling differs or audit trail required
  DO NOT use when: simple CRUD - use architecture-paradigms first.
```
**Savings**: 100 chars vs original, but preserves all critical trigger information

## Implementation Plan

1. Restore triggers/use-when/do-not-use to the 27 optimized files
2. Keep condensed format (5-8 keywords, brief scenarios)
3. Verify budget stays under 15,000
4. Test that pre-commit hooks pass
