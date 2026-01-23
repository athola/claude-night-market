# Module Loading Guide

This guide covers how we handle dependencies, progressive loading, and shared utilities across the ecosystem.

## Overview

Our architecture allows skills to depend on other skills, load modules progressively to save tokens, and share common utilities.

## Module Frontmatter Format

Every module file (`modules/*.md`) requires specific frontmatter for the system to index it correctly.

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

Skills list their dependencies in the frontmatter.

```yaml
# SKILL.md
dependencies:
  - pensive:shared              # Use pensive shared utilities
  - imbue:evidence-logging      # Use imbue evidence logging
```

### 2. Module Dependencies

Modules can be more specific.

```yaml
# modules/specific-module.md
dependencies:
  - parent-skill:shared          # Use parent skill's shared modules
  - imbue:evidence-logging       # Cross-plugin dependency
  - plugin:other-skill           # Plugin-to-plugin dependency
```

### 3. Load Statements

We use `@include` or `Load:` to pull content in only when needed.

```yaml
# In skill content
**For basic analysis**:
- @include modules/analysis-basics.md

**For advanced features**:
- Load: modules/advanced-patterns.md
```

## Shared Utilities

### pensive:shared

This provides the core infrastructure for review skills.

```
plugins/pensive/skills/shared/
├── SKILL.md                     # Main shared skill
└── modules/
    ├── review-workflow-core.md  # 5-step review workflow
    ├── output-format-templates.md
    └── quality-checklist-patterns.md
```

Used by all pensive review skills, including `api-review`, `bug-review`, and `rust-review`.

### imbue:shared

This standardizes analysis patterns and evidence logging.

```
plugins/imbue/skills/shared/
├── SKILL.md                     # Main shared skill
└── modules/
    ├── todowrite-patterns.md    # TodoWrite conventions
    ├── evidence-formats.md      # Evidence capture formats
    └── analysis-workflows.md    # Common analysis patterns
```

Used by `pensive` skills, `sanctum` skills, and anywhere we need a reproducible paper trail.

## Loading Patterns

### Progressive Loading

We avoid loading everything at once.

```yaml
# SKILL.md
progressive_loading: true
modules:
  - basic-analysis.md            # Always loaded
  - advanced-patterns.md         # Loaded on demand
  - expert-audit.md              # Loaded for expert review
```

### Load Priority

`load_priority` dictates the order:
- **1-2**: Core modules everyone needs.
- **3**: Standard analysis tools.
- **4-5**: Specialized or optional extras.

## Best Practices

**Module Design**
Design each module to do one thing well. This makes them reusable and easier to document. Always include examples and tests.

**Dependencies**
Be explicit. Use the full `plugin:skill` format. Avoid circular dependencies—they break the loader. Document *why* a dependency exists.

**Loading Strategy**
Load modules only when the user's task requires them. Use priorities to keep the initial context window small.

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

Our test suite ensures:
1. All modules have valid frontmatter.
2. Dependencies point to real skills.
3. No circular chains exist.
4. Progressive loading configuration matches the files on disk.

Run the tests:
```bash
python -m pytest tests/integration/test_module_dependencies.py -v
```

## Migration Guide

To add dependencies to an existing module, update its frontmatter with `parent_skill`, `dependencies`, `load_priority`, and `estimated_tokens`. Then, update the parent skill to use `@include` or `Load:` statements. This integrates the module into the shared ecosystem.
