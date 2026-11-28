# Scope Classification Framework

Every finding must be classified:

| Category | Definition | Action |
|----------|------------|--------|
| **BLOCKING** | Bug, security issue, or regression introduced by this change | Must fix before merge |
| **IN-SCOPE** | Issue directly related to stated requirements | Should address in this PR |
| **SUGGESTION** | Improvement within changed code, not required | Author decides |
| **BACKLOG** | Good idea but outside PR scope | Create GitHub issue |
| **REVISIT** | Disagreement with a decision settled before the PR (Q1 or Q2) | Ask, then comment on the record (issue or discussion) or list it in the report (file record) |
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

**REVISIT:**
- "This should have been an event, not a poll," when the ADR chose polling
- "Is this feature needed?" when the linked issue accepted it

A REVISIT does not block the merge. When the PR surfaces new facts the
decision did not have, such as a constraint the design missed, the
finding is BLOCKING instead, with that fact as its evidence. Under
`--hold-insights`, REVISIT findings are held in chat with the other
direction findings. Routing: `review-questions.md`.

**IGNORE:**
- Personal style preferences
- Theoretical improvements with no practical impact
- Premature optimization suggestions
