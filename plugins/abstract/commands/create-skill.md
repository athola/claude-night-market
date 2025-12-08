---
name: create-skill
description: Guided skill creation with brainstorming and TDD methodology. Refines ideas through Socratic questioning, creates directory structure, generates SKILL.md, and runs validation. Use when starting a new skill.
usage: /create-skill [skill-description] [--skip-brainstorm] [--plugin <name>]
---

# Create Skill Command

Creates new skills through a structured workflow: **brainstorm → scaffold → validate**. Uses Socratic questioning to refine rough ideas into well-designed skills before generating any files.

## Usage

```bash
# Start with brainstorming (recommended)
/create-skill "a skill for analyzing test coverage gaps"

# Skip brainstorming if you already have a clear design
/create-skill analyzing-coverage --skip-brainstorm

# Create in specific plugin
/create-skill "debugging async race conditions" --plugin parseltongue
```

## Workflow

### Phase 0: Brainstorming (Default)

Before creating any files, we refine the skill idea through collaborative dialogue.

**Invoke the brainstorming skill:**
```
Use superpowers:brainstorming to refine this skill idea before scaffolding.
```

The brainstorming phase will:

1. **Understand the idea** - One question at a time:
   - What problem does this skill solve?
   - Who is the target user? (beginner, intermediate, advanced)
   - What triggers this skill's use? ("Use when..." clause)
   - What should this skill NOT be used for?

2. **Explore approaches** - Present 2-3 alternatives:
   - Single comprehensive skill vs. modular with hub
   - Technique-focused vs. pattern-focused vs. reference-focused
   - Standalone vs. integrated with existing skills

3. **Validate the design** - Present in sections:
   - Core principles (what makes this skill effective?)
   - Quick start example (the 80% use case)
   - Edge cases and anti-patterns
   - Module breakdown (if modular)

4. **Document the design**:
   - Write to `docs/plans/YYYY-MM-DD-<skill-name>-design.md`
   - Commit the design document

**Skip brainstorming** with `--skip-brainstorm` only when:
- You have a written design document already
- The skill is a simple extraction from existing content
- You're creating a module for an existing skill

### Phase 1: Gather Requirements

After brainstorming (or with `--skip-brainstorm`), the command prompts for:

1. **Skill name** (if not provided)
   - Must be kebab-case
   - Maximum 64 characters
   - Gerund form preferred (e.g., `processing-pdfs`, `analyzing-logs`)
   - No `SKILL` suffix in name

2. **Skill type**:
   - `technique` (default): Concrete methods and procedures
   - `pattern`: Mental models and frameworks
   - `reference`: API documentation and lookup tables

3. **Brief description**:
   - Third-person perspective
   - Must include "Use when" clause
   - 1-2 sentences maximum

4. **Target audience** (optional):
   - Beginner, intermediate, advanced
   - Specific roles (backend dev, data scientist, etc.)

5. **Category tags** (optional):
   - testing, performance, security, architecture, etc.

### Phase 2: Create Directory Structure

```bash
# Standard skill structure
skills/${skill_name}/
├── SKILL.md              # Main skill file (hub)
├── modules/              # Optional modules directory
├── scripts/              # Optional automation scripts
└── baseline-scenarios.md # TDD test scenarios
```

For modular skills, creates additional structure:
```bash
skills/${skill_name}/
├── SKILL.md
├── modules/
│   └── README.md         # Module organization guide
├── scripts/
│   └── README.md         # Script usage guide
└── baseline-scenarios.md
```

### Phase 3: Generate SKILL.md Template

Creates SKILL.md with:

