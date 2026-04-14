---
name: plan-versioner
description: >-
  Copy plan iterations to .attune/plan-history/,
  generate line-level diff summaries between versions,
  and record version metadata in mission state.
parent_skill: attune:mission-orchestrator
category: workflow-orchestration
estimated_tokens: 200
---

# Plan Versioner

## Purpose

Track every iteration of the implementation plan as a
separate file. Generate human-readable diff summaries
showing what changed between versions and why.

## Storage Layout

```
.attune/
  plan-history/
    plan-v1.md          # First version
    plan-v2.md          # After round 1 feedback
    plan-v3.md          # After round 2 feedback
    feedback/
      round-1.json      # Feedback that prompted v2
      round-2.json      # Feedback that prompted v3
```

## Versioning Protocol

### On Initial Plan Creation

When `Skill(attune:project-planning)` produces
`docs/implementation-plan.md`:

1. Create `.attune/plan-history/` if it does not exist
2. Copy `docs/implementation-plan.md` to
   `.attune/plan-history/plan-v1.md`
3. Record version 1 in mission state

```bash
mkdir -p .attune/plan-history/feedback
cp docs/implementation-plan.md .attune/plan-history/plan-v1.md
```

### On Plan Revision

When the planning skill produces a revised plan after
feedback:

1. Copy new `docs/implementation-plan.md` to
   `.attune/plan-history/plan-v{N}.md`
2. Generate diff summary between v{N-1} and v{N}
3. Record version N in mission state

```bash
cp docs/implementation-plan.md .attune/plan-history/plan-v${N}.md
```

## Diff Summary Generation

Compare the previous and current versions section by
section. Produce a human-readable summary:

```
--- Changes in v2 (from round 1 feedback) ---
 Architecture: +12 lines, -8 lines
   Addressed: "Split API layer" -> added read/write separation
 Phase 1: unchanged
 Phase 3: +4 lines (new error handling tasks)
----------------------------------------------
```

### Algorithm

1. Split both versions by heading (`## ` or `### `)
2. For each section present in both versions:
   - If identical: report "unchanged"
   - If different: count added/removed lines, summarize
     what changed by correlating with the feedback that
     prompted the revision
3. For sections only in the new version: report "new"
4. For sections only in the old version: report "removed"

### Diff Command

```bash
diff --unified=3 \
  .attune/plan-history/plan-v${PREV}.md \
  .attune/plan-history/plan-v${CURR}.md \
  | head -100
```

## Cleanup

After execution phase completes, plan history can be
kept for retrospectives or removed:

```bash
# Optional cleanup (not automatic)
rm -rf .attune/plan-history/
```

The orchestrator does NOT auto-delete plan history.
Users decide whether to keep it.
