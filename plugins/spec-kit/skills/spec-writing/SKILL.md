---
name: spec-writing
description: Create clear, testable specifications from natural language descriptions. Focus on what users need and why, not implementation details.
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

Guides the creation of clear, complete, and testable specifications from natural language feature descriptions. Specifications focus on user value and business needs, avoiding implementation details.

## When to Use

- Creating new feature specifications
- Refining existing specifications
- Writing user stories and acceptance criteria
- Defining success criteria

## Core Principles

### Focus on What, Not How
- Describe user needs and business value
- Avoid technology choices and implementation details
- Write for business stakeholders, not developers

### Make It Testable
- Every requirement should be verifiable
- Use measurable criteria where possible
- Define clear acceptance scenarios

### Limit Clarifications
- Maximum 3 clarification markers per spec
- Make informed guesses using industry standards
- Document assumptions explicitly

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
- "API response time under 200ms" → Use: "Pages load in under 2 seconds"
- "Redis cache hit rate above 80%" → Use: "Frequently accessed data loads instantly"
- "React components render efficiently" → Use: "UI updates appear smooth with no visible lag"

**See**: `success-criteria-patterns` module for detailed examples and conversion process

## Related Skills

- `speckit-orchestrator`: Workflow coordination
- `task-planning`: Converting specs to tasks
