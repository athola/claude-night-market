---
name: scope-guard
description: Prevents overengineering through worthiness scoring, opportunity cost comparison, and branch threshold monitoring. Use when evaluating features during brainstorming, planning, or when branches approach size limits.
category: workflow-methodology
tags: [anti-overengineering, scope, YAGNI, prioritization, backlog]
dependencies: []
tools: []
usage_patterns:
  - feature-evaluation
  - scope-validation
  - threshold-monitoring
  - backlog-management
complexity: intermediate
estimated_tokens: 2500
---

# Scope Guard

Prevents overengineering by both Claude and human during the brainstorm→plan→execute workflow. Forces explicit evaluation of every proposed feature against business value, opportunity cost, and branch constraints.

## When to Use

- During brainstorming sessions before documenting designs
- During planning sessions before finalizing implementation plans
- When evaluating "should we add this?" decisions
- Automatically via hooks when branches approach thresholds
- When proposing new features, abstractions, or patterns

## When NOT to Use

- Bug fixes with clear, bounded scope
- Documentation-only changes
- Trivial single-file edits (< 50 lines)
- Emergency production fixes

## Activation Patterns

**Trigger Keywords**: scope, feature, implement, add, extend, refactor, abstraction, pattern, "what if", "we could also"

**Contextual Cues**:
- End of brainstorming session
- Before finalizing implementation plans
- When proposing additions to current work
- When branch metrics approach thresholds

**Auto-Load When**: superpowers:brainstorming or superpowers:writing-plans completes, or branch threshold hook fires.

## Superpowers Integration

This skill integrates with the superpowers brainstorm→plan→execute workflow:

### After superpowers:brainstorming
When a brainstorming session concludes (design documented to `docs/plans/`), automatically:
1. List all proposed features/components from the design
2. Score each with Worthiness formula
3. Defer items scoring < 1.0 to `docs/backlog/queue.md`
4. Verify remaining items fit within branch budget

**Self-invoke prompt**: "Before documenting this design, let me evaluate the proposed features with scope-guard."

### After superpowers:writing-plans
When an implementation plan is being finalized, automatically:
1. Verify all planned items have Worthiness > 1.0
2. Compare against existing backlog queue
3. Confirm total scope fits within branch budget
4. Document any deferrals to backlog

**Self-invoke prompt**: "Before finalizing this plan, let me verify scope with scope-guard."

### During superpowers:execute-plan
Periodically during execution (especially if session is long-running):
1. Run threshold check: lines, files, commits, days
2. Warn if Yellow zone reached
3. Require justification if Red zone reached

**Self-invoke prompt**: "This branch has grown significantly. Let me check scope-guard thresholds."

## Required TodoWrite Items

When evaluating a feature, create these todos:

1. `scope-guard:worthiness-scored`
2. `scope-guard:backlog-compared`
3. `scope-guard:budget-checked`
4. `scope-guard:decision-documented`

---

## Core Workflow

### Step 1: Calculate Worthiness Score (`scope-guard:worthiness-scored`)

**Formula:**
```
Worthiness = (Business Value + Time Criticality + Risk Reduction) / (Complexity + Token Cost + Scope Drift)
```

**Score each factor on Fibonacci scale (1, 2, 3, 5, 8, 13):**

#### Value Factors (Numerator)

| Factor | 1 | 5 | 13 |
|--------|---|---|---|
| **Business Value** | Nice-to-have, no stated requirement | Addresses indirect need | Directly required by spec/customer |
| **Time Criticality** | No deadline | Soft deadline this quarter | Hard deadline, blocking release |
| **Risk Reduction** | Hypothetical future risk | Documented risk, low impact | Active production risk |

#### Cost Factors (Denominator)

| Factor | 1 | 5 | 13 |
|--------|---|---|---|
| **Complexity** | < 100 lines, single file | 300-500 lines, 3-5 files | 1000+ lines, architectural change |
| **Token Cost** | Quick implementation, minimal iteration | Moderate exploration needed | Research-heavy, multiple attempts |
| **Scope Drift** | Core to branch purpose | Related but adjacent | Different epic entirely |

**Example Calculation:**
```
Feature: Add retry logic to API client

Business Value: 8 (addresses known flakiness complaints)
Time Criticality: 3 (no hard deadline)
Risk Reduction: 5 (reduces documented intermittent failures)

Complexity: 3 (< 200 lines, 2 files)
Token Cost: 2 (straightforward pattern)
Scope Drift: 2 (related to current API work)

Worthiness = (8 + 3 + 5) / (3 + 2 + 2) = 16 / 7 = 2.3

Decision: > 2.0 → Implement now
```

### Step 2: Compare Against Backlog (`scope-guard:backlog-compared`)

1. Check `docs/backlog/queue.md` for existing items
2. If relevant items exist:
   - Compare Worthiness Scores
   - New item must beat top queued item OR fit within branch budget
3. If no relevant items in queue:
   - Generate 2 reasonable alternatives
   - Score alternatives
   - Compare and pick highest

**Comparison Prompt:**
```
Proposed: [Feature X] - Worthiness: 1.8

Top backlog items for comparison:
1. [Feature A] - Worthiness: 2.1 - Added: 2025-12-01
2. [Feature B] - Worthiness: 1.6 - Added: 2025-12-05

Does Feature X (1.8) justify:
- Displacing Feature A (2.1)?
- OR consuming branch budget?
```

### Step 3: Check Branch Budget (`scope-guard:budget-checked`)

**Default budget: 3 major features per branch**

- Count current features in branch scope
- If at budget, adding new feature requires:
  - Dropping an existing feature, OR
  - Splitting to new branch, OR
  - Explicit override with documented justification

