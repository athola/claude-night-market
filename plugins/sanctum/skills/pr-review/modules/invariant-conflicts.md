---
name: invariant-conflicts
description: "Phase 4.6 of pr-review: detect a change that weakens an invariant the codebase relies on, and how to report it."
---

### Phase 4.6: Invariant Conflict Detection

Check whether the PR touches existing design invariants.
This is a judgment problem that models get wrong far too
often: surface conflicts for human review rather than
silently accepting or rejecting them.

**Quick detection heuristic:**

1. Do changed files cross module boundaries that
   previously didn't interact?
2. Do changes introduce a new pattern alongside an
   existing one (two ways to do the same thing)?
3. Do interface/type/schema files change shape?
4. Do data flow directions change?
5. Are ADR-documented decisions being contradicted?

```bash
# Check for structural pattern changes
git diff --name-only HEAD...origin/master 2>/dev/null \
  | rg "(interface|types|schema|model|base|core|contract)" \
  || git diff --name-only HEAD...origin/master 2>/dev/null \
  | grep -E "(interface|types|schema|model|base|core|contract)"
```

**When a conflict is detected:**

Do NOT resolve it. Add to the report as a special
category:

| Category | Definition | Action |
|----------|------------|--------|
| **INVARIANT** | Change conflicts with an existing design decision | Escalate to human with 3-option analysis |

**For each invariant conflict, present:**

1. **The invariant**: Name the design decision and why
   it was made (reference ADRs if available)
2. **The conflict**: What this PR does that clashes
3. **Option A, Preserve**: Don't merge this change;
   the invariant pays dividends elsewhere
4. **Option B, Layer**: Merge as-is and accept
   the inelegance. Not every feature must be elegant
5. **Option C, Revise**: The invariant is wrong;
   here's what a redesign would look like

**Classification:** INVARIANT findings are always
BLOCKING, not because the code is wrong, but because
the judgment call requires human input. Only the human
reviewer can decide which of the three options is right.

**With `--hold-insights`:** the same holding pattern covers
every finding about the direction of the change, its
architecture, or a question the diff leaves open, not only
the ones that conflict with a recorded invariant. Present them
in chat, then ask with the prompt Phase 5 uses for backlog
issues: "I have N observations on direction and design. Post
which? [y/n/select]". Post only what is selected. The rest
stays in the conversation. This is the reviewer's judgment
being exercised before the author sees it, which is where a
question about direction belongs.

**Why this matters:** Bad invariant decisions compound.
A few wrong calls and the codebase becomes unsalvageable.
This is not a context problem solvable with better
documentation: it is a judgment problem that requires
human wisdom.
