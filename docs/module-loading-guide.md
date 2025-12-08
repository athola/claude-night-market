# Module Loading Guide

This guide explains how module dependencies, loading patterns, and shared utilities work across the plugin ecosystem.

## Overview

The plugin architecture supports:
- **Skill dependencies** - Skills can depend on other skills
- **Module loading** - Progressive loading of skill modules
- **Shared utilities** - Common functionality across plugins

## Module Frontmatter Format

All module files (`modules/*.md`) must include proper frontmatter:

```yaml
---
parent_skill: plugin:skill-name  # Required: Parent skill that owns this module
name: module-name                # Required: Unique module identifier
description: Brief description    # Required: What this module does
category: category-name          # Required: For organization
tags: [tag1, tag2]              # Required: For discovery

# Optional but recommended
dependencies:
  - shared:utility-name         # Dependencies on other skills
  - plugin:other-skill
load_priority: 1                # Integer 1-5, lower loads first
estimated_tokens: 250           # Approximate token cost
---
```

## Dependency Patterns

### 1. Skill Dependencies

Skills declare dependencies in their frontmatter:

```yaml
# SKILL.md
dependencies:
  - pensive:shared              # Use pensive shared utilities
  - imbue:evidence-logging      # Use imbue evidence logging
```

### 2. Module Dependencies

Modules can have more granular dependencies:

```yaml
# modules/specific-module.md
dependencies:
  - parent-skill:shared          # Use parent skill's shared modules
  - imbue:evidence-logging       # Cross-plugin dependency
  - plugin:other-skill           # Plugin-to-plugin dependency
```

### 3. Load Statements

Skills use `@include` or `Load:` for progressive loading:

```yaml
# In skill content
**For basic analysis**:
- @include modules/analysis-basics.md

**For advanced features**:
- Load: modules/advanced-patterns.md
```

## Shared Utilities

### pensive:shared

Provides common review infrastructure for all pensive review skills:

```
plugins/pensive/skills/shared/
├── SKILL.md                     # Main shared skill
└── modules/
    ├── review-workflow-core.md  # 5-step review workflow
    ├── output-format-templates.md
    └── quality-checklist-patterns.md
```

Used by:
- `pensive:api-review`
- `pensive:bug-review`
- `pensive:architecture-review`
- `pensive:test-review`
- `pensive:rust-review`
- `pensive:makefile-review`
- `pensive:math-review`
- `pensive:unified-review`

### imbue:shared

Provides analysis patterns and evidence logging:

```
plugins/imbue/skills/shared/
├── SKILL.md                     # Main shared skill
└── modules/
    ├── todowrite-patterns.md    # TodoWrite conventions
    ├── evidence-formats.md      # Evidence capture formats
    └── analysis-workflows.md    # Common analysis patterns
```

Used by:
- `pensive:*` skills (via dependencies)
- `sanctum` skills
- Any skill needing reproducible evidence trails

## Loading Patterns

### Progressive Loading

Skills can load modules progressively based on needs:

```yaml
# SKILL.md
progressive_loading: true
modules:
  - basic-analysis.md            # Always loaded
  - advanced-patterns.md         # Loaded on demand
  - expert-audit.md              # Loaded for expert review
```

### Load Priority

Use `load_priority` to control loading order:

- **1-2**: Core/essential modules
- **3**: Standard analysis modules
- **4-5**: Specialized/optional modules

## Best Practices

### 1. Module Design

- **Single responsibility**: Each module focuses on one concern
- **Reusable**: Design modules to be used across skills
- **Documented**: Include clear usage examples
- **Tested**: Include test cases where applicable

### 2. Dependencies

- **Minimal**: Only declare necessary dependencies
- **Explicit**: Use full `plugin:skill` format
- **Circular free**: Avoid circular dependencies
- **Documented**: Explain why each dependency is needed

### 3. Loading Strategy

- **Progressive**: Load modules as needed
- **Prioritized**: Set appropriate load priorities
- **Efficient**: Consider token costs
- **User-controlled**: Let users choose loading options

## Common Patterns

### Review Skill Pattern

```yaml
# pensive/review-skills/SKILL.md
dependencies:
  - pensive:shared
  - imbue:evidence-logging

progressive_loading: true
modules:
  - modules/basic-checks.md      # load_priority: 1
  - modules/deep-analysis.md     # load_priority: 2
  - modules/expert-audit.md      # load_priority: 3
```

### Analysis Skill Pattern

```yaml
# plugin/analysis-skills/SKILL.md
dependencies:
  - imbue:evidence-logging
  - plugin:shared-utilities

progressive_loading: true
modules:
  - modules/context-analysis.md   # Always loaded
  - modules/pattern-detection.md  # Load for pattern work
```

### Cross-Plugin Integration

```yaml
# Plugin A skill using Plugin B utilities
dependencies:
  - plugin-b:shared-utilities
  - imbue:evidence-logging
```

## Testing Integration

The test suite verifies:

1. **Module completeness**: All modules have required frontmatter
2. **Dependency validity**: All dependencies point to existing skills
3. **Circular dependencies**: No circular dependency chains
4. **Load consistency**: Progressive loading matches available modules
5. **Backward compatibility**: Existing skills continue to work

Run tests with:
```bash
python -m pytest tests/integration/test_module_dependencies.py -v
```

## Migration Guide

### Adding Dependencies to Existing Modules

1. Add `parent_skill` to module frontmatter
2. Add `dependencies` section if needed
3. Add `load_priority` and `estimated_tokens`
4. Update skill to use `@include` or `Load:` statements

Example migration:

```yaml
# Before
---
name: my-module
description: A module
---

# After
---
parent_skill: my-plugin:my-skill
name: my-module
description: A module
category: analysis
tags: [analysis, patterns]
dependencies:
  - shared:utilities
load_priority: 2
estimated_tokens: 300
---
```

This ensures proper integration with the shared utilities ecosystem.