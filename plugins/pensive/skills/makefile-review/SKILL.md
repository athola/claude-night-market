---
name: makefile-review
description: Deprecated alias for unified-review's makefile module. Use when an existing caller still names pensive:makefile-review.
alwaysApply: false
category: build
estimated_tokens: 100
role: entrypoint
---

# Makefile Review (Deprecated)

> **Deprecated**. Makefile review is now a module of unified-review
> (ADR-0014, #616). This stub is kept for one release, then removed.

Invoke `Skill(pensive:unified-review)` with the makefile focus and follow
its `modules/makefile-review.md`. That module carries the workflow, the
five rule modules, the output format and the verdict.

## When To Use

- An existing caller still names `pensive:makefile-review`

## When NOT To Use

- New callers: invoke `Skill(pensive:unified-review)` with the makefile
  focus directly

## Exit Criteria

- [ ] `Skill(pensive:unified-review)` was invoked with the makefile focus
- [ ] The exit criteria in unified-review's `modules/makefile-review.md`
  were met
