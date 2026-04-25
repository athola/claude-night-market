---
name: pr-review
description: Review pull requests with scope validation, code analysis, and line comments. Supports GitHub PRs and GitLab MRs.
usage: /pr-review [<pr-number> | <pr-url> | <mr-url>] [--scope-mode strict|standard|flexible] [--auto-approve-safe-prs] [--no-auto-issues] [--no-insights] [--dry-run] [--local [path]] [--no-line-comments] [--skip-version-check] [--skip-doc-review] [--stack] [--no-stack] [--base <branch>]
extends: "superpowers:receiving-code-review"
---

# Enhanced PR/MR Review

Integrates Sanctum's disciplined scope validation with superpowers:receiving-code-review's detailed analysis to provide thorough, balanced reviews that prevent scope creep while ensuring code quality. Supports both GitHub PRs and GitLab MRs via `leyline:git-platform` detection.

## Core Philosophy

**Scope-Aware Quality Validation**
- Validate implementation against stated requirements
- Prevent overengineering through scope discipline
- validate code quality without blocking valid implementations
- Route out-of-scope improvements to backlog

## Key Enhancements

### Sanctum Contributions
- **Scope Baseline Establishment**: Analyzes plan/spec artifacts
- **Requirements Compliance Checking**: Validates against original specs
- **Automatic Issue Creation**: Out-of-scope items are automatically logged to GitHub issues
- **Structured Reporting**: Clear classification of findings

### Superpowers Contributions
- **Automated Code Analysis**: Deep review of implementation quality
- **Best Practice Validation**: Industry-standard checks
- **Security Scanning**: Vulnerability detection
- **Performance Impact Assessment**: Efficiency considerations

## When To Use

- Reviewing feature branch PRs
- Validating implementation against requirements
- Pre-merge quality gates
- Generating actionable review feedback
- Creating improvement backlog

## When NOT To Use

- Self-reviewing trivial changes
- Draft PRs not ready for review

## Documentation

| Document | Purpose |
|----------|---------|
| **[Workflow Details](pr-review/modules/review-workflow.md)** | Detailed review phases, examples, advanced features |
| **[Classification Framework](pr-review/modules/review-framework.md)** | Review classification system and scope modes |
| **[Configuration & Options](pr-review/modules/review-configuration.md)** | Command options, configuration, best practices |

## Quick Start

### Basic Usage
```bash
# Review PR/MR with default settings
/pr-review 123

# Review with platform URL
/pr-review https://github.com/org/repo/pull/123
/pr-review https://gitlab.com/org/repo/-/merge_requests/123
```

### Scope Modes
```bash
# Strict scope enforcement
/pr-review --scope-mode strict

# Standard (balanced) - default
/pr-review --scope-mode standard

# Flexible (minimal blocking)
/pr-review --scope-mode flexible
```

### Common Options
```bash
# Dry run (no comments posted)
/pr-review --dry-run

# Write report to local .md file instead of posting to PR
/pr-review --local
/pr-review --local reviews/my-review.md

# Auto-approve safe PRs
/pr-review --auto-approve-safe-prs

# Skip automatic issue creation for out-of-scope items (issues are created by default)
/pr-review --no-auto-issues

# Skip posting review findings as Insights to Discussions (insights posted by default)
/pr-review --no-insights

# Skip version consistency check
/pr-review --skip-version-check
```

### Stack Mode (Multi-PR Review)

When the target PR is part of a stack of dependent PRs
rooted at a common base branch, `/pr-review` can review
the entire stack in one invocation. Each PR still gets
its own review comment, test plan, and PR description
update; the root PR additionally receives a consolidated
stack-level summary.

```bash
# Explicit: review the whole stack containing PR 123
/pr-review 123 --stack

# Override the base branch (default: master)
/pr-review 123 --stack --base main

# Force single-PR mode even if a stack is detected
/pr-review 123 --no-stack
```

**Behavior**:

1. Before running its main workflow, `/pr-review` loads
   `Skill(sanctum:stack-mode)` to resolve the stack.
   Detection uses three strategies: branch-name convention
   (`stack/<feat>/<slice>`), the `## Stack` summary
   comment posted by `stack-push`, and a base-chain walk.
2. Without `--stack` but with a detected stack of size
   >= 2, the command prompts before iterating. Default
   is single-PR mode.
3. With `--stack`, the main review workflow runs once
   per PR in base-to-tip order. Per-PR outputs (review
   comment, test plan, description update) remain
   mandatory and unchanged.
4. After successful iteration, one stack summary comment
   is posted on the root PR listing each PR, its status,
   and a link to its per-PR review comment.
5. If any PR fails its mandatory outputs, iteration
   halts. Downstream PRs are left untouched because
   their review context may now be stale.

**Stack-mode contract**: see `Skill(sanctum:stack-mode)`
for the shared detection, iteration, and summary
format used by both `/pr-review --stack` and
`/fix-pr --stack`.

