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

## Pilot Learnings (Phase 1)

### YAML Quoting (CRITICAL)
**Always quote descriptions containing colons:**
```yaml
# ✗ WRONG - YAML parse error
description: Guide ideation. Use when: starting projects

# ✓ CORRECT
description: "Guide ideation. Use when: starting projects"
```

### Length Management
Pilot results (3 components):
- project-brainstorming: 283 chars (target: 150-200)
- brainstorm command: 126 chars (target: 50-100)
- project-architect: 282 chars (target: 75-125)

**Observation**: Initial descriptions trend 40-60% over target. When crafting:
1. Start with core WHAT (30-50 chars)
2. Add 3-4 trigger keywords (40-60 chars)
3. Add 1-2 boundary conditions (20-40 chars)
4. Trim if > target by removing less-critical keywords

### Pattern Validation
✅ **Works Well**:
- WHAT + WHEN + WHEN NOT formula
- Explicit boundaries prevent false positives
- "When NOT To Use" sections guide users to alternatives
- Custom metadata clearly separated with comments

⚠️ **Watch Out**:
- Long technical terms can inflate character count quickly
- Multiple "Use when" scenarios add up fast
- Balance comprehensiveness with brevity

## References

- Skill patterns: `skill-discoverability-template.md`
- Command patterns: `command-discoverability-template.md`
- Agent patterns: `agent-discoverability-template.md`
- Research: `.claude/discoverability-patterns-summary.md`
- Official spec: `.claude/frontmatter-spec-findings.md`
- Plan: `docs/implementation-plan-attune-discoverability-v1.4.0.md`
