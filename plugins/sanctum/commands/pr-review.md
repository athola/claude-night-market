---
name: pr-review
description: Comprehensive PR review with scope validation and code analysis
usage: /pr-review [<pr-number> | <pr-url>] [--scope-mode strict|standard|flexible] [--auto-approve-safe-prs] [--create-backlog-issues] [--dry-run] [--no-line-comments] [--skip-version-check]
extends: "superpowers:receiving-code-review"
modules: [scope-validation, version-check, review-workflow]
---

# Enhanced PR Review

<identification>
triggers: PR review, code review, pull request, pre-merge

use_when:
- Reviewing feature PRs or enforcing quality gates
- Pre-merge validation with scope discipline
</identification>

Integrates Sanctum's disciplined scope validation with superpowers:receiving-code-review's detailed analysis for thorough, balanced PR reviews that prevent scope creep while ensuring code quality.

## Core Philosophy

**Scope-Aware Quality Validation**
- Validate implementation against stated requirements
- Prevent overengineering through scope discipline
- Validate code quality without blocking valid implementations
- Route out-of-scope improvements to backlog

## Quick Start

```bash
# Review PR with standard scope checking
/pr-review 42

# Strict scope enforcement for critical PRs
/pr-review 42 --scope-mode strict

# Review with automatic backlog issue creation
/pr-review 42 --create-backlog-issues

# Skip version validation (use sparingly)
/pr-review 42 --skip-version-check

# Dry run (no GitHub comments)
/pr-review 42 --dry-run
```

## Workflow Overview

### Phase 1: Scope Establishment (Sanctum)
1. **Discover Scope Artifacts**: Search plan.md, spec.md, tasks.md, PR description
2. **Check Existing Backlog**: Avoid duplicate issue creation
3. **Establish Requirements Baseline**: Extract requirements from artifacts

### Phase 1.5: Version Validation (MANDATORY)
**CRITICAL**: Validates version consistency across all version-bearing files.

**Bypass Conditions**:
- CLI flag: `--skip-version-check`
- GitHub label: `skip-version-check`
- PR description: `[skip-version-check]`

If versions misaligned: **BLOCKING** - PR cannot merge until resolved.

### Phase 2: Code Analysis (Superpowers)
Delegates to superpowers:receiving-code-review for:
- Automated code quality analysis
- Best practice validation
- Security scanning
- Performance impact assessment

### Phase 3: Synthesis & Validation
- Combine scope analysis with code review findings
- Classify issues (blocking, in-scope, suggestions, backlog)
- Validate compliance with requirements

### Phase 4: GitHub Review Submission (MANDATORY)
**CRITICAL**: Posts structured findings as GitHub review comments.

Options:
- `--no-line-comments`: Skip inline comments (summary only)
- `--dry-run`: Preview without posting

### Phase 5: Test Plan Generation (MANDATORY)
Creates comprehensive test plan for QA validation.

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--scope-mode strict\|standard\|flexible` | Scope enforcement level | standard |
| `--auto-approve-safe-prs` | Auto-approve docs-only/trivial PRs | false |
| `--create-backlog-issues` | Create GitHub issues for backlog items | false |
| `--dry-run` | Preview review without posting | false |
| `--no-line-comments` | Skip inline comments | false |
| `--skip-version-check` | Skip version validation | false |

## Review Classification Framework

### Blocking Issues
- **Must fix before merge**
- Security vulnerabilities
- Breaking changes without migration
- Critical bugs
- Version misalignment (if not skipped)

### In-Scope Issues
- **Should fix in this PR**
- Implementation bugs
- Performance problems
- Code quality issues within scope

### Suggestions (Author's Discretion)
- **Consider for improvement**
- Code style preferences
- Minor optimizations
- Alternative approaches

### Backlog Items
- **Defer to future PRs**
- Out-of-scope features
- Nice-to-have improvements
- Future optimizations

## Scope Mode Details

### Strict Mode
- Zero tolerance for scope creep
- All out-of-scope changes → BLOCKING
- Use for: Critical releases, security fixes

### Standard Mode (Default)
- Balanced approach
- In-scope improvements allowed
- Out-of-scope items → backlog
- Use for: Regular feature development

### Flexible Mode
- Lenient scope enforcement
- Improvements encouraged
- Minimal blocking
- Use for: Exploratory work, prototypes

## Enhanced Example

```
PR #42: Add user authentication system
=======================================

SCOPE COMPLIANCE ANALYSIS
--------------------------
Requirements (from spec.md):
1. ✅ JWT-based authentication
2. ✅ Password hashing (bcrypt)
3. ✅ Session management
4. ❌ NOT REQUIRED: Rate limiting (out of scope)
5. ❌ NOT REQUIRED: OAuth integration (out of scope)

VERSION VALIDATION
------------------
✅ PASS - All versions aligned at 1.2.0

SUPERPOWERS CODE ANALYSIS
--------------------------
Security: 8/10
Performance: 9/10
Maintainability: 7/10

BLOCKING ISSUES (2)
-------------------
1. [SECURITY] Password minimum length not enforced
2. [SECURITY] Missing input sanitization in username field

IN-SCOPE ISSUES (3)
-------------------
1. JWT secret hardcoded (should use environment variable)
2. Session timeout not configurable
3. Missing error messages for failed auth

SUGGESTIONS (4)
---------------
1. Consider adding refresh tokens
2. Could cache user lookups
3. Improve error handling readability
4. Add JSDoc comments

BACKLOG → GitHub Issues Created (5)
-----------------------------------
#43: Add rate limiting to auth endpoints
#44: Implement OAuth2 providers
#45: Add 2FA support
#46: Create admin user management UI
#47: Add password reset functionality

RECOMMENDATION
--------------
⚠️  REQUEST CHANGES

Must fix 2 BLOCKING issues before merge.
In-scope issues should be addressed.
Suggestions and backlog items documented.
```

## Detailed Documentation

For comprehensive review patterns and implementation:
- **[Complete Guide](pr-review/modules/complete-guide.md)** - Full review methodology
- **[Scope Validation](pr-review/modules/scope-validation.md)** - Scope enforcement patterns
- **[Version Check](pr-review/modules/version-check.md)** - Version validation details
- **[Review Workflow](pr-review/modules/review-workflow.md)** - Phase-by-phase breakdown

## Integration

```bash
# Pre-review preparation
gh pr view 42                    # View PR details
/pr-review 42 --dry-run          # Preview review

# Actual review
/pr-review 42                    # Standard review
/pr-review 42 --create-backlog-issues  # With issue creation

# Post-review
gh pr checks 42                  # Verify CI passes
gh pr merge 42 --squash          # Merge if approved
```

## See Also

- **/fix-pr**: Fix PR review feedback
- **/prepare-pr**: Prepare PR for submission
- **superpowers:receiving-code-review**: Code review engine
- **sanctum:git-workspace-review**: Repository analysis
