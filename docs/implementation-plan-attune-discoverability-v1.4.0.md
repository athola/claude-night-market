# Attune Plugin Discoverability Enhancement - Implementation Plan v1.4.0

**Date**: 2026-02-05
**Author**: Claude Code (Opus)
**Branch**: `feature/attune-discoverability-v1.4.0`
**Based On**: Brainstorm + War Room session (`.claude/session-state.md`)
**Estimated Duration**: ~29 hours (4-5 working days)

## Executive Summary

Implement superpowers-inspired discoverability patterns in the attune plugin to improve automatic skill/command/agent matching. Uses a **hybrid approach** combining template development with incremental rollout across 20 components (9 skills, 9 commands, 2 agents).

### Critical Discovery from Research

**Only the `description` field matters for Claude's skill matching.** All other frontmatter fields (`category`, `tags`, `complexity`, etc.) are custom metadata for our ecosystem only.

**Token Budget**: 15,000 chars total for all skill descriptions combined across entire plugin ecosystem.

## Architecture Design

### Component Structure

```
plugins/attune/
├── skills/
│   ├── project-brainstorming/SKILL.md      ← High priority
│   ├── project-specification/SKILL.md      ← High priority
│   ├── project-planning/SKILL.md           ← High priority
│   ├── project-execution/SKILL.md          ← High priority
│   ├── war-room/SKILL.md                   ← High priority
│   ├── makefile-generation/SKILL.md        ← Medium priority
│   ├── precommit-setup/SKILL.md            ← Medium priority
│   ├── workflow-setup/SKILL.md             ← Medium priority
│   └── war-room-checkpoint/SKILL.md        ← Low priority
├── commands/
│   ├── brainstorm.md                       ← High priority
│   ├── specify.md                          ← High priority
│   ├── plan.md                             ← High priority
│   ├── execute.md                          ← High priority
│   ├── war-room.md                         ← High priority
│   ├── arch-init.md                        ← Medium priority
│   ├── project-init.md                     ← Medium priority
│   ├── validate.md                         ← Medium priority
│   └── upgrade-project.md                  ← Low priority
├── agents/
│   ├── project-architect.md                ← High priority
│   └── project-implementer.md              ← High priority
└── templates/                              ← NEW DIRECTORY
    ├── skill-discoverability-template.md
    ├── command-discoverability-template.md
    ├── agent-discoverability-template.md
    └── TEMPLATE-GUIDE.md
```

### Description Pattern Architecture

**Universal Formula** (for all component types):
```
[WHAT it does] + [WHEN to use: keywords] + [WHEN NOT to use: boundary]
```

**Example (project-brainstorming skill)**:
```yaml
description: Guide project ideation through Socratic questioning and constraint analysis to create actionable project briefs. Use when: starting projects, exploring problem spaces, comparing approaches, validating feasibility. Do not use when: requirements already clear and specification exists.
```

**Token Targets**:
- Skills: 100-150 chars (complex skills can go to 200)
- Commands: 50-100 chars (simpler, action-oriented)
- Agents: 75-125 chars (capability-focused)

### Template Architecture

Each template contains:
1. **Frontmatter section** - Standard + custom metadata
2. **Description formula** - WHAT + WHEN + WHEN NOT pattern
3. **Trigger keyword guide** - 5-10 keywords per component
4. **Content structure** - "When To Use" and "When NOT To Use" sections
5. **Examples** - Before/after transformations

## Implementation Plan

### Phase 0: Foundation (3 hours)

#### TASK-000: Create Feature Branch

**Type**: Infrastructure
**Priority**: P0
**Estimate**: 0.25 hours
**Dependencies**: None

**Acceptance Criteria**:
- [ ] Branch created: `feature/attune-discoverability-v1.4.0`
- [ ] Branch pushed to remote
- [ ] Working directory clean

**Commands**:
```bash
git checkout -b feature/attune-discoverability-v1.4.0
git push -u origin feature/attune-discoverability-v1.4.0
```

#### TASK-001: Create Templates Directory

**Type**: Infrastructure
**Priority**: P0
**Estimate**: 0.25 hours
**Dependencies**: TASK-000

**Acceptance Criteria**:
- [ ] Directory created: `plugins/attune/templates/`
- [ ] Directory tracked in git
- [ ] plugin.json updated if necessary

**Commands**:
```bash
mkdir -p plugins/attune/templates
git add plugins/attune/templates/.gitkeep
```

#### TASK-002: Develop Skill Template

**Type**: Implementation
**Priority**: P0
**Estimate**: 1 hour
**Dependencies**: TASK-001

**Deliverable**: `plugins/attune/templates/skill-discoverability-template.md`

