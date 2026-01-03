---
name: brainstorm
description: Brainstorm project ideas and requirements using Socratic questioning and ideation techniques
---

# Attune Brainstorm Command

Facilitate project ideation through Socratic questioning, constraint analysis, and creative exploration.

## Usage

```bash
# Start interactive brainstorming session
/attune:brainstorm

# Brainstorm with specific domain
/attune:brainstorm --domain "web application"

# Resume previous brainstorm
/attune:brainstorm --resume
```

## What This Command Does

1. **Invokes brainstorming skill** with superpowers integration
2. **Guides ideation** through Socratic questioning
3. **Explores constraints** and requirements
4. **Documents outcomes** in structured format
5. **Generates project brief** for planning phase

## Integration with Superpowers

When superpowers plugin is available:
- Uses `Skill(superpowers:brainstorming)` for Socratic method
- Leverages structured ideation frameworks
- Applies constraint-based thinking

Without superpowers:
- Falls back to attune's native brainstorming skill
- Provides similar guided questioning
- Documents ideas systematically

## Workflow

```bash
# 1. Invoke brainstorming skill
Skill(attune:project-brainstorming)

# 2. Guide through phases:
#    - Problem definition
#    - Constraint identification
#    - Solution exploration
#    - Approach comparison
#    - Decision documentation

# 3. Generate project brief
#    - Saved to docs/project-brief.md
#    - Includes problem, goals, constraints, approach

# 4. Transition to specification
#    Next: /attune:specify (use brief as input)
```

## Brainstorming Phases

### Phase 1: Problem Definition

**Questions**:
- What problem are we solving?
- Who experiences this problem?
- What is the current solution (if any)?
- What are the pain points?

**Output**: Problem statement document

### Phase 2: Constraint Identification

**Questions**:
- What are the technical constraints?
- What are the resource constraints (time, budget, team)?
- What are the regulatory/compliance requirements?
- What are the integration requirements?

**Output**: Constraints matrix

### Phase 3: Solution Exploration

**Techniques**:
- Multiple approach generation (3-5 approaches)
- Trade-off analysis for each approach
- Pros/cons documentation
- Risk assessment

**Output**: Approach comparison table

### Phase 4: Approach Selection

**Criteria**:
- Alignment with constraints
- Technical feasibility
- Resource efficiency
- Risk vs. reward
- Time to value

**Output**: Selected approach with rationale

### Phase 5: Brief Generation

**Sections**:
- Problem statement
- Goals and success criteria
- Constraints
- Selected approach
- Trade-offs and decisions
- Next steps

**Output**: `docs/project-brief.md`

## Arguments

- `--domain <domain>` - Project domain (web, cli, library, etc.)
- `--resume` - Resume previous brainstorm session
- `--output <path>` - Custom output path for brief (default: docs/project-brief.md)
- `--skip-superpowers` - Don't use superpowers integration

## Examples

### Example 1: Web Application Brainstorm

```bash
/attune:brainstorm --domain "web application"
```

**Session Flow**:
```
🧠 Brainstorming: Web Application Project

Problem Definition:
→ What specific problem does this web app solve?
  [User input: "Help developers track technical debt"]

→ Who are the primary users?
  [User input: "Development teams, tech leads"]

→ What do they currently use?
  [User input: "Spreadsheets, GitHub issues, nothing systematic"]

Constraints:
→ Must integrate with existing tools (GitHub, Jira)?
  [User input: "Yes, GitHub primarily"]

→ Team size and timeline?
  [User input: "2 developers, 3 months MVP"]

Approaches:
1. Standalone SaaS (Django + React)
2. GitHub App integration (GitHub API + webhooks)
3. CLI tool with web dashboard (FastAPI + Vue)

...
```

**Output**: `docs/project-brief.md`

```markdown
# Technical Debt Tracker - Project Brief

## Problem Statement
Development teams lack systematic tracking of technical debt...

## Goals
1. Centralize technical debt tracking
2. Integrate with GitHub issues
3. Provide prioritization framework

## Constraints
- 3-month timeline for MVP
- 2 developers
- Must integrate with GitHub
- No dedicated ops resources

## Selected Approach
**GitHub App integration** (Approach 2)

Rationale: Lowest friction for adoption...

## Trade-offs
- Pros: Native GitHub integration, automatic discovery
- Cons: Locked into GitHub ecosystem
```

### Example 2: Resume Previous Brainstorm

```bash
/attune:brainstorm --resume
```

Loads previous session state from `.attune/brainstorm-session.json`

## Output Format

### Project Brief Template

```markdown
# [Project Name] - Project Brief

## Problem Statement
[Clear description of the problem being solved]

## Goals
1. [Primary goal]
2. [Secondary goal]
...

## Success Criteria
- [ ] [Measurable success criterion]
- [ ] [Measurable success criterion]
...

## Constraints
- **Technical**: [Technical constraints]
- **Resources**: [Time, budget, team]
- **Compliance**: [Regulatory requirements]
- **Integration**: [System dependencies]

## Approach Comparison

### Approach 1: [Name]
**Pros**: ...
**Cons**: ...
**Risk**: ...

### Approach 2: [Name] ⭐ SELECTED
**Pros**: ...
**Cons**: ...
**Risk**: ...

## Rationale for Selection
[Explanation of why this approach was chosen]

## Trade-offs Accepted
- [Trade-off 1 with mitigation]
- [Trade-off 2 with mitigation]

## Out of Scope
- [Explicitly excluded feature]
- [Deferred capability]

## Next Steps
1. /attune:specify - Create detailed specification
2. /attune:plan - Plan architecture and implementation
3. /attune:init - Initialize project structure
```

## Session State

Brainstorm sessions are saved to `.attune/brainstorm-session.json`:

```json
{
  "session_id": "20260102-143022",
  "phase": "approach-selection",
  "problem": "...",
  "constraints": [...],
  "approaches": [...],
  "decisions": {},
  "timestamp": "2026-01-02T14:30:22Z"
}
```

## Integration with Full Cycle

```
/attune:brainstorm    ← You are here
      ↓
/attune:specify       ← Define requirements
      ↓
/attune:plan          ← Plan architecture
      ↓
/attune:init          ← Initialize project
      ↓
/attune:execute       ← Implement systematically
```

## Related Commands

- `/attune:specify` - Create detailed specification from brief
- `/attune:plan` - Plan project architecture
- `/imbue:feature-review` - Review feature worthiness

## Related Skills

- `Skill(attune:project-brainstorming)` - Brainstorming methodology
- `Skill(superpowers:brainstorming)` - Socratic questioning (if available)
- `Skill(imbue:scope-guard)` - Anti-overengineering checks

## Superpowers Integration

When superpowers is installed, this command automatically:
- Invokes `Skill(superpowers:brainstorming)` for questioning framework
- Applies structured ideation patterns
- Uses decision documentation templates

Check if superpowers is available:
```bash
/plugin list | grep superpowers
```

Install superpowers:
```bash
/plugin marketplace add obra/superpowers
/plugin install superpowers@superpowers-marketplace
```
