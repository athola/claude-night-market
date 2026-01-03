# Cross-Plugin Integration Guide

## Overview

Leyline provides infrastructure building blocks that other plugins can use for consistent, production-grade functionality. This guide explains how to integrate leyline patterns into your plugins.

## Integration Patterns

### 1. Reference Pattern (Recommended)

Reference leyline skills in your skill's frontmatter:

```yaml
---
name: my-skill
dependencies: [leyline:quota-management, leyline:error-patterns]
references:
  - leyline/skills/quota-management/modules/threshold-strategies.md
  - leyline/skills/error-patterns/modules/recovery-strategies.md
---
```

This creates a logical dependency without code coupling. Users loading your skill will know to also load leyline patterns.

### 2. Import Pattern

Import leyline Python utilities directly:

```python
from leyline.quota_tracker import QuotaTracker
from leyline.usage_logger import UsageLogger

tracker = QuotaTracker(service="my-service")
logger = UsageLogger(service="my-service")
```

### 3. Adaptation Pattern

Copy and adapt leyline patterns for service-specific needs:

```python
# Base from leyline
from leyline.quota_tracker import QuotaTracker, QuotaConfig

# Service-specific configuration
MY_SERVICE_QUOTA = QuotaConfig(
    requests_per_minute=100,
    requests_per_day=5000,
    tokens_per_minute=500000,
    tokens_per_day=10000000
)

tracker = QuotaTracker(service="my-service", config=MY_SERVICE_QUOTA)
```

## Plugin Integration Examples

### Conjure → Leyline

Conjure uses leyline for delegation infrastructure:

```yaml
# conjure/skills/delegation-core/SKILL.md
dependencies:
  - leyline:quota-management
  - leyline:usage-logging
  - leyline:service-registry
  - leyline:error-patterns
  - leyline:authentication-patterns
```

### Conservation → Leyline

Conservation can use leyline for context metrics:

```yaml
# conserve/skills/context-optimization/SKILL.md
dependencies:
  - leyline:quota-management  # For context budget tracking
  - leyline:usage-logging     # For optimization metrics
```

### Memory Palace → Leyline

Memory Palace can use leyline for external source handling:

```yaml
# memory-palace/skills/knowledge-intake/SKILL.md
dependencies:
  - leyline:authentication-patterns  # For external API auth
  - leyline:error-patterns           # For fetch failure handling
```

## Shared Data Locations

Leyline stores data in `~/.claude/leyline/`:

```
~/.claude/leyline/
├── quota/
│   ├── {service}_usage.json
│   └── ...
├── usage/
│   ├── {service}.jsonl
│   ├── {service}_session.json
│   └── ...
└── config/
    └── services.yaml
```

## Version Compatibility

When depending on leyline, specify version constraints:

```json
// In your plugin's metadata.json
{
  "dependencies": {
    "leyline": ">=1.0.0"
  }
}
```

## Best Practices

1. **Don't duplicate** - Use leyline patterns instead of reimplementing
2. **Extend, don't modify** - Create service-specific wrappers
3. **Share sessions** - Pass session IDs for cross-service correlation
4. **Log consistently** - Use leyline logging for unified analytics
5. **Handle errors uniformly** - Use leyline error classification
