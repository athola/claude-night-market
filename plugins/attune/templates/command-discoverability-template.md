# Command Discoverability Template

Commands are action-oriented - focus on tangible outputs and workflow position.

## Frontmatter Pattern

```yaml
---
name: command-name
description: [Action verb] [tangible outcome] using [method] - concise, 50-100 chars
---
```

## Description Formula

```
[Imperative verb] [specific deliverable] [key differentiator/method]
```

**Target**: 50-100 characters (max 150)

**Examples**:
- "Generate implementation plan with architecture design and dependency-ordered tasks from specification"
- "Execute implementation plan systematically with progress tracking and checkpoint validation"
- "Guide project ideation through structured Socratic questioning to generate actionable project briefs"

## Content Structure

```markdown
# Command Title

[One sentence: What this command produces and its value]

## When To Use

Use this command when you need to:
- [Specific use case 1]
- [Specific use case 2]
- [Workflow stage 3]

## When NOT To Use

Avoid this command if:
- [Boundary condition 1]
- [Alternative is better for scenario X]

## What This Command Does

1. **[Key action 1]** - [Brief explanation]
2. **[Key action 2]** - [Brief explanation]
3. **[Key output]** - [What user gets]

## Usage

[Standard usage patterns, examples, workflow integration]
```

## Example: brainstorm Command

```yaml
---
name: brainstorm
description: Guide project ideation through structured Socratic questioning to generate actionable project briefs with approach comparisons
---

# Attune Brainstorm Command

Transform vague project ideas into structured briefs with validated approaches.

## When To Use

Use this command when you need to:
- Start a new project without clear requirements
- Explore and compare multiple technical approaches
- Validate project feasibility before committing resources
- Document decision rationale for stakeholders

## When NOT To Use

Avoid this command if:
- Requirements and specification already exist (use /attune:plan instead)
- Refining existing specs (use /attune:specify instead)
- Project scope is well-defined (jump to /attune:project-init)

## What This Command Does

1. **Problem Definition** - Socratic questioning to clarify core problem
2. **Constraint Discovery** - Identify technical, resource, compliance limits
3. **Approach Generation** - Create 3-5 distinct solution approaches
4. **War Room Deliberation** - Multi-LLM expert pressure-testing
5. **Decision Documentation** - Generate project brief with rationale
```

## Validation Checklist

- [ ] Description 50-100 chars (max 150)
- [ ] Action-oriented (starts with verb)
- [ ] Workflow position clear
- [ ] Links to related commands
- [ ] "When To Use" and "When NOT To Use" sections present
- [ ] Output/deliverable explicit

---

**See Also**: `skill-discoverability-template.md` for patterns
