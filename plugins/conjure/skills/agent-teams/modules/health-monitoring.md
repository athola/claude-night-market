---
name: health-monitoring
description: Agent health tracking, stall detection, and automated recovery via heartbeat monitoring and claim expiry
parent_skill: conjure:agent-teams
category: delegation-framework
estimated_tokens: 250
---

# Health Monitoring

## Member Health Fields

Each team member's config gains a `health` object for tracking operational status:

```json
{
  "agent_id": "backend@my-team",
  "name": "backend",
  "role": "implementer",
  "health": {
    "status": "healthy",
    "last_heartbeat": "2026-02-07T22:15:00Z",
    "last_task_update": "2026-02-07T22:14:30Z",
    "stall_count": 0,
    "replacement_count": 0
  }
}
```

Members without a `health` object operate as before (no health monitoring — backward compatible).

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `healthy`, `stalled`, `unresponsive`, `replaced` |
| `last_heartbeat` | ISO 8601 | Last heartbeat message timestamp |
| `last_task_update` | ISO 8601 | Last task status change by this agent |
| `stall_count` | integer | Number of times this agent has been marked stalled |
| `replacement_count` | integer | Number of times this agent has been replaced |

## Task Claim Fields

Tasks gain claim tracking fields in metadata:

```json
{
  "id": "5",
  "owner": "backend@my-team",
  "metadata": {
    "claimed_at": "2026-02-07T22:10:00Z",
    "claim_expiry_seconds": 300
  }
}
```

| Field | Default | RED | CRITICAL |
|-------|---------|-----|----------|
| `claim_expiry_seconds` | 300 (5 min) | 600 (10 min) | 900 (15 min) |

Higher-risk tasks get longer claim windows because they legitimately take more time and require more careful execution.

## Health Check Protocol

### Lead Polling Loop

The lead agent checks team health every 60 seconds:

```
Every 60s:
  For each member where status != "replaced":
    1. Check last_heartbeat age
    2. If age > claim_expiry_seconds:
       → Enter 2-stage stall detection
    3. If status == "stalled" and stall_duration > 60s:
       → Mark as "unresponsive"
       → Trigger recovery
```

### 2-Stage Stall Detection

Stage 1 prevents false positives from temporary delays:

```
Stage 1: Probe
  Send health_check message to agent's inbox
  Wait 30 seconds

Stage 2: Confirm
  Check if agent responded with heartbeat
  If yes: Reset stall timer, mark "healthy"
  If no:  Mark "stalled", increment stall_count
```

### Recovery Actions

When an agent is confirmed stalled or unresponsive:

```
stalled (stall_count == 1):
  → Release claimed tasks (set owner = null, status = "pending")
  → Send stall_alert broadcast to team
  → Attempt restart: kill tmux pane, respawn with same identity

stalled (stall_count >= 2):
  → Mark as "unresponsive"
  → Release all tasks
  → Follow leyline:damage-control/modules/agent-crash-recovery.md
  → "Replace don't wait" doctrine: spawn fresh agent

replaced:
  → Agent is permanently decommissioned
  → Inbox preserved for audit
  → All tasks reassigned to other agents
```

## Member Health States

State machine for member health:

```
           heartbeat received
healthy ◄──────────────────── stalled
  │                              │
  │ no heartbeat                 │ no response to
  │ (> claim_expiry)             │ health_check (30s)
  │                              │
  v                              v
stalled ──────────────────► unresponsive
                                 │
                                 │ replacement spawned
                                 │
                                 v
                              replaced
```

**Transitions:**
- `healthy → stalled`: No heartbeat within claim_expiry_seconds
- `stalled → healthy`: Agent responds to health_check
- `stalled → unresponsive`: Agent fails to respond within 30s of health_check
- `unresponsive → replaced`: After 2 failed recovery attempts, fresh agent spawned
- `replaced`: Terminal state — agent is decommissioned

## Heartbeat Protocol

Agents send periodic heartbeat messages to maintain healthy status:

```json
{
  "from": "backend",
  "type": "heartbeat",
  "text": "{\"task_id\": \"5\", \"progress_percent\": 60}",
  "timestamp": "2026-02-07T22:15:00Z"
}
```

Heartbeats are sent:
- Every 60 seconds during active work
- After each task status change
- In response to `health_check` messages from the lead

## Integration with Damage Control

When recovery actions fail, escalate through `leyline:damage-control`:

- Agent crash → `leyline:damage-control/modules/agent-crash-recovery.md`
- Context overflow detected → `leyline:damage-control/modules/context-overflow.md`
- Task failures after replacement → `leyline:damage-control/modules/partial-failure-handling.md`
