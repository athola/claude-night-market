---
name: delegation-core
description: Delegates execution to eight CLIs (Gemini, Qwen, MiniMax, GLM, Muse, Codex, OpenCode, Glimmer). Use for execution tasks. Do not use for secrets.
alwaysApply: false
category: delegation-framework
tags:
- delegation
- external-llm
- gemini
- qwen
- minimax
- glm
- muse
- codex
- opencode
- task-management
- quality-control
dependencies:
- leyline:quota-management
- leyline:usage-logging
- leyline:service-registry
- leyline:error-patterns
- leyline:authentication-patterns
tools: []
usage_patterns:
- task-assessment
- delegation-planning
- quality-validation
- integration-workflows
complexity: intermediate
model_hint: standard
estimated_tokens: 600
progressive_loading: true
modules:
- modules/provider-onboarding.md
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
- references/execution-modes.md
---

# Delegation Core Framework

## Overview

A method for deciding when and how to delegate tasks to external LLM services. Core principle: **delegate execution, retain high-level reasoning**.

## Default Posture

**Delegation is on. Declining it is the step that takes a decision.**

Any conjure operation, mission phase, or workflow that reaches eligible
work delegates it without being asked.
Eligible means the work is execution rather than reasoning, which the
philosophy below defines and `modules/task-assessment.md` classifies.
An operator who wants delegation off says so once, in one of the two
places under Declining Delegation.

This inverts the earlier framing, which listed the occasions on which to
delegate and so made delegation something a caller had to remember.
The occasions were correct and are now the exception list instead.

## Keep Local

Delegation stops at the boundary the philosophy draws.
Keep the work local when any of these hold:

- The task is reasoning: architecture, design, trade-offs, judgment.
- The prompt or context carries a secret, a credential, or data that
  should not leave the machine.
- The task needs iteration with the operator turn by turn.
- Correctness cannot be validated after the fact.

The first is the standing exception and covers most of what Claude does.
The rest are the red flags `modules/task-assessment.md` already lists.

## Declining Delegation

Two switches, environment over file.

| Scope | How | Effect |
|-------|-----|--------|
| One run | `CONJURE_DELEGATION=off` | No provider is probed or spawned |
| One machine | `"enabled": false` in `~/.claude/hooks/delegation/config.json` | Same, until the key changes |

`CONJURE_DELEGATION` accepts `off`, `0`, `false`, `no` and their
opposites, in any case.
Setting it to an on spelling re-enables delegation that the config file
turned off, so the narrower scope wins.
A disabled delegator returns a result whose `fallback_reason` is
`delegation_disabled` and spawns nothing, so opting out costs nothing.

## When No Provider Answers

`smart_delegate` works down the registry order and returns the first
real answer.
A provider that is missing, unauthenticated, failing, or answering with
an empty stdout is recorded and the chain moves on.

When it reaches the end, it returns a result with
`fallback_reason` set to `providers_exhausted` and an `attempts` trail
naming what each provider did.
**That result is the instruction to do the work locally.** Read it, say
which providers were tried and why none answered, and then do the task
yourself.
Do not treat it as an error to report and stop on: a machine with no CLI
installed is the ordinary case for this default, not a fault.

When the operator wants providers answering rather than falling back,
`modules/provider-onboarding.md` carries the per-provider steps and the
failure shapes that do not look like authentication problems.
Start with `make -C plugins/conjure delegate-doctor`.

## Philosophy

**Delegate execution, retain reasoning.** Claude handles architecture, strategy, design, and review. External LLMs perform data processing, pattern extraction, bulk operations, and summarization.

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

Classify the task:
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

## MCP Authentication

### OAuth Client Credentials (Claude Code 2.1.30+)

For MCP servers that don't support Dynamic Client Registration (e.g., Slack), pre-configured OAuth client credentials can be provided:

```bash
claude mcp add <server-name> --client-id <id> --client-secret <secret>
```

This enables delegation workflows through MCP servers that require pre-configured OAuth, expanding the range of external services available for task delegation.

### Claude.ai MCP Connectors (Claude Code 2.1.46+)

As an alternative to manual OAuth setup, users can configure MCP servers directly in claude.ai at claude.ai/settings/connectors. These connectors are automatically available in Claude Code when logged in with a claude.ai account: no `claude mcp add` or credential management required. This provides a browser-based auth flow that may be simpler for services with complex OAuth requirements.

## Worktree Isolation for File-Modifying Delegations (Claude Code 2.1.49+)

When delegating tasks that modify files to subagents, use `isolation: worktree` in the agent frontmatter to run each agent in a temporary git worktree. This prevents file conflicts when multiple delegated agents operate in parallel on overlapping paths. The worktree is auto-cleaned if no changes are made; preserved with commits if the agent produces changes.

```yaml
# Agent frontmatter for isolated delegation
isolation: worktree
```

## Leyline Infrastructure

Conjure uses leyline infrastructure:

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
- `Skill(conjure:minimax-delegation)`: MiniMax CLI specifics.
- `Skill(conjure:glm-delegation)`: GLM via the Z.ai endpoint swap.
- `Skill(conjure:muse-delegation)`: Meta Muse Code CLI specifics.
- `Skill(conjure:codex-delegation)`: OpenAI Codex CLI specifics.
- `Skill(conjure:opencode-delegation)`: OpenCode CLI specifics.

## Execution Modes

When delegating to multiple agents, choose the appropriate
execution mode:

| Mode | When to Use | How It Works |
|------|-------------|--------------|
| single-session | Sequential tasks, same-file edits | Claude works through tasks in order |
| subagents | Parallel independent tasks | Agents work independently, report back |
| agent-team | Parallel coordinated tasks | Agents can communicate with each other |

See `references/execution-modes.md` for the selection decision
matrix, mode compatibility notes, and anti-patterns to avoid.

## Module Reference

- **provider-onboarding.md**: Install and auth per provider, and how
  to read a half-configured one.
- **task-assessment.md**: Complexity classification, decision matrix.
- **cost-estimation.md**: Pricing, budgets, cost tracking.
- **handoff-patterns.md**: Request templates, workflows.
- **troubleshooting.md**: Common problems, service failures.

## Exit Criteria

- [ ] Task assessed and classified.
- [ ] Work that stayed local names which Keep Local clause held it.
- [ ] A `providers_exhausted` result was reported with its attempts
      trail and then completed locally, not abandoned.
- [ ] Results validated before integration.
- [ ] Lessons captured.
