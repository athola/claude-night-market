# Attune Plugin Discoverability Enhancement - Brainstorming Session

**Date**: 2026-02-05
**Session ID**: attune-discoverability-2026-02-05
**Objective**: Improve skill/command/agent matching and context workflow integration based on superpowers patterns

## Research Summary

### Superpowers Plugin Patterns

Based on research of the [obra/superpowers project](https://github.com/obra/superpowers):

**Key Discovery Patterns**:

1. **Description First Approach**:
   - Lead with WHAT the skill/command does and WHY it's useful
   - Example: `"Guidance on when to ask clarifying questions vs proceed with standard approaches. Reduces interaction rounds while preventing wrong assumptions."`
   - Pattern: `"[Utility statement]. [Benefit statement]. Use when: [triggers]."`

2. **Trigger Keywords**:
   - Embedded directly in description frontmatter
   - Prefix: `"Use when: keyword1, keyword2, phrase1, phrase2"`
   - Covers: user language, technical terms, workflow phases
   - Example: `"Use when: question threshold, decisive, autonomous, clarifying questions"`

3. **When To Use / When NOT To Use**:
   - Explicit sections providing usage guidance
   - Prevents misapplication and improves precision
   - Example: "Use when claiming work is complete... Do not use when asking questions or for work clearly in-progress"

4. **Frontmatter Structure**:
   ```yaml
   ---
   name: skill-name
   description: '[What it does]. [Why useful]. Use when: [triggers].'
   category: workflow|code-quality|testing|etc
   tags: [relevant, keywords, for, taxonomy]
   complexity: low|intermediate|high
   estimated_tokens: 500
   ---
   ```

5. **Mandatory Usage Markers**:
   - Skills can declare themselves MANDATORY for certain contexts
   - Example: `"MANDATORY: This skill is required before any completion claim"`

### Current Attune Plugin State

**Strengths**:
- Strong content and methodology
- Well-structured skills and commands
- Clear workflow integration

**Opportunities**:
- Descriptions don't consistently lead with utility
- Trigger keywords missing or not in standard format
- "When to use" guidance sometimes buried in content
- Agent descriptions lack discoverability optimization

## Problem Statement

**Who**: Claude Code users and the AI agent itself
**What**: Skills, commands, and agents in the attune plugin are not consistently matched when relevant prompts or contexts occur
**Where**: During session workflow when user describes a task or linked skills invoke related capabilities
**Why**: Descriptions don't follow discovery-optimized patterns, lacking:
  - Utility-first descriptions
  - Explicit trigger keywords
  - Usage boundary guidance
**Current State**: Manual invocation required; auto-discovery unreliable

## Goals

1. **Increase Auto-Discovery**: Skills/commands/agents automatically matched to relevant user prompts
2. **Improve Context Matching**: Linked skills properly pull in related capabilities
3. **Reduce False Positives**: "When NOT to use" guidance prevents misapplication
4. **Standardize Format**: Consistent discoverability patterns across all components
5. **Maintain Compatibility**: Work within existing Claude Code and plugin ecosystem

## Success Criteria

- [ ] All skills have utility-first descriptions with trigger keywords
- [ ] All commands have "What This Does" and "When To Use" sections
- [ ] All agents have capability-focused descriptions with invocation keywords
- [ ] Reduced need for manual skill invocation (measurable via usage logs)
- [ ] No regression in existing functionality
- [ ] Documentation updated to reflect patterns

## Constraints

### Technical
- Must work with current Claude Code plugin system
- Must maintain backward compatibility with existing skill/command references
- Frontmatter schemas must follow plugin.json specifications
- Token budgets: Keep descriptions under 200 tokens, skills under 2000 tokens each

### Resources
- Single developer/maintainer context
- Changes should be incremental and testable
- Must not break existing attune workflows
- Documentation updates required

### Integration
- Must integrate with existing attune workflow (brainstorm → specify → plan → execute)
- Should complement superpowers integration patterns
- Must work with conserve plugin token optimization
- Should support abstract plugin validation

### Compliance
- Follow claude-night-market plugin standards
- Maintain ADR documentation pattern
- Update CHANGELOG with semantic versioning
- Test changes with abstract:validate-plugin

## Approach Generation

### Approach 1: Comprehensive Rewrite

**Description**: Systematically rewrite all skill/command/agent descriptions following superpowers patterns, update all frontmatter, add usage guidance sections.

**Stack**: Manual editing, abstract:validate-plugin for verification

**Pros**:
- Complete consistency across plugin
- Addresses all discoverability issues at once
- Creates clear before/after comparison
- Establishes gold standard for future additions

**Cons**:
- High time investment upfront
- Risk of introducing errors across many files
- Difficult to test incrementally
- May miss edge cases until full deployment

**Risks**:
- Breaking existing skill references (likelihood: medium)
- Token budget overruns in descriptions (likelihood: low)
- Regression in functionality (likelihood: low with validation)

**Effort**: XL (9+ skills, 9 commands, 2 agents, hooks, docs)

**Trade-offs**:
- Completeness vs. Time - Accepts longer timeline for thorough improvement
- Risk vs. Quality - Accepts testing burden for consistency

### Approach 2: Incremental Enhancement

**Description**: Prioritize high-value skills/commands, enhance iteratively, validate each batch, gather feedback before proceeding.

**Stack**: Phased rollout, abstract:skill-auditor for quality checks

**Pros**:
- Lower risk per iteration
- Faster initial value delivery
- Can pivot based on feedback
- Easier to roll back individual changes
- Testable with real usage patterns

**Cons**:
- Inconsistent experience during transition
- Requires multiple rounds of documentation updates
- May miss systemic issues until later phases
- Coordination overhead for related skills

**Risks**:
- Inconsistent patterns across phases (likelihood: medium)
- User confusion during transition (likelihood: low)
- Loss of momentum between phases (likelihood: medium)

**Effort**: M per phase (3-4 phases total)

**Trade-offs**:
- Consistency vs. Speed - Accepts temporary inconsistency for faster learning
- Completeness vs. Risk - Prioritizes safety over thoroughness

### Approach 3: Template-Driven Generation

**Description**: Create templates for skill/command/agent patterns, use abstract:create-* skills to generate enhanced versions, semi-automated migration.

**Stack**: Python scripts for bulk transformation, templates, validation tools

**Pros**:
- Faster execution through automation
- Enforces consistency via templates
- Reusable patterns for future additions
- Reduces manual editing errors
- Built-in validation in generation process

**Cons**:
- Upfront template development time
- May lose nuance in automated transformation
- Requires careful template design
- Testing overhead for generation logic
- May need manual touch-ups anyway

**Risks**:
- Template doesn't capture all cases (likelihood: high)
- Generated content lacks domain nuance (likelihood: medium)
- Over-standardization reduces clarity (likelihood: low)

**Effort**: L (template dev + generation + review)

**Trade-offs**:
- Automation vs. Quality - Accepts some loss of nuance for speed
- Consistency vs. Flexibility - Enforces patterns but limits customization

### Approach 4: Hybrid - Templates + Incremental

**Description**: Develop templates and patterns first, apply incrementally to high-priority components, validate and refine templates based on results, scale to remaining components.

**Stack**: Templates (reusable), phased rollout (safe), validation tools (quality)

**Pros**:
- Balances speed and quality
- Templates evolve based on real application
- Lower risk per iteration
- Reusable patterns for future work
- Can stop/pivot if approach isn't working

**Cons**:
- Requires two phases (template dev + application)
- Initial templates may need significant revision
- Longer total timeline than full automation
- Requires discipline to follow process

**Risks**:
- Template iteration extends timeline (likelihood: medium)
- Inconsistency between template versions (likelihood: low)
- Losing focus during multi-phase work (likelihood: low)

**Effort**: L total (M for templates, M for phased application)

**Trade-offs**:
- Speed vs. Quality - Balanced approach accepting moderate timeline
- Risk vs. Learning - Iterative learning reduces long-term risk

## War Room Deliberation (REQUIRED)

**Status**: 🔴 PENDING - Must convene War Room before approach selection

**Reversibility Assessment Required**:
- This decision affects ALL attune plugin components
- Changes impact discoverability patterns across claude-night-market ecosystem
- Template decisions create precedent for other plugins
- Potential to break existing workflows if done incorrectly

**War Room Trigger**: RS likely > 0.60 (Type 1.5 or Type 1 decision)

**Context for War Room**:
- 4 distinct approaches with different risk/reward profiles
- Decision creates patterns for 17 other plugins in ecosystem
- Trade-offs between consistency, speed, quality, and risk
- Impacts developer experience for all attune users

**Next Step**: Invoke `Skill(attune:war-room)` with full brainstorming context

---

## Draft Pattern Templates (Pre-War Room)

These templates are PRELIMINARY and subject to War Room review:

### Skill Description Pattern

```yaml
---
name: skill-name
description: '[Active verb] [what it does] [outcome/benefit]. Use when: [trigger1], [trigger2], [phrase describing when]. Do not use when: [boundary condition].'
category: workflow|methodology|code-quality|infrastructure
tags: [searchable, keywords]
complexity: low|intermediate|high
estimated_tokens: [estimate]
version: 1.3.9
---
```

**Example (project-brainstorming)**:
```yaml
description: 'Guide project ideation through Socratic questioning and structured exploration to create actionable project briefs. Use when: starting new projects, exploring problem spaces, comparing approaches, validating feasibility. Do not use when: requirements are already clear and documented.'
```

### Command Description Pattern

```markdown
---
name: command-name
description: [Active verb] [what it achieves] [how it helps users]
---

# Command Name

[One sentence: What this command does and why it's valuable]

## When To Use

- Starting [scenario 1]
- Need to [scenario 2]
- Before [scenario 3]

## When NOT To Use

- If [boundary 1]
- When [boundary 2]

## Usage

[Standard usage patterns]
```

### Agent Description Pattern

```yaml
---
name: agent-name
description: '[Role] - [primary capability] to [outcome]. Use when: [invocation context].'
model: claude-sonnet-4|claude-opus-4
tools_allowed: [relevant tools]
max_iterations: [appropriate limit]
---
```

**Example (project-architect)**:
```yaml
description: 'Architecture design specialist - analyzes requirements and generates system architecture with technology selection. Use when: planning system design, defining components, selecting technology stack, architectural decisions.'
```

## Component Inventory

### Skills (9 total)

| Skill | Priority | Current Description Quality | Enhancement Needed |
|-------|----------|----------------------------|-------------------|
| project-brainstorming | HIGH | Good, but lacks triggers | Add trigger keywords, "when not to use" |
| project-specification | HIGH | Generic | Utility-first rewrite, add triggers |
| project-planning | HIGH | Generic | Utility-first rewrite, add triggers |
| project-execution | HIGH | Generic | Utility-first rewrite, add triggers |
| war-room | HIGH | Complex, needs clarity | Simplify description, add clear triggers |
| makefile-generation | MEDIUM | Technical focus | Add utility statement, usage guidance |
| precommit-setup | MEDIUM | Technical focus | Add utility statement, usage guidance |
| workflow-setup | MEDIUM | Generic | Utility-first rewrite |
| war-room-checkpoint | MEDIUM | Specialized | Clear trigger conditions needed |

### Commands (9 total)

| Command | Priority | Current Description Quality | Enhancement Needed |
|---------|----------|----------------------------|-------------------|
| brainstorm | HIGH | Good structure | Add "When To Use" section upfront |
| specify | HIGH | Needs work | Add "What This Does" and "When To Use" |
| plan | HIGH | Needs work | Add "What This Does" and "When To Use" |
| execute | HIGH | Needs work | Add "What This Does" and "When To Use" |
| war-room | HIGH | Complex | Simplify, add clear invocation guidance |
| arch-init | MEDIUM | Technical | Add utility-first description |
| project-init | MEDIUM | Technical | Add utility-first description |
| validate | MEDIUM | Technical | Add utility-first description |
| upgrade-project | LOW | Technical | Add utility-first description |

### Agents (2 total)

| Agent | Priority | Current Description Quality | Enhancement Needed |
|-------|----------|----------------------------|-------------------|
| project-architect | HIGH | Descriptive but not utility-first | Add "Use when" triggers, capability focus |
| project-implementer | HIGH | Needs review | Add "Use when" triggers, capability focus |

### Hooks (0 in attune)

No hooks currently in attune plugin. Consider if any are needed for workflow automation.

## Implementation Checklist (Post-War Room)

### Phase 0: Preparation
- [ ] Convene War Room for approach selection
- [ ] Develop/refine templates based on War Room output
- [ ] Create validation criteria
- [ ] Set up testing methodology
- [ ] Create backup branch

### Phase 1: High-Priority Skills (If Incremental)
- [ ] project-brainstorming - Add triggers and boundaries
- [ ] project-specification - Utility-first rewrite
- [ ] project-planning - Utility-first rewrite
- [ ] project-execution - Utility-first rewrite
- [ ] war-room - Simplify and clarify

### Phase 2: High-Priority Commands
- [ ] brainstorm - Add "When To Use" section
- [ ] specify - Add utility sections
- [ ] plan - Add utility sections
- [ ] execute - Add utility sections
- [ ] war-room - Simplify invocation guidance

### Phase 3: Agents
- [ ] project-architect - Capability-focused description
- [ ] project-implementer - Capability-focused description

### Phase 4: Remaining Components
- [ ] Medium-priority skills
- [ ] Medium-priority commands
- [ ] Low-priority commands

### Phase 5: Documentation & Validation
- [ ] Update README with new patterns
- [ ] Update CHANGELOG
- [ ] Create ADR documenting pattern decisions
- [ ] Run abstract:validate-plugin
- [ ] Run abstract:skills-eval
- [ ] Update tutorial examples
- [ ] Test with conserve:context-report

## Red Flags To Surface

- ⚠️ **Token Budget Overruns**: Enhanced descriptions may push skills over token limits
- ⚠️ **Breaking Changes**: Renaming or restructuring may break existing references
- ⚠️ **Over-Standardization**: Templates may remove valuable nuance
- ⚠️ **Scope Creep**: Could expand to all 18 plugins (conserve scope to attune for now)
- ⚠️ **Testing Gaps**: Hard to validate auto-discovery without production usage
- ⚠️ **Documentation Drift**: Multiple files need updates for consistency

## Measuring Success

### Quantitative Metrics
- Skill auto-discovery rate (via logging if available)
- False positive invocation rate
- Token budget compliance (all descriptions < 200 tokens)
- Validation passing rate (abstract:validate-plugin, abstract:skills-eval)

### Qualitative Metrics
- User feedback on skill/command relevance
- Developer experience during manual testing
- Consistency score across components (subjective review)
- Clarity of "when to use" guidance (user comprehension)

## Next Steps

1. **🔴 MANDATORY**: Invoke `Skill(attune:war-room)` with this brainstorm context
2. **After War Room**: Select approach based on Supreme Commander synthesis
3. **Create ADR**: Document approach selection and rationale
4. **Execute Phase 0**: Set up templates and validation
5. **Begin Implementation**: Follow selected approach

## Related Patterns & Skills

- `Skill(superpowers:brainstorming)` - Socratic method applied here
- `Skill(abstract:validate-plugin)` - Validation tooling
- `Skill(abstract:skills-eval)` - Quality assessment
- `Skill(conserve:context-report)` - Token optimization
- `Skill(attune:war-room)` - **NEXT STEP** - Multi-LLM deliberation required

## Sources

- [GitHub - obra/superpowers](https://github.com/obra/superpowers)
- [GitHub - obra/superpowers-lab](https://github.com/obra/superpowers-lab)
- [GitHub - obra/superpowers-skills](https://github.com/obra/superpowers-skills)
- claude-night-market internal patterns and ADRs
- Superpowers integration guide: docs/guides/superpowers-integration.md

---

**Status**: ✅ Brainstorming Complete - Ready for War Room
**Deliverable**: This document serves as input to War Room deliberation
**Owner**: Attune plugin maintainer
**Next Review**: After War Room synthesis