```markdown
---
name: ${skill_name}
description: ${description}
version: 0.1.0
category: ${category}
tags: [${tags}]
status: draft
created: ${date}
updated: ${date}
---

# ${Skill Title}

## Overview

${description_expanded}

## When to Use

Use this skill when:
- ${condition_1}
- ${condition_2}
- ${condition_3}

Do NOT use when:
- ${anti_condition_1}
- ${anti_condition_2}

## Quick Start

### Basic Usage

${quick_example}

### Common Scenarios

1. **${scenario_1}**
   ${scenario_1_description}

2. **${scenario_2}**
   ${scenario_2_description}

## Core Principles

${principles}

## Modules

<!-- Add module references as you create them -->

## Troubleshooting

### Common Issues

**Issue**: ${issue_1}
**Solution**: ${solution_1}

## Related Skills

- See also: ${related_skill_1}
- Complements: ${related_skill_2}

## References

- ${reference_1}
- ${reference_2}
```

### Phase 4: TDD Preparation

Creates `baseline-scenarios.md` for documenting test-first development:

```markdown
# Baseline Testing Scenarios

## Purpose

Document Claude's behavior WITHOUT this skill to identify gaps and validate improvements.

## Test Scenarios

### Scenario 1: ${scenario_name}

**Context**: ${setup_context}

**Task**: ${task_description}

**Expected Issues** (without skill):
- ${expected_issue_1}
- ${expected_issue_2}

**Baseline Response**:
```
${verbatim_response_placeholder}
```

**Failure Mode**: ${what_went_wrong}

**Rationalization Detected**: ${excuses_given}

---

### Scenario 2: ${scenario_name}

...

## Testing Protocol

1. **RED Phase**: Run scenarios WITHOUT skill loaded
   - Document exact responses
   - Note all failures and rationalizations
   - Identify patterns

2. **GREEN Phase**: Run scenarios WITH skill loaded
   - Document improvements
   - Note any remaining issues
   - Identify new rationalizations

3. **REFACTOR Phase**: Bulletproof the skill
   - Add explicit counters for rationalizations
   - Close loopholes
   - Re-test until perfect

## Success Criteria

- [ ] All scenarios pass with skill loaded
- [ ] No new failure modes introduced
- [ ] Rationalizations eliminated or countered
- [ ] Skill instructions followed consistently
```

### Phase 5: Initial Validation

Runs validation checks automatically:

```bash
# Validate frontmatter structure
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_frontmatter.py \
  skills/${skill_name}/SKILL.md

# Validate skill structure
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skill_analyzer.py \
  skills/${skill_name}/SKILL.md --validate

# Check for common issues
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/abstract_validator.py \
  skills/${skill_name}/
```

Output:
```
Validation Results:
  ✓ Frontmatter valid
  ✓ Directory structure correct
  ✓ Name follows conventions
  ✓ Description includes "Use when"
  ⚠ No modules yet (expected for new skill)
  ⚠ Baseline scenarios need completion

Status: READY FOR DEVELOPMENT
```

### Phase 6: Next Steps Guide

Provides actionable guidance:

```
✓ Skill scaffolding complete: skills/${skill_name}/

Next Steps (TDD Workflow):

1. RED PHASE - Document Baseline Failures
   - Edit baseline-scenarios.md with 3+ pressure scenarios
   - Run scenarios WITHOUT skill loaded
   - Document exact failures and rationalizations
   - Command: /test-skill skills/${skill_name} --phase red

2. GREEN PHASE - Write Minimal Content
   - Edit SKILL.md with minimal content to address failures
   - Keep it simple and focused
   - Run scenarios WITH skill loaded
   - Document improvements
   - Command: /test-skill skills/${skill_name} --phase green

3. REFACTOR PHASE - Bulletproof the Skill
   - Identify new rationalizations from GREEN testing
   - Add explicit counters and close loopholes
   - Create rationalization table
   - Re-test until bulletproof
   - Command: /bulletproof-skill skills/${skill_name}

4. VALIDATE & DEPLOY
   - Run final validation: /validate-plugin
   - Analyze tokens: /estimate-tokens skills/${skill_name}
   - Update version to 1.0.0
   - Remove 'draft' status
```

## Examples

### Example 1: Simple Technique Skill

