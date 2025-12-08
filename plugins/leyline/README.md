# Leyline

> *Like ancient ley lines connecting sacred sites, leyline provides the foundational patterns that connect and power plugin ecosystems.*

## Overview

Leyline is the infrastructure and pipeline building blocks plugin for Claude Code. It provides shared utilities, patterns, and services that other plugins can leverage to build robust, consistent functionality.

## Philosophy

**Abstract** handles meta-concerns about Claude itself (skill evaluation, modular design patterns, plugin validation).

**Leyline** handles infrastructure concerns that plugins share:
- Resource tracking (quotas, usage, metrics)
- Service integration (authentication, execution, logging)
- Pipeline patterns (error handling, retry logic, circuit breakers)
- Cross-plugin utilities (shared base classes, common interfaces)

## Skills

| Skill | Purpose | Use When |
|-------|---------|----------|
| `quota-management` | Track and enforce resource limits | Building services with rate limits |
| `usage-logging` | Session-aware usage tracking | Need audit trails or cost tracking |
| `service-registry` | Manage external service connections | Integrating multiple services |
| `error-patterns` | Standardized error handling | Building robust error recovery |
| `authentication-patterns` | Common auth flows | Connecting to external APIs |

## Integration

Other plugins can reference leyline patterns:

```yaml
# In your skill's frontmatter
dependencies: [leyline:quota-management]
references:
  - leyline/skills/error-patterns/modules/recovery-strategies.md
```

## Scripts

Reusable Python utilities for common infrastructure tasks:

```bash
# Quota tracking
python -m leyline.quota_tracker --service myservice --check

# Usage logging
python -m leyline.usage_logger --log "operation" --tokens 1000

# Service health check
python -m leyline.service_registry --verify myservice
```

## Design Principles

1. **Zero coupling** - Patterns are reference-only, no hard dependencies
2. **Progressive adoption** - Use what you need, ignore the rest
3. **Consistent interfaces** - Same patterns across all utilities
4. **Plugin-agnostic** - Works with any plugin architecture

## Related Plugins

- **abstract** - Meta-skills for Claude (evaluation, modular design)
- **conjure** - LLM delegation (uses leyline for quota/logging)
- **conservation** - Context optimization (can use leyline metrics)
