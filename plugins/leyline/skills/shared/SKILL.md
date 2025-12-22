---
name: shared
description: |
  Foundational infrastructure patterns shared across all leyline skills.

  Triggers: leyline patterns, shared infrastructure, python imports, config patterns,
  leyline foundation, cross-skill patterns

  Use when: other leyline skills need common patterns, creating new infrastructure
  skills, ensuring consistency across leyline plugin

  DO NOT use directly: this skill is infrastructure for other leyline skills.

  This skill provides shared patterns consumed by other leyline skills.
category: infrastructure
tags: [shared, patterns, infrastructure, foundation]
provides:
  infrastructure: [python-imports, error-handling, config-patterns]
reusable_by: [all leyline skills, conservation, conjure, abstract]
estimated_tokens: 150
---

# Shared Infrastructure for Leyline

## Purpose

Foundational patterns for the leyline infrastructure layer. These patterns are used across all leyline skills and by plugins that depend on leyline.

## Modules

### Python Import Patterns
The `modules/python-imports.md` module documents how to import leyline utilities:
- Standard import paths
- Fallback patterns for different contexts
- Type hints and protocols

### Error Handling Patterns
The `modules/error-handling.md` module standardizes error handling:
- Error classification (retryable, fatal, user-facing)
- Recovery strategies
- Logging conventions

### Config Patterns
The `modules/config-patterns.md` module provides configuration standards:
- Environment variable naming
- YAML config file structure
- Default value handling

## Leyline Architecture

```
leyline/skills/
├── shared/              # This skill - foundational patterns
├── mecw-patterns/       # Context window management
├── progressive-loading/ # On-demand content loading
├── evaluation-framework/# Scoring and decision thresholds
├── storage-templates/   # Knowledge storage formats
├── pytest-config/       # Testing infrastructure
├── testing-quality-standards/  # Test quality criteria
├── quota-management/    # Service quota tracking
├── usage-logging/       # Audit trail patterns
├── service-registry/    # Service configuration
├── error-patterns/      # Error handling
└── authentication-patterns/  # Auth verification
```

## Integration Notes

Leyline provides the foundation layer. Other plugins reference leyline skills:
- `conservation` uses `mecw-patterns`, `progressive-loading`
- `conjure` uses `quota-management`, `usage-logging`, `service-registry`
- `memory-palace` uses `evaluation-framework`, `storage-templates`
