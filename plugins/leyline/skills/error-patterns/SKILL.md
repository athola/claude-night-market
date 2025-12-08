---
name: error-patterns
description: Standardized error handling patterns for robust plugin development. Provides error classification, recovery strategies, and logging patterns.
category: infrastructure
tags: [errors, error-handling, recovery, resilience, debugging]
dependencies: [usage-logging]
provides:
  infrastructure: [error-handling, error-classification, recovery]
  patterns: [graceful-degradation, error-logging, debugging]
usage_patterns:
  - error-handling
  - resilience-patterns
  - debugging-workflows
complexity: beginner
estimated_tokens: 450
progressive_loading: true
modules:
  - modules/classification.md
  - modules/recovery-strategies.md
---

# Error Patterns

## Overview

Standardized error handling patterns for consistent, robust behavior across plugins. Provides error classification, recovery strategies, and debugging workflows.

## When to Use

- Building resilient integrations
- Need consistent error handling
- Want graceful degradation
- Debugging production issues

## Error Classification

### By Severity

| Level | Action | Example |
|-------|--------|---------|
| **Critical** | Halt, alert | Auth failure, service down |
| **Error** | Retry or fallback | Rate limit, timeout |
| **Warning** | Log, continue | Partial results, deprecation |
| **Info** | Log only | Non-blocking issues |

### By Recoverability

```python
class ErrorCategory(Enum):
    TRANSIENT = "transient"      # Retry likely to succeed
    PERMANENT = "permanent"       # Retry won't help
    CONFIGURATION = "config"      # User action needed
    RESOURCE = "resource"         # Quota/limit issue
```

## Quick Start

### Standard Error Handler
```python
from leyline.error_patterns import handle_error, ErrorCategory

try:
    result = service.execute(prompt)
except RateLimitError as e:
    return handle_error(e, ErrorCategory.RESOURCE, {
        "retry_after": e.retry_after,
        "service": "gemini"
    })
except AuthError as e:
    return handle_error(e, ErrorCategory.CONFIGURATION, {
        "action": "Run 'gemini auth login'"
    })
```

### Error Result
```python
@dataclass
class ErrorResult:
    category: ErrorCategory
    message: str
    recoverable: bool
    suggested_action: str
    metadata: dict
```

## Common Patterns

### Authentication Errors (401/403)
- Verify credentials exist
- Check token expiration
- Validate permissions/scopes
- Suggest re-authentication

### Rate Limit Errors (429)
- Extract retry-after header
- Log for quota tracking
- Implement backoff
- Consider alternative service

### Timeout Errors
- Increase timeout for retries
- Break into smaller requests
- Use async patterns
- Consider different model

### Context Too Large (400)
- Estimate tokens before request
- Split into multiple requests
- Reduce input content
- Use larger context model

## Integration Pattern

```yaml
# In your skill's frontmatter
dependencies: [leyline:error-patterns]
```

## Detailed Resources

- **Classification**: See `modules/classification.md` for error taxonomy
- **Recovery**: See `modules/recovery-strategies.md` for handling patterns

## Exit Criteria

- Error classified correctly
- Appropriate recovery attempted
- User-actionable message provided
- Error logged for debugging
