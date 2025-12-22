---
name: shared
description: |
  Shared infrastructure and patterns for sanctum git/workspace skills.

  Triggers: sanctum patterns, todowrite patterns, git commands, output templates,
  sanctum infrastructure, shared patterns, git conventions

  Use when: developing new sanctum skills, refactoring existing skills,
  ensuring consistency across sanctum workflows, referencing standard patterns

  DO NOT use directly: this skill is infrastructure for other sanctum skills.

  Provides reusable patterns consumed by all sanctum git and workspace skills.
category: infrastructure
tags: [shared, patterns, templates, git]
provides:
  infrastructure: [todowrite-patterns, git-commands, output-templates]
reusable_by: [all sanctum skills]
estimated_tokens: 200
---

# Shared Infrastructure for Sanctum

## Purpose
This skill provides reusable patterns, templates, and conventions used across all sanctum git and workspace skills. It ensures consistency in TodoWrite naming, git command usage, and output formatting.

## Modules

### TodoWrite Patterns
The `modules/todowrite-patterns.md` module documents the naming convention for TodoWrite items across all sanctum skills:
- Pattern: `skill-name:step-name`
- Examples from commit-messages, pr-prep, git-workspace-review, doc-updates, version-updates
- Best practices for creating meaningful step names

### Git Commands
The `modules/git-commands.md` module extracts common git commands used throughout sanctum workflows:
- Repository confirmation commands
- Diff commands (staged, unstaged, stat, detailed)
- Branch and merge-base operations
- Status parsing patterns

### Output Templates
The `modules/output-templates.md` module provides standardized output formats:
- Conventional commit message structure
- Pull request description template
- Documentation update format
- Version update summary format

## When to Reference
- **New skill development**: Use these patterns to maintain consistency
- **Workflow refactoring**: Reference when updating existing skills
- **Cross-skill integration**: Check TodoWrite naming and git command patterns
- **Template generation**: Use output templates for standardized artifacts

## Integration Notes
This skill is infrastructure-only and does not define executable workflows. It serves as a reference for pattern consistency across sanctum's git and workspace operations.

All sanctum skills should follow these shared patterns to ensure predictable behavior and maintainable code.
