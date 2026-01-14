---
name: spec-writing
description: |

Triggers: specification, user-stories, requirements, speckit, acceptance-criteria
  Create clear, testable specifications with user stories and acceptance criteria.

  Triggers: spec writing, feature specification, requirements, user stories
  Use when: creating new specifications or writing acceptance criteria
  DO NOT use when: generating implementation tasks - use task-planning.
category: specification
tags: [speckit, specification, requirements, user-stories, acceptance-criteria]
dependencies:
  - spec-kit:shared
  - superpowers:brainstorming
tools: []
usage_patterns:
  - feature-specification
  - requirements-documentation
  - user-story-creation
complexity: intermediate
estimated_tokens: 1200
progressive_loading: true
modules:
  - success-criteria-patterns
  - specification-structure
---

# Spec Writing

## Overview

Create clear, complete, and testable specifications from natural language feature descriptions. Specifications focus on user value and business needs, avoiding implementation details.

## When to Use

- Creating new feature specifications
- Refining existing specifications
- Writing user stories and acceptance criteria
- Defining success criteria

## Core Principles

The spec writing process is guided by several core principles to ensure high-quality documentation. We focus on describing what the system must do for the user rather than how it should be implemented, which involves avoiding specific technology choices in the requirement definition. Every requirement must be testable and verifiable, using measurable criteria and clear acceptance scenarios wherever possible. To maintain momentum, we limit the number of clarification markers per specification and instead make informed assumptions based on industry standards, ensuring that all such assumptions are explicitly documented.

## Specification Structure

### Mandatory Sections
1. **Overview/Context**: What problem does this solve?
2. **User Scenarios**: Who uses it and how?
3. **Functional Requirements**: What must it do?
4. **Success Criteria**: How do we know it works?

### Optional Sections
- Non-Functional Requirements (when performance/security critical)
- Edge Cases (when special handling needed)
- Dependencies (when external systems involved)
- Assumptions (when decisions made with incomplete info)

**See**: `specification-structure` module for detailed templates and guidelines

## Quality Checklist

- [ ] No implementation details present
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] User scenarios cover primary flows
- [ ] Edge cases identified
- [ ] Scope clearly bounded

## Success Criteria Quick Reference

### Good (User-focused, Measurable, Technology-agnostic)
- "Users complete checkout in under 3 minutes"
- "System supports 10,000 concurrent users"
- "95% of searches return results in under 1 second"

### Bad (Implementation-focused, Internal metrics)
- "API response time under 200ms" -> Use: "Pages load in under 2 seconds"
- "Redis cache hit rate above 80%" -> Use: "Frequently accessed data loads with no noticeable delay"
- "React components render efficiently" -> Use: "UI updates appear with no visible frame drops"

**See**: `success-criteria-patterns` module for detailed examples and conversion process

## Related Skills

- `speckit-orchestrator`: Workflow coordination
- `task-planning`: Converting specs to tasks
## Troubleshooting

### Common Issues

**Command not found**
Ensure all dependencies are installed and in PATH

**Permission errors**
Check file permissions and run with appropriate privileges

**Unexpected behavior**
Enable verbose logging with `--verbose` flag