**Budget Check:**
```
Branch: feature/auth-improvements
Budget: 3 features

Current allocation:
1. OAuth2 flow refactor (primary)
2. Token refresh logic (secondary)
3. [OPEN SLOT]

Proposed: Session timeout handling
Decision: Fits in slot 3 → Proceed
```

### Step 4: Document Decision (`scope-guard:decision-documented`)

Record the outcome:
- If implementing: Note Worthiness Score and budget slot
- If deferring: Add to `docs/backlog/queue.md` with score and context
- If rejecting: Document why (low value, out of scope, etc.)

---

## Decision Thresholds

| Score | Decision | Action |
|-------|----------|--------|
| > 2.0 | **Implement now** | Proceed with work |
| 1.0 - 2.0 | **Discuss** | Justify before proceeding, consider alternatives |
| < 1.0 | **Defer to backlog** | Add to queue.md with full context |

---

## Branch Threshold Monitoring

### Metrics & Thresholds

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| **Lines changed** | < 1000 | 1000-1500 | > 2000 |
| **New files created** | < 8 | 8-12 | > 15 |
| **Commits on branch** | < 15 | 15-25 | > 30 |
| **Days on branch** | < 3 | 3-7 | > 7 |

### Check Command

```bash
# Quick threshold check
lines=$(git diff main --stat | tail -1 | awk '{print $4}')
files=$(git diff main --name-only --diff-filter=A | wc -l)
commits=$(git rev-list --count main..HEAD)
days=$(( ($(date +%s) - $(git log -1 --format=%ct $(git merge-base main HEAD))) / 86400 ))

echo "Lines: $lines | Files: $files | Commits: $commits | Days: $days"
```

### Yellow Zone Prompt

```
⚠️ Branch approaching thresholds:
- Lines: 1,247 (Yellow zone)
- Commits: 18 (Yellow zone)

Before continuing, confirm:
1. Does this still match the original scope?
2. What's the current Worthiness Score?
3. Can anything be split to backlog?
```

### Red Zone Prompt

```
🛑 Branch exceeds thresholds:
- Lines: 2,341 (Red zone)
- Days: 9 (Red zone)

Required before PR:
1. Document why scope expanded
2. Identify items to split to backlog or future branch
3. Re-score Worthiness with current scope
4. Explicit approval to continue
```

---

## Backlog Management

### Directory Structure

```
docs/backlog/
├── queue.md              # Active ranked queue
└── archive/
    ├── ideas.md          # Deferred feature ideas
    ├── optimizations.md  # Deferred performance work
    ├── refactors.md      # Deferred cleanup
    └── abstractions.md   # Deferred patterns
```

### Adding to Queue

When deferring an item, add to `docs/backlog/queue.md`:

```markdown
| Rank | Item | Worthiness | Added | Branch/Epic | Category |
|------|------|------------|-------|-------------|----------|
| 1 | [New item description] | 1.8 | 2025-12-08 | current-branch | idea |
```

Re-rank by Worthiness Score after adding.

### Queue Rules

- Max 10 items in active queue
- Items older than 30 days without pickup → move to archive
- Re-score monthly or when project context changes

### Archiving

When moving to archive, add full context:

```markdown
## [IDEA-001] Feature Name
- **Original Score:** 1.4
- **Added:** 2025-11-15
- **Archived:** 2025-12-08
- **Reason:** Lower priority than queue items; revisit Q2
- **Original Context:** [Why it was proposed]
```

---

## Integration Points

### With superpowers:brainstorming

At end of brainstorming, before documenting design:
1. List all proposed features/components
2. Score each with Worthiness formula
3. Defer items scoring < 1.0 to backlog
4. Check branch budget for remaining items

### With superpowers:writing-plans

Before finalizing implementation plan:
1. Verify all planned items have Worthiness > 1.0
2. Compare against backlog queue
3. Confirm within branch budget
4. Document any deferrals

### Hook: pre-pr-scope-check

Automatically runs before PR creation:
1. Check all threshold metrics
2. Warn on Yellow, block on Red (configurable)
3. Require justification for Red zone branches

---

## Anti-Rationalization Checklist

**If you find yourself thinking:**

| Thought | Reality Check |
|---------|---------------|
| "This is a small addition" | Did you score it? Small additions compound. |
| "We'll need this eventually" | Score Time Criticality honestly. "Eventually" = 1. |
| "It's already half done" | Sunk cost fallacy. Re-score from current state. |
| "Users might want this" | "Might" = Business Value of 1-2 max. |
| "This is the right way to do it" | Is it the simplest way that works? |
| "It's just refactoring" | Refactoring still has Complexity cost. Score it. |

**Red flags that indicate overengineering:**
- Enjoying the solution more than solving the problem
- Adding "flexibility" for unspecified future needs
- Creating abstractions before the third use case
- Discussing patterns before discussing requirements
- Branch metrics climbing without proportional value delivery

---

## Quick Reference

**Worthiness Formula:**
```
(BizValue + TimeCrit + RiskReduce) / (Complexity + TokenCost + ScopeDrift)
```

**Thresholds:** > 2.0 implement | 1.0-2.0 discuss | < 1.0 defer

**Branch Limits:** 1000/1500/2000 lines | 8/12/15 files | 15/25/30 commits | 3/7/7+ days

**Budget:** 3 major features per branch (default)

---

## Related Skills

- `superpowers:brainstorming` - Ideation workflow this guards
- `superpowers:writing-plans` - Planning workflow this validates
- `imbue:review-core` - Review methodology pattern
