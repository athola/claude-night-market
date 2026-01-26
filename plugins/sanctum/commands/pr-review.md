---
name: pr-review
description: Comprehensive PR review with scope validation and code analysis
usage: /pr-review [<pr-number> | <pr-url>] [--scope-mode strict|standard|flexible] [--auto-approve-safe-prs] [--no-auto-issues] [--dry-run] [--no-line-comments] [--skip-version-check] [--skip-doc-review]
extends: "superpowers:receiving-code-review"
---

# Enhanced PR Review

<identification>
triggers: PR review, code review, pull request, pre-merge

use_when:
- Reviewing feature PRs or enforcing quality gates
- Pre-merge validation with scope discipline
</identification>

Integrates Sanctum's disciplined scope validation with superpowers:receiving-code-review's detailed analysis to provide thorough, balanced PR reviews that prevent scope creep while ensuring code quality.

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

## When to Use

- Reviewing feature branch PRs
- Validating implementation against requirements
- Pre-merge quality gates
- Generating actionable review feedback
- Creating improvement backlog

## Documentation

| Document | Purpose |
|----------|---------|
| **[Workflow Details](pr-review/modules/review-workflow.md)** | Detailed review phases, examples, advanced features |
| **[Classification Framework](pr-review/modules/review-framework.md)** | Review classification system and scope modes |
| **[Configuration & Options](pr-review/modules/review-configuration.md)** | Command options, configuration, best practices |

## Quick Start

### Basic Usage
```bash
# Review PR with default settings
/pr-review 123

# Review with PR URL
/pr-review https://github.com/org/repo/pull/123
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

# Auto-approve safe PRs
/pr-review --auto-approve-safe-prs

# Skip automatic issue creation for out-of-scope items (issues are created by default)
/pr-review --no-auto-issues

# Skip version consistency check
/pr-review --skip-version-check
```

## Workflow Summary

1. **Scope Establishment** - Discover requirements from plan/spec/tasks
2. **Version Validation** - Ensure version consistency (mandatory unless bypassed)
3. **Code Analysis** - Deep technical review
4. **Documentation Review** - AI slop detection on changed docs (via scribe)
5. **GitHub Review** - Post review comments to PR (MANDATORY)
6. **Test Plan** - Post verification checklist to PR (MANDATORY)
7. **PR Description** - Update PR body OR create from commits/scope if empty (MANDATORY)

**MANDATORY OUTPUTS:** Review comment, Test plan comment, PR description update.
If any are missing, the review is INCOMPLETE.

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

## Integration

This command integrates with:
- **superpowers:receiving-code-review**: Core review logic
- **scribe:slop-detector**: Documentation quality analysis
- **scribe:doc-editor**: Interactive doc cleanup (if needed)
- **gh CLI**: Fetch PR data, post comments, create issues
- **imbue:scope-guard**: Scope worthiness evaluation
- **backlog system**: Issue creation and tracking

## Getting Help

- **Workflow Phases**: See [Workflow Details](pr-review/modules/review-workflow.md)
- **Options Reference**: See [Configuration & Options](pr-review/modules/review-configuration.md)
- **Framework Guide**: See [Classification Framework](pr-review/modules/review-framework.md)

## See Also

- `/fix-pr` - Address PR review feedback
- `/pr` - Create pull request
- `/update-tests` - Update test suite
- `/slop-scan` - Direct AI slop detection (scribe plugin)
- `/doc-polish` - Interactive documentation cleanup (scribe plugin)
- **Superpowers**: `superpowers:receiving-code-review`
