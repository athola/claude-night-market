---
name: elegant-code-review
description: Review the current working diff against the elegant-code decision ladder and propose deletions, honoring the negligence floor.
usage: /elegant-code-review [--staged] [--base REF]
---

# Elegant Code Review

Walk the current working diff against the `elegant-code` decision
ladder. For each added hunk, name the rung that justifies it, flag any
rung skipped, and propose concrete deletions. This is a per-change
review. For whole-codebase cleanup, use `/unbloat`.

## When To Use

- After writing or generating a change, before committing.
- When a diff feels larger than the problem it solves.
- When a new dependency appears in a lockfile or manifest.

## When NOT To Use

- Whole-codebase dead-code sweeps: use `/unbloat` or `/bloat-scan`.
- Throwaway scripts where review cost is near zero.

## Steps

1. Load the rubric: `Skill(conserve:elegant-code)`.
2. Collect the diff:
   - Default: `git diff` (unstaged) plus `git diff --staged`.
   - `--staged`: staged changes only.
   - `--base REF`: `git diff REF...HEAD`.
3. For each added hunk, assign the lowest ladder rung that justifies
   it:
   1. Need-to-exist
   2. Builtin / stdlib
   3. Native platform
   4. Installed dependency
   5. A few lines
   A new dependency is the last resort, below rung 5. If one was
   added, confirm it with `Skill(imbue:dependency-verification)` and
   check whether an installed dependency already covered the need.
4. Cross-check deletability with a real tool when available, treating
   output as candidates only:

   ```bash
   command -v knip >/dev/null && knip || echo "knip absent; skipping"
   command -v vulture >/dev/null && vulture . || echo "vulture absent; skipping"
   ```

5. Apply the negligence floor before proposing any deletion. Never
   propose removing input validation, authorization, data-loss
   handling, error handling, security paths, or accessibility.
6. Check completeness, not just excess. Flag a hunk that handles only
   the happy path: missing edge cases (empty, `None`, zero, boundary),
   missing negative or failure paths, or an obvious performance trap
   (quadratic loop, N+1 query). Minimal code that omits these is
   unfinished, not lean.

## Output

A short table, one row per reviewed hunk:

| File:line | Chosen rung | Lower rung available? | Proposed action |
|-----------|-------------|-----------------------|-----------------|

Close with a one-line verdict: `minimal and complete`,
`trim suggested`, `new dependency unjustified`, or
`incomplete: add coverage`. List proposed deletions, and any missing
edge, negative, or performance coverage, as concrete diffs the user
approves before anything changes.

## Notes

- Read-only by default: propose, do not delete without approval.
- Composes `leyline:additive-bias-defense` for the burden-of-proof
  verdict on each addition.
