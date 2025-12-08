---
name: pr-review-wrapper
description: Enhanced PR review that combines Sanctum's scope-focused validation with superpowers:receiving-code-review for comprehensive analysis and automated quality checks
usage: /pr-review-wrapper [<pr-number> | <pr-url>] [--scope-mode strict|standard|flexible] [--auto-approve-safe-prs] [--create-backlog-issues]
extends: "superpowers:receiving-code-review"
---

# Enhanced PR Review Wrapper

Integrates Sanctum's disciplined scope validation with superpowers:receiving-code-review's comprehensive analysis to provide thorough, balanced PR reviews that prevent scope creep while ensuring code quality.

## Core Philosophy

**Scope-Aware Quality Validation**
- Validate implementation against stated requirements
- Prevent overengineering through scope discipline
- Ensure code quality without blocking valid implementations
- Route out-of-scope improvements to backlog

## Key Enhancements

### Sanctum Contributions
- **Scope Baseline Establishment**: Analyzes plan/spec artifacts
- **Requirements Compliance Checking**: Validates against original specs
- **Backlog Triage**: Creates GitHub issues for out-of-scope items
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

## Workflow

### Phase 1: Scope Establishment (Sanctum)

1. **Discover Scope Artifacts**
   ```bash
   # Search in priority order:
   1. docs/plans/*-<branch-name>*.md
   2. plan.md or spec.md
   3. tasks.md with completed items
   4. PR description and commit history
   ```

2. **Establish Requirements Baseline**
   ```markdown
   This PR aims to: [extracted from artifacts]

   Requirements:
   1. [Requirement from plan]
   2. [Requirement from spec]
   3. [Requirement from tasks]
   ```

### Phase 2: Code Analysis (Superpowers)

3. **Comprehensive Code Review**
   ```bash
   Skill(superpowers:receiving-code-review)
   ```
   - Analyzes all changed files
   - Checks against best practices
   - Identifies potential issues
   - Suggests improvements

4. **Quality Classification**
   - Security vulnerabilities
   - Performance issues
   - Maintainability concerns
   - Test coverage gaps

### Phase 3: Synthesis & Validation

5. **Scope-Aware Triage**
   Each finding evaluated against scope:

   | Finding Type | In Scope? | Action |
   |--------------|-----------|--------|
   | Bug introduced by change | Always | Block |
   | Missing requirement | Yes | Block |
   | Security issue | Always | Block |
   | Refactoring suggestion | No | Backlog |
   | Style improvement | No | Ignore |
   | Performance optimization | No | Backlog |

6. **Generate Structured Report**
   Combines scope validation with code analysis

## Options

- `--scope-mode`: Set strictness level (default: standard)
  - `strict`: All requirements must be complete
  - `standard`: Core requirements required
  - `flexible`: MVP implementation acceptable
- `--auto-approve-safe-prs`: Auto-approve PRs with no issues
- `--create-backlog-issues`: Create GitHub issues for improvements
- `pr-number`/`pr-url`: Target specific PR (default: current branch)

## Review Classification Framework

### Blocking Issues
Must fix before merge:
- Bugs introduced by this change
- Security vulnerabilities
- Breaking changes without migration
- Missing core requirements
- Test failures in new code

### In-Scope Issues
Should address in this PR:
- Incomplete requirement implementation
- Missing error handling specified in requirements
- Performance issues affecting feature
- Edge cases not covered

### Suggestions (Author's Discretion)
Nice improvements:
- Better variable names
- Minor optimizations
- Additional test cases
- Documentation improvements

### Backlog Items
Create GitHub issues:
- Refactoring opportunities
- "While we're here" improvements
- Feature expansions
- Technical debt in adjacent code

## Enhanced Example

```bash
/pr-review-wrapper 42 --scope-mode standard --create-backlog-issues
```

### Sample Output

