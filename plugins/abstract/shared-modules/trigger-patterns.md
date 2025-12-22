# Trigger Pattern Templates

## The Core Problem

Claude's skill selection uses the `description` field to decide which skill to read. If conditional logic lives in the skill body, Claude must already be reading the skill to discover it applies - a chicken-and-egg problem.

**Solution**: Put ALL trigger logic in the description field (frontmatter).

## Description Field Structure

```yaml
description: |
  [ACTION VERB + CAPABILITY]. [1-2 sentences max]

  Triggers: [comma-separated keywords for discovery]

  Use when: [specific scenarios, symptoms, or contexts]

  DO NOT use when: [explicit negative triggers] - use [ALTERNATIVE] instead.

  [ENFORCEMENT if applicable]
```

## CSO (Claude Search Optimization)

### Effective Trigger Keywords

Use concrete, specific terms that match what users actually say or what Claude observes:

**Symptoms and errors:**
- "flaky tests", "race conditions", "performance issues"
- "TypeError", "undefined", "null reference", "memory leak"
- "timeout", "deadlock", "infinite loop"

**Task types:**
- "auditing", "refactoring", "debugging", "optimizing"
- "code review", "security scan", "compliance check"
- "migration", "upgrade", "deprecation"

**Technology-specific:**
- "React hooks", "async/await", "API endpoints"
- "database queries", "caching layer", "authentication"
- "CI/CD pipeline", "deployment", "containerization"

### Avoid Generic Terms

These don't help with discovery:
- "help", "process", "handle", "manage"
- "improve", "fix", "update" (without specificity)
- "work with", "deal with", "take care of"
- Overly broad categories like "development" or "coding"

## Negative Triggers

**Always include "DO NOT use when"** to prevent overtriggering:

```yaml
DO NOT use when: creating new skills from scratch - use modular-skills instead.
DO NOT use when: writing prose for humans - use writing-clearly-and-concisely.
DO NOT use when: debugging runtime errors - use systematic-debugging.
```

### Why Negative Triggers Matter

Without them:
1. Skills with overlapping domains trigger simultaneously
2. Claude wastes context reading irrelevant skills
3. Users get confused about which skill applies

With them:
1. Clear boundaries between related skills
2. Explicit handoff to the right alternative
3. Faster, more accurate skill selection

## Complete Examples

### Discipline-Enforcing Skill (Maximum Intensity)

```yaml
---
name: test-driven-development
description: |
  Enforce RED-GREEN-REFACTOR discipline for all code changes.

  Triggers: TDD, testing, new feature, bug fix, refactor, code changes

  Use when: writing any new code, fixing bugs, or refactoring existing code

  DO NOT use when: exploring/reading code only - no skill needed.
  DO NOT use when: writing documentation - use technical-writing.

  YOU MUST use this skill before writing any production code.
  This is NON-NEGOTIABLE. No exceptions without explicit user permission.
---
```

### Workflow Skill (High Intensity)

```yaml
---
name: brainstorming
description: |
  Structure creative exploration before implementation decisions.

  Triggers: new feature, design decision, architecture, multiple options, trade-offs

  Use when: starting any feature implementation, facing design choices,
  evaluating multiple approaches, or when requirements are ambiguous

  DO NOT use when: implementing well-defined tasks with clear specs.
  DO NOT use when: fixing obvious bugs with known solutions.

  Use this skill BEFORE starting implementation. Check even if unsure.
---
```

### Technique Skill (Medium Intensity)

```yaml
---
name: caching-patterns
description: |
  Apply caching strategies to reduce latency and resource usage.

  Triggers: slow API, repeated queries, performance bottleneck, cache,
  memoization, redundant computation

  Use when: profiling reveals redundant work, API responses are slow,
  or database queries repeat frequently

  DO NOT use when: premature optimization without profiling data.

  Consider this skill when performance issues involve repeated operations.
---
```

### Reference Skill (Low Intensity)

```yaml
---
name: plugin-schema-reference
description: |
  Reference documentation for Claude Code plugin.json schema.

  Triggers: plugin.json, plugin configuration, plugin fields, plugin structure

  Use when: need to look up plugin.json field names, types, or requirements

  DO NOT use when: creating new plugins - use create-plugin workflow.

  Available for configuration questions. Consult when needed.
---
```

## Trigger Isolation Checklist

Before shipping a skill, verify:

- [ ] **ALL** conditional logic is in the description field
- [ ] No "When to Use" section in the body duplicates description triggers
- [ ] Triggers use concrete, searchable keywords
- [ ] Negative triggers explicitly name alternatives
- [ ] Enforcement language matches skill category (see enforcement-language.md)
- [ ] Description is self-contained (readable without skill body)

## Usage

**From SKILL.md** (in `skills/<skill-name>/SKILL.md`):
```markdown
## Frontmatter Design

This skill follows the [trigger patterns guide](../../shared-modules/trigger-patterns.md).
```

**From a module** (in `skills/<skill-name>/modules/*.md`):
```markdown
See [trigger patterns](../../../shared-modules/trigger-patterns.md).
```
