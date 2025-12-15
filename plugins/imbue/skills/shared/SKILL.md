---
name: shared
description: Shared infrastructure and patterns for imbue analysis skills
category: infrastructure
tags: [shared, patterns, templates, analysis]
provides:
  infrastructure: [todowrite-patterns, evidence-formats, analysis-workflows]
reusable_by: [all imbue skills, pensive skills, sanctum skills]
estimated_tokens: 150
---

# Shared Infrastructure for Imbue

## Purpose

Reusable patterns for analysis workflows, evidence logging, and structured outputs used across imbue skills and by dependent plugins (pensive, sanctum).

## Modules

### TodoWrite Patterns
The `modules/todowrite-patterns.md` module documents naming conventions:
- Pattern: `skill-name:step-name`
- Common prefixes: evidence-logging, diff-analysis, review-core, catchup
- Examples from all imbue skills

### Evidence Formats
The `modules/evidence-formats.md` module standardizes evidence capture:
- Command logging format `[E1]`, `[E2]`
- Citation format `[C1]`, `[C2]`
- Artifact indexing conventions
- Reference linking in findings

### Analysis Workflows
The `modules/analysis-workflows.md` module provides workflow templates:
- Diff analysis flow
- Catchup workflow patterns
- Structured output generation

## When to Reference

- **New skill development**: Use patterns for consistency
- **Cross-plugin integration**: Reference evidence formats from pensive, sanctum
- **Template generation**: Use output formats for reports

## Integration Notes

This skill provides infrastructure used by:
- `pensive:*-review` skills via `dependencies: [imbue:evidence-logging]`
- `sanctum:git-workspace-review` for analysis patterns
- Any skill needing reproducible evidence trails
