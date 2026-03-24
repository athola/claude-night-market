# PR/MR Review: Workflow Details

Detailed workflow phases, examples, and advanced features.

> **See Also**: [Main Command](../../pr-review.md) |
> [Framework](review-framework.md) |
> [Configuration](review-configuration.md)

**Platform Note**: Commands below show GitHub (`gh`) examples. Check
session context for `git_platform:` and consult
`Skill(leyline:git-platform)` for GitLab (`glab`) / Bitbucket
equivalents.

## Workflow Modules

| Module | Phases | Contents |
|--------|--------|----------|
| [Phases 1-4](review-workflow-phases-1-4.md) | 1, 1.5, 1.7, 2, 2.5, 3, 4 | Scope establishment, version validation, slop detection, code analysis, synthesis, review output |
| [Phases 5-6](review-workflow-phases-5-6.md) | 5, 6 | Test plan generation, PR description update |
| [Enforcement](review-workflow-enforcement.md) | — | Mandatory output verification, command options |

## Phase Overview

### Phase 1: Scope Establishment (Sanctum)

Discover scope artifacts (plan files, PR description, commit
history), check existing backlog to avoid duplicate issues, and
establish a requirements baseline.

### Phase 1.5: Version Validation (MANDATORY)

Validate version consistency across all version-bearing files before
code analysis. Can be bypassed via `--skip-version-check`, GitHub
label `skip-version-check`, or PR description marker
`[skip-version-check]`.

### Phase 1.7: Slop Detection (MANDATORY)

Run AI slop detection on changed `.md` files and commit messages
using `Skill(scribe:slop-detector)` before code review.

### Phase 2: Code Analysis (Superpowers)

Detailed code review examining implementation correctness,
requirement coverage, and finding classification.

### Phase 2.5: Code Quality Analysis (MANDATORY)

Targeted quality checks with completion checklist.

### Phase 3: Synthesis & Validation

Cross-reference findings with scope requirements, classify by
severity, generate GitHub issues for out-of-scope items.

### Phase 4: Review Output (MANDATORY)

Post inline comments and submit review summary via GitHub API. With
`--local`, write full report to a local `.md` file.

### Phase 5: Test Plan Generation (MANDATORY)

Generate and post a detailed test plan as a separate PR comment so
`/fix-pr` can reference and execute verification steps.

### Phase 6: PR Description Update (MANDATORY)

Update PR description with review summary table. Detect and inject
test plan if not already present.

## Mandatory Outputs

All three outputs are required for a complete review:

| Output | Phase | Verification |
|--------|-------|--------------|
| Review comment | Phase 4 | `gh pr view --json comments` contains "PR Review" |
| Test plan comment | Phase 5 | `gh pr view --json comments` contains "Test Plan" |
| PR description | Phase 6 | `gh pr view --json body` is non-empty and contains "Review Summary" |

See [Enforcement](review-workflow-enforcement.md) for the full
verification script and options reference.

**Full workflow details**: See the phase modules linked in the table
above for complete implementation guidance.