## Workflow Summary

1. **Scope Establishment** - Discover requirements from plan/spec/tasks
2. **Version Validation** - Ensure version consistency (mandatory unless bypassed)
3. **Slop Detection** - AI content markers in docs, commits, PR description (MANDATORY)
4. **PR Hygiene** - Atomicity, self-review signals, agent curation (MANDATORY)
5. **Code Analysis** - Deep technical review
6. **Code Quality** - Duplication, redundancy, test quality analysis
7. **GitHub Review** - Post review comments to PR (MANDATORY; or write to local file with `--local`)
8. **Test Plan** - Post verification checklist to PR (MANDATORY; or include in local file with `--local`)
9. **PR Description** - Update PR body OR create from commits/scope if empty (MANDATORY; skipped with `--local`)
10. **Discussion Insights** - Post review findings as Insights to GitHub Discussions (DEFAULT; opt-out with `--no-insights`)

**MANDATORY OUTPUTS:** Review comment, Test plan comment, PR description update.
If any are missing, the review is INCOMPLETE.

### Discussion Insights (Step 10)

After the review comment, test plan, and PR description are posted,
write the full review markdown to `reviews/pr-<NNN>-review.md` (the
same path used by `--local`) and run:

```bash
python3 plugins/abstract/scripts/post_review_insights.py \
  reviews/pr-<NNN>-review.md --pr <NNN>
```

Each blocker becomes a high-severity `[PR Finding]` discussion, each
non-blocking row a medium-severity one. The InsightRegistry deduplicates
by `{type|skill|summary}` content hash with 30-day staleness, so
re-running on the same review is idempotent. The user observed that
cron-driven Phase 6a Learning posts were the only auto-post path,
leaving recent iterative review work invisible to the collective
intelligence layer; this step closes that loop.

Skip with `--no-insights` for trivial reviews where the findings
aren't worth posting (e.g., typo fixes, version bumps).

### PR Description Update (CRITICAL)

**DO NOT use `gh pr edit`** - it requires `read:org` scope which many tokens don't have.

**Use `gh api` PATCH instead** (only requires `repo` scope):

```bash
# Get owner/repo from current directory
OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

# Update PR description via REST API
gh api "repos/$OWNER_REPO/pulls/$PR_NUM" \
  -X PATCH \
  -f title="$NEW_TITLE" \
  -f body="$NEW_BODY"
```

**Fallback if API fails**: Post description as a comment instead of failing the review.

```bash
# If API fails (e.g., fork PR without write access)
gh pr comment $PR_NUM --body "## PR Summary (Auto-generated)

$NEW_BODY

---
*Note: Could not update PR description. Posted as comment instead.*"
```

### Verification Checklist

After completing `/pr-review`, verify all mandatory outputs:

```bash
# Set PR number
PR_NUM=123  # Replace with actual PR number

# 1. Verify review comment exists
gh pr view $PR_NUM --json comments --jq '[.comments[].body | contains("PR Review")] | any'
# Expected: true

# 2. Verify test plan exists
gh pr view $PR_NUM --json comments --jq '[.comments[].body | ascii_downcase | contains("test plan")] | any'
# Expected: true

# 3. Verify PR description is not empty
gh pr view $PR_NUM --json body --jq '.body | length > 0'
# Expected: true
```

**If any check returns `false`, the review is INCOMPLETE.**

**Full workflow details**: See [Workflow Details](pr-review/modules/review-workflow.md)

## War Room Checkpoint (Automatic)

**Purpose**: Assess whether complex PR findings warrant expert deliberation before finalizing verdict.

**Auto-triggers when** (moderate approach):
- >3 blocking issues identified, OR
- Architecture changes detected (new services, major refactors), OR
- ADR non-compliance found, OR
- Scope-mode=strict with out-of-scope findings requiring judgment

**Checkpoint invocation** (automatic, after Phase 4):

```markdown
Skill(attune:war-room-checkpoint) with context:
  source_command: "pr-review"
  decision_needed: "Review verdict for PR #123"
  blocking_items: [
    {type: "blocking", description: "Missing error handling"},
    {type: "architecture", description: "New service without ADR"},
    {type: "scope", description: "Unrelated payment refactor"}
  ]
  files_affected: [list of changed files]
  profile: [from user settings, default: "default"]
```

**War Room Questions** (when escalated):
- "Should this PR be split into smaller, reviewable chunks?"
- "Which blocking issues are truly blocking vs. nice-to-have?"
- "Is the architectural change warranted given the stated scope?"

**Response handling**:

| RS Score | Mode | Action |
|----------|------|--------|
| RS <= 0.40 | Express | Quick verdict recommendation, continue immediately |
| RS 0.41-0.60 | Lightweight | 3-expert panel deliberates on blocking/non-blocking classification |
| RS > 0.60 | Full Council | Full panel reviews architecture decisions |

