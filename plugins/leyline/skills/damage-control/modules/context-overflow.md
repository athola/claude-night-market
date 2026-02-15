---
name: context-overflow
description: Detection signals, graceful handoff protocol, and progressive context shedding for agent context window exhaustion
parent_skill: leyline:damage-control
category: infrastructure
estimated_tokens: 250
---

# Context Overflow Handling

## Detection Signals

Context overflow may not produce explicit errors. Watch for these signals:

| Signal | Confidence | Detection Method |
|--------|-----------|------------------|
| Response truncation | High | Output ends mid-sentence or mid-code |
| Degraded reasoning | Medium | Agent repeats earlier mistakes, loses track of plan |
| Instruction amnesia | Medium | Agent ignores established conventions or skips steps |
| Hallucinated file paths | High | Agent references files that don't exist |
| Increased latency | Low | Response time grows significantly |

**Automated detection:**
- Monitor response length trends (sudden drops suggest truncation)
- Track task completion quality (declining quality signals degraded reasoning)
- Watch for repeated errors on previously-resolved issues

## Graceful Handoff Protocol

When context overflow is detected, execute a structured handoff:

### Step 1: Summarize Current State

The overflowing agent produces a handoff summary:

```markdown
## Handoff Summary

### Completed Work
- [List of completed tasks with commit hashes]

### Current Task
- Task ID: T005
- Progress: 70% complete
- Last action: Implemented validation layer
- Next action: Write integration tests
- Key decisions made: [list]

### Important Context
- [Architecture decisions relevant to remaining work]
- [Gotchas or edge cases discovered]
- [File paths and line numbers for in-progress changes]

### Remaining Tasks
- [Ordered list of uncompleted tasks]
```

### Step 2: Create Continuation Task

```json
{
  "subject": "Continue: [original task subject]",
  "description": "[Handoff summary from Step 1]",
  "metadata": {
    "continuation_of": "T005",
    "handoff_reason": "context_overflow",
    "handoff_agent": "backend@my-team",
    "handoff_at": "2026-02-07T23:00:00Z"
  }
}
```

### Step 3: Transfer to Fresh Agent

Lead assigns continuation task to:
1. Same agent after context clear (preferred if agent type matches)
2. New agent with appropriate role and tools

References `conserve:clear-context` for context window management patterns.

## Progressive Context Shedding

When approaching context limits, shed context in priority order (least important first):

```
Priority (drop first → last):
1. Historical message exchanges (keep summaries only)
2. Completed task details (keep outcomes, drop process)
3. File contents already committed (re-read from disk if needed)
4. Module documentation (re-load specific modules on demand)
5. Current task context (NEVER drop — this is the active work)
```

**Implementation:**
- Use `progressive_loading: true` in skill frontmatter to load modules on demand
- Summarize completed work into task metadata checkpoints
- Prefer re-reading files over keeping file content in context
- Drop verbose error output after extracting actionable information

## Prevention

- Set appropriate `max_iterations` on agent definitions
- Use focused skill modules instead of loading entire skill trees
- Checkpoint frequently to enable recovery from any point
- Prefer multiple focused agents over one agent doing everything
