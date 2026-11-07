---
name: usage-logging
description: Session-aware JSONL usage logging for audit trails, usage analytics, and per-call cost tracking
parent_skill: leyline:service-registry
category: infrastructure
tags: [logging, usage, audit, metrics, sessions, analytics, cost-tracking]
estimated_tokens: 450
---

# Usage Logging

## Overview

Records individual call costs and usage events. For aggregate budget
enforcement, see `modules/quota-management.md`.

Session-aware logging infrastructure for tracking operations across plugins.
Provides structured JSONL logging with automatic session management for
audit trails and analytics.

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
**Verification:** Run the command with `--help` flag to verify availability.

## Quick Start

### Initialize Logger
```python
from leyline.usage_logger import UsageEvent, UsageLogger

logger = UsageLogger(service="my-service")
```
**Verification:** `python -m leyline.usage_logger --help` prints the
query options.

### Log Operations
```python
logger.log_usage(
    UsageEvent(
        "analyze_files",
        tokens=5000,
        success=True,
        duration=2.5,
        metadata={"files": 10},
    )
)
```
**Verification:** `plugins/leyline/tests/unit/test_usage_logger_quick_start.py`
runs this call and reads it back.

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
**Verification:** Run the command with `--help` flag to verify availability.

## Integration Pattern

```yaml
# In your skill's frontmatter
dependencies: [leyline:service-registry]
```
**Verification:** Run the command with `--help` flag to verify availability.

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
**Verification:** Run the command with `--help` flag to verify availability.

## Detailed Resources

- **Session Patterns**: See `modules/session-patterns.md` for session management
- **Log Formats**: See `modules/log-formats.md` for structured formats

## Exit Criteria

- [ ] Operation logged with all required fields
- [ ] Session tracked for grouping
- [ ] Logs queryable for analytics
