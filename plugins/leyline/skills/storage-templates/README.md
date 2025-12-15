# Storage Templates

Generic template patterns and lifecycle management for structured content storage.

## Overview

The storage-templates skill provides reusable template patterns, maturity progression models, and file naming conventions that work across different storage domains. It enables consistent lifecycle management for knowledge bases, documentation systems, and configuration management.

## Features

- **Generic Templates**: Reusable patterns for evergreen, growing, seedling, and reference content
- **Maturity Lifecycle**: Clear progression model from seedling → growing → evergreen → archive
- **File Naming Conventions**: Consistent patterns based on maturity stage
- **Domain Adaptable**: Works with knowledge management, specifications, commit templates, and more
- **Promotion Criteria**: Clear guidelines for advancing content through lifecycle stages

## Quick Start

### Basic Usage

```yaml
# Include in your skill
dependencies: [leyline:storage-templates]
```

### Template Selection

Choose template based on content stability:

| Content Type | Template | File Pattern |
|--------------|----------|--------------|
| Proven pattern | Evergreen | `topic-name.md` |
| Active development | Growing | `topic-name.md` |
| Early idea | Seedling | `2025-12-05-topic.md` |
| Tool reference | Reference | `tool-version.md` |

### Maturity Progression

```
seedling (1-2 weeks) → growing (1-3 months) → evergreen (permanent)
                                                      ↓
                                                  archive
```

## Domain Applications

### Knowledge Management (memory-palace)

```yaml
---
maturity: evergreen
palace: learning-methods
district: meta-learning
tags: [learning, memory]
---
```

### Commit Messages (sanctum)

```yaml
---
maturity: reference
scope: conventional-commits
version: 1.0.0
tags: [git, commits]
---
```

### Specifications (spec-kit)

```yaml
---
maturity: growing
phase: planning
status: draft
tags: [spec, feature]
---
```

## Structure

```
storage-templates/
├── SKILL.md                      # Hub - overview and quick start
├── README.md                     # Documentation
└── modules/
    ├── template-patterns.md      # Detailed template structures
    └── lifecycle-stages.md       # Maturity progression patterns
```

## Resources

- **SKILL.md**: Overview and quick reference
- **modules/template-patterns.md**: Detailed template structures and examples
- **modules/lifecycle-stages.md**: Maturity progression and promotion criteria

## Integration Examples

### Create Seedling

```bash
cat > 2025-12-05-new-idea.md <<EOF
---
title: New Idea
created: 2025-12-05
maturity: seedling
review_after: 2025-12-19
---

## Key Insight
Captured insight here

## Next Action
What to do with this
EOF
```

### Promote to Growing

```bash
# Remove date prefix, update maturity
mv 2025-12-05-new-idea.md new-idea.md
# Update frontmatter: maturity: growing
```

### Archive Deprecated

```bash
# Move to archive with date
mv old-pattern.md archive/2025-12-05-old-pattern.md
# Update frontmatter: maturity: archive, superseded_by: new-pattern.md
```

## Promotion Criteria

### Seedling → Growing
- Accessed 2+ times
- Connected to other content
- Insight validated

### Growing → Evergreen
- Stable for 3+ months
- Proven valuable
- Well-connected

### Evergreen → Archive
- Superseded by better approach
- Technology deprecated
- No longer applicable

## Best Practices

1. **Start with Seedlings**: Capture ideas quickly without over-investing
2. **Date Prefix Only Seedlings**: Use `YYYY-MM-DD-` prefix only for seedlings
3. **Regular Reviews**: Don't let content stagnate
4. **Archive Boldly**: Remove outdated content decisively
5. **Clean Metadata**: Remove unused frontmatter fields
6. **Stable Names**: Don't rename evergreen content

## Token Estimates

- SKILL.md: ~600 tokens
- template-patterns.md: ~800 tokens
- lifecycle-stages.md: ~600 tokens
- Total: ~2000 tokens (progressive loading)

## Dependencies

None - this is a foundational leyline skill.

## Used By

- memory-palace: Knowledge storage patterns
- sanctum: Commit message templates
- spec-kit: Specification templates
- Other plugins requiring structured content lifecycle

## License

MIT
