---
name: dorodango
description: Polishes working code through successive quality passes in fresh subagents. Use after tests pass when code needs multi-dimension refinement before release.
alwaysApply: false
category: workflow
tags:
  - polishing
  - iterative-refinement
  - code-quality
  - convergence
progressive_loading: true
dependencies:
  hub: []
  modules:
    - modules/pass-definitions.md
complexity: intermediate
model_hint: standard
estimated_tokens: 400
---
# Dorodango Polishing Workflow

Named after the Japanese art of polishing a ball of
dirt into a high-gloss sphere. Applied to code: take
the initial implementation (the "mud ball") and refine
it through successive quality passes until it shines.

## When To Use

- After initial implementation is complete and tests
  pass
- Code works but needs refinement across multiple
  quality dimensions
- Preparing code for review or release
- Resuming a previous polishing session

## When NOT To Use

- Code does not compile or pass basic tests (fix first)
- Single-dimension improvement needed (use the specific
  skill directly: pensive:code-refinement, etc.)
- Greenfield design phase (use brainstorming instead)

## Pass Sequence

Four quality dimensions, each a self-contained pass:

1. **Correctness** - run tests, fix failures
2. **Clarity** - code readability and structure
3. **Consistency** - naming, patterns, style alignment
4. **Polish** - documentation, error messages, edges

See `modules/pass-definitions.md` for detailed scope
of each pass type.

## Convergence Model

- Each pass targets one dimension
- A pass that finds `issues_found: 0` marks that
  dimension as **converged**
- Convergence is irreversible per run; a converged
  dimension is not re-run
- When all 4 dimensions converge, polishing is complete
- Maximum 10 total passes (hard limit)
- If not converged after 10 passes, surface state to
  human with recommendation to split into smaller units

## State Persistence

State tracked in `.attune/dorodango-state.json`:

```json
{
  "target": "plugins/foo",
  "started_at": "2026-03-18T12:00:00Z",
  "pass_count": 3,
  "passes": [
    {
      "type": "correctness",
      "issues_found": 2,
      "issues_fixed": 2
    },
    {
      "type": "clarity",
      "issues_found": 5,
      "issues_fixed": 5
    },
    {
      "type": "consistency",
      "issues_found": 0
    }
  ],
  "converged_dimensions": ["consistency"],
  "converged": false
}
```

This file enables resume across sessions. On resume,
skip converged dimensions and continue from the next
unconverged dimension.

## Subagent Isolation

Each pass dispatches a self-contained subagent to
prevent context accumulation. The subagent receives:

- Target directory/files
- Pass type and scope (from pass-definitions module)
- Previous pass results (summary only, not full context)

Subagent dispatch is optional for targets under 100
lines of code; in-session review is sufficient for
small files.

## Workflow

1. Initialize state file (or load existing)
2. Determine next unconverged dimension
3. Dispatch subagent for that dimension
4. Record results in state file
5. If dimension converged (0 issues), mark it
6. If all dimensions converged or 10 passes reached,
   stop
7. Otherwise, proceed to next dimension

## Cross-References

- `pensive:code-refinement` - used in clarity pass
- `conserve:code-quality-principles` - KISS/YAGNI/SOLID
- `imbue:latent-space-engineering` - frame pass prompts
  with emotional framing for better results

## Exit Criteria

- [ ] `.attune/dorodango-state.json` exists with `"converged": true` and all four dimensions
  (`correctness`, `clarity`, `consistency`, `polish`) listed under `converged_dimensions`.
- [ ] Total `pass_count` in the state file is <= 10; if 10 passes complete without full
  convergence, the skill surfaces the unconverged dimensions to the user with a recommendation
  to split the target into smaller units.
- [ ] The correctness dimension converges only after all tests pass (exit code 0); a
  correctness pass that finds failing tests never marks the dimension as converged.
- [ ] Each pass is dispatched as a separate subagent for targets over 100 lines, confirmed by
  the state file recording individual pass results rather than a single bulk entry.
