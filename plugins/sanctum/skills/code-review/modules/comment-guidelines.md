# Code Comment Guidelines

Research-based guidelines for code commenting in reviews.

## Status: Draft

These guidelines are under discussion. See [Issue #66](https://github.com/athola/claude-night-market/issues/66) for context.

## Core Principle

**Explain "why", not "what"**. Code shows what happens; comments explain intent.

## When Comments Add Value

### COMMENT These

| Situation | Example | Rationale |
|-----------|---------|-----------|
| **Business logic decisions** | Why this threshold? Why this algorithm? | Intent not obvious from code |
| **Edge case handling** | `# Empty string = use default, None = skip` | Behavior distinction unclear |
| **Non-obvious constraints** | `# Max 3 retries due to Lambda timeout` | External constraints |
| **Complex algorithms** | Step-by-step explanation | Aids future maintenance |
| **Workarounds** | `# Workaround for library bug #1234` | Prevents "cleanup" that breaks code |
| **Public API contracts** | Docstrings with params, returns, raises | Consumer documentation |

### DO NOT Comment These

| Situation | Example | Why Avoid |
|-----------|---------|-----------|
| **Obvious code** | `i += 1  # Increment i` | Adds noise, no value |
| **Self-documenting names** | `user_count = len(users)  # Count users` | Redundant |
| **Implementation details** | `# Use a for loop` | Code already shows this |
| **Changelog in code** | `# Changed 2025-01-01 by John` | Use git history |

## Good vs Bad Examples

### Python

```python
# Good: Explains WHY
def retry_with_backoff(max_attempts=3):
    """Retry with exponential backoff for transient API failures.

    AWS Lambda has 15-minute timeout. With 1s/2s/4s backoff,
    max_attempts=3 keeps total time under timeout.
    """

# Bad: Explains WHAT (code already does this)
def retry_with_backoff(max_attempts=3):
    """Retries a function with exponential backoff."""
```

```python
# Good: Documents edge case distinction
if user_input == "":  # Empty string = use default, None = skip entirely
    return DEFAULT_VALUE

# Bad: States the obvious
if user_input == "":  # Check if user_input is empty string
    return DEFAULT_VALUE
```

### Rust

```rust
// Good: Explains non-obvious constraint
const MAX_CONNECTIONS: usize = 10;  // Postgres default; increase requires server config

// Bad: Obvious from code
const MAX_CONNECTIONS: usize = 10;  // Maximum number of connections
```

## Comment Density Guidelines

### Target Ratio

| Code Type | Suggested Ratio | Notes |
|-----------|-----------------|-------|
| Library/API | 1 docstring per public item | Consumers need documentation |
| Complex algorithm | 1 comment per logical section | Aids comprehension |
| Business logic | Comments on non-obvious decisions | Preserve institutional knowledge |
| Simple CRUD | Minimal to none | Self-explanatory |

### Red Flags

- **Over-commented**: Every line has a comment
- **Under-commented**: Complex algorithm with zero explanation
- **Stale comments**: Comment contradicts code behavior
- **Comment instead of refactor**: Long comment explaining confusing code

## Review Checklist

When reviewing code, check comments for:

- [ ] **Value**: Does this comment add information not in the code?
- [ ] **Accuracy**: Does the comment match current behavior?
- [ ] **Necessity**: Would better naming eliminate need for comment?
- [ ] **Completeness**: Are complex sections explained?

## Anti-Patterns to Flag

### Commented-Out Code

```python
# Don't leave this in PRs:
# old_implementation()
# def deprecated_func(): ...
```

Action: Remove or move to git history.

### TODO Without Context

```python
# Bad
# TODO: fix this

# Good
# TODO(issue-123): Handle timeout when API returns 504
```

### Stale Comments

```python
# Comment says one thing, code does another
# Returns user count
def get_users():
    return list(users)  # Actually returns users, not count
```

## References

- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) - "Progressive disclosure over exhaustive comments"
- [Level Up Coding](https://levelup.gitconnected.com/demystifying-software-development-principles) - "Clear, concise code complemented by effective documentation"
- Issue #66: Discussion thread
