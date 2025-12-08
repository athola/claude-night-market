# Usage Examples for storage-templates

This document shows how different plugins can integrate and use the storage-templates skill.

## memory-palace Integration

The memory-palace plugin can use storage-templates for its knowledge intake system.

### Before (memory-palace specific)

```yaml
# plugins/memory-palace/skills/knowledge-intake/modules/storage-patterns.md
---
name: storage-patterns
description: Structured formats for storing different types of external knowledge
dependencies: [knowledge-intake]
---

# Knowledge Storage Patterns

[Full evergreen template definition]
[Full seedling template definition]
[Full reference template definition]
```

### After (using leyline)

```yaml
# plugins/memory-palace/skills/knowledge-intake/SKILL.md
---
dependencies: [leyline:storage-templates]
---

# Knowledge Intake

Use leyline storage-templates for base structure, extend with palace-specific fields:

```yaml
# Evergreen knowledge entry
---
title: Franklin Protocol
maturity: evergreen
palace: learning-methods    # memory-palace extension
district: meta-learning     # memory-palace extension
---
```

## sanctum Integration

The sanctum plugin can use storage-templates for commit message formats.

### Usage

```yaml
# plugins/sanctum/skills/commit-messages/SKILL.md
---
dependencies: [leyline:storage-templates]
---

# Commit Messages

Use reference template for commit format specifications:

```yaml
# Conventional Commit Reference
---
title: Conventional Commits v1.0.0
maturity: reference
version: 1.0.0
scope: commit-messages      # sanctum extension
format: conventional        # sanctum extension
---

# Conventional Commits

## Template
type(scope): subject

## Valid Types
feat, fix, docs, style, refactor, test, chore
```

## spec-kit Integration

The spec-kit plugin can use storage-templates for specification lifecycle.

### Usage

```yaml
# plugins/spec-kit/skills/spec-writing/SKILL.md
---
dependencies: [leyline:storage-templates]
---

# Specification Writing

Use maturity lifecycle for spec progression:

```yaml
# Feature Specification
---
title: User Authentication Feature
maturity: growing           # from storage-templates
phase: planning             # spec-kit extension
status: draft               # spec-kit extension
created: 2025-12-05
review_date: 2025-12-12
---

# User Authentication

## Requirements
[Content]

## Open Questions
[Items to resolve before promoting to evergreen]
```

Lifecycle mapping:
- seedling → idea phase
- growing → draft specification
- evergreen → approved specification
- archive → superseded specification

## Generic Documentation System

Any plugin building a documentation system can use storage-templates.

### Example: Plugin Documentation

```yaml
# plugins/my-plugin/docs/architecture.md
---
title: Plugin Architecture
maturity: evergreen
created: 2025-12-01
updated: 2025-12-05
tags: [architecture, design, core]
---

# Plugin Architecture

[Stable architectural documentation]
```

```yaml
# plugins/my-plugin/docs/2025-12-05-new-pattern.md
---
title: New Error Pattern
maturity: seedling
created: 2025-12-05
review_after: 2025-12-19
tags: [errors, experimental]
---

# New Error Pattern

## Key Insight
[Quick capture of idea]

## Next Action
[Validate in next sprint]
```

## Integration Best Practices

### 1. Extend, Don't Replace

```yaml
# Base from leyline:storage-templates
---
title: Content Title
maturity: evergreen
created: 2025-12-05
---

# Your domain-specific additions
palace: learning          # memory-palace
scope: commits            # sanctum
phase: planning           # spec-kit
custom_field: value       # your plugin
```

### 2. Use Lifecycle Consistently

All plugins benefit from consistent maturity progression:

```
seedling (experimental) 
   ↓
growing (under development)
   ↓
evergreen (stable, canonical)
   ↓
archive (deprecated)
```

### 3. Follow File Naming

- Seedlings: `YYYY-MM-DD-topic.md` (date prefix)
- Growing/Evergreen: `topic-name.md` (no date)
- References: `tool-version.md` (version included)

### 4. Review Cycles

Set appropriate review cycles based on maturity:

```yaml
maturity: seedling
review_after: 2025-12-19  # 2 weeks

maturity: growing
review_date: 2026-03-05   # quarterly

maturity: evergreen
# no review_date - stable
```

## Code Integration

If your plugin has Python tooling:

```python
from leyline.storage_templates import (
    EvergreenTemplate,
    GrowingTemplate,
    SeedlingTemplate,
    ReferenceTemplate,
    promote_content,
    check_promotion_eligibility
)

# Create new seedling
seedling = SeedlingTemplate.create(
    title="New Pattern Idea",
    insight="Core concept here",
    action="Validate and test"
)

# Check promotion eligibility
if check_promotion_eligibility('2025-12-05-new-pattern.md'):
    promote_content('2025-12-05-new-pattern.md', to='growing')
```

## Migration Strategy

### Step 1: Identify Current Templates

Find your plugin's existing template definitions:
- Knowledge storage formats
- Documentation templates
- Configuration templates

### Step 2: Map to Storage Templates

Determine which storage-template type each corresponds to:
- Stable documentation → evergreen
- Draft specs → growing
- Quick notes → seedling
- Tool references → reference

### Step 3: Extract Domain Extensions

Identify fields specific to your domain:
- memory-palace: palace, district
- sanctum: scope, format
- spec-kit: phase, status

### Step 4: Update Dependencies

Add to your skill frontmatter:

```yaml
dependencies: [leyline:storage-templates]
```

### Step 5: Simplify Your Skill

Remove generic template definitions, keep only domain-specific extensions.

## Benefits

1. **Consistency**: All plugins use same maturity model
2. **Reusability**: Don't redefine common patterns
3. **Interoperability**: Content can move between systems
4. **Maintainability**: One place to update template patterns
5. **Documentation**: Shared understanding of lifecycle stages
