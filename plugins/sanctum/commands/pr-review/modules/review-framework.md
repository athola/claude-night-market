# PR Review: Classification Framework

Review classification system and scope mode details.

> **See Also**: [Main Command](../pr-review.md) | [Workflow](review-workflow.md) | [Configuration](review-configuration.md)

## Review Classification Framework

### Blocking Issues
Must fix before merge:
- **Version mismatches** (marketplace vs actual, CHANGELOG missing, etc.)
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
Create GitHub issues (primary storage):
- Refactoring opportunities
- "While we're here" improvements
- Feature expansions
- Technical debt in adjacent code

**Important**: GitHub issues are the source of truth for backlog items. Reference existing `docs/backlog/*.md` files for context (e.g., `docs/backlog/queue.md`, `docs/backlog/technical-debt.md`) to avoid duplicates.

## Enhanced Example

```bash
/pr-review 42 --scope-mode standard --create-backlog-issues
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