**Auto-continue logic**:
- If confidence > 0.8: Apply War Room's blocking/non-blocking reclassification
- If confidence <= 0.8: Present findings to user before posting review

**Skip conditions** (checkpoint not invoked):
- 0 blocking issues (clean PR)
- All issues are clearly minor (typos, formatting)
- `--skip-war-room` flag
- `--dry-run` mode (assessment shown but not posted)

## Review Classification

Reviews classify findings into:
- **Blocking Issues** - Must fix before merge
- **Non-Blocking Improvements** - Nice-to-have enhancements
- **Out-of-Scope** - Valid ideas for future work

**Classification details**: See [Classification Framework](pr-review/modules/review-framework.md)

## Documentation Review

When the PR includes documentation changes (`.md` files), the review automatically:

1. **Scans for AI slop** via `Skill(scribe:slop-detector)`
2. **Reports findings** in the review comment
3. **Suggests remediation** for high-severity markers

```bash
# Skip documentation review
/pr-review --skip-doc-review

# Include doc findings in dry run
/pr-review --dry-run  # Shows what would be reported
```

### Documentation Findings Format

```markdown
### Documentation Quality

**Files scanned**: 3
**Slop score**: 2.1/10 (Light)

| File | Score | Top Issues |
|------|-------|------------|
| docs/guide.md | 3.2 | "comprehensive", em dash density |
| README.md | 1.5 | Clean |

**Recommendation**: Consider running `/doc-polish docs/guide.md`
```

Documentation findings are **non-blocking** by default. Use `--strict` to treat them as blocking.

## Scope Modes

| Mode | Behavior | When to Use |
|------|----------|-------------|
| **strict** | Enforce exact requirements | Critical features, API changes |
| **standard** | Balanced validation (default) | Most PRs |
| **flexible** | Minimal scope blocking | Exploratory work, prototypes |

**Mode details**: See [Classification Framework](pr-review/modules/review-framework.md#scope-mode-details)

## Agent Teams (Default for Large PRs)

Agent teams is **on by default** for PRs with 15+ changed files spanning multiple subsystems. Teammates parallelize review aspects (security, architecture, tests, docs) and the lead synthesizes before posting. Use `--no-agent-teams` to force sequential review.

**Automatic downgrade**: Agent teams is skipped for PRs with <15 changed files. Use `--no-agent-teams` to disable for any invocation.

**Requires**: Claude Code 2.1.32+, tmux, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Falls back to sequential review if unavailable.

```bash
# Large PR uses agent teams by default
/pr-review 123

# Disable agent teams explicitly
/pr-review 123 --no-agent-teams
```

## Integration

This command integrates with:
- **superpowers:receiving-code-review**: Core review logic
- **pensive:code-refinement**: Code quality and deduplication analysis (optional)
- **pensive:code-refinement**: Code quality patterns
- **scribe:slop-detector**: Documentation quality analysis
- **scribe:doc-editor**: Interactive doc cleanup (if needed)
- **gh CLI**: Fetch PR data, post comments, create issues
- **imbue:scope-guard**: Scope worthiness evaluation
- **backlog system**: Issue creation and tracking
- **Agent Teams** (2.1.32+): Optional parallel review for large PRs
- **sanctum:stack-mode**: Multi-PR stack iteration contract (used by `--stack`)

### Code Quality Analysis (MANDATORY - NON-NEGOTIABLE)

**This analysis is REQUIRED and cannot be bypassed.**

Every PR review automatically invokes `pensive:code-refinement` patterns for:
- **Duplication detection**: Near-identical blocks, similar functions
- **Redundancy analysis**: Repeated patterns, copy-paste indicators
- **Clean code checks**: Complexity, naming, magic values
- **Agent curation**: Incomplete refactors, premature abstractions, scope drift
- **Test quality (the revert test)**: Do tests break if the fix is reverted?

Code quality findings are classified as:
- **BLOCKING**: Exact duplication >10 lines, tests that pass on revert
- **IN-SCOPE**: Similar patterns to consolidate, uncurated agent code, tests that only assert old behavior
- **SUGGESTION**: Minor redundancy, PR atomicity recommendations

## Getting Help

- **Workflow Phases**: See [Workflow Details](pr-review/modules/review-workflow.md)
- **Options Reference**: See [Configuration & Options](pr-review/modules/review-configuration.md)
- **Framework Guide**: See [Classification Framework](pr-review/modules/review-framework.md)

## See Also

- `/fix-pr` - Address PR review feedback (also supports `--stack`)
- `/pr` - Create pull request
- `/update-tests` - Update test suite
- `/slop-scan` - Direct AI slop detection (scribe plugin)
- `/doc-polish` - Interactive documentation cleanup (scribe plugin)
- `Skill(sanctum:stack-mode)` - Shared multi-PR stack iteration contract
- `Skill(sanctum:stack-create)` / `stack-push` / `stack-rebase` - Stack lifecycle primitives
- **Superpowers**: `superpowers:receiving-code-review`
