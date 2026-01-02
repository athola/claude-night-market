# Leyline

Infrastructure and pipeline building blocks plugin for Claude Code.

## Overview

Leyline provides shared utilities, patterns, and services that other plugins can use to build consistent functionality.

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
| `error-patterns` | Standardized error handling | Building error recovery |
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

1. **Zero coupling**: Patterns are reference-only, no hard dependencies.
2. **Progressive adoption**: Use what you need.
3. **Consistent interfaces**: Same patterns across all utilities.
4. **Plugin-agnostic**: Works with any plugin architecture.

## Related Plugins

- **abstract**: Meta-skills for Claude (evaluation, modular design).
- **conjure**: LLM delegation (uses leyline for quota/logging).
- **conserve**: Context optimization (can use leyline metrics).

## Plugin Metadata Best Practices (Claude Code 2.0.73+)

Claude Code 2.0.73+ adds search filtering to the plugin discover screen. Users can filter by name, description, and marketplace tags.

### Optimizing for Discoverability

**Plugin Description Guidelines**:

1. **Lead with purpose**: Start description with what the plugin does
   ```json
   // Good
   "description": "Infrastructure and pipeline building blocks for shared utilities and services"

   // Avoid
   "description": "A plugin for stuff"
   ```

2. **Include searchable keywords**: Add relevant terms users might search for
   ```json
   "description": "Infrastructure patterns: quota management, service registry, error handling, authentication flows, circuit breakers"
   ```

3. **Be specific**: Mention concrete capabilities
   ```json
   // Good
   "description": "Resource tracking (quotas, usage, metrics), service integration, pipeline patterns (retry, circuit breakers)"

   // Avoid
   "description": "Helps with infrastructure"
   ```

4. **Use domain terminology**: Include technical terms your audience knows
   ```json
   "description": "Cross-plugin utilities: base classes, common interfaces, standardized error patterns, auth flows"
   ```

### Example: Well-Optimized Plugin Metadata

```json
{
  "name": "leyline",
  "version": "1.1.0",
  "description": "Infrastructure and pipeline patterns for Claude Code plugins: quota management, service registry, error handling, authentication flows, circuit breakers, shared utilities",
  "keywords": [
    "infrastructure",
    "utilities",
    "patterns",
    "services",
    "error-handling",
    "authentication",
    "quotas",
    "pipeline"
  ],
  "category": "infrastructure"
}
```

### Testing Discoverability

Ask yourself: **"Would users find this plugin when searching for..."**
- Common use cases? ✓ "quota management"
- Problem domains? ✓ "error handling"
- Technical terms? ✓ "circuit breaker"
- Related concepts? ✓ "service integration"

### Validation Checklist

When publishing or updating plugins:

- [ ] Description starts with purpose/benefit
- [ ] Contains 3-5 searchable keywords
- [ ] Mentions specific capabilities
- [ ] Uses domain-appropriate terminology
- [ ] Length: 50-150 characters (readable at a glance)
- [ ] Keywords array includes search terms
- [ ] Category accurately represents plugin function

See `plugins/abstract/docs/claude-code-compatibility.md` for compatibility details.
