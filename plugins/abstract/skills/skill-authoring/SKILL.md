---
name: skill-authoring
description: Guide to effective Claude Code skill authoring using TDD methodology and persuasion principles. Use when creating new skills, improving existing skills, or learning skill authoring best practices. Covers description writing, progressive disclosure, anti-rationalization, and deployment validation through empirical testing.
version: 1.0.0
category: skill-development
tags: [authoring, tdd, skills, writing, best-practices, validation]
dependencies: [modular-skills]
estimated_tokens: 1500
---

# Skill Authoring Guide

## Overview

This skill teaches how to write effective Claude Code skills using Test-Driven Development (TDD) methodology, persuasion principles from compliance research, and official Anthropic best practices. It treats skill writing as **process documentation requiring empirical validation** rather than theoretical instruction writing.

### Core Concept

Skills are not essays or documentation—they are **behavioral interventions** designed to change Claude's behavior in specific, measurable ways. Like software, they must be tested against real failure modes before deployment.

### Key Benefits

- **Empirical Validation**: TDD ensures skills address real failure modes, not imagined ones
- **Research-Backed Persuasion**: Compliance techniques proven to double adherence rates
- **Discoverability**: Optimized descriptions for Claude's skill selection process
- **Progressive Disclosure**: Efficient token usage through modular file structures
- **Anti-Rationalization**: Bulletproofing against Claude's tendency to explain away requirements

## The Iron Law

**NO SKILL WITHOUT A FAILING TEST FIRST**

Every skill must begin with documented evidence of Claude failing without it. This ensures you're solving real problems, not building imaginary solutions.

## When to Use This Skill

✅ **Use when:**
- Creating new skills from scratch
- Improving existing skills with low compliance rates
- Learning skill authoring best practices
- Validating skill quality before deployment
- Understanding what makes skills effective

❌ **Don't use when:**
- Evaluating existing skills (use skills-eval instead)
- Analyzing skill architecture (use modular-skills instead)
- Writing general documentation for humans

## Skill Types

### 1. Technique Skills
**Purpose**: Teach specific methods or approaches

**Examples**: TDD workflow, commit message style, API design patterns

**Structure**: Step-by-step procedures with decision points

### 2. Pattern Skills
**Purpose**: Document recurring solutions to common problems

**Examples**: Error handling patterns, module organization, testing strategies

**Structure**: Problem-solution pairs with variations

### 3. Reference Skills
**Purpose**: Provide quick lookup information

**Examples**: Command reference, configuration options, best practice checklists

**Structure**: Tables, lists, and indexed information

## Quick Start

### Minimal Viable Skill Creation

1. **Document Baseline Failure** (RED)
   - Run 3+ pressure scenarios WITHOUT skill
   - Copy-paste Claude's actual responses verbatim
   - Note specific failure patterns

2. **Write Minimal Skill** (GREEN)
   - Create SKILL.md with required frontmatter
   - Add just enough content to address documented failures
   - Test with skill present, verify improvement

3. **Bulletproof Against Rationalization** (REFACTOR)
   - Identify new excuses Claude makes
   - Add explicit counters and tables
   - Iterate until compliance is consistent

### File Structure Requirements

**Required:**
- `SKILL.md` - Main skill file with YAML frontmatter

**Optional (use only when needed):**
- `modules/` - Supporting content for progressive disclosure
- `scripts/` - Executable tools and validators
- `README.md` - Plugin-level overview (not skill-level)

**Naming Convention:**
- Flat namespace (no nested skill directories)
- Lowercase with hyphens: `skill-name`
- Module files: descriptive kebab-case

## Description Optimization

Skill descriptions are critical for Claude's discovery process. They must be optimized for both semantic search and explicit triggering.

### Formula

```
[What it does] + [When to use it] + [Key triggers]
```

### Requirements

✅ **Always:**
- Third person voice ("Teaches...", "Provides...", "Guides...")
- Include "Use when..." clause
- Specific, concrete language
- Key discovery terms

