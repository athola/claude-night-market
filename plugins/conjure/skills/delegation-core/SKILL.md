---
name: delegation-core
description: Framework for delegating tasks to external LLM services, with a focus on strategic oversight and quality control. Uses leyline infrastructure for quota, logging, and error handling.
category: delegation-framework
tags: [delegation, external-llm, gemini, qwen, task-management, quality-control]
dependencies:
  - leyline:quota-management
  - leyline:usage-logging
  - leyline:service-registry
  - leyline:error-patterns
  - leyline:authentication-patterns
tools: [delegation-executor]
usage_patterns:
  - task-assessment
  - delegation-planning
  - quality-validation
  - integration-workflows
complexity: intermediate
estimated_tokens: 250
progressive_loading: true
modules:
  - modules/task-assessment.md
  - modules/cost-estimation.md
  - modules/handoff-patterns.md
  - modules/troubleshooting.md
references:
  - leyline/skills/quota-management/SKILL.md
  - leyline/skills/usage-logging/SKILL.md
  - leyline/skills/error-patterns/SKILL.md
  - leyline/skills/authentication-patterns/SKILL.md
  - leyline/skills/service-registry/SKILL.md
---

# Delegation Core Framework

## Overview

A structured method for deciding when, what, and how to delegate tasks to external LLM services (Gemini, Qwen, local models, etc.). This approach helps maintain quality control and strategic oversight. The core principle: **delegate execution, retain Claude's intelligence**.

## When to Use
- Before invoking any external LLM for task assistance
- When operations are token-heavy and exceed local context limits
- When batch processing benefits from different model characteristics
- When tasks require routing between models

## Philosophy

**Delegate execution, retain intelligence:**
- **Claude handles**: Architecture, strategy, design decisions, complex reasoning, quality review
- **External LLMs perform**: Data processing, pattern extraction, bulk operations, summarization

## Delegation Flow

1. **Task Assessment** - Classify task by intelligence level and context size
2. **Suitability Evaluation** - Check prerequisites and service fit
3. **Handoff Planning** - Formulate request and document plan
4. **Execution & Integration** - Run delegation, validate, and integrate results

## Quick Decision Matrix

| Intelligence | Context | Recommendation |
|-------------|---------|----------------|
| High | Any | Keep local |
| Low | Large | Delegate |
| Low | Small | Either |

**High Intelligence**: Architecture, design decisions, trade-offs, strategic recommendations, nuanced review, creative problem solving

**Low Intelligence**: Pattern counting, bulk extraction, boilerplate generation, summarization, repetitive transformations

## Detailed Workflow Steps

### 1. Task Assessment (`delegation-core:task-assessed`)

Classify your task using intelligence level and context requirements:
- See `modules/task-assessment.md` for detailed classification criteria
- Use token estimates to determine delegation thresholds
- Apply the decision matrix to determine recommendation

**Exit Criteria**: Task classified with intelligence level, context size, and delegation recommendation

### 2. Suitability Evaluation (`delegation-core:delegation-suitability`)

Verify prerequisites and service fit:
- See `modules/handoff-patterns.md` for prerequisite checklist
- Evaluate cost-benefit ratio using `modules/cost-estimation.md`
- Check for red flags (security, real-time iteration, complex reasoning)

**Exit Criteria**: Service authenticated, quotas verified, cost justified, no red flags

### 3. Handoff Planning (`delegation-core:handoff-planned`)

Create a concrete delegation plan:
- See `modules/handoff-patterns.md` for request formulation template
- Document service, command, input context, expected output
- Define validation method and contingency plan

**Exit Criteria**: Complete delegation plan documented

### 4. Execution & Integration (`delegation-core:results-integrated`)

Execute and validate results:
- Run delegation and capture full output
- Validate format, plausibility, and correctness
- Integrate only after validation passes
- Log usage and lessons learned

**Exit Criteria**: Results validated and integrated, usage logged

## Leyline Infrastructure

Conjure uses **leyline** for shared infrastructure patterns:

| Leyline Skill | Used For |
|---------------|----------|
| `quota-management` | Track service quotas, thresholds, estimation |
| `usage-logging` | Session-aware audit trails, cost tracking |
| `service-registry` | Unified service configuration and execution |
| `error-patterns` | Consistent error handling and recovery |
| `authentication-patterns` | Auth verification across services |

See `modules/cost-estimation.md` for leyline integration examples.

## Service-Specific Skills

For detailed service workflows:
- `Skill(conjure:gemini-delegation)` - Gemini CLI specifics
- `Skill(conjure:qwen-delegation)` - Qwen MCP specifics

## Module Reference

- **task-assessment.md**: Intelligence classification, decision matrix, token estimates
- **cost-estimation.md**: Pricing, budgets, optimization strategies, cost tracking
- **handoff-patterns.md**: Request templates, collaborative workflows, anti-patterns
- **troubleshooting.md**: Common problems, quality control, service failures

## Exit Criteria

- [ ] Task assessed and classified correctly
- [ ] Delegation decision justified with clear rationale
- [ ] Results validated before integration
- [ ] Lessons captured for future delegations
