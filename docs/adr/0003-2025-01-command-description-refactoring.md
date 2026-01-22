# ADR 0003: Command Description Refactoring

**Date**: 2025-01-09
**Status**: Accepted
**Context**: Command UX and Skill Discovery

## Problem

Long frontmatter descriptions (600+ chars) created poor UX when typing `/` in Claude Code. The description field served two conflicting purposes:
1. **Display** - What users see in the `/` menu (should be short)
2. **Identification** - What Claude uses to match skills (needs triggers/use-when logic)

### Audit Results

| Priority | Plugin | Commands | Avg Chars |
|----------|--------|----------|-----------|
| P0 | abstract | 13 | 650 |
| P1 | sanctum | 4 | 217 |
| P1 | conserve | 2 | 218 |
| P2 | spec-kit | 1 | 262 |
| Borderline | various | 9 | 110 |

**Total**: 20 commands needed refactoring, 9 borderline

## Decision

Implement a two-part structure separating display from identification:

### Standard Template

**Before (Long Description)**
```yaml
---
name: bulletproof-skill
description: |
  Anti-rationalization workflow for skills against bypass behaviors.

  Triggers: bulletproof, harden skill, rationalization, loopholes...

  Use when: hardening skills against rationalization behaviors,
  identifying loopholes in skill language...

  DO NOT use when: testing skill functionality - use /test-skill instead.
  DO NOT use when: evaluating skill quality - use /skills-eval instead.

  Use this command before deploying any critical skill.
usage: /bulletproof-skill [skill-path]
---
```

**After (Short Description + Body Section)**
```yaml
---
name: bulletproof-skill
description: Harden skills against rationalization and bypass behaviors
usage: /bulletproof-skill [skill-path]
---

# Bulletproof Skill Command

<identification>
triggers: bulletproof, harden skill, rationalization, loopholes, bypass, red flags, skill hardening, anti-bypass, skill compliance

use_when:
- Hardening skills against rationalization and bypass behaviors
- Identifying loopholes in skill language
- Generating rationalization tables
- Creating red flags lists
- Preparing skills for production

do_not_use_when:
- Testing skill functionality - use /test-skill instead
- Evaluating skill quality - use /skills-eval instead
- Creating new skills - use /create-skill instead
</identification>

## What It Does
...
```

### Refactoring Rules

1. **Description limit**: Max 80 characters, single line
2. **Format**: Active voice, starts with verb (Harden, Analyze, Create, Generate)
3. **Identification section**: Use `<identification>` tags in body (first section after h1)
4. **Preserve all content**: Move triggers, use_when, do_not_use_when to body
5. **Test after refactor**: Ensure skill matching still works

## Implementation Results

| Metric | Before | After |
|--------|--------|-------|
| 🔴 Red (>200 chars) | 20 | 0 |
| 🟡 Yellow (100-200) | 9 | 0 |
| ✅ Green (<100) | ~36 | 65 |
| With `<identification>` | 0 | 28 |
| **Total commands** | 65 | 65 |

### Batches Completed

**Batch 1: abstract (13 commands)**
- validate-hook, context-report, analyze-skill, bulletproof-skill
- skills-eval, estimate-tokens, analyze-hook, create-hook
- hooks-eval, test-skill, make-dogfood, create-skill, create-command

**Batch 2: sanctum (4 commands)**
- fix-pr, fix-workflow, pr-review, do-issue

**Batch 3: conserve + spec-kit (3 commands)**
- unbloat, bloat-scan, speckit-clarify

## Consequences

All command descriptions are now under 100 characters, improving `/` menu scannability. Separating display text from matching logic maintains identification accuracy while establishing a consistent format. Moving identification logic to the body keeps the UI clean without impacting LLM performance.

## Validation

After each batch:
1. Run `/abstract:validate-plugin <plugin>`
2. Test command discovery with `/` menu
3. Verify skill matching with sample prompts

## Success Metrics

Command descriptions are under 100 characters with no loss in identification accuracy. The `/` menu UX is improved, and the two-part structure is now the standard pattern across the ecosystem.

## Related

- See ADR-0004 for skill description budget optimization
- See [Capabilities Reference](../../book/src/reference/capabilities-commands.md) for command documentation
