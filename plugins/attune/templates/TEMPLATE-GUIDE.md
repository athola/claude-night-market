# Template Guide - Quick Reference

## The Formula

```
description: [WHAT]. Use when: [keywords]. Do not use when: [boundary].
```

## Critical Discovery

**Only `description` affects Claude matching.** All other frontmatter fields (`category`, `tags`, `complexity`, etc.) are custom metadata for our ecosystem only.

From official Claude Code docs:
> "The description field provides a brief summary of what the skill does, and is the primary signal Claude uses to determine when to invoke a skill."

**Token Budget**: 15,000 chars total for all skill descriptions across the entire plugin ecosystem.

## Description Budgets

- Skills: 100-150 chars (max 200 for complex skills)
- Commands: 50-100 chars (max 150)
- Agents: 75-125 chars (max 175)
- **Attune target**: < 3,000 chars (20% of ecosystem budget)

## Workflow

1. Read appropriate template
2. Apply to component
3. Validate: `/abstract:validate-plugin attune`
4. Check budget: `/conserve:estimate-tokens`
5. Commit

## Trigger Keyword Strategy

Select 5-10 keywords mixing:
- **User language**: "new project", "starting from scratch"
- **Technical terms**: "requirements", "architecture", "testing"
- **Workflow stages**: "before implementation", "after completion"
- **Problem indicators**: "unclear requirements", "multiple options"

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

## Anti-Patterns to Avoid

❌ **Vague descriptions**: "Helps with project stuff"
✅ **Specific outcomes**: "Generates actionable project briefs with validated approaches"

❌ **How-focused**: "Uses Socratic questioning"
✅ **What-focused**: "Guides project ideation" (how is in content)

❌ **No boundaries**: Applicable to everything
✅ **Clear boundaries**: "Do not use when: requirements already clear"

❌ **Missing triggers**: Only in description prose
✅ **Explicit triggers**: "Use when: keyword1, keyword2, phrase"

❌ **Token bloat**: Description is a paragraph
✅ **Concise utility**: 1-2 sentences max in description

## References

- Skill patterns: `skill-discoverability-template.md`
- Command patterns: `command-discoverability-template.md`
- Agent patterns: `agent-discoverability-template.md`
- Implementation plan: `docs/implementation-plan-attune-discoverability-v1.4.0.md`
- Architecture decision: `docs/adr/0005-attune-discoverability-enhancement.md`