**Acceptance Criteria**:
- [ ] Frontmatter section with official + custom fields
- [ ] Description formula with WHAT/WHEN/WHEN NOT pattern
- [ ] Trigger keyword strategy (5-10 keywords)
- [ ] "When To Use" and "When NOT To Use" sections
- [ ] Before/after example transformation
- [ ] Token budget guidance
- [ ] Validation checklist

**Content Structure**:
```markdown
# Skill Discoverability Template

## Frontmatter Pattern

```yaml
---
name: skill-kebab-case
description: [WHAT it does]. Use when: [keyword1], [keyword2], [scenario]. Do not use when: [boundary].
# Custom metadata (not used by Claude for matching):
version: 1.3.9
category: workflow|methodology|code-quality|infrastructure
tags: [discoverability, keywords]
complexity: low|intermediate|high
estimated_tokens: [realistic estimate]
---
```

## Description Formula

[Active verb] [specific outcome/benefit]. Use when: [trigger1], [trigger2], [user scenario]. Do not use when: [boundary condition].

**Target**: 100-150 chars (max 200 for complex skills)

## Trigger Keyword Strategy

Select 5-10 keywords mixing:
- User language: "new project", "starting from scratch"
- Technical terms: "requirements", "architecture", "testing"
- Workflow stages: "before implementation", "after completion"
- Problem indicators: "unclear requirements", "multiple options"

## Content Structure

# Skill Title

[One powerful sentence: What this skill does and why it matters]

## When To Use

- [Specific scenario 1]
- [Specific scenario 2]
- [Triggering condition 3]

## When NOT To Use

- [Boundary 1 - when it's inappropriate]
- [Boundary 2 - when alternative is better]

## Core Content

[Detailed methodology follows]

## Example Transformation

**Before**:
```yaml
---
name: example-skill
description: Helps with testing
---
```

**After**:
```yaml
---
name: example-skill
description: Generate comprehensive test suites using TDD methodology. Use when: implementing features, fixing bugs, adding test coverage, test-driven development. Do not use when: tests already exist and passing.
# Custom metadata:
version: 1.3.9
category: testing
tags: [tdd, testing, quality]
complexity: intermediate
estimated_tokens: 1200
---
```
```

#### TASK-003: Develop Command Template

**Type**: Implementation
**Priority**: P0
**Estimate**: 0.75 hours
**Dependencies**: TASK-002

**Deliverable**: `plugins/attune/templates/command-discoverability-template.md`

**Acceptance Criteria**:
- [ ] Similar structure to skill template
- [ ] Command-specific description pattern (action-oriented)
- [ ] Usage section with workflow integration
- [ ] Example command transformation

**Key Differences from Skill Template**:
- Shorter descriptions (50-100 chars)
- More imperative ("Create", "Generate", "Execute")
- Focus on tangible outputs
- Clear workflow position

#### TASK-004: Develop Agent Template

**Type**: Implementation
**Priority**: P0
**Estimate**: 0.75 hours
**Dependencies**: TASK-002

**Deliverable**: `plugins/attune/templates/agent-discoverability-template.md`

**Acceptance Criteria**:
- [ ] Agent-specific frontmatter (model, tools_allowed, max_iterations)
- [ ] Capability-focused descriptions
- [ ] Invocation context guidance
- [ ] Delegation syntax examples

**Agent Description Pattern**:
```yaml
description: [Role/expertise] - [primary capability] to achieve [outcome]. Use when: [invocation context], [decision type], [workflow stage].
```

#### TASK-005: Create Template Guide

**Type**: Documentation
**Priority**: P0
**Estimate**: 1 hour
**Dependencies**: TASK-002, TASK-003, TASK-004

**Deliverable**: `plugins/attune/templates/TEMPLATE-GUIDE.md`

**Acceptance Criteria**:
- [ ] Overview of discoverability patterns
- [ ] When to use each template
- [ ] Token budget guidelines
- [ ] Validation checklist
- [ ] Common pitfalls and anti-patterns
- [ ] References to research documents

### Phase 1: Pilot Enhancement (4 hours)

#### TASK-006: Enhance project-brainstorming Skill

**Type**: Implementation
**Priority**: P0
**Estimate**: 1 hour
**Dependencies**: TASK-005

**Target**: `plugins/attune/skills/project-brainstorming/SKILL.md`

**Current Description** (assumed):
```yaml
description: Socratic questioning and ideation methodology for project conception
```

