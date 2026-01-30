---
name: shared
description: |

Triggers: infrastructure, foundation, shared, patterns
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
reusable_by: [all leyline skills, conserve, conjure, abstract]
estimated_tokens: 150
version: 1.3.7
---

# Shared Infrastructure for Leyline

## Purpose

Foundational patterns for the leyline infrastructure layer. These patterns are used across all leyline skills and by plugins that depend on leyline.

## Core Patterns

### Python Import Patterns
Standard import paths for leyline utilities:
- `from leyline.skills import <skill_name>`
- Secondary patterns with type hints and protocols

### Error Handling Patterns
Error handling standards:
- Error classification (retryable, fatal, user-facing)
- Recovery strategies and logging conventions
- See `error-patterns` skill for detailed patterns

### Config Patterns
Configuration standards:
- Environment variable naming (`LEYLINE_*`)
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
**Verification:** Run `pytest -v` to verify tests pass.

## Integration Notes

Leyline provides the foundation layer. Other plugins reference leyline skills:
- `conservation` uses `mecw-patterns`, `progressive-loading`
- `conjure` uses `quota-management`, `usage-logging`, `service-registry`
- `memory-palace` uses `evaluation-framework`, `storage-templates`
## Troubleshooting

### Common Issues

**Command not found**
Ensure all dependencies are installed and in PATH

**Permission errors**
Check file permissions and run with appropriate privileges

**Unexpected behavior**
Enable verbose logging with `--verbose` flag
