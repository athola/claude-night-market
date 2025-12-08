---
name: usage-logging
description: Session-aware usage logging infrastructure for audit trails, cost tracking, and analytics. Provides structured logging with JSONL format and session management.
category: infrastructure
tags: [logging, usage, audit, metrics, sessions, analytics]
dependencies: []
tools: [usage-logger]
provides:
  infrastructure: [usage-logging, session-management, audit-trails]
  patterns: [structured-logging, metrics-collection, cost-tracking]
usage_patterns:
  - audit-logging
  - cost-tracking
  - usage-analytics
  - session-management
complexity: beginner
estimated_tokens: 450
progressive_loading: true
modules:
  - modules/session-patterns.md
  - modules/log-formats.md
---

# Usage Logging

## Overview

Session-aware logging infrastructure for tracking operations across plugins. Provides structured JSONL logging with automatic session management for audit trails and analytics.

## When to Use

- Need audit trails for operations
- Tracking costs across sessions
- Building usage analytics
- Debugging with operation history

## Core Concepts

### Session Management

Sessions group related operations:
- Auto-created on first operation
- Timeout after 1 hour of inactivity
- Unique session IDs for tracking

### Log Entry Structure

```json
{
  "timestamp": "2025-12-05T10:30:00Z",
  "session_id": "session_1733394600",
  "service": "my-service",
  "operation": "analyze_files",
  "tokens": 5000,
  "success": true,
  "duration_seconds": 2.5,
  "metadata": {}
}
```

## Quick Start

### Initialize Logger
```python
from leyline.usage_logger import UsageLogger

logger = UsageLogger(service="my-service")
```

### Log Operations
```python
logger.log_usage(
    operation="analyze_files",
    tokens=5000,
    success=True,
    duration=2.5,
    metadata={"files": 10}
)
```

### Query Usage
```python
# Recent operations
recent = logger.get_recent_operations(hours=24)

# Usage summary
summary = logger.get_usage_summary(days=7)
print(f"Total tokens: {summary['total_tokens']}")
print(f"Total cost: ${summary['estimated_cost']:.2f}")

# Recent errors
errors = logger.get_recent_errors(count=10)
```

## Integration Pattern

```yaml
# In your skill's frontmatter
dependencies: [leyline:usage-logging]
```

Standard integration flow:
1. Initialize logger for your service
2. Log operations after completion
3. Query for analytics and debugging

## Log Storage

Default location: `~/.claude/leyline/usage/{service}.jsonl`

```bash
# View recent logs
tail -20 ~/.claude/leyline/usage/my-service.jsonl | jq .

# Query by date
grep "2025-12-05" ~/.claude/leyline/usage/my-service.jsonl
```

## Detailed Resources

- **Session Patterns**: See `modules/session-patterns.md` for session management
- **Log Formats**: See `modules/log-formats.md` for structured formats

## Exit Criteria

- Operation logged with all required fields
- Session tracked for grouping
- Logs queryable for analytics