**Enhanced Description**:
```yaml
description: Guide project ideation through Socratic questioning and constraint analysis to create actionable project briefs. Use when: starting projects, exploring problem spaces, comparing approaches, validating feasibility. Do not use when: requirements already clear and specification exists.
# Custom metadata:
version: 1.3.9
category: workflow
tags: [brainstorming, ideation, planning, requirements, socratic-method]
complexity: intermediate
estimated_tokens: 1800
```

**Content Additions**:
```markdown
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
```

**Acceptance Criteria**:
- [ ] Description follows WHAT/WHEN/WHEN NOT formula
- [ ] 5-10 trigger keywords in description
- [ ] "When To Use" section added to content
- [ ] "When NOT To Use" section added to content
- [ ] Token estimate within budget
- [ ] Passes abstract:validate-plugin

#### TASK-007: Enhance brainstorm Command

**Type**: Implementation
**Priority**: P0
**Estimate**: 0.75 hours
**Dependencies**: TASK-006

**Target**: `plugins/attune/commands/brainstorm.md`

**Enhanced Description**:
```yaml
description: Guide project ideation through structured Socratic questioning to generate actionable project briefs with approach comparisons
```

**Content Additions**:
```markdown
## When To Use

Use this command when you need to:
- Start a new project without clear requirements
- Explore and compare multiple technical approaches
- Validate project feasibility before committing resources
- Document decision rationale for stakeholders

## When NOT To Use

Avoid this command if:
- Requirements and specification already exist (use /attune:plan instead)
- You need to refine existing specs (use /attune:specify instead)
- Project scope is well-defined (jump to /attune:project-init)

## What This Command Does

1. **Problem Definition** - Socratic questioning to clarify the core problem
2. **Constraint Discovery** - Identify technical, resource, and compliance limits
3. **Approach Generation** - Create 3-5 distinct solution approaches
4. **War Room Deliberation** - Multi-LLM expert panel pressure-tests approaches
5. **Decision Documentation** - Generate project brief with rationale
```

**Acceptance Criteria**:
- [ ] Description concise and action-oriented
- [ ] Usage sections clear and workflow-integrated
- [ ] Links to related commands (specify, plan, init)
- [ ] Passes validation

#### TASK-008: Enhance project-architect Agent

**Type**: Implementation
**Priority**: P0
**Estimate**: 0.75 hours
**Dependencies**: TASK-006

**Target**: `plugins/attune/agents/project-architect.md`

**Enhanced Description**:
```yaml
description: Architecture design specialist - analyzes requirements and generates component-based system architecture with technology selection and rationale. Use when: designing system architecture, defining components and interfaces, selecting technology stack, making architectural decisions.
```

**Enhanced Frontmatter**:
```yaml
---
name: project-architect
description: Architecture design specialist - analyzes requirements and generates component-based system architecture with technology selection and rationale. Use when: designing system architecture, defining components and interfaces, selecting technology stack, making architectural decisions.
model: claude-sonnet-4
tools_allowed: [Read, Write, Grep, Glob]
max_iterations: 10
# Custom metadata:
version: 1.3.9
category: agent
tags: [architecture, design, planning, technical-decisions]
complexity: intermediate
---
```

**Content Additions**:
```markdown
# Project Architect Agent

Transforms specifications into production-ready system architectures with component design, technology recommendations, and deployment strategies.

## Capabilities

- **Component Design**: Break systems into modular, testable components
- **Technology Selection**: Evaluate and recommend appropriate tech stacks
- **Interface Definition**: Design clean component boundaries and APIs
- **Architecture Documentation**: Generate diagrams and decision rationale

## When To Invoke

Delegate to this agent when you need:
- System architecture design from specifications
- Component decomposition and interface definition
- Technology stack evaluation and selection
- Architectural decision documentation
- Design review and optimization

## Invocation

```bash
# Via attune:plan command (automatic)
/attune:plan

# Direct invocation with context
[Delegate architecture design for {project} to project-architect agent]
```
```

**Acceptance Criteria**:
- [ ] Description follows agent pattern (role + capability + outcome)
- [ ] Capabilities section clearly defined
- [ ] Invocation context explicit
- [ ] Frontmatter uses official fields (tools_allowed, model)

#### TASK-009: Validate Pilot Components

**Type**: Validation
**Priority**: P0
**Estimate**: 1 hour
**Dependencies**: TASK-006, TASK-007, TASK-008

**Validation Steps**:

1. **Plugin Validation**:
   ```bash
   /abstract:validate-plugin attune
   ```

2. **Skill Quality Audit**:
   ```bash
   /abstract:skills-eval project-brainstorming
   ```

3. **Token Budget Check**:
   ```bash
   /conserve:estimate-tokens plugins/attune/skills/project-brainstorming/SKILL.md
   /conserve:estimate-tokens plugins/attune/commands/brainstorm.md
   /conserve:estimate-tokens plugins/attune/agents/project-architect.md
   ```

