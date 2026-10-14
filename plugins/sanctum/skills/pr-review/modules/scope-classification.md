# Scope Classification Framework

Every finding must be classified:

| Category | Definition | Action |
|----------|------------|--------|
| **BLOCKING** | Bug, security issue, or regression introduced by this change | Must fix before merge |
| **IN-SCOPE** | Issue directly related to stated requirements | Should address in this PR |
| **SUGGESTION** | Improvement within changed code, not required | Author decides |
| **BACKLOG** | Good idea but outside PR scope | Create GitHub issue |
| **IGNORE** | Nitpick, style preference, or not worth tracking | Skip entirely |

### Classification Examples

**BLOCKING:**
- Null pointer exception in new code path
- SQL injection in new endpoint
- Breaking change to public API without migration
- Test that was passing now fails

**IN-SCOPE:**
- Missing error handling specified in requirements
- Feature doesn't match spec behavior
- Incomplete implementation of planned functionality

**SUGGESTION:**
- Better variable name in changed function
- Slightly more efficient algorithm
- Additional edge case test

**BACKLOG:**
- Refactoring opportunity in adjacent code
- "While we're here" improvements
- Technical debt in files touched but not changed
- Features sparked by seeing the code

**IGNORE:**
- Personal style preferences
- Theoretical improvements with no practical impact
- Premature optimization suggestions
