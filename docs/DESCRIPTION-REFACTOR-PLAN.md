# Command Description Refactoring Plan

## Status: COMPLETE ✅

Refactored all 29 commands (20 red + 9 yellow) to green zone (<100 chars).

| Metric | Before | After |
|--------|--------|-------|
| 🔴 Red (>200 chars) | 20 | 0 |
| 🟡 Yellow (100-200) | 9 | 0 |
| ✅ Green (<100) | ~36 | 65 |
| With `<identification>` | 0 | 28 |
| **Total commands** | 65 | 65 |

## Problem

Long frontmatter descriptions (600+ chars) create poor UX when typing `/` in Claude Code. The description field serves two conflicting purposes:
1. **Display** - What users see in the `/` menu (should be short)
2. **Identification** - What Claude uses to match skills (needs triggers/use-when logic)

## Audit Results

| Priority | Plugin | Commands | Avg Chars |
|----------|--------|----------|-----------|
| P0 | abstract | 13 | 650 |
| P1 | sanctum | 4 | 217 |
| P1 | conserve | 2 | 218 |
| P2 | spec-kit | 1 | 262 |
| Borderline | various | 9 | 110 |

**Total**: 20 commands need refactoring, 9 borderline

## Standard Template

### Before (Long Description)
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

### After (Short Description + Body Section)
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

## Refactoring Rules

1. **Description limit**: Max 80 characters, single line
2. **Format**: Active voice, starts with verb (Harden, Analyze, Create, Generate)
3. **Identification section**: Use `<identification>` tags in body (first section after h1)
4. **Preserve all content**: Move triggers, use_when, do_not_use_when to body
5. **Test after refactor**: Ensure skill matching still works

## Implementation Batches

### Batch 1: abstract (13 commands) - HIGHEST PRIORITY
```
abstract:validate-hook
abstract:context-report
abstract:analyze-skill
abstract:bulletproof-skill
abstract:skills-eval
abstract:estimate-tokens
abstract:analyze-hook
abstract:create-hook
abstract:hooks-eval
abstract:test-skill
abstract:make-dogfood
abstract:create-skill
abstract:create-command
```

### Batch 2: sanctum (4 commands)
```
sanctum:fix-pr
sanctum:fix-workflow
sanctum:pr-review
sanctum:fix-issue
```

### Batch 3: conserve + spec-kit (3 commands)
```
conserve:unbloat
conserve:bloat-scan
spec-kit:speckit-clarify
```

## Validation

After each batch:
1. Run `/abstract:validate-plugin <plugin>`
2. Test command discovery with `/` menu
3. Verify skill matching with sample prompts

## Success Metrics

- All descriptions < 100 chars
- No loss of skill identification accuracy
- Improved `/` menu UX