```bash
/create-skill analyzing-logs --type technique

Creating skill: analyzing-logs
Type: technique
Directory: skills/analyzing-logs/

Prompts:
  Description: Systematic log analysis techniques for debugging. Use when investigating errors or performance issues.
  Category: debugging
  Tags: logs, debugging, troubleshooting

Created:
  ✓ skills/analyzing-logs/SKILL.md (412 bytes)
  ✓ skills/analyzing-logs/modules/ (empty)
  ✓ skills/analyzing-logs/scripts/ (empty)
  ✓ skills/analyzing-logs/baseline-scenarios.md (1,247 bytes)

Validation: PASSED (2 warnings)

Next: Document baseline scenarios in baseline-scenarios.md
```

### Example 2: Pattern Skill

```bash
/create-skill mental-models --type pattern

Creating skill: mental-models
Type: pattern

Prompts:
  Description: Core thinking frameworks for software design decisions. Use when evaluating architectural tradeoffs.
  Category: architecture
  Tags: patterns, architecture, decision-making

Created:
  ✓ skills/mental-models/SKILL.md (534 bytes)
  ✓ skills/mental-models/modules/
  ✓ skills/mental-models/modules/README.md
  ✓ skills/mental-models/baseline-scenarios.md

Pattern skills typically benefit from modularization.
Consider: /analyze-skill skills/mental-models after initial content
```

### Example 3: Reference Skill

```bash
/create-skill api-reference --type reference

Creating skill: api-reference
Type: reference

Prompts:
  Description: Quick lookup for common API patterns and signatures. Use when implementing API endpoints or clients.
  Category: reference
  Tags: api, rest, graphql, reference

Created:
  ✓ skills/api-reference/SKILL.md (398 bytes)
  ✓ skills/api-reference/modules/
  ✓ skills/api-reference/scripts/

Reference skills work best as modular hubs.
Recommend: Create focused modules for each API type
```

## Validation Rules

### Name Validation
- Must be kebab-case (lowercase with hyphens)
- Maximum 64 characters
- Alphanumeric and hyphens only
- Cannot start or end with hyphen
- No consecutive hyphens

### Description Validation
- Must be third person ("Provides...", "Analyzes...", not "Use this to...")
- Must include "Use when" clause
- Minimum 20 characters
- Maximum 200 characters
- Cannot be generic ("A helpful skill...")

### Type Validation
- Must be one of: `technique`, `pattern`, `reference`
- Defaults to `technique` if not specified

### Directory Validation
- Skill name must be unique within plugin
- Parent `skills/` directory must exist
- No conflicts with existing directories

## Error Handling

### Common Errors

**Error**: Skill name already exists
```
ERROR: Skill 'analyzing-logs' already exists at skills/analyzing-logs/
Suggestion: Choose a different name or delete existing skill first
```

**Error**: Invalid name format
```
ERROR: Skill name 'Analyze_Logs' is invalid
Must be kebab-case: 'analyze-logs'
```

**Error**: Missing description "Use when" clause
```
ERROR: Description must include "Use when" clause
Example: "Systematic log analysis. Use when debugging production issues."
```

## Integration with TDD Workflow

This command is the entry point to the full TDD skill development cycle:

1. **Create** → Use this command for scaffolding
2. **Red** → Use `/test-skill --phase red` for baseline testing
3. **Green** → Edit SKILL.md, then `/test-skill --phase green`
4. **Refactor** → Use `/bulletproof-skill` for anti-rationalization
5. **Validate** → Use `/validate-plugin` for final checks

## Implementation

```bash
# Python script handles interactive prompts and file generation
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skill_creator.py \
  --name "${1}" \
  --type "${2:-technique}" \
  --interactive
```

## See Also

- `/test-skill` - TDD testing workflow
- `/bulletproof-skill` - Anti-rationalization hardening
- `/analyze-skill` - Complexity analysis
- `/validate-plugin` - Structure validation
- `docs/modular-skills/guide.md` - Modularization best practices
