# Meta-Skills Enhancement Plan

**Date**: 2025-12-06
**Status**: Approved for Implementation
**Scope**: plugins/abstract - meta skills, hooks, and commands

## Executive Summary

This plan enhances the abstract plugin's meta-capabilities based on deep research into:
1. [Superpowers writing-skills skill](https://github.com/obra/superpowers) - TDD methodology for skills
2. [Anthropic best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) - Official guidance
3. Persuasion research (Meincke et al. 2025) - Psychological principles for compliance
4. Graphviz conventions - Process diagram standards

## Key Insights from Research

### Skills as Modular Code

Apply software engineering principles to skill authoring:

| Code Principle | Skill Application |
|----------------|-------------------|
| Single Responsibility | Each skill/module does ONE thing well |
| Loose Coupling | Skills reference but don't duplicate each other |
| High Cohesion | Related content stays together in modules |
| DRY | Share common patterns via cross-references |
| Interface Segregation | SKILL.md exposes only what's needed |
| Open/Closed | Extend via modules, don't modify core |

**Practical implications**:
- Skills should be focused (not kitchen-sink collections)
- Modules should be reusable across skills
- Shared patterns belong in dedicated reference skills
- Dependencies should be explicit and minimal
- Each file has a clear, single purpose

### Iron Law: TDD for Skills
> "NO SKILL WITHOUT A FAILING TEST FIRST"

Skills require the same RED-GREEN-REFACTOR cycle as code:
- **RED**: Run pressure scenarios WITHOUT skill, document baseline failures
- **GREEN**: Write minimal skill addressing those failures
- **REFACTOR**: Identify rationalizations, add explicit counters, iterate

### Persuasion Principles (Research-Backed)
Meincke et al. (2025) found persuasion techniques doubled compliance (33% → 72%):
- **Authority**: Imperative language ("YOU MUST", "No exceptions")
- **Commitment**: Explicit declarations and tracking
- **Scarcity**: Time-bound requirements ("IMMEDIATELY before proceeding")
- **Social Proof**: Universal norms ("Every time. Without exception.")
- **Unity**: Collaborative language ("our codebase", "we're colleagues")

### Claude 4.x Model Considerations
From official docs:
> "Claude Opus 4.5 is more responsive to the system prompt... Where you might have said 'CRITICAL: You MUST', you can use more normal prompting."

This means our skills should dial back aggressive language for newer models.

### Anti-Rationalization Patterns
Skills that enforce discipline need explicit loophole closures:
- List specific exceptions up front
- Create rationalization tables from baseline testing
- Build red flags lists for self-checking
- Address "spirit vs. letter" arguments early

---

## Implementation Tasks

### Task 1: Create `skill-authoring` Skill

**Location**: `plugins/abstract/skills/skill-authoring/`

**Purpose**: Complete guide for writing effective Claude Code skills using TDD methodology

**Structure**:
```
skill-authoring/
├── SKILL.md              # Main skill (< 500 lines)
├── modules/
│   ├── tdd-methodology.md        # RED-GREEN-REFACTOR for skills
│   ├── persuasion-principles.md  # Research-backed compliance techniques
│   ├── graphviz-conventions.md   # Process diagram standards
│   ├── description-writing.md    # Discovery optimization
│   ├── progressive-disclosure.md # File structure patterns
│   ├── anti-rationalization.md   # Bulletproofing techniques
│   ├── testing-with-subagents.md # Pressure testing methodology
│   └── deployment-checklist.md   # Final validation
└── scripts/
    └── skill-validator.py        # Validate skill structure
```

**Key Content**:
1. Frontmatter requirements (name ≤64 chars, description ≤1024 chars)
2. Third-person description writing
3. TDD cycle with baseline documentation
4. Persuasion principles application
5. Anti-rationalization tables
6. Graphviz conventions for flowcharts
7. Progressive disclosure patterns
8. Token budget management (< 500 lines)

### Task 2: Update `skills-eval` Skill

**Location**: `plugins/abstract/skills/skills-eval/`

**Changes**:
1. Add `modules/authoring-checklist.md` - Comprehensive validation checklist
2. Add `modules/skill-authoring-best-practices.md` - Official guidance integration
3. Update `modules/quality-metrics.md` - Add persuasion and anti-rationalization metrics
4. Add rationalization detection to compliance checker

**New Metrics**:
- Persuasion technique usage (authority, commitment, social proof)
- Anti-rationalization coverage (loophole closures, red flags lists)
- Description specificity (discovery optimization score)
- Progressive disclosure compliance
- Model-appropriate language (dial back for Opus 4.5)

### Task 3: Create `hook-authoring` Skill

**Location**: `plugins/abstract/skills/hook-authoring/`

**Purpose**: Complete guide for writing Claude Code and SDK hooks

**Structure**:
```
hook-authoring/
├── SKILL.md              # Main skill
├── modules/
│   ├── hook-types.md             # PreToolUse, PostToolUse, etc.
│   ├── sdk-callbacks.md          # Python SDK patterns
│   ├── security-patterns.md      # Safe hook implementation
│   ├── performance-guidelines.md # Non-blocking, timeout handling
│   ├── scope-selection.md        # Plugin vs project vs global
│   └── testing-hooks.md          # Hook testing methodology
└── scripts/
    └── hook-validator.py         # Validate hook structure
```

**Key Content**:
1. Hook event types (PreToolUse, PostToolUse, UserPromptSubmit, Stop, SubagentStop, PreCompact)
2. SDK callback signatures and examples
3. Security vulnerability prevention
4. Performance optimization (non-blocking, timeouts)
5. Scope decision framework
6. Integration testing patterns

### Task 4: Add New Commands

**Location**: `plugins/abstract/commands/`

**New Commands**:

1. **`/create-skill`** - Guided skill creation workflow
   - Prompts for name, description, type
   - Creates directory structure
   - Generates SKILL.md template
   - Runs initial validation

2. **`/test-skill`** - TDD testing workflow
   - Runs baseline test (without skill)
   - Documents failures
   - Runs with skill
   - Compares results

3. **`/validate-hook`** - Hook validation command
   - Security scan
   - Performance check
   - Compliance verification
   - SDK compatibility

4. **`/bulletproof-skill`** - Anti-rationalization workflow
   - Identifies loopholes
   - Generates rationalization table
   - Creates red flags list
   - Suggests counters

### Task 5: Update Hooks

**Location**: `plugins/abstract/hooks/`

**Changes**:

1. **Update `pre-skill-load.json`**:
   - Add description quality validation
   - Add progressive disclosure check
   - Add token budget verification

2. **Create `post-skill-create.json`**:
   - Trigger after skill creation
   - Run validation automatically
   - Suggest improvements
   - Check naming conventions

### Task 6: Update `plugin.json`

**Changes**:
- Add new skills: `skill-authoring`, `hook-authoring`
- Add new commands: `create-skill`, `test-skill`, `validate-hook`, `bulletproof-skill`
- Update keywords with authoring-related terms
- Update version to 2.1.0

---

## File Creation Details

### SKILL.md Template for skill-authoring

```yaml
---
name: skill-authoring
description: Complete guide for writing effective Claude Code skills using TDD methodology. Use when creating new skills, improving existing skills, or learning skill authoring best practices. Covers description writing, progressive disclosure, anti-rationalization, and deployment validation.
version: 1.0.0
category: skill-development
tags: [authoring, tdd, skills, writing, best-practices, validation]
dependencies: [modular-skills]
estimated_tokens: 1500
---
```

### Hook Event Types Reference

| Event | Trigger | Use Case |
|-------|---------|----------|
| PreToolUse | Before tool execution | Validation, filtering |
| PostToolUse | After tool execution | Logging, analysis |
| UserPromptSubmit | User sends message | Context injection |
| Stop | Agent stops | Cleanup, reporting |
| SubagentStop | Subagent completes | Result processing |
| PreCompact | Before context compact | State preservation |

### Persuasion Principle Application

| Principle | Skill Application | Example |
|-----------|------------------|---------|
| Authority | Non-negotiable rules | "YOU MUST run tests before claiming completion" |
| Commitment | Explicit declarations | "Announce which skill you're using" |
| Scarcity | Time-bound requirements | "IMMEDIATELY request review before proceeding" |
| Social Proof | Universal norms | "Steps get skipped. Every time." |
| Unity | Collaborative language | "our codebase", "we're building together" |

---

## Execution Strategy

### Phase 1: Create skill-authoring Skill (Subagent 1)
- Create directory structure
- Write SKILL.md with core content
- Create all modules
- Add validation script

### Phase 2: Update skills-eval (Subagent 2)
- Add new modules
- Update quality metrics
- Enhance compliance checker
- Add persuasion detection

### Phase 3: Create hook-authoring Skill (Subagent 3)
- Create directory structure
- Write SKILL.md
- Create all modules
- Add hook validator script

### Phase 4: Add Commands (Subagent 4)
- Create command files
- Add workflow documentation
- Test command execution

### Phase 5: Update Configuration (Subagent 5)
- Update plugin.json
- Update hooks
- Run validation

---

## Success Criteria

1. All new skills pass `make check` validation
2. Token budgets under 500 lines for SKILL.md files
3. Description fields optimized for discovery
4. Persuasion principles appropriately applied
5. Anti-rationalization patterns documented
6. All commands functional
7. Plugin validates successfully

---

## References

- [Superpowers writing-skills](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md)
- [Anthropic skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Persuasion with LLMs survey](https://arxiv.org/html/2411.06837v1)
- [Meincke et al. 2025 - AI persuasion research](https://www.nature.com/articles/s41598-024-53755-0)
