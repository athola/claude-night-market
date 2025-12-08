---
name: catchup
description: Quickly understand recent changes and extract actionable insights
usage: /catchup [baseline]
---

# Catchup on Changes

Rapidly acquires context on recent changes using imbue's catchup methodology: confirm context, capture delta, extract insights, and record follow-ups.

## Usage

```bash
# Catchup from last known state
/catchup

# Catchup from specific baseline
/catchup HEAD~10

# Catchup from date
/catchup --since "2 days ago"
```

## What It Does

1. **Confirms Context**: Establishes current state and baseline for comparison
2. **Captures Delta**: Enumerates changes efficiently without deep-diving
3. **Extracts Insights**: Summarizes what changed and why it matters
4. **Records Follow-ups**: Identifies actionable next steps

## Workflow

```
Baseline → Current → Delta → Insights → Follow-ups
   ↓          ↓        ↓        ↓           ↓
 Known     Target   Changes  Meaning    Actions
 state     state    list     summary    needed
```

## Examples

```bash
/catchup
# Output:
# Catchup Summary
# ===============
# Scope: feature/payments branch
# Baseline: main (merge-base)
# Current: HEAD (15 commits ahead)
#
# Key Changes:
# - Payment processing overhaul (12 files)
# - New Stripe integration (3 files)
# - Test coverage additions (8 files)
#
# Follow-ups:
# - [ ] Review Stripe API key handling
# - [ ] Verify webhook endpoint security

/catchup --since "1 week ago"
# Week-based catchup with date filtering
```

## Integration

Works with:
- `diff-analysis` - For semantic categorization
- `evidence-logging` - For reproducible context
- Git workspace commands for raw data

## Output Format

```markdown
## Summary
[2-3 sentence theme + risk overview]

## Key Changes
- [Item 1]: [what/why/implication]
- [Item 2]: [what/why/implication]

## Follow-ups
- [ ] [Concrete action with owner if known]

## Blockers/Questions
- [Item requiring resolution]
```

## Token Conservation

- References file paths instead of reproducing content
- Summarizes rather than pasting large outputs
- Defers deep analysis to specialized skills
