---
name: shell-review
description: Deprecated alias for unified-review's shell module. Use when an existing caller still names pensive:shell-review.
alwaysApply: false
category: build
model_hint: standard
estimated_tokens: 100
role: entrypoint
---

# Shell Script Review (Deprecated)

> **Deprecated**. Shell review is now a module of unified-review
> (ADR-0014, #615). This stub is kept for one release, then removed.

Invoke `Skill(pensive:unified-review)` with the shell focus and follow
its `modules/shell-review.md`. That module carries the workflow, the
four rule modules, the output format and the verdict.

## When To Use

- An existing caller still names `pensive:shell-review`

## When NOT To Use

- New callers: invoke `Skill(pensive:unified-review)` with the shell
  focus directly

## Exit Criteria

- [ ] `Skill(pensive:unified-review)` was invoked with the shell focus
- [ ] The exit criteria in unified-review's `modules/shell-review.md`
  were met