4. **Description Length Check**:
   - project-brainstorming: Should be 150-200 chars
   - brainstorm command: Should be 75-100 chars
   - project-architect: Should be 100-150 chars

5. **Manual Discovery Testing**:
   Test prompts that should trigger each component:
   - "I want to start a new web app project" → brainstorm
   - "How do I compare technical approaches?" → project-brainstorming
   - "Design the system architecture" → project-architect

**Acceptance Criteria**:
- [ ] All validation checks pass
- [ ] Token budgets within targets
- [ ] Description lengths appropriate
- [ ] No breaking changes to existing references
- [ ] Manual testing shows improved discovery

#### TASK-010: Refine Templates Based on Pilot

**Type**: Refinement
**Priority**: P0
**Estimate**: 0.5 hours
**Dependencies**: TASK-009

**Activities**:
- Analyze pilot validation results
- Identify template gaps or ambiguities
- Document edge cases discovered
- Update templates and guide

**Acceptance Criteria**:
- [ ] Template adjustments documented
- [ ] Edge cases added to TEMPLATE-GUIDE.md
- [ ] Templates ready for Phase 2 rollout

### Phase 2: High-Priority Skills (4 hours)

#### TASK-011: Enhance project-specification Skill

**Type**: Implementation
**Priority**: P1
**Estimate**: 1 hour
**Dependencies**: TASK-010

**Target**: `plugins/attune/skills/project-specification/SKILL.md`

**Enhanced Description**:
```yaml
description: Transform project briefs into detailed, testable specifications using spec-driven development methodology. Use when: translating requirements, defining acceptance criteria, creating technical specs, before implementation. Do not use when: already have detailed specification.
```

**Acceptance Criteria**:
- [ ] Description follows pattern
- [ ] Trigger keywords include: specification, requirements, acceptance criteria, define scope
- [ ] Links to related skills (brainstorming, planning)
- [ ] Passes validation

#### TASK-012: Enhance project-planning Skill

**Type**: Implementation
**Priority**: P1
**Estimate**: 1 hour
**Dependencies**: TASK-010

**Target**: `plugins/attune/skills/project-planning/SKILL.md`

**Enhanced Description**:
```yaml
description: Transform specifications into structured implementation plans with architecture design and dependency-ordered task breakdown. Use when: converting specs to plans, designing architecture, breaking down tasks, estimating effort. Do not use when: no specification exists yet.
```

**Acceptance Criteria**:
- [ ] Description follows pattern
- [ ] Trigger keywords include: implementation plan, architecture, task breakdown, dependencies
- [ ] Workflow integration clear (after specification, before execution)

#### TASK-013: Enhance project-execution Skill

**Type**: Implementation
**Priority**: P1
**Estimate**: 1 hour
**Dependencies**: TASK-010

**Target**: `plugins/attune/skills/project-execution/SKILL.md`

**Enhanced Description**:
```yaml
description: Execute implementation plans systematically with checkpoint validation, progress tracking, and continuous validation. Use when: implementing tasks, executing plans, tracking progress, validating checkpoints. Do not use when: no implementation plan exists.
```

**Acceptance Criteria**:
- [ ] Description follows pattern
- [ ] Trigger keywords include: execute, implement, build, progress tracking
- [ ] Clear position in workflow (after planning)

#### TASK-014: Enhance war-room Skill

**Type**: Implementation
**Priority**: P1
**Estimate**: 1 hour
**Dependencies**: TASK-010

**Target**: `plugins/attune/skills/war-room/SKILL.md`

**Enhanced Description**:
```yaml
description: Multi-LLM deliberation framework for strategic decisions through expert pressure-testing and consensus building. Use when: critical decisions, irreversible changes, architecture choices, conflicting approaches, high stakes. Do not use when: decision is trivial, easily reversible, or already made.
```

**Acceptance Criteria**:
- [ ] Description emphasizes strategic decision context
- [ ] Trigger keywords include: critical decision, irreversible, war room, expert panel, high stakes
- [ ] Usage boundaries clear (Type 1 vs Type 2 decisions)

### Phase 3: High-Priority Commands (4 hours)

#### TASK-015: Enhance specify Command

**Type**: Implementation
**Priority**: P1
**Estimate**: 1 hour
**Dependencies**: TASK-011

**Target**: `plugins/attune/commands/specify.md`

**Enhanced Description**:
```yaml
description: Create detailed specifications from project briefs using spec-driven methodology with acceptance criteria and testable requirements
```

