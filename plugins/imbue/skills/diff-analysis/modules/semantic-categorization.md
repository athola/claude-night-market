---
name: semantic-categorization
description: Framework for categorizing changes by type and semantic meaning
parent_skill: imbue:diff-analysis
category: analysis-framework
tags: [categorization, semantic-analysis, change-types]
estimated_tokens: 300
---

# Semantic Categorization

## Change Categories

Group changes by their structural nature:

- **Additions**: New capabilities, files, or entities introduced
- **Modifications**: Changes to existing behavior or structure
- **Deletions**: Removed capabilities or deprecated items
- **Renames/Moves**: Reorganization without functional change

## Semantic Categories

Classify changes by their purpose and impact:

- **Features**: New user-facing capabilities or functionality
- **Fixes**: Corrections to existing behavior, bug resolutions
- **Refactors**: Structural improvements without behavior change
- **Tests**: Test coverage additions or modifications
- **Documentation**: Explanatory content, guides, or inline documentation changes
- **Configuration**: Settings, environment variables, infrastructure, or build configuration changes

## Entity-Level Diff (Primary: sem)

When [sem](https://github.com/Ataraxy-Labs/sem) is
available (see `leyline:sem-integration`), use
entity-level diffs:

```bash
# Check sem availability
if command -v sem &>/dev/null; then
  sem diff --json <baseline>
fi
```

This returns entities (functions, classes, methods)
with `change_type` of added, modified, deleted, or
renamed. Group by `change_type` to populate the
structural categories above.

## File-Level Diff (Fallback: git)

When sem is unavailable, use git's `--diff-filter`
flag to isolate change types at file level:

```bash
git diff --name-only --diff-filter=A <baseline>  # Added files
git diff --name-only --diff-filter=M <baseline>  # Modified files
git diff --name-only --diff-filter=D <baseline>  # Deleted files
git diff --name-only --diff-filter=R <baseline>  # Renamed files
```

## Cross-Cutting Changes

Identify changes that span multiple categories or subsystems:
- Feature additions that also update tests and documentation
- Refactors that touch multiple modules
- Configuration changes that affect multiple environments
- Breaking changes that require coordinated updates

## Categorization Workflow

1. **Structural First**: Group by addition/modification/deletion
2. **Semantic Second**: Within each structural group, classify by purpose
3. **Cross-Reference**: Note changes that appear in multiple semantic categories
4. **Prioritize**: Order by impact (breaking > feature > fix > refactor)
