---
name: validate-mr
description: Generate and self-execute a diff-derived test plan for an MR. Reads
  the diff, groups changes by area, runs targeted verifications, proves
  revert-tests are genuine guards, and reports a structured summary table.
usage: /sanctum:validate-mr [<mr-number> | <pr-url> | <mr-url>] [--post] [--revert-tests <N>]
---

# validate-mr

Generate and self-execute a step-by-step validation plan matched to what
actually changed in an MR. Bridges the gap between "tests pass" and "the
fix does what it claims."

## When To Use

- Standalone after any MR fix, to produce targeted validation evidence
- Called automatically by `/fix-pr` at the end of Step 5 (Validate)
- When you need proof that revert-tests catch regressions

## When NOT To Use

- `--scope minor` in `/fix-pr` with only formatting or doc changes
- No diff available (clean branch, nothing changed)
- Pass `--skip-validate` to `/fix-pr` to bypass

## Options

| Option | Description |
|--------|-------------|
| `<mr-number>` | Target MR/PR number (default: current branch PR) |
| `<pr-url>` / `<mr-url>` | Full GitHub or GitLab URL to the PR/MR |
| `--post` | Post the summary table as a PR/MR comment |
| `--revert-tests <N>` | Number of revert-test quality checks to run (default: 1) |

## Quick Reference

```bash
# Run on current branch PR
/sanctum:validate-mr

# Run on a specific PR
/sanctum:validate-mr 123

# Run and post results as a PR comment
/sanctum:validate-mr 123 --post

# Run with two revert-test checks
/sanctum:validate-mr 123 --revert-tests 2
```

## Workflow

See `Skill(sanctum:validate-mr)` for the full algorithm:

1. Fetch the MR diff and group changed files by area (Rust, Python, Shell,
   grammar, build/config)
2. Generate at least one verification step per area
3. Execute each step, capture output as evidence (`[E1]`, `[E2]`, ...)
4. Run a revert-test quality check: break a representative fix, confirm
   the corresponding test fails, restore via `git checkout — <file>`
5. Run the final full-suite test (cargo test --workspace or uv run pytest)
6. Produce a summary table: Area | Step | Evidence | Result
7. If `--post`: post the table as a PR comment

## Failure Behaviour

If any step produces **FAIL**, the command reports all failures and exits
with non-zero status. When called from `/fix-pr`, it halts before Step 6
(Complete / Gate 3). Pass `--skip-validate` to `/fix-pr` to bypass.

## Output Format

```markdown
### validate-mr: PR #123

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

- `Skill(sanctum:validate-mr)` — full algorithm and step details
- `/fix-pr` — calls this skill automatically after Step 4 (Fix)
- `Skill(imbue:proof-of-work)` — `[E1]`/`[E2]` evidence capture conventions
- `Skill(leyline:git-platform)` — GitHub/GitLab CLI command mapping
