---
name: damage-control
description: 'Agent-level error recovery patterns for multi-agent coordination. Maps
  service-level error categories to agent-level equivalents and defines escalation
  ladders for crash recovery, context overflow, merge conflicts, and partial failures.'
category: infrastructure
tags:
- damage-control
- agent-recovery
- error-handling
- resilience
- multi-agent
dependencies:
- error-patterns
provides:
  infrastructure:
  - agent-crash-recovery
  - context-overflow-handling
  - merge-conflict-resolution
  - partial-failure-handling
  patterns:
  - escalation-ladder
  - replace-dont-wait
  - graceful-handoff
usage_patterns:
- agent-recovery
- multi-agent-resilience
- error-escalation
complexity: intermediate
estimated_tokens: 500
progressive_loading: true
modules:
- modules/agent-crash-recovery.md
- modules/context-overflow.md
- modules/merge-conflict-resolution.md
- modules/partial-failure-handling.md
---
## Table of Contents

- [Overview](#overview)
- [When to Use](#when-to-use)
- [Error Categories](#error-categories)
- [Escalation Ladder](#escalation-ladder)
- [Quick Reference](#quick-reference)
- [Module Reference](#module-reference)
- [Integration Pattern](#integration-pattern)
- [Exit Criteria](#exit-criteria)


# Damage Control

## Overview

Adapts service-level error patterns from `leyline:error-patterns` to agent-level recovery in multi-agent coordination scenarios. Provides structured playbooks for the four most common agent failure modes.

## When To Use

- Multi-agent coordination encounters agent failures
- Context windows overflow during complex tasks
- Merge conflicts arise from parallel agent work
- Partial failures need triage and salvage
- Orchestrators need standardized recovery procedures

## When NOT To Use

- Single-agent work (use `leyline:error-patterns` directly)
- Service-level errors without agent coordination (API failures, rate limits)
- Simple retry scenarios handled by existing error patterns

## Error Categories

Agent-level error categories extend the service-level taxonomy from `leyline:error-patterns`:

| Agent Category | Service Equivalent | Severity | Recovery |
|----------------|-------------------|----------|----------|
| **AGENT_CRASH** | PERMANENT | Critical | Replace agent, reassign tasks |
| **CONTEXT_OVERFLOW** | RESOURCE | Error | Graceful handoff, context shed |
| **MERGE_CONFLICT** | TRANSIENT | Warning | Stop, resolve, resume |
| **PARTIAL_FAILURE** | Mixed | Varies | Triage by sub-category |

## Escalation Ladder

Three-tier escalation with clear handoff points:

```
Tier 1: Agent Self-Recovery
  Agent detects issue, attempts automated recovery
  (retry, context shed, conflict resolution)
        |
        | Fails after 2 attempts
        v
Tier 2: Lead Agent Intervention
  Lead reassigns tasks, spawns replacement agents,
  coordinates resolution across team
        |
        | Cannot resolve or CRITICAL severity
        v
Tier 3: Human Escalation
  Human notified with full context, recommended actions,
  and current state summary
```

## Quick Reference

| Scenario | Module | First Action |
|----------|--------|--------------|
| Agent stops responding | `agent-crash-recovery` | Check heartbeat, reassign tasks |
| Response truncation | `context-overflow` | Summarize state, create continuation |
| File conflicts after parallel work | `merge-conflict-resolution` | Stop agents, lead resolves |
| Some tasks fail, others succeed | `partial-failure-handling` | Triage by error category |

## Module Reference

- **agent-crash-recovery.md**: Orphaned task detection, "replace don't wait" doctrine, state recovery
- **context-overflow.md**: Detection signals, graceful handoff, progressive context shedding
- **merge-conflict-resolution.md**: Post-execution conflict detection, resolution protocol, prevention
- **partial-failure-handling.md**: Error triage, per-category recovery, salvage protocol

## Integration Pattern

```yaml
# In your skill's frontmatter
dependencies: [leyline:damage-control]
```

Consumers should reference specific modules for targeted recovery:

```markdown
# In orchestrator or coordination skill
On agent crash: follow `leyline:damage-control/modules/agent-crash-recovery.md`
On context overflow: follow `leyline:damage-control/modules/context-overflow.md`
```

## Exit Criteria

- Failed agent identified and replaced (or escalated)
- Orphaned tasks reassigned to healthy agents
- Successful work preserved and committed
- Recovery actions logged for post-mortem
