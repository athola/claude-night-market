---
name: quota-management
description: |
  Quota tracking, threshold monitoring, and graceful degradation for rate-limited API services.

  Triggers: quota, rate limiting, usage limits, thresholds
  Use when: integrating rate-limited services or tracking API usage
category: infrastructure
tags: [quota, rate-limiting, resource-management, cost-tracking, thresholds]
dependencies: []
tools: [quota-tracker]
provides:
  infrastructure: [quota-tracking, threshold-monitoring, usage-estimation]
  patterns: [graceful-degradation, quota-enforcement, cost-optimization]
usage_patterns:
  - service-integration
  - rate-limit-management
  - cost-tracking
  - resource-monitoring
complexity: intermediate
estimated_tokens: 500
progressive_loading: true
modules:
  - modules/threshold-strategies.md
  - modules/estimation-patterns.md
---

# Quota Management

## Overview

Universal patterns for tracking and enforcing resource quotas across any rate-limited service. This skill provides the foundational infrastructure that other plugins can use for consistent quota handling.

## When to Use

- Building integrations with rate-limited APIs
- Need to track usage across sessions
- Want graceful degradation when limits approached
- Require cost estimation before operations

## Core Concepts

### Quota Thresholds

Three-tier threshold system for proactive management:

| Level | Usage | Action |
|-------|-------|--------|
| **Healthy** | <80% | Proceed normally |
| **Warning** | 80-95% | Alert, consider batching |
| **Critical** | >95% | Defer non-urgent, use fallbacks |

### Quota Types

```python
@dataclass
class QuotaConfig:
    requests_per_minute: int = 60
    requests_per_day: int = 1000
    tokens_per_minute: int = 100000
    tokens_per_day: int = 1000000
```

## Quick Start

### Check Quota Status
```python
from leyline.quota_tracker import QuotaTracker

tracker = QuotaTracker(service="my-service")
status, warnings = tracker.get_quota_status()

if status == "CRITICAL":
    # Defer or use fallback
    pass
```

### Record Usage
```python
tracker.record_request(
    tokens=estimated_tokens,
    success=True,
    duration=elapsed_seconds
)
```

### Estimate Before Execution
```python
can_proceed, issues = tracker.can_handle_task(estimated_tokens)
if not can_proceed:
    print(f"Quota issues: {issues}")
```

## Integration Pattern

Other plugins reference this skill:

```yaml
# In your skill's frontmatter
dependencies: [leyline:quota-management]
```

Then use the shared patterns:
1. Initialize tracker for your service
2. Check quota before operations
3. Record usage after operations
4. Handle threshold warnings gracefully

## Detailed Resources

- **Threshold Strategies**: See `modules/threshold-strategies.md` for degradation patterns
- **Estimation Patterns**: See `modules/estimation-patterns.md` for token/cost estimation

## Exit Criteria

- Quota status checked before operation
- Usage recorded after operation
- Threshold warnings handled appropriately
