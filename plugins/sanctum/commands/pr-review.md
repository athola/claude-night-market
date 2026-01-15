---
name: pr-review
description: Comprehensive PR review with scope validation and code analysis
usage: /pr-review [<pr-number> | <pr-url>] [--scope-mode strict|standard|flexible] [--auto-approve-safe-prs] [--no-auto-issues] [--dry-run] [--no-line-comments] [--skip-version-check]
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
4. **GitHub Review** - Post review comments to PR (MANDATORY)
5. **Test Plan** - Post verification checklist to PR (MANDATORY)
6. **PR Description** - Update PR body OR create from commits/scope if empty (MANDATORY)

**MANDATORY OUTPUTS:** Review comment, Test plan comment, PR description update.
If any are missing, the review is INCOMPLETE.

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

## Review Classification

Reviews classify findings into:
- **Blocking Issues** - Must fix before merge
- **Non-Blocking Improvements** - Nice-to-have enhancements
- **Out-of-Scope** - Valid ideas for future work

**Classification details**: See [Classification Framework](pr-review/modules/review-framework.md)

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
- **Superpowers**: `superpowers:receiving-code-review`
