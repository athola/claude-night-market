# Enforcement Patterns for Skill Design

## Overview

This module provides patterns for designing skill frontmatter so a session finds the skill when it fits and skips it when it does not. These patterns complement the shared modules in `shared-modules/` with skill-specific guidance.

## The Frontmatter-Only Trigger Pattern

### Problem

Claude's skill selection uses the `description` field to decide which skill to read. If conditional logic is in the skill body:

1. Claude must already be reading the skill to discover it applies (chicken-and-egg)
2. Skills get read unnecessarily, wasting tokens
3. Skill triggering becomes inconsistent

### Solution

Put ALL trigger logic in the description field:

```yaml
description: |
  [ACTION VERB + CAPABILITY]. [1-2 sentences max]

  Triggers: [comma-separated keywords for discovery]

  Use when: [specific scenarios, symptoms, or contexts]

  DO NOT use when: [explicit negative triggers] - use [ALTERNATIVE] instead.

  [ENFORCEMENT if applicable]
```

### Implementation Checklist

When creating a new skill:

- [ ] Write description with Triggers, Use when, DO NOT use when
- [ ] Do NOT add "When to Use" section in body
- [ ] Triggers describe fit accurately, without pressure language
- [ ] Name alternative skills explicitly in negative triggers
- [ ] Verify description is self-contained (readable alone)

## Skill Category Classification

Classify your skill to determine appropriate enforcement language:

| Category | Description | Examples |
|----------|-------------|----------|
| **Discipline-Enforcing** | Process must be followed exactly | TDD, security, compliance |
| **Workflow** | Step-by-step approach to tasks | Brainstorming, debugging, review |
| **Technique** | Best practices, optional patterns | Caching, optimization |
| **Reference** | Information retrieval | API docs, examples |

## How Hard Should the Description Push

The description's job is discovery: helping a session find this skill
when it is the right one, and skip it when it is not. That is a
matching problem, and it is solved by accurate triggers rather than by
pressure.

This section used to prescribe four intensity tiers, escalating to
"YOU MUST", "NON-NEGOTIABLE", "NEVER skip", "No exceptions" for the
top one. The workflow tier told the reader: "If you think this doesn't
apply, reconsider - it probably does."

That instruction is the problem in one line. It tells a session to
distrust its own read of the situation in favour of an author who
never saw the situation. When the author was right, it adds nothing
that accurate triggers would not have. When the author was wrong, it
is the only thing standing between the session and the correct call.

Write the description to be accurate about fit:

```yaml
description: |
  [ACTION VERB + CAPABILITY]. [1-2 sentences max]

  Triggers: [comma-separated keywords for discovery]

  Use when: [specific scenarios, symptoms, or contexts]

  DO NOT use when: [explicit negative triggers] - use [ALTERNATIVE] instead.
```

If a skill is being passed over where it genuinely applies, the fix is
in the triggers: the words are wrong, too generic, or absent. Pressure
language papers over a discovery bug and leaves it in place.

### Where a Line Genuinely Has to Hold

A few skills guard something unrecoverable: a trust boundary, a
destructive command, a safety-critical contract. Those say so plainly,
once, in the body, naming what is behind the line:

```markdown
Never pass unvalidated input to this API. It reaches the query
planner directly, and `tests/security/test_injection.py` is what
catches a regression here.
```

Plain, specific, and checkable beats emphatic. Note the difference
from the tiers above: this constrains one concrete action and says
why, rather than instructing a reader not to trust their own judgment
in general. `Skill(pensive:safety-critical-patterns)` is the
documented case where defense in depth is required by design, and it
is deliberately exempt from this guidance.

## Negative Trigger Design

### Why Negative Triggers Matter

Without explicit "DO NOT use when":
- Skills with overlapping domains trigger simultaneously
- Claude wastes context reading irrelevant skills
- Users get confused about which skill applies

### Pattern for Negative Triggers

Always:
1. Identify skills with overlapping domains
2. Name each explicitly in "DO NOT use when"
3. Provide clear handoff guidance

```yaml
DO NOT use when: evaluating existing skill quality - use skills-eval instead.
DO NOT use when: writing prose for humans - use writing-clearly-and-concisely.
DO NOT use when: debugging runtime errors - use systematic-debugging instead.
```

### Common Overlaps to Address

| Your Skill Domain | Common Overlaps | Resolution |
|------------------|-----------------|------------|
| Skill creation | Skill evaluation | modular-skills vs skills-eval |
| Debugging | Code review | systematic-debugging vs code-review |
| Planning | Brainstorming | writing-plans vs brainstorming |
| Testing | Security | TDD vs security-review |

## CSO (Claude Search Optimization)

### Effective Keywords

Use concrete, specific terms that match what users say:

**Good triggers:**
- "flaky tests", "race conditions", "memory leak"
- "TypeError", "undefined", "null reference"
- "refactoring skills", "breaking down monolith"
- "token optimization", "context efficiency"

**Avoid generic terms:**
- "help", "process", "manage"
- "improve", "fix", "update" (without specificity)
- "work with", "handle"

### Keyword Selection Process

1. List user phrases that should trigger this skill
2. Include error messages and symptoms
3. Add task-type keywords
4. Include technology-specific terms
5. Remove generic words that don't differentiate

## Integration with Modular Design

When designing modular skills:

1. **SKILL.md frontmatter**: All trigger logic here
2. **SKILL.md body**: Start immediately with workflow/overview
3. **modules/**: Progressive disclosure of details
4. **Shared modules**: Reference via relative paths

```
skills/<skill-name>/
├── SKILL.md           # Frontmatter has ALL triggers
│                      # Body has NO "When to Use" section
└── modules/
    └── *.md           # Deep-dive content, loaded on demand
```

## Validation

Before shipping a skill, verify with skills-eval:

```bash
# Check trigger isolation compliance
python scripts/compliance_checker.py --skill-path path/to/skill/SKILL.md
```

Expected output:
- No "Body contains 'When to Use'" warnings
- Trigger isolation score >= 7/10
- All negative triggers present

## Related Resources

- [Trigger Patterns](../../../shared-modules/trigger-patterns.md) - Description field templates
- [Instruction Strength](../../skill-authoring/modules/persuasion-principles.md) - How much to push, and when
- `.claude/rules/bounded-autonomy.md` - The repository-wide statement
- [Trigger Isolation Analysis](../../skills-eval/modules/trigger-isolation-analysis.md) - Evaluation criteria
