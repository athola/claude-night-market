---
name: partial-failure-handling
description: Triage failed tasks by error category, per-category recovery strategies, and salvage protocol for preserving successful work
parent_skill: leyline:damage-control
category: infrastructure
estimated_tokens: 250
---

# Partial Failure Handling

## Overview

When a multi-agent execution completes with mixed results (some tasks succeed, some fail), use this module to triage failures, recover where possible, and salvage successful work.

## Triage Failed Tasks

Classify each failed task by error category to determine the appropriate recovery:

| Error Category | Signal | Recovery | Example |
|---------------|--------|----------|---------|
| **TRANSIENT** | Timeout, rate limit, flaky test | Retry (up to 2x) | API timeout during test |
| **CRASH** | Agent unresponsive, pane dead | Reassign to new agent | Agent ran out of context |
| **PERMANENT** | Logic error, missing dependency | Escalate to lead/human | Required API doesn't exist |
| **CONFLICT** | Merge conflict, semantic clash | Resolve then retry | Two agents edited same file |

### Triage Protocol

```
For each failed task:
  1. Read error output / agent's last messages
  2. Classify error category (TRANSIENT/CRASH/PERMANENT/CONFLICT)
  3. Check retry count (max 2 for TRANSIENT, max 1 for CRASH)
  4. Route to appropriate recovery strategy
  5. If unrecoverable, mark as BLOCKED with reason
```

## Per-Category Recovery

### TRANSIENT Recovery

```
Attempt 1: Retry immediately
Attempt 2: Retry with increased timeout / reduced scope
Attempt 3: ESCALATE — reclassify as PERMANENT
```

- Increase timeouts by 2x on retry
- If rate-limited, wait for `retry_after` header
- If flaky test, isolate and run individually

### CRASH Recovery

```
Attempt 1: Spawn new agent, assign task with checkpoint context
Attempt 2: Spawn new agent with simplified task scope
Attempt 3: ESCALATE — human intervention required
```

- Follow `agent-crash-recovery.md` for full protocol
- Transfer task metadata checkpoints to new agent
- Consider splitting task into smaller subtasks

### PERMANENT Recovery

Permanent failures cannot be retried without changes:

1. **Document the failure**: Error message, root cause hypothesis, affected dependencies
2. **Assess blast radius**: Which other tasks depend on this one?
3. **Propose alternatives**: Can the task be achieved differently?
4. **Escalate**: Present options to lead or human for decision

### CONFLICT Recovery

1. **Resolve conflict**: Follow `merge-conflict-resolution.md`
2. **Retry affected task**: With resolved codebase as starting point
3. **Prevent recurrence**: Update task assignments to avoid future conflicts

## Salvage Protocol

When some tasks succeed and others fail, preserve the successful work:

### Step 1: Commit Successful Work

```bash
# Identify branches/commits from successful agents
git log --oneline --all --since="[execution-start]"

# Cherry-pick or merge successful work
git merge --no-ff <successful-agent-branch>
```

### Step 2: Isolate Failures

```
For each failed task:
  - If it has uncommitted changes: stash or discard (agent decision)
  - If it has commits: keep on separate branch for investigation
  - Update task status: "blocked" with failure reason
```

### Step 3: Continue Unblocked Tasks

After salvaging successful work, check the dependency graph:

```
Remaining tasks:
  T005: BLOCKED (depends on failed T003)
  T006: READY (no dependency on failed tasks)
  T007: READY (dependency T002 succeeded)

Action: Continue T006, T007 in parallel
        T005 waits for T003 resolution
```

### Step 4: Report

Generate a failure report for the lead/human:

```markdown
## Partial Failure Report

### Summary
- Total tasks: 8
- Succeeded: 5 (committed and merged)
- Failed: 2 (T003: PERMANENT, T004: TRANSIENT)
- Blocked: 1 (T005: depends on T003)

### Failed Task Details

**T003**: Implement payment webhook
- Category: PERMANENT
- Error: Stripe webhook secret not configured
- Action needed: Configure STRIPE_WEBHOOK_SECRET env var
- Blocks: T005

**T004**: Generate API documentation
- Category: TRANSIENT (timeout)
- Recovery: Retried 2x, succeeded on 3rd attempt
- Status: RESOLVED

### Recommendation
Configure Stripe webhook secret, then retry T003.
T005 will unblock automatically after T003 succeeds.
```
