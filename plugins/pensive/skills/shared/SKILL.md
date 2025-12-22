---
name: pensive:shared
description: |
  Shared infrastructure and reusable modules for all pensive review skills.

  Triggers: pensive patterns, review workflow, output templates, quality checklists,
  pensive infrastructure, shared review patterns

  Use when: other pensive skills need common patterns, creating new review skills,
  ensuring consistency across pensive plugin

  DO NOT use directly: this skill is infrastructure for other pensive skills.

  This skill provides shared patterns consumed by other pensive skills.
category: review-infrastructure
tags: [shared, infrastructure, review, patterns]
version: 1.0.0
estimated_tokens: 50
---

# Pensive Shared Review Infrastructure

This skill provides reusable modules and patterns shared across all pensive review skills.

## Purpose

Centralized infrastructure for:
- Common workflow patterns
- Output format templates
- Quality checklist patterns
- Evidence logging integration

## Module Structure

```
modules/
├── review-workflow-core.md       # Core 5-step workflow pattern
├── output-format-templates.md    # Standard output structures
└── quality-checklist-patterns.md # Reusable quality checklists
```

## Usage

Review skills include these modules to inherit common patterns:

```yaml
includes:
  - ../shared/modules/review-workflow-core.md
  - ../shared/modules/output-format-templates.md
  - ../shared/modules/quality-checklist-patterns.md
```

## Consumers

All pensive review skills:
- `pensive:bug-review`
- `pensive:api-review`
- `pensive:architecture-review`
- `pensive:test-review`
- `pensive:rust-review`
- `pensive:makefile-review`
- `pensive:math-review`
- `pensive:unified-review`