❌ **Never:**
- First person ("I teach...", "We provide...")
- Vague descriptions ("Helps with coding")
- Marketing language
- Missing use case context

### Example Patterns

**Good:**
```yaml
description: Guides API design using RESTful principles and best practices. Use when designing new APIs, reviewing API proposals, or standardizing endpoint patterns. Covers resource modeling, HTTP method selection, and versioning strategies.
```

**Bad:**
```yaml
description: This skill helps you design better APIs.
```

## The TDD Cycle for Skills

### RED Phase: Document Baseline Failures

**Goal**: Establish empirical evidence that intervention is needed

**Process:**
1. Create 3+ pressure scenarios combining:
   - Time pressure ("quickly", "simple task")
   - Ambiguity ("standard approach", "best practices")
   - Multiple requirements
   - Edge cases

2. Run scenarios in fresh Claude instances WITHOUT skill

3. Document failures verbatim:
   ```markdown
   ## Baseline Scenario 1: Simple API endpoint

   **Prompt**: "Quickly add a user registration endpoint"

   **Claude Response** (actual, unedited):
   [paste exact response]

   **Failures Observed**:
   - Skipped error handling
   - No input validation
   - Missing rate limiting
   - Didn't consider security
   ```

4. Identify patterns across failures

### GREEN Phase: Minimal Skill Implementation

**Goal**: Create smallest intervention that addresses documented failures

**Process:**
1. Write SKILL.md with required frontmatter:
   ```yaml
   ---
   name: skill-name
   description: [optimized description]
   version: 1.0.0
   category: [appropriate category]
   tags: [discovery, keywords, here]
   dependencies: []
   estimated_tokens: [realistic estimate]
   ---
   ```

2. Add content that directly counters baseline failures

3. Include ONE example showing correct behavior

4. Test with skill present:
   - Run same pressure scenarios
   - Document new behavior
   - Verify improvement over baseline

### REFACTOR Phase: Bulletproof Against Rationalization

**Goal**: Eliminate Claude's ability to explain away requirements

**Process:**
1. Run new pressure scenarios with skill active

2. Document rationalizations:
   ```markdown
   **Scenario**: Add authentication to API

   **Claude's Rationalization**:
   "Since this is a simple internal API, basic authentication
   is sufficient for now. We can add OAuth later if needed."

   **What Should Happen**:
   Security requirements apply regardless of API scope.
   Internal APIs need proper authentication.
   ```

3. Add explicit counters:
   - Exception tables with "No Exceptions" rows
   - Red flag lists
   - Decision flowcharts with escape hatches blocked
   - Commitment statements

4. Iterate until rationalizations stop

## Anti-Rationalization Techniques

Claude is sophisticated at finding ways to bypass requirements while appearing compliant. Skills must explicitly counter common rationalization patterns.

### Common Rationalization Patterns

| Excuse | Counter |
|--------|---------|
| "This is just a simple task" | Complexity doesn't exempt you from core practices. Use skills anyway. |
| "I remember the key points" | Skills evolve. Always run current version. |
| "Spirit vs letter of the law" | Foundational principles come first. No shortcuts. |
| "User just wants quick answer" | Quality and speed aren't exclusive. Both matter. |
| "Context is different here" | Skills include context handling. Follow the process. |
| "I'll add it in next iteration" | Skills apply to current work. No deferral. |

### Red Flags for Self-Checking

Skills should include explicit red flag lists:

```markdown
## Red Flags That You're Rationalizing

Stop immediately if you think:
- "This is too simple for the full process"
- "I already know this, no need to review"
- "The user wouldn't want me to do all this"
- "We can skip this step just this once"
- "The principle doesn't apply here because..."
```

### Explicit Exception Handling

When exceptions truly exist, document them explicitly:

