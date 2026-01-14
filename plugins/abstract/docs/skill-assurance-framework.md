# Skill Assurance Framework

## Overview

The Skill Assurance Framework validates skills, agents, and hooks are reliably discovered and executed by Claude Code through three core patterns:

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
Skills that are marked as infrastructure, such as `shared` skills, provide modules consumed by other skills rather than being invoked directly by users. These should include a `DO NOT use directly:` clause in their description instead of the standard `DO NOT use when:` trigger.

### Overlapping Triggers
When multiple skills could apply to a given context, the system prioritizes the more specific skill, such as selecting `rust-review` over a generic `unified-review`. To manage these overlaps, include explicit routing in the negative triggers using the `- use [specific-skill] instead` pattern.

### Agent vs Skill Selection
The distinction between agents and skills is based on the level of autonomy required. Agents are designed for autonomous, multi-step tasks and include `examples:` in their descriptions for matching. Skills are used for guided workflows and rely on `Triggers:` keywords for discovery. Both utilize `DO NOT use when:` clauses to ensure proper routing.

### Progressive Loading Skills
For skills with `progressive_loading: true`, core content loads by default while additional modules are loaded via `@include` only when necessary. The skill description should explicitly mention the availability of these optional modules to guide the assistant's loading decisions.

## Migration Guide for External Authors

To migrate existing skills to the framework, first audit the current description for any conditional logic in the body and move it to the YAML frontmatter. Rewrite the description using the standard template, focusing on active verbs and concrete triggers. Delete any "When to Use" sections from the skill body to avoid duplication. Then, calibrate the enforcement language intensity based on the skill category, ranging from "YOU MUST" for discipline-related skills to "Available for" for reference materials. Every skill must also include negative triggers with explicit exclusions and alternatives. Finally, run the `skills-eval` tool to verify compliance.

## Compliance Criteria

The framework evaluates compliance based on five weighted criteria. Trigger isolation, which accounts for 15% of the score, requires all conditional logic to be in the description. Enforcement language and negative triggers are each weighted at 10%, ensuring appropriate intensity and explicit routing. Keyword optimization also contributes 10% through the use of concrete triggers, while anti-rationalization patterns contribute 5% by referencing established enforcement modules.

## Shared Modules

Located in `plugins/abstract/shared-modules/`:

- `anti-rationalization.md`: Red flags table for common excuses
- `enforcement-language.md`: Tiered language templates
- `trigger-patterns.md`: Description field templates

Reference these in skills that need enforcement patterns.
