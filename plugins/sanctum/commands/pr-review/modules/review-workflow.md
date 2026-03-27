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

### Phase 1.9: PR Hygiene Checks

**Run PR hygiene checks BEFORE detailed code analysis.**

See `plugins/sanctum/skills/pr-review/modules/pr-hygiene.md`
for the full detection heuristics.

1. **Atomicity check (one PR = one logical change)**

   ```bash
   # Count distinct conventional commit types
   COMMIT_TYPES=$(gh pr view $PR_NUMBER --json commits \
     --jq '.commits[].messageHeadline' | \
     grep -oE '^(feat|fix|refactor|docs|test|chore|style|perf)' | \
     sort -u | wc -l)

   CHANGED_FILES=$(gh pr view $PR_NUMBER --json changedFiles \
     --jq '.changedFiles')

   if [[ "$COMMIT_TYPES" -gt 2 ]]; then
     echo "[G-ATOMICITY] $COMMIT_TYPES distinct commit types"
   fi

   if [[ "$CHANGED_FILES" -gt 30 ]]; then
     echo "[G-ATOMICITY] $CHANGED_FILES files changed"
   fi
   ```

2. **Self-review signals**

   ```bash
   # Check for unsquashed fixup/typo commits
   FIXUPS=$(gh pr view $PR_NUMBER --json commits \
     --jq '.commits[].messageHeadline' | \
     grep -ciE '(fixup|fix typo|oops|wip|forgot|actually)' || true)

   # Check for formatting commits mixed with logic
   FMT_COMMITS=$(gh pr view $PR_NUMBER --json commits \
     --jq '.commits[].messageHeadline' | \
     grep -ciE '(fmt|format|lint|style|whitespace|cleanup)' || true)

   if [[ "$FIXUPS" -gt 2 ]]; then
     echo "[G-SELFREVIEW] $FIXUPS fixup commits - author may not have self-reviewed"
   fi

   if [[ "$FMT_COMMITS" -gt 0 ]]; then
     echo "[G-SELFREVIEW] Formatting commits mixed with feature work"
   fi
   ```

3. **Agent-generated code signals (structural)**

   Run Tier 1 checks from `modules/pr-hygiene.md`:

   ```bash
   # Debug/TODO left in new code
   DEBUG_LINES=$(gh pr diff $PR_NUMBER | \
     grep -cE '^\+.*(console\.log|print\(|debugger|TODO|FIXME|HACK)' || true)

   # Wrapper functions (body is a single delegation call)
   WRAPPERS=$(gh pr diff $PR_NUMBER | \
     awk '/^\+.*def |^\+.*fn |^\+.*function /{name=$0; getline; \
     if(/^\+\s*(return |self\.)/ && !/^\+\s*$/) print name}' \
     2>/dev/null | wc -l || true)

   # Add/delete ratio (agents add 5x+ more than they remove)
   STATS=$(gh pr view $PR_NUMBER --json additions,deletions \
     --jq '"\(.additions) \(.deletions)"')
   ADDITIONS=$(echo $STATS | cut -d' ' -f1)
   DELETIONS=$(echo $STATS | cut -d' ' -f2)
   if [[ "$DELETIONS" -gt 0 ]]; then
     RATIO=$((ADDITIONS / DELETIONS))
   else
     RATIO="$ADDITIONS"
   fi

   if [[ "$DEBUG_LINES" -gt 0 ]]; then
     echo "[S-CURATION] $DEBUG_LINES debug/TODO lines in new code"
   fi
   if [[ "$WRAPPERS" -gt 0 ]]; then
     echo "[S-CURATION] $WRAPPERS possible wrapper functions"
   fi
   if [[ "$RATIO" -gt 5 ]]; then
     echo "[S-CURATION] Add/delete ratio $RATIO:1"
   fi
   ```

   For PRs with >10 files, also run Tier 2 checks
   (import bloat, directory spread). See
   `modules/pr-hygiene.md` for the full heuristic set.

**Classification:**

| Signal | Severity |
|--------|----------|
| Mixed commit types (>2) | SUGGESTION |
| >30 files changed | SUGGESTION |
| Unsquashed fixup commits (>2) | SUGGESTION |
| Formatting commits mixed with logic | SUGGESTION |
| Debug statements in new code | IN-SCOPE |
| Wrapper functions (single-call body) | SUGGESTION |
| Add/delete ratio >5:1 | SUGGESTION |
| Incomplete refactor (old + new coexist) | IN-SCOPE |

**Output from this phase:**

```markdown
### PR Hygiene

**Atomicity**: N commit types, M files changed
**Self-Review Signals**: [clean | N issues found]
**Agent Curation Signals**: [clean | N issues found]

[Detailed findings if any]
```

### Phase 2: Code Analysis (Superpowers)

Detailed code review examining implementation correctness,
requirement coverage, and finding classification.

### Phase 2.5: Code Quality Analysis (MANDATORY)

Targeted quality checks with completion checklist.
See `review-workflow-phases-1-4.md` for full Phase 2.5
details including duplication scan, quality findings
classification, and test quality analysis.

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
