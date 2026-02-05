# Skill Discoverability Template

Use this template when creating or enhancing attune plugin skills to follow proven discoverability patterns.

## Frontmatter Pattern

```yaml
---
name: skill-kebab-case
description: [WHAT it does]. Use when: [keyword1, keyword2, scenario]. Do not use when: [boundary].
# Custom metadata (not used by Claude for matching):
version: 1.4.0
category: workflow|methodology|code-quality|infrastructure
tags: [discoverability, keywords]
complexity: low|intermediate|high
estimated_tokens: [realistic estimate]
---
```

### Official Fields (Used by Claude)
- **`name`**: Skill identifier (kebab-case)
- **`description`**: **PRIMARY MATCHING SIGNAL** - See formula below

### Custom Fields (Our Metadata Only)
- `version`, `category`, `tags`, `complexity`, `estimated_tokens` - Not used by Claude for matching

## Description Formula

```
[Active verb] [specific outcome/benefit]. Use when: [trigger1, trigger2, scenario]. Do not use when: [boundary condition].
```

**Target Length**: 100-150 characters (max 200 for complex skills)

### Formula Components

1. **WHAT** (30-50 chars): Active verb + specific outcome
   - ✅ "Guide project ideation through Socratic questioning"
   - ❌ "Helps with projects" (too vague)

2. **Use when:** (40-80 chars): 3-5 trigger keywords/scenarios
   - ✅ "Use when: starting projects, exploring approaches, validating feasibility"
   - ❌ "Use when: needed" (too generic)

3. **Do not use when:** (20-40 chars): Clear boundary
   - ✅ "Do not use when: requirements already clear"
   - ❌ Missing boundary (allows false positives)

## Trigger Keyword Strategy

Select **5-10 keywords** mixing:

1. **User Language**: Natural phrases users might say
   - "new project", "starting from scratch", "need help with"

2. **Technical Terms**: Domain-specific vocabulary
   - "requirements", "architecture", "testing", "debugging"

3. **Workflow Stages**: Where in development lifecycle
   - "before implementation", "after completion", "during planning"

4. **Problem Indicators**: Signs that skill applies
   - "unclear requirements", "multiple approaches", "failing test"

## Content Structure

```markdown
# Skill Title

[One powerful sentence: What this skill does and why it matters]

## When To Use

- [Specific scenario 1]
- [Specific scenario 2]
- [Triggering condition 3]
- [User need 4]
- [Workflow stage 5]

## When NOT To Use

- [Boundary 1 - when it's inappropriate]
- [Boundary 2 - when alternative is better]
- [Edge case to avoid]

## Core Methodology

[Detailed skill content follows...]
```

## Example Transformations

### Example 1: project-brainstorming

**Before** (generic):
```yaml
---
name: project-brainstorming
description: Socratic questioning and ideation methodology for project conception
category: workflow
tags: [brainstorming]
---
```

**After** (discoverability-optimized):
```yaml
---
name: project-brainstorming
description: Guide project ideation through Socratic questioning and constraint analysis to create actionable project briefs. Use when: starting projects, exploring problem spaces, comparing approaches, validating feasibility. Do not use when: requirements already clear and specification exists.
# Custom metadata (not used by Claude for matching):
version: 1.4.0
category: workflow
tags: [brainstorming, ideation, planning, requirements, socratic-method]
complexity: intermediate
estimated_tokens: 1800
---

# Project Brainstorming

Transform vague project ideas into structured briefs with validated approaches through multi-phase Socratic exploration.

## When To Use

- Starting a new project without clear requirements
- Exploring and comparing multiple technical approaches
- Validating project feasibility before commitment
- Documenting decision rationale for stakeholders
- Need to clarify the core problem being solved

## When NOT To Use

- Requirements and specification already exist (use project-planning instead)
- Refining existing specs (use project-specification instead)
- Project scope is well-defined (jump to project-init)
- Mid-project pivots (use war-room for strategic decisions)

## Core Methodology

[Existing skill content...]
```

### Example 2: Simple Testing Skill

**Before**:
```yaml
---
name: test-generation
description: Creates tests
---
```

**After**:
```yaml
---
name: test-generation
description: Generate comprehensive test suites using TDD methodology with behavior-driven scenarios. Use when: implementing features, fixing bugs, adding test coverage, test-driven development. Do not use when: tests already exist and passing.
# Custom metadata:
version: 1.4.0
category: testing
tags: [tdd, testing, quality, bdd]
complexity: intermediate
estimated_tokens: 1200
---

# Test Generation

Create thorough test coverage using Test-Driven Development principles and Given/When/Then scenarios.

## When To Use

- Implementing new features (TDD: test first)
- Fixing bugs (write failing test, then fix)
- Adding test coverage to untested code
- Following test-driven development workflow
- Need behavior-driven test scenarios

## When NOT To Use

- Tests already exist and are passing
- Need to run existing tests (not create new ones)
- Debugging test failures (use systematic-debugging instead)

## Core Methodology

[Test generation content...]
```

## Validation Checklist

Before committing enhanced skill:

- [ ] Description starts with WHAT (active verb + outcome)
- [ ] "Use when:" keywords present in description
- [ ] "Do not use when:" boundary present in description
- [ ] Description length: 100-200 characters
- [ ] 5-10 trigger keywords in description
- [ ] "When To Use" section in content (3-5 bullets)
- [ ] "When NOT To Use" section in content (2-3 bullets)
- [ ] Custom metadata fields documented with comment
- [ ] Token estimate realistic
- [ ] Passes: `/abstract:validate-plugin attune`
- [ ] Passes pre-commit hooks

## Token Budget

**Per Skill**:
- Description: 100-150 chars (max 200)
- Total skill content: 1500-2500 tokens (max 3000)

**Total Budget** (all attune skills):
- All descriptions combined: < 3000 chars (20% of 15k token budget)

Check with:
```bash
/conserve:estimate-tokens plugins/attune/skills/*/SKILL.md
```

## Anti-Patterns to Avoid

| ❌ Avoid | ✅ Use Instead |
|---------|---------------|
| "Helps with project stuff" | "Guide project ideation to create actionable briefs" |
| "Uses Socratic questioning" | "Guide ideation through Socratic questioning" (how → content) |
| No boundaries mentioned | "Do not use when: requirements already clear" |
| Generic triggers only | Mix user language + technical terms + workflow stages |
| Description is a paragraph | 1-2 sentences max (100-200 chars) |

## References

- Official Claude Code spec: `.claude/frontmatter-spec-findings.md`
- Pattern catalog: `.claude/discoverability-patterns-summary.md`
- Superpowers examples: `~/.claude-code/plugins/superpowers/skills/*/SKILL.md`
- Implementation plan: `docs/implementation-plan-attune-discoverability-v1.4.0.md`

---

**Template Version**: 1.0 (2026-02-05)
**Status**: Ready for use
**Next**: Apply to pilot skills, validate, refine
