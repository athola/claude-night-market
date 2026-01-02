---
name: delegation-core
description: |
  Delegate tasks to external LLM services (Gemini, Qwen) with quota, logging, and error handling.

  Triggers: delegate task, external LLM, gemini, qwen, large context, offload
  Use when: tasks exceed context window or need cheaper processing
  DO NOT use when: task requires Claude's reasoning.
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

A method for deciding when and how to delegate tasks to external LLM services. The core principle: **delegate execution, retain high-level reasoning**.

## When to Use
- Before invoking any external LLM for task assistance.
- When operations are token-heavy and exceed local context limits.
- When batch processing benefits from different model characteristics.
- When tasks require routing between models.

## Philosophy

**Delegate execution, retain reasoning:**
- **Claude handles**: Architecture, strategy, design, and review.
- **External LLMs perform**: Data processing, pattern extraction, bulk operations, summarization.

## Delegation Flow

1. **Task Assessment**: Classify task by complexity and context size.
2. **Suitability Evaluation**: Check prerequisites and service fit.
3. **Handoff Planning**: Formulate request and document plan.
4. **Execution & Integration**: Run delegation, validate, and integrate results.

## Quick Decision Matrix

| Complexity | Context | Recommendation |
|------------|---------|----------------|
| High | Any | Keep local |
| Low | Large | Delegate |
| Low | Small | Either |

**High Complexity**: Architecture, design decisions, trade-offs, creative problem solving.

**Low Complexity**: Pattern counting, bulk extraction, boilerplate generation, summarization.

## Detailed Workflow Steps

### 1. Task Assessment (`delegation-core:task-assessed`)

Classify your task:
- See `modules/task-assessment.md` for classification criteria.
- Use token estimates to determine thresholds.
- Apply the decision matrix.

**Exit Criteria**: Task classified with complexity level, context size, and delegation recommendation.

### 2. Suitability Evaluation (`delegation-core:delegation-suitability`)

Verify prerequisites:
- See `modules/handoff-patterns.md` for checklist.
- Evaluate cost-benefit ratio using `modules/cost-estimation.md`.
- Check for red flags (security, real-time iteration).

**Exit Criteria**: Service authenticated, quotas verified, cost justified.

### 3. Handoff Planning (`delegation-core:handoff-planned`)

Create a delegation plan:
- See `modules/handoff-patterns.md` for request template.
- Document service, command, input context, expected output.
- Define validation method.

**Exit Criteria**: Delegation plan documented.

### 4. Execution & Integration (`delegation-core:results-integrated`)

Execute and validate results:
- Run delegation and capture output.
- Validate format and correctness.
- Integrate only after validation passes.
- Log usage.

**Exit Criteria**: Results validated and integrated, usage logged.

## Leyline Infrastructure

Conjure uses **leyline** for shared infrastructure:

| Leyline Skill | Used For |
|---------------|----------|
| `quota-management` | Track service quotas and thresholds. |
| `usage-logging` | Session-aware audit trails. |
| `service-registry` | Unified service configuration. |
| `error-patterns` | Consistent error handling. |
| `authentication-patterns` | Auth verification. |

See `modules/cost-estimation.md` for leyline integration examples.

## Service-Specific Skills

For detailed service workflows:
- `Skill(conjure:gemini-delegation)`: Gemini CLI specifics.
- `Skill(conjure:qwen-delegation)`: Qwen MCP specifics.

## Module Reference

- **task-assessment.md**: Complexity classification, decision matrix.
- **cost-estimation.md**: Pricing, budgets, cost tracking.
- **handoff-patterns.md**: Request templates, workflows.
- **troubleshooting.md**: Common problems, service failures.

## Exit Criteria

- [ ] Task assessed and classified.
- [ ] Delegation decision justified.
- [ ] Results validated before integration.
- [ ] Lessons captured.