```markdown
## PR #42: Add user authentication system

### Scope Compliance Analysis
**Source:** docs/plans/2025-12-01-auth-design.md

**Requirements:**
1. [x] JWT token generation - Implemented in auth.py
2. [x] Password hashing with bcrypt - Implemented in utils.py
3. [x] Login endpoint - Implemented in routes/auth.py
4. [x] Token validation middleware - Partially implemented
5. [ ] Password reset flow - **Missing**

### Superpowers Code Analysis
**Files Changed:** 12 files, +542/-89 lines
**Coverage:** New code 85% covered

### Blocking Issues (2)
> Must fix before merge

1. **[B1] Missing token validation**
   - Location: middleware/auth.py:45
   - Issue: Always returns True, validation not implemented
   - Superpowers finding: Critical security gap
   - Fix: Implement JWT signature verification

2. **[B2] SQL injection vulnerability**
   - Location: models/user.py:123
   - Issue: String interpolation in query
   - Superpowers finding: High severity security issue
   - Fix: Use parameterized queries

### In-Scope Issues (3)
> Related to requirements

1. **[S1] Password reset flow missing**
   - Requirement: "Users must be able to reset passwords"
   - Status: Not implemented
   - Fix: Add password reset endpoints and email handling

2. **[S2] Error handling incomplete**
   - Location: auth.py:78
   - Issue: No error handling for invalid tokens
   - Fix: Add try/catch with proper error responses

### Suggestions (4)
> Author's discretion

1. **[G1] Add rate limiting to login endpoint**
   - Superpowers recommendation: Prevent brute force attacks
   - Location: routes/auth.py:23

2. **[G2] Consider using refresh tokens**
   - Superpowers finding: Better security pattern
   - Location: auth.py:45

### Backlog → GitHub Issues Created (5)
> Out of scope for this PR

1. #247 - Add two-factor authentication support
2. #248 - Implement user roles and permissions
3. #249 - Add audit logging for authentication events
4. #250 - Social login integration (OAuth2)
5. #251 - Session management dashboard

### Recommendation
**REQUEST CHANGES**
Address blocking issues B1-B2 and in-scope issue S1 before merge.
Implementation looks promising once core requirements are complete.
```

## Scope Mode Details

### Strict Mode
All requirements must be fully implemented:
- No missing features
- Complete error handling
- Full test coverage
- Documentation complete

### Standard Mode (Default)
Core functionality required:
- Main features working
- Basic error handling
- Critical tests passing
- Essential documentation

### Flexible Mode
MVP acceptable:
- Basic functionality works
- Critical path tested
- Security requirements met
- Future work tracked

## Advanced Features

### 1. Automated Issue Creation
```bash
# For each backlog item:
gh issue create \
  --title "[Enhancement] <title>" \
  --body="## Context
Identified during PR #<number> review

## Details
<finding details>

## Suggested Approach
<implementation notes>

## Priority
Medium - Improvement opportunity

---
*Auto-created by pr-review-wrapper*" \
  --label="enhancement,backlog"
```

### 2. Quality Metrics Integration
```markdown
### Quality Metrics
- **Code Coverage**: 85% (target: 80%) ✅
- **Complexity**: Low (new functions < 10 cyclomatic) ✅
- **Duplication**: 2% (target: <5%) ✅
- **Security**: 0 high-severity issues ✅
```

### 3. Reviewer Guidance
```markdown
### Review Focus Areas
Based on scope and analysis:
1. Verify JWT implementation (security)
2. Check password hashing (security)
3. Validate error handling (robustness)
4. Review test coverage (quality)
```

## Integration Benefits

### For Reviewers
- Clear understanding of PR scope
- Prioritized feedback (blocking vs suggestions)
- Context-aware recommendations
- Reduced review time through automation

### For Authors
- Specific, actionable feedback
- Clear path to approval
- Backlog items automatically created
- Quality metrics provided

### For Teams
- Consistent review standards
- Scope discipline enforced
- Technical debt tracked
- Quality gates automated

## Error Handling

### No Scope Artifacts Found
```markdown
Warning: No plan/spec found for this PR
Using PR description as scope baseline
Recommendation: Create plan.md for future PRs
```

### Analysis Failures
```bash
Error: Superpowers code review failed
Falling back to manual review mode
```

### GitHub API Issues
```bash
Warning: Cannot create backlog issues (rate limit)
Please create manually from backlog section
```

## Configuration

```yaml
pr_review_wrapper:
  default_scope_mode: "standard"
  auto_approve_threshold: 0  # No blocking issues
  create_backlog_issues: true
  require_test_coverage: true
  min_coverage_percent: 80

  quality_gates:
    max_complexity: 10
    max_duplication: 5
    require_documentation: true

  backlog_settings:
    auto_create: true
    default_priority: "medium"
    assign_to_author: false
```

## Best Practices

### Before Review
1. Ensure PR description is clear
2. Verify CI pipeline passed
3. Check for scope artifacts
4. Confirm tests are running

### During Review
1. Establish scope baseline first
2. Classify findings consistently
3. Provide actionable feedback
4. Create issues for improvements

### After Review
1. Verify all issues are tracked
2. Check recommendation accuracy
3. Update scope artifacts if needed
4. Follow up on backlog items

## Migration from /pr-review

```bash
# Original command (still supported)
/pr-review

# Enhanced wrapper
/pr-review-wrapper

# With options
/pr-review-wrapper --scope-mode strict --create-backlog-issues
```

## Notes

- Maintains full backward compatibility with /pr-review
- Requires superpowers plugin for enhanced analysis
- GitHub CLI needed for issue creation
- All Sanctum scope validation preserved
- Adds comprehensive code quality checks