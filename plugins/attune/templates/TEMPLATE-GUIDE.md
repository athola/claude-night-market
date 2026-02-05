# Template Guide - Quick Reference

## The Formula

```
description: [WHAT]. Use when: [keywords]. Do not use when: [boundary].
```

## Budgets

- Skills: 100-150 chars (max 200)
- Commands: 50-100 chars (max 150)
- Agents: 75-125 chars (max 175)
- **Total all descriptions**: < 3000 chars

## Workflow

1. Read appropriate template
2. Apply to component
3. Validate: `/abstract:validate-plugin attune`
4. Check budget: `/conserve:estimate-tokens`
5. Commit

## Critical

**Only `description` affects Claude matching.** All other frontmatter is metadata.

## References

- Skill patterns: `skill-discoverability-template.md`
- Command patterns: `command-discoverability-template.md`
- Agent patterns: `agent-discoverability-template.md`
- Research: `.claude/discoverability-patterns-summary.md`
- Official spec: `.claude/frontmatter-spec-findings.md`
- Plan: `docs/implementation-plan-attune-discoverability-v1.4.0.md`
