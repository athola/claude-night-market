# Agent Discoverability Template

Agents = specialized roles. Focus on capabilities and delegation context.

## Pattern

```yaml
---
name: agent-name
description: "[Role] - [capability] to achieve [outcome]. Use when: [context], [decision type]."
# model and effort are read by Claude Code to select the subagent's
# model; the rest is custom metadata not used for matching. Pin a tier
# alias, never a dated ID: an agent that omits model inherits the
# session's, and a dated ID is retired on a rolling basis.
model: sonnet
effort: medium
tools_allowed: [Read, Write, Grep, Glob]
max_iterations: 10
category: agent
tags: [relevant, keywords]
complexity: intermediate
---
```

**CRITICAL**: Always quote the description field (contains colons).

```markdown
# Agent Title

[Expertise statement]

## Capabilities
- **[Skill 1]**: [What it does]
- **[Skill 2]**: [What it does]

## When To Invoke

Delegate when:
- [Scenario 1]
- [Scenario 2]
```

## Example

```yaml
---
name: project-architect
description: Architecture design specialist - analyzes requirements and generates component-based system architecture with technology selection. Use when: designing system architecture, defining components, selecting technology stack, making architectural decisions.
model: sonnet
effort: medium
tools_allowed: [Read, Write, Grep, Glob]
max_iterations: 10
---
```

**Target**: 75-125 chars (max 175)