**Acceptance Criteria**:
- [ ] Command-style description (action-oriented, concise)
- [ ] Usage workflow integration (after brainstorm, before plan)
- [ ] Links to specification skill

#### TASK-016: Enhance plan Command

**Type**: Implementation
**Priority**: P1
**Estimate**: 1 hour
**Dependencies**: TASK-012

**Target**: `plugins/attune/commands/plan.md`

**Enhanced Description**:
```yaml
description: Generate implementation plan with architecture design and dependency-ordered tasks from specification
```

**Acceptance Criteria**:
- [ ] Concise action-oriented description
- [ ] Clear position in workflow
- [ ] Example outputs

#### TASK-017: Enhance execute Command

**Type**: Implementation
**Priority**: P1
**Estimate**: 1 hour
**Dependencies**: TASK-013

**Target**: `plugins/attune/commands/execute.md`

**Enhanced Description**:
```yaml
description: Execute implementation plan systematically with progress tracking and checkpoint validation
```

**Acceptance Criteria**:
- [ ] Clear execution workflow
- [ ] Checkpoint validation emphasis
- [ ] Progress tracking features

#### TASK-018: Enhance war-room Command

**Type**: Implementation
**Priority**: P1
**Estimate**: 1 hour
**Dependencies**: TASK-014

**Target**: `plugins/attune/commands/war-room.md`

**Enhanced Description**:
```yaml
description: Convene multi-LLM expert panel to pressure-test strategic decisions and build consensus through deliberation
```

**Acceptance Criteria**:
- [ ] Strategic decision context
- [ ] Multi-LLM emphasis
- [ ] When to use War Room (Type 1 decisions)

### Phase 4: Remaining Components (6 hours)

#### TASK-019: Enhance project-implementer Agent

**Type**: Implementation
**Priority**: P2
**Estimate**: 1 hour
**Dependencies**: TASK-010

**Target**: `plugins/attune/agents/project-implementer.md`

**Enhanced Description**:
```yaml
description: Implementation specialist - executes tasks from plans with TDD methodology, writes tests, and validates acceptance criteria. Use when: implementing features, writing code, test-driven development, executing task lists.
```

**Acceptance Criteria**:
- [ ] Agent pattern (role + capability + outcome)
- [ ] Clear delegation context
- [ ] TDD emphasis

#### TASK-020: Enhance makefile-generation Skill

**Type**: Implementation
**Priority**: P2
**Estimate**: 1 hour
**Dependencies**: TASK-010

**Target**: `plugins/attune/skills/makefile-generation/SKILL.md`

**Enhanced Description**:
```yaml
description: Generate language-specific Makefiles with common development targets for testing, linting, and automation. Use when: initializing projects, setting up development workflow, standardizing commands. Do not use when: Makefile already exists.
```

#### TASK-021: Enhance precommit-setup Skill

**Type**: Implementation
**Priority**: P2
**Estimate**: 1 hour
**Dependencies**: TASK-010

**Target**: `plugins/attune/skills/precommit-setup/SKILL.md`

**Enhanced Description**:
```yaml
description: Configure three-layer pre-commit quality system with linting, type checking, and testing hooks. Use when: setting up quality gates, configuring pre-commit, establishing code quality standards. Do not use when: pre-commit already configured.
```

#### TASK-022: Enhance workflow-setup Skill

**Type**: Implementation
**Priority**: P2
**Estimate**: 1 hour
**Dependencies**: TASK-010

**Target**: `plugins/attune/skills/workflow-setup/SKILL.md`

**Enhanced Description**:
```yaml
description: Configure GitHub Actions CI/CD workflows for automated testing, linting, and deployment. Use when: setting up CI/CD, configuring GitHub Actions, automating quality checks. Do not use when: CI/CD already configured.
```

#### TASK-023: Enhance Medium-Priority Commands

**Type**: Implementation
**Priority**: P2
**Estimate**: 2 hours
**Dependencies**: TASK-020, TASK-021, TASK-022

**Targets**:
- `plugins/attune/commands/arch-init.md`
- `plugins/attune/commands/project-init.md`
- `plugins/attune/commands/validate.md`

**Acceptance Criteria** (for each):
- [ ] Command-style descriptions
- [ ] Usage workflow integration
- [ ] Links to corresponding skills

#### TASK-024: Enhance Low-Priority Components

**Type**: Implementation
**Priority**: P3
**Estimate**: 1 hour
**Dependencies**: TASK-010

**Targets**:
- `plugins/attune/skills/war-room-checkpoint/SKILL.md`
- `plugins/attune/commands/upgrade-project.md`

