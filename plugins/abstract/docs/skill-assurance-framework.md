# Skill Assurance Framework

## Overview

The Skill Assurance Framework ensures skills, agents, and hooks are reliably discovered and executed by Claude Code through three core patterns:

1. **Frontmatter-Only Triggers**: All conditional logic in YAML `description` field
2. **Tiered Enforcement Language**: Intensity calibrated to skill category
3. **Negative Triggers**: Explicit "DO NOT use when" clauses with alternatives

## Description Field Template

```yaml
description: |
  [ACTION VERB + CAPABILITY]. [1-2 sentences max]

  Triggers: [comma-separated keywords for discovery]

  Use when: [specific scenarios, symptoms, or contexts]

  DO NOT use when: [explicit negative triggers] - use [ALTERNATIVE] instead.

  [ENFORCEMENT if applicable]
```

## Enforcement Language Tiers

| Level | Category | Language | Example |
|-------|----------|----------|---------|
| 1 | Discipline (TDD, security) | Maximum | "YOU MUST. NON-NEGOTIABLE." |
| 2 | Workflow (planning, review) | High | "Use BEFORE starting." |
| 3 | Technique (patterns) | Medium | "Use when encountering [X]." |
| 4 | Reference (docs) | Low | "Available for [X]." |

## Edge Cases & Exceptions

### Infrastructure Skills

Skills marked "DO NOT use directly" (like `shared` skills) are infrastructure:
- They provide modules consumed by other skills
- They should never be invoked directly by users
- Use `DO NOT use directly:` instead of `DO NOT use when:`

### Overlapping Triggers

When multiple skills could apply:
1. More specific skill wins (e.g., `rust-review` over `unified-review`)
2. Include explicit routing in negative triggers
3. Use `- use [specific-skill] instead` pattern

### Agent vs Skill Selection

Agents are for autonomous multi-step work; skills are for guided workflows:
- Agent descriptions include `examples:` for Claude's matching
- Skills use `Triggers:` keywords for discovery
- Both use `DO NOT use when:` for routing

### Progressive Loading Skills

Skills with `progressive_loading: true`:
- Core content loads by default
- Modules load via `@include` when needed
- Description should mention module availability

## Migration Guide for External Authors

### Step 1: Audit Current Description

Check if your skill has conditional logic in the body:
```markdown
## When to Use
Use this skill when...
```

This needs to move to frontmatter.

### Step 2: Rewrite Description

Transform:
```yaml
description: Evaluate skill quality.
```

To:
```yaml
description: |
  Evaluate and improve Claude skill quality through comprehensive auditing.

  Triggers: skill audit, quality review, compliance check

  Use when: reviewing skill quality, preparing skills for production

  DO NOT use when: creating new skills - use modular-skills.

  Use this skill before shipping any skill to production.
```

### Step 3: Remove Body Duplication

Delete "When to Use" sections from skill body - they now live in frontmatter.

### Step 4: Calibrate Enforcement

Match language intensity to skill category:
- TDD/security skills: Maximum ("YOU MUST")
- Workflow skills: High ("Use BEFORE")
- Pattern skills: Medium ("Use when")
- Reference skills: Low ("Available for")

### Step 5: Add Negative Triggers

Every skill needs explicit exclusions:
```yaml
DO NOT use when: [scenario] - use [alternative] instead.
```

### Step 6: Validate

Run `Skill(abstract:skills-eval)` to check compliance.

## Compliance Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Trigger Isolation | 15% | All conditional logic in description |
| Enforcement Language | 10% | Appropriate intensity for category |
| Negative Triggers | 10% | Explicit "don't use when" scenarios |
| Keyword Optimization | 10% | Concrete triggers in description |
| Anti-Rationalization | 5% | References enforcement patterns |

## Shared Modules

Located in `plugins/abstract/shared-modules/`:

- `anti-rationalization.md`: Red flags table for common excuses
- `enforcement-language.md`: Tiered language templates
- `trigger-patterns.md`: Description field templates

Reference these in skills that need enforcement patterns.
