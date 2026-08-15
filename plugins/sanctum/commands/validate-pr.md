---
name: validate-pr
description: Generate and self-execute a diff-derived test plan for a PR. Reads
  the diff, groups changes by area, runs targeted verifications, proves
  revert-tests are genuine guards, and reports a structured summary table.
usage: /sanctum:validate-pr [<pr-number> | <pr-url>] [--post] [--revert-tests <N>]
---

# validate-pr

Generate and self-execute a step-by-step validation plan matched to what
actually changed in a PR. Bridges the gap between "tests pass" and "the
fix does what it claims."

## When To Use

- Standalone after any PR fix, to produce targeted validation evidence
- Called automatically by `/fix-pr` at the end of Step 5 (Validate)
- When you need proof that revert-tests catch regressions

## When NOT To Use

- `--scope minor` in `/fix-pr` with only formatting or doc changes
- No diff available (clean branch, nothing changed)
- Pass `--skip-validate` to `/fix-pr` to bypass

## Options

| Option | Description |
|--------|-------------|
| `<pr-number>` | Target PR number (default: current branch PR) |
| `<pr-url>` | Full GitHub or GitLab URL to the PR |
| `--post` | Post the summary table as a PR comment |
| `--revert-tests <N>` | Number of revert-test quality checks to run (default: 1) |

## Quick Reference

```bash
# Run on current branch PR
/sanctum:validate-pr

# Run on a specific PR
/sanctum:validate-pr 123

# Run and post results as a PR comment
/sanctum:validate-pr 123 --post

# Run with two revert-test checks
/sanctum:validate-pr 123 --revert-tests 2
```

## Workflow

See `Skill(sanctum:validate-pr)` for the full algorithm:

1. Fetch the PR diff and group changed files by area (Rust, Python, Shell,
   grammar, build/config)
2. Generate at least one verification step per area
3. Execute each step, capture output as evidence (`[E1]`, `[E2]`, ...)
4. Run a revert-test quality check: break a representative fix, confirm
   the corresponding test fails, restore via `git checkout -- <file>`
5. Read the PR body's `## Test plan`. Execute every step that can run
   here and capture evidence the same way. Report a step that needs a
   human (a browser, a device, a staging credential) as `MANUAL`
   rather than silently dropping it
6. Run the final full-suite test (cargo test --workspace or uv run pytest)
7. Produce a summary table: Area | Step | Evidence | Result
8. If `--post`: post the table as a PR comment

## Manual Test Plans

Step 5 is the bridge between the diff-derived steps this command
generates and the manual test plan the author wrote. The two are not
the same: diff-derived steps cover what changed, and a manual plan
covers what a reviewer would otherwise have to figure out how to
exercise.

Triggers for a manual test plan, and its numbered-step format, are in
`sanctum:pr-prep/modules/pr-template.md`. This command consumes that
section rather than defining its own.

Three outcomes for an author-written step:

| Outcome | Meaning |
|---------|---------|
| PASS / FAIL | Ran here, with evidence captured |
| MANUAL | Needs a human or an environment this run lacks. Reported, never dropped |
| MALFORMED | The step states no expected result, so it cannot be failed |

A PR that fires a trigger but carries no `## Test plan` is reported as
a gap in the summary table. That is a finding, not a hard failure: the
author may have a reason, and the report puts it in front of a
reviewer.

## Failure Behaviour

If any step produces **FAIL**, the command reports all failures and exits
with non-zero status. When called from `/fix-pr`, it halts before Step 6
(Complete / Gate 3). Pass `--skip-validate` to `/fix-pr` to bypass.

## Output Format

```markdown
### validate-pr: PR #123

| Area | Step | Evidence | Result |
|------|------|----------|--------|
| Rust: token-types | cargo build --workspace | [E1] 0 errors | PASS |
| Rust: token-types | cargo test -p token-types | [E2] 12 passed | PASS |
| Shell: hooks/pre-commit | shellcheck | [E3] 0 issues | PASS |
| Revert-test: lib.rs:45 | break/fail/restore | [RT-1..5] genuine guard | PASS |
| Final: cargo test --workspace | full suite | [E4] 694 passed | PASS |

**Totals**: 5 steps — 5 PASS, 0 FAIL, 0 INCONCLUSIVE
```

## See Also

- `Skill(sanctum:validate-pr)`: full algorithm and step details
- `/fix-pr`: calls this skill automatically after Step 4 (Fix)
- `Skill(imbue:proof-of-work)`: `[E1]`/`[E2]` evidence capture conventions
- `Skill(leyline:git-platform)`: GitHub/GitLab CLI command mapping