**Acceptance Criteria**:
- [ ] Consistent with pattern
- [ ] Clear usage context
- [ ] Passes validation

### Phase 5: Documentation & Validation (5 hours)

#### TASK-025: Update README

**Type**: Documentation
**Priority**: P1
**Estimate**: 1.5 hours
**Dependencies**: TASK-024

**Target**: `plugins/attune/README.md`

**Updates Required**:
- [ ] Document new discoverability patterns
- [ ] Explain description formula
- [ ] Show before/after examples
- [ ] Update skill/command descriptions in README
- [ ] Add section on "How Skills Are Discovered"
- [ ] Link to templates for contributors

**Acceptance Criteria**:
- [ ] README reflects all enhancements
- [ ] Examples updated
- [ ] Contributing section updated with templates

#### TASK-026: Update CHANGELOG

**Type**: Documentation
**Priority**: P1
**Estimate**: 0.5 hours
**Dependencies**: TASK-024

**Target**: `plugins/attune/CHANGELOG.md`

**Entry Format**:
```markdown
## [1.4.0] - 2026-02-05

### Added
- Discoverability templates for skills, commands, and agents
- "When To Use" and "When NOT To Use" sections in all components
- Trigger keyword optimization in all descriptions

### Changed
- Enhanced descriptions for all skills following WHAT/WHEN/WHEN NOT pattern
- Enhanced descriptions for all commands with action-oriented language
- Enhanced agent descriptions with capability focus
- Frontmatter updated to distinguish official vs custom fields

### Improved
- Auto-discovery of skills from user prompts
- Reduced false positives through usage boundaries
- Consistent discoverability patterns across plugin
```

**Acceptance Criteria**:
- [ ] Version bump to 1.4.0 documented
- [ ] All changes categorized (Added/Changed/Improved)
- [ ] References to research documents

#### TASK-027: Create ADR

**Type**: Documentation
**Priority**: P1
**Estimate**: 1 hour
**Dependencies**: TASK-024

**Target**: `docs/adr/0010-attune-discoverability-enhancement.md` (or next ADR number)

**ADR Structure**:
```markdown
# ADR 0010: Attune Plugin Discoverability Enhancement

## Status

Accepted - 2026-02-05

## Context

Skills, commands, and agents in attune plugin were not consistently discovered by Claude when relevant prompts or contexts occurred. Research of obra/superpowers plugin revealed proven discoverability patterns.

Official Claude Code specification indicates only `description` field is used for skill matching, with 15k char budget across all skills.

## Decision

Implement hybrid approach combining:
1. Template development for standardization
2. Incremental rollout to manage risk
3. Description formula: WHAT + WHEN + WHEN NOT
4. Token budget management (100-200 chars per description)

## Consequences

### Positive
- Improved auto-discovery of skills from user prompts
- Reduced false positives through usage boundaries
- Consistent patterns across all components
- Reusable templates for future additions

### Negative
- Upfront time investment (~29 hours)
- Temporary inconsistency during rollout
- Requires ongoing maintenance of patterns

### Neutral
- Custom metadata fields documented as non-functional (category, tags, etc.)
- Token budgets require monitoring with conserve tools

## References

- `.claude/brainstorm-attune-discoverability.md`
- `.claude/discoverability-patterns-summary.md`
- `.claude/frontmatter-spec-findings.md`
- `.claude/attune-enhancement-action-plan.md`
```

**Acceptance Criteria**:
- [ ] ADR follows standard format
- [ ] Context explains problem and research
- [ ] Decision documents hybrid approach
- [ ] Consequences balanced and realistic

#### TASK-028: Comprehensive Validation

**Type**: Validation
**Priority**: P0
**Estimate**: 2 hours
**Dependencies**: TASK-024

**Validation Activities**:

1. **Plugin Structure Validation**:
   ```bash
   /abstract:validate-plugin attune
   ```

2. **Skill Quality Audit** (all enhanced skills):
   ```bash
   /abstract:skills-eval project-brainstorming
   /abstract:skills-eval project-specification
   /abstract:skills-eval project-planning
   /abstract:skills-eval project-execution
   /abstract:skills-eval war-room
   # ... continue for all skills
   ```

3. **Token Budget Analysis**:
   ```bash
   /conserve:estimate-tokens plugins/attune/skills/*/SKILL.md
   /conserve:estimate-tokens plugins/attune/commands/*.md
   /conserve:estimate-tokens plugins/attune/agents/*.md
   /conserve:context-report plugins/attune/skills
   ```

4. **Description Length Audit**:
   - Count characters in all descriptions
   - Verify targets met (skills: 100-200, commands: 50-100, agents: 75-125)
   - Total budget check: All descriptions should total < 3000 chars (20% of 15k)

