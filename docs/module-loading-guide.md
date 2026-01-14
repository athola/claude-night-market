# Module Loading Guide

This guide covers module dependencies, loading patterns, and shared utilities within the plugin ecosystem.

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

### Module Design
Effective module design relies on the single responsibility principle, ensuring each module focuses on a single concern. This approach promotes reusability across multiple skills and simplifies documentation. When creating modules, provide clear usage examples and include test cases to verify functionality within the larger ecosystem.

### Dependencies
Maintain explicit and minimal dependencies by using the full `plugin:skill` format in the frontmatter. Avoid circular dependency chains, as they can cause loading failures and increase complexity. It is also helpful to document the rationale for each dependency to assist future maintenance and refactoring efforts.

### Loading Strategy
Utilize progressive loading to pull in modules only when they are required for the current task. By setting appropriate load priorities, you can control the execution order and optimize for token costs. Providing user options for loading specialized modules ensures that the system remains efficient while still offering deep analysis capabilities when needed.

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

To add dependencies to existing modules, first update the module frontmatter by adding the `parent_skill`, `dependencies`, `load_priority`, and `estimated_tokens` fields. Once the frontmatter is correctly configured, update the parent skill file to use `@include` or `Load:` statements for progressive loading. This ensures the module is properly integrated with the shared utilities ecosystem and follows established performance patterns.
