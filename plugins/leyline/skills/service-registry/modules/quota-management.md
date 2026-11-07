---
name: quota-management
description: Quota tracking, threshold tiers, and graceful degradation for rate-limited services
parent_skill: leyline:service-registry
category: infrastructure
tags: [quota, rate-limiting, resource-management, thresholds]
estimated_tokens: 500
---

# Quota Management

## Overview

Tracks cumulative token budgets and enforces limits. For per-call logging,
see `modules/usage-logging.md`.

Patterns for tracking and enforcing resource quotas across rate-limited
services. This module describes the infrastructure that other plugins use for
consistent quota handling.

## Core Concepts

### Quota Thresholds

Three-tier threshold system for proactive management:

| Level | Usage | Action |
|-------|-------|--------|
| **Healthy** | <80% | Proceed normally |
| **Warning** | 80-95% | Alert, consider batching |
| **Critical** | >95% | Defer non-urgent, use secondary services |

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

if status == "critical":
    # Defer or use secondary service
    pass
```

### Record Usage
```python
tracker.record_request(tokens=estimated_tokens, success=True, duration=elapsed_seconds)
```

### Estimate Before Execution
```python
can_proceed, issues = tracker.can_handle_task(estimated_tokens)
if not can_proceed:
    print(f"Quota issues: {issues}")
```

## Integration Pattern

Other plugins reference the parent skill:

```yaml
# In your skill's frontmatter
dependencies: [leyline:service-registry]
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

- [ ] Quota status checked before operation
- [ ] Usage recorded after operation
- [ ] Threshold warnings handled appropriately