5. **Manual Discovery Testing**:

   | Test Prompt | Expected Match | Result |
   |-------------|----------------|--------|
   | "I want to start a new web app project" | brainstorm command | ✓/✗ |
   | "How do I compare technical approaches?" | project-brainstorming skill | ✓/✗ |
   | "Create a specification from requirements" | specify command | ✓/✗ |
   | "Design the system architecture" | project-architect agent | ✓/✗ |
   | "I've finished the implementation" | NOT attune (imbue:proof-of-work) | ✓/✗ |
   | "Execute my implementation plan" | execute command | ✓/✗ |
   | "Should I convene a war room?" | war-room skill | ✓/✗ |

6. **Regression Testing**:
   - [ ] Existing attune workflows still function
   - [ ] Manual skill invocation works: `Skill(attune:project-brainstorming)`
   - [ ] Command invocation works: `/attune:brainstorm`
   - [ ] Agent delegation works: `[Delegate to project-architect]`

**Acceptance Criteria**:
- [ ] 100% validation pass rate
- [ ] Token budgets compliant
- [ ] Manual discovery test: 6/7 correct matches (85%+)
- [ ] No regressions in existing functionality
- [ ] Documentation reflects current state

## Dependency Graph

```
TASK-000 (Branch)
    └─▶ TASK-001 (Templates Dir)
            ├─▶ TASK-002 (Skill Template)
            │       ├─▶ TASK-003 (Command Template)
            │       └─▶ TASK-004 (Agent Template)
            └─▶ TASK-005 (Template Guide)
                    ├─▶ TASK-006 (Enhance brainstorm skill)
                    │       ├─▶ TASK-007 (Enhance brainstorm cmd)
                    │       ├─▶ TASK-008 (Enhance architect agent)
                    │       └─▶ TASK-009 (Validate pilot)
                    └─▶ TASK-010 (Refine templates)
                            ├─▶ TASK-011 (Enhance specification skill)
                            ├─▶ TASK-012 (Enhance planning skill)
                            ├─▶ TASK-013 (Enhance execution skill)
                            ├─▶ TASK-014 (Enhance war-room skill)
                            ├─▶ TASK-015 (Enhance specify cmd)
                            ├─▶ TASK-016 (Enhance plan cmd)
                            ├─▶ TASK-017 (Enhance execute cmd)
                            ├─▶ TASK-018 (Enhance war-room cmd)
                            ├─▶ TASK-019 (Enhance implementer agent)
                            ├─▶ TASK-020 (Enhance makefile skill)
                            ├─▶ TASK-021 (Enhance precommit skill)
                            ├─▶ TASK-022 (Enhance workflow skill)
                            ├─▶ TASK-023 (Enhance medium-priority cmds)
                            └─▶ TASK-024 (Enhance low-priority)
                                    ├─▶ TASK-025 (Update README)
                                    ├─▶ TASK-026 (Update CHANGELOG)
                                    ├─▶ TASK-027 (Create ADR)
                                    └─▶ TASK-028 (Comprehensive validation)
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Token budget overruns | Medium | Medium | Check with conserve tools at each phase; shorten descriptions if needed |
| Breaking skill references | Low | High | Use abstract:validate-plugin before merge; test manual invocations |
| Template doesn't fit all cases | High | Low | Refine after pilot; allow flexibility for edge cases |
| Discoverability not improved | Medium | Medium | Document test scenarios; gather feedback; iterate |
| Scope creep to other plugins | Medium | Low | Explicit boundary: attune only; document patterns for future |
| Description formula too rigid | Low | Medium | Templates are guidelines; allow contextual adaptation |
| False positives increase | Low | Medium | Strong "When NOT to use" boundaries; validation testing |

## Success Metrics

### Quantitative (Measurable)

- [ ] **100%** of skills have utility-first descriptions
- [ ] **100%** of skills have explicit trigger keywords in description
- [ ] **100%** of commands have "When To Use" sections
- [ ] **100%** of agents have capability-focused descriptions
- [ ] **0** token budget violations
- [ ] **100%** pass rate on abstract:validate-plugin
- [ ] **85%+** manual discovery test accuracy (6/7 correct matches)
- [ ] **< 3000 chars** total for all descriptions (20% of 15k budget)

### Qualitative (Subjective)

- [ ] Descriptions read clearly and purposefully
- [ ] Triggers are comprehensive and intuitive
- [ ] Usage boundaries prevent misapplication
- [ ] Pattern consistency across all components
- [ ] Documentation clearly explains patterns

### User Experience (Testable)

- [ ] Sample prompts trigger appropriate skills
- [ ] No false positives on boundary cases
- [ ] Linked skills properly invoke dependencies
- [ ] Manual invocation still works as before

## Timeline

| Phase | Tasks | Effort | Duration | Deliverables |
|-------|-------|--------|----------|--------------|
| **Phase 0: Foundation** | TASK-000 to TASK-005 | 3h | 0.5 days | Templates created |
| **Phase 1: Pilot** | TASK-006 to TASK-010 | 4h | 0.5 days | 3 components enhanced + validated |
| **Phase 2: High-Priority Skills** | TASK-011 to TASK-014 | 4h | 0.5 days | 4 skills enhanced |
| **Phase 3: High-Priority Commands** | TASK-015 to TASK-018 | 4h | 0.5 days | 4 commands enhanced |
| **Phase 4: Remaining Components** | TASK-019 to TASK-024 | 6h | 1 day | All components enhanced |
| **Phase 5: Documentation** | TASK-025 to TASK-028 | 5h | 1 day | Docs + validation complete |
| **Total** | 29 tasks | **29h** | **~4 days** | Attune v1.4.0 ready |

**Note**: Assumes focused work sessions; calendar time may vary.

## Rollback Plan

### Triggers for Rollback

- Validation failures that can't be quickly fixed (>4 hours debug time)
- Token budgets exceeded by >20% (>3600 chars total)
- Breaking changes to existing workflows discovered in testing
- User feedback indicates confusion or degraded experience

### Rollback Strategies

1. **Individual Component Issues**:
   ```bash
   git checkout HEAD~1 -- plugins/attune/skills/problematic-skill/SKILL.md
   ```

2. **Phase Rollback**:
   ```bash
   git revert <phase-commit-hash>
   ```

3. **Complete Rollback**:
   ```bash
   git checkout master
   git branch -D feature/attune-discoverability-v1.4.0
   ```

4. **Template Issues**:
   - Fix templates
   - Re-apply to affected components
   - No need to rollback already-working components

## Next Steps

### Immediate Actions (Start of Implementation)

1. **Confirm Decisions**:
   - [ ] User confirms hybrid approach
   - [ ] User confirms incremental rollout plan
   - [ ] User confirms 1.4.0 version bump

2. **Create Feature Branch**:
   ```bash
   git checkout -b feature/attune-discoverability-v1.4.0
   git push -u origin feature/attune-discoverability-v1.4.0
   ```

3. **Begin Phase 0**:
   ```bash
   mkdir -p plugins/attune/templates
   # Start TASK-002: Develop Skill Template
   ```

### Tracking Progress

Use this plan as checklist:
- Check off tasks as completed
- Update estimates if significantly off
- Document learnings in TEMPLATE-GUIDE.md
- Commit after each phase completion

### Communication

**Commit Messages**:
```
feat(attune): create discoverability templates [TASK-002]

