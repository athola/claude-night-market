# Progressive Loading Skill

Standardized patterns for context-aware, progressive module loading in Claude Code skills.

## Overview

This skill provides reusable patterns for building skills that:
- Load modules dynamically based on context
- Optimize token usage through selective loading
- Maintain MECW compliance in long sessions
- Support hub-and-spoke architecture

## Core Principle

**Start minimal, expand intelligently, monitor continuously.**

## Files

- `SKILL.md` - Hub with overview, architecture, integration patterns
- `modules/selection-strategies.md` - Strategies for choosing which modules to load
- `modules/loading-patterns.md` - Implementation patterns for module lifecycle

## Quick Example

```markdown
# My Skill

## Progressive Loading

**Git Workflow**: Load `modules/git-patterns.md` for git tasks
**Python Analysis**: Load `modules/python-patterns.md` for Python code

**Always Available**: Core concepts, exit criteria
```

## Integration

Reference this skill in your plugin's skill frontmatter:

```yaml
dependencies: [leyline:progressive-loading, leyline:mecw-patterns]
progressive_loading: true
```

## Selection Strategies

1. **Intent-based** - Load based on user goals
2. **Artifact-based** - Load based on detected files/systems
3. **Budget-aware** - Load within token budget
4. **Progressive** - Load in tiers (core → common → advanced)
5. **Mutually-exclusive** - Load one path from alternatives

## Loading Patterns

1. **Conditional includes** - Hub references modules by context
2. **Lazy loading** - Load on first use
3. **Tiered disclosure** - Progressive complexity levels
4. **Context switching** - Change modules mid-session
5. **Preemptive unloading** - Remove modules under pressure

## Use Cases

- Multi-domain skills (imbue:catchup, sanctum:workspace-tools)
- Context-heavy analysis workflows
- Shared plugin infrastructure

## Token Budget

- SKILL.md: ~800 tokens (141 lines)
- selection-strategies.md: ~2500 tokens
- loading-patterns.md: ~3200 tokens

Load modules based on actual needs to stay within MECW constraints.
