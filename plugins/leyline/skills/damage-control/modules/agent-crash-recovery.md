---
name: agent-crash-recovery
description: Orphaned task detection, agent replacement, and state recovery from task metadata checkpoints
parent_skill: leyline:damage-control
category: infrastructure
estimated_tokens: 250
---

# Agent Crash Recovery

## Orphaned Task Detection

An orphaned task is one with `status: "in_progress"` whose owning agent has no heartbeat or has been confirmed unresponsive.

**Detection signals:**
- No heartbeat message received within `claim_expiry_seconds` (default: 300s)
- tmux pane for agent no longer exists (`tmux list-panes` check)
- Agent inbox has unread `health_check` messages older than 60s without a response
- Task `claimed_at` timestamp exceeds `claim_expiry_seconds` with no `last_task_update`

**Detection protocol:**
1. Lead polls team member health every 60s
2. For each `in_progress` task, verify owner agent is responsive
3. If unresponsive: mark task as orphaned, release for reassignment

## Task Reassignment Protocol

When an agent is confirmed crashed:

1. **Identify affected tasks**: Find all tasks where `owner` matches the crashed agent
2. **Release tasks**: Set `status: "pending"`, clear `owner` field
3. **Preserve partial work**: If agent committed any changes, note commit hash in task metadata
4. **Broadcast availability**: Send `stall_alert` message to team with released task list
5. **Prioritize reassignment**: Lead assigns to available healthy agents, respecting dependencies

## "Replace Don't Wait" Doctrine

After **2 failed recovery attempts**, do not retry the same agent. Instead:

```
Attempt 1: Send health_check message, wait 30s
Attempt 2: Kill tmux pane, respawn agent with same identity
Attempt 3: REPLACE — spawn new agent with fresh identity
            Transfer all pending tasks from old agent
            Log replacement in team config
```

**Rationale**: Waiting for a stalled agent compounds delay. A fresh agent with the same task context is more likely to succeed than debugging a corrupted agent state.

## State Recovery from Task Metadata

Agents should checkpoint progress in task metadata to enable recovery:

```json
{
  "id": "5",
  "status": "in_progress",
  "owner": "backend@my-team",
  "metadata": {
    "checkpoint": {
      "last_commit": "abc123",
      "files_modified": ["src/api/users.py", "tests/test_users.py"],
      "progress_percent": 60,
      "last_action": "Tests written, implementing endpoint",
      "checkpoint_at": "2026-02-07T22:15:00Z"
    }
  }
}
```

**Recovery steps for replacement agent:**
1. Read task metadata checkpoint
2. Verify `last_commit` exists in git history
3. Read modified files to understand current state
4. Continue from `last_action` description
5. Update checkpoint metadata as work progresses

## Escalation Triggers

Escalate to human (Tier 3) when:
- Same task has crashed 3+ agents
- Crash affects CRITICAL-tier tasks
- Crash caused data corruption or inconsistent state
- No healthy agents available for reassignment