- Add skill, command, and agent templates
- Document description formula: WHAT + WHEN + WHEN NOT
- Include token budget guidance and validation checklist

Ref: .claude/session-state.md
```

**PR Description Template**:
```markdown
## Summary

Implements superpowers-inspired discoverability patterns in attune plugin to improve automatic skill/command/agent matching.

## Changes

- Created discoverability templates for skills, commands, and agents
- Enhanced descriptions for 9 skills, 9 commands, 2 agents
- Added "When To Use" and "When NOT To Use" sections
- Updated README, CHANGELOG, and created ADR

## Testing

- ✅ All components pass abstract:validate-plugin
- ✅ Token budgets compliant (< 3000 chars total)
- ✅ Manual discovery testing: 6/7 correct (85%)
- ✅ No regressions in existing workflows

## References

- Brainstorm: `.claude/brainstorm-attune-discoverability.md`
- Patterns: `.claude/discoverability-patterns-summary.md`
- Spec Findings: `.claude/frontmatter-spec-findings.md`
- Implementation Plan: `docs/implementation-plan-attune-discoverability-v1.4.0.md`
```

## Questions for User

Before proceeding, please confirm:

1. **Hybrid Approach Approved?** Templates + incremental rollout?
2. **Timeline Acceptable?** ~29 hours over 4-5 days?
3. **Version Bump to 1.4.0?** Minor version for enhancements?
4. **Pilot Components Correct?** project-brainstorming, brainstorm cmd, project-architect agent?
5. **Any Additional Requirements?** Missing concerns or requirements?

---

**Status**: ✅ Plan Complete - Awaiting User Confirmation
**Next Action**: User approval → Execute TASK-000 (Create feature branch)
**Owner**: Attune plugin maintainer
**Tracking**: This document + git branch + PR workflow
