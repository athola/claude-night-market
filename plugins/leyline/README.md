# Leyline

Infrastructure and pipeline building blocks for Claude Code plugins.

## Overview

Leyline provides shared utilities, patterns, and services to support consistent plugin functionality.

## Philosophy

Leyline delivers the foundational building blocks for plugin functionality, handling resource tracking, service integration, and pipeline patterns like error handling and circuit breakers. Unlike the Abstract plugin, which manages meta-concerns such as skill evaluation, Leyline concentrates on practical implementation and ensuring interoperability across the system.

## Skills

| Skill | Purpose | Use When |
|-------|---------|----------|
| `quota-management` | Track and enforce resource limits. | Building services with rate limits. |
| `usage-logging` | Session-aware usage tracking. | Need audit trails or cost tracking. |
| `service-registry` | Manage external service connections. | Integrating multiple services. |
| `error-patterns` | Standardized error handling. | Building error recovery. |
| `authentication-patterns` | Common auth flows. | Connecting to external APIs. |

## Integration

Other plugins can reference leyline patterns:

```yaml
# In your skill's frontmatter
dependencies: [leyline:quota-management]
references:
  - leyline/skills/error-patterns/modules/recovery-strategies.md
```

## Scripts

Python utilities for infrastructure tasks:

```bash
# Quota tracking
python -m leyline.quota_tracker --service myservice --check

# Usage logging
python -m leyline.usage_logger --log "operation" --tokens 1000

# Service health check
python -m leyline.service_registry --verify myservice
```

## Optional Dependencies

| Package | Purpose | Fallback |
|---------|---------|----------|
| tiktoken | Accurate token estimation | Heuristic estimation (~4 chars/token) |

Leyline is fully functional without tiktoken. Install with full features:
```bash
uv sync --extra tokens
```

## Design Principles

The plugin adheres to principles of loose coupling, ensuring patterns remain reference-only to support progressive adoption. It enforces consistent interfaces across all utilities and maintains a plugin-agnostic design, guaranteeing compatibility with any plugin architecture.

## Related Plugins

- **abstract**: Meta-skills for evaluation and design.
- **conjure**: LLM delegation (uses leyline for quota/logging).
- **conserve**: Context optimization.

## Plugin Metadata Best Practices (Claude Code 2.0.73+)

Claude Code 2.0.73+ supports search filtering in the plugin discovery screen.

### Optimizing Discoverability

**Plugin Description Guidelines**:

1. **Focus on purpose**: Start with a direct statement of functionality.
   - Example: "Infrastructure and pipeline building blocks for shared utilities."
2. **Include keywords**: Add terms users likely search for, such as "quota management" or "error handling".
3. **Be specific**: Mention concrete capabilities like "circuit breakers" or "auth flows".
4. **Use domain terminology**: Include technical terms relevant to the audience.

### Example: Optimized Plugin Metadata

```json
{
  "name": "leyline",
  "version": "1.1.0",
  "description": "Infrastructure patterns for Claude Code plugins: quota management, service registry, error handling, authentication flows, circuit breakers, shared utilities",
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

### Validation Checklist

- [ ] Description starts with purpose.
- [ ] Contains 3-5 searchable keywords.
- [ ] Mentions specific capabilities.
- [ ] Uses domain-appropriate terminology.
- [ ] Length: 50-150 characters.
- [ ] Keywords array includes search terms.
- [ ] Category accurately represents plugin function.

See `plugins/abstract/docs/claude-code-compatibility.md` for compatibility details.