```markdown
## When NOT to Use This Skill

❌ **Don't use when:**
- User explicitly requests prototype/draft quality
- Exploring multiple approaches quickly (note for follow-up)
- Working in non-production environment (document shortcut)

✅ **Still use for:**
- "Quick" production changes
- "Simple" fixes to production code
- Internal tools and scripts
```

## Module References

For detailed implementation guidance:

- **TDD Methodology**: See `modules/tdd-methodology.md` for RED-GREEN-REFACTOR cycle details
- **Persuasion Principles**: See `modules/persuasion-principles.md` for compliance research and techniques
- **Description Writing**: See `modules/description-writing.md` for discovery optimization
- **Progressive Disclosure**: See `modules/progressive-disclosure.md` for file structure patterns
- **Anti-Rationalization**: See `modules/anti-rationalization.md` for bulletproofing techniques
- **Graphviz Conventions**: See `modules/graphviz-conventions.md` for process diagram standards
- **Testing with Subagents**: See `modules/testing-with-subagents.md` for pressure testing methodology
- **Deployment Checklist**: See `modules/deployment-checklist.md` for final validation

## Deployment Checklist

Before deploying a new skill:

### Quality Gates

- [ ] **RED Phase Complete**: 3+ baseline scenarios documented with actual failures
- [ ] **GREEN Phase Complete**: Skill tested and shows measurable improvement
- [ ] **REFACTOR Phase Complete**: Rationalizations identified and countered
- [ ] **Frontmatter Valid**: All required YAML fields present and correct
- [ ] **Description Optimized**: Third person, includes "Use when", has key terms
- [ ] **Line Count**: SKILL.md under 500 lines (move extras to modules)
- [ ] **Module References**: All referenced files exist and are linked correctly
- [ ] **Examples Present**: At least one concrete example included
- [ ] **Scripts Executable**: Any tools tested and working
- [ ] **No Orphans**: No dead links or missing dependencies

### Validation Command

```bash
python scripts/skill_validator.py
```

Exit codes:
- `0` = Success, ready to deploy
- `1` = Warnings, should fix but can deploy
- `2` = Errors, must fix before deploying

## Common Pitfalls

### 1. Writing Without Testing
**Problem**: Creating skills based on what "should" work

**Solution**: Always start with documented failures (RED phase)

### 2. Vague Descriptions
**Problem**: "Helps with testing" - not discoverable or actionable

**Solution**: "Guides TDD workflow with RED-GREEN-REFACTOR cycle. Use when writing new tests, refactoring existing code, or ensuring test coverage."

### 3. Monolithic Skills
**Problem**: Everything in SKILL.md, 1000+ lines

**Solution**: Keep main file under 500 lines, use progressive disclosure with modules

### 4. Missing Anti-Rationalization
**Problem**: Claude finds creative ways to bypass requirements

**Solution**: Add explicit exception tables, red flags, and commitment statements

### 5. Theoretical Examples
**Problem**: Examples show ideal scenarios, not real challenges

**Solution**: Use actual failure cases from RED phase as examples

## Integration with Other Skills

### With modular-skills
- Use skill-authoring for **creating individual skills**
- Use modular-skills for **architecting skill structure**

### With skills-eval
- Use skill-authoring for **initial creation and testing**
- Use skills-eval for **ongoing quality assessment**

### Workflow
1. Create new skill using skill-authoring (TDD approach)
2. Validate structure using modular-skills (architecture check)
3. Assess quality using skills-eval (compliance and metrics)
4. Iterate based on feedback

## Summary

Effective skill authoring requires:
1. **Empirical Testing**: Start with real failures (RED)
2. **Minimal Intervention**: Solve actual problems (GREEN)
3. **Bulletproofing**: Counter rationalizations (REFACTOR)
4. **Optimized Discovery**: Write descriptions for activation
5. **Progressive Disclosure**: Structure for token efficiency
6. **Persuasive Design**: Apply compliance research
7. **Validation**: Test before deploying

Remember: Skills are behavioral interventions, not documentation. If you haven't tested it against real failure modes, you haven't validated that it works.
