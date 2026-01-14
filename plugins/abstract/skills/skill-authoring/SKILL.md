---
name: skill-authoring
description: |

Triggers: skills, validation, skill, authoring, tdd
  Guide to effective Claude Code skill authoring using TDD methodology and
  persuasion principles.

  Triggers: skill authoring, skill writing, new skill, TDD skills, skill creation,
  skill best practices, skill validation, skill deployment, skill compliance

  Use when: creating new skills from scratch, improving existing skills with
  low compliance rates, learning skill authoring best practices, validating
  skill quality before deployment, understanding what makes skills effective

  DO NOT use when: evaluating existing skills - use skills-eval instead.
  DO NOT use when: analyzing skill architecture - use modular-skills instead.
  DO NOT use when: writing general documentation for humans.

  YOU MUST write a failing test before writing any skill. This is the Iron Law.
version: 1.0.0
category: skill-development
tags: [authoring, tdd, skills, writing, best-practices, validation]
dependencies: [modular-skills]
estimated_tokens: 1500
---
## Table of Contents

- [Overview](#overview)
- [Core Concept](#core-concept)
- [Key Benefits](#key-benefits)
- [The Iron Law](#the-iron-law)
- [Skill Types](#skill-types)
- [1. Technique Skills](#1-technique-skills)
- [2. Pattern Skills](#2-pattern-skills)
- [3. Reference Skills](#3-reference-skills)
- [Quick Start](#quick-start)
- [Minimal Viable Skill Creation](#minimal-viable-skill-creation)
- [File Structure Requirements](#file-structure-requirements)
- [Description Optimization](#description-optimization)
- [Formula](#formula)
- [Requirements](#requirements)
- [Example Patterns](#example-patterns)
- [The TDD Cycle for Skills](#the-tdd-cycle-for-skills)
- [RED Phase: Document Baseline Failures](#red-phase:-document-baseline-failures)
- [GREEN Phase: Minimal Skill Implementation](#green-phase:-minimal-skill-implementation)
- [REFACTOR Phase: Bulletproof Against Rationalization](#refactor-phase:-bulletproof-against-rationalization)
- [Anti-Rationalization Techniques](#anti-rationalization-techniques)
- [Common Rationalization Patterns](#common-rationalization-patterns)
- [Red Flags for Self-Checking](#red-flags-for-self-checking)
- [Red Flags That You're Rationalizing](#red-flags-that-you're-rationalizing)
- [Explicit Exception Handling](#explicit-exception-handling)
- [When NOT to Use This Skill](#when-not-to-use-this-skill)
- [Module References](#module-references)
- [Deployment Checklist](#deployment-checklist)
- [Quality Gates](#quality-gates)
- [Validation Command](#validation-command)
- [Common Pitfalls](#common-pitfalls)
- [1. Writing Without Testing](#1-writing-without-testing)
- [2. Vague Descriptions](#2-vague-descriptions)
- [3. Monolithic Skills](#3-monolithic-skills)
- [4. Missing Anti-Rationalization](#4-missing-anti-rationalization)
- [5. Theoretical Examples](#5-theoretical-examples)
- [Integration with Other Skills](#integration-with-other-skills)
- [With modular-skills](#with-modular-skills)
- [With skills-eval](#with-skills-eval)
- [Workflow](#workflow)
- [Summary](#summary)


# Skill Authoring Guide

## Overview

This skill teaches how to write effective Claude Code skills using Test-Driven Development (TDD) methodology, persuasion principles from compliance research, and official Anthropic best practices. It treats skill writing as **process documentation requiring empirical validation** rather than theoretical instruction writing.

### Core Concept

Skills are not essays or documentation—they are **behavioral interventions** designed to change Claude's behavior in specific, measurable ways. Like software, they must be tested against real failure modes before deployment.

### Key Technical Benefits

The Skill Authoring framework provides several technical advantages for plugin development. By using TDD, we validate that skills address actual failure modes identified through empirical testing. The use of optimized descriptions improves discoverability within the marketplace, while a modular file structure supports progressive disclosure for efficient token usage. Additionally, the framework includes anti-rationalization patterns that prevent the assistant from bypassing core requirements.

## The Iron Law

**NO SKILL WITHOUT A FAILING TEST FIRST**

Every skill must begin with documented evidence of Claude failing without it. This validates you're solving real problems, not building imaginary solutions.

This principle extends to ALL implementation work:
- **Skills**: No skill without documented Claude failure
- **Code**: No implementation without failing test
- **Claims**: No completion claim without evidence

For comprehensive enforcement patterns (adversarial verification, git history analysis, pre-commit hooks, coverage gates), see `imbue:proof-of-work` and its [iron-law-enforcement.md](../../../imbue/skills/proof-of-work/modules/iron-law-enforcement.md) module.

## Skill Types

We categorize skills into three primary types based on their function. Technique skills teach specific methods or approaches, such as TDD workflows or API design patterns, using step-by-step procedures. Pattern skills document recurring solutions to common problems, like error handling or module organization, through problem-solution pairs. Reference skills provide quick lookup information, such as command references and best practice checklists, typically organized in tables and indexed lists.

## Quick Start

### Skill Analysis
\`\`\`bash
# Analyze skill complexity
python scripts/analyze.py

# Estimate tokens
python scripts/tokens.py
\`\`\`

### Validation
\`\`\`bash
# Validate skill structure
python scripts/abstract_validator.py --check
\`\`\`

**Verification**: Run analysis and review token estimates before proceeding.
## Description Optimization

Skill descriptions are critical for Claude's discovery process. They must be optimized for both semantic search and explicit triggering.

### Formula

```
[What it does] + [When to use it] + [Key triggers]
```
**Verification:** Run the command with `--help` flag to verify availability.

### Requirements

 **Always:**
- Third person voice ("Teaches...", "Provides...", "Guides...")
- Include "Use when..." clause
- Specific, concrete language
- Key discovery terms

 **Never:**
- First person ("I teach...", "We provide...")
- Vague descriptions ("Helps with coding")
- Marketing language
- Missing use case context

### Example Patterns

**Good:**
```yaml
description: Guides API design using RESTful principles and best practices. Use when designing new APIs, reviewing API proposals, or standardizing endpoint patterns. Covers resource modeling, HTTP method selection, and versioning strategies.
```
**Verification:** Run the command with `--help` flag to verify availability.

**Bad:**
```yaml
description: This skill helps you design better APIs.
```
**Verification:** Run the command with `--help` flag to verify availability.

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
   **Verification:** Run the command with `--help` flag to verify availability.

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

   # Claude Code 2.1.0+ Optional Fields:
   context: fork              # Run in isolated sub-agent context
   agent: agent-name          # Specify agent type for execution
   user-invocable: false      # Hide from slash command menu (default: true)
   model: sonnet              # Model override for this skill

   # YAML-style allowed-tools (cleaner syntax)
   allowed-tools:
     - Read
     - Grep
     - Bash(npm *)            # Wildcard patterns supported

   # Lifecycle hooks scoped to skill
   hooks:
     PreToolUse:
       - matcher: "Bash"
         command: "./validate.sh"
         once: true           # Run only once per session
     Stop:
       - command: "./cleanup.sh"
   ---
   ```
   **Verification:** Run the command with `--help` flag to verify availability.

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
   **Verification:** Run the command with `--help` flag to verify availability.

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
**Verification:** Run the command with `--help` flag to verify availability.

### Explicit Exception Handling

When exceptions truly exist, document them explicitly:

```markdown
## When NOT to Use This Skill

 **Don't use when:**
- User explicitly requests prototype/draft quality
- Exploring multiple approaches quickly (note for follow-up)
- Working in non-production environment (document shortcut)

 **Still use for:**
- "Quick" production changes
- "Simple" fixes to production code
- Internal tools and scripts
```
**Verification:** Run the command with `--help` flag to verify availability.

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
**Verification:** Run `python --version` to verify Python environment.

Exit codes:
- `0` = Success, ready to deploy
- `1` = Warnings, should fix but can deploy
- `2` = Errors, must fix before deploying

## Common Pitfalls

Several common pitfalls can reduce the effectiveness of a skill. Writing skills based on theoretical behavior instead of documented failures often results in interventions that do not solve real problems. Vague descriptions, such as "helps with testing," make skills hard to discover and trigger. We also avoid monolithic files by keeping the primary skill under 500 lines and using progressive disclosure for deeper details. Finally, failing to include anti-rationalization patterns or using only ideal examples can allow the assistant to bypass requirements in complex real-world scenarios.

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

Effective skill authoring relies on empirical testing through the RED-GREEN-REFACTOR cycle to ensure that each intervention solves a real problem. By optimizing descriptions for discovery and using progressive disclosure for token efficiency, we can maintain a high activation rate and consistent performance. Bulletproofing against rationalizations and applying persuasive design principles further strengthens the skill's effectiveness. Final validation through structured quality gates confirms that the skill is ready for production deployment.
## Troubleshooting

### Common Issues

**Skill not loading**
Check YAML frontmatter syntax and required fields

**Token limits exceeded**
Use progressive disclosure - move details to modules

**Modules not found**
Verify module paths in SKILL.md are correct
