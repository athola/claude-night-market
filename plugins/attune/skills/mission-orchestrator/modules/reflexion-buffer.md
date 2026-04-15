---
name: reflexion-buffer
description: >-
  Episodic memory of phase execution failures that
  feeds typed self-critiques back into retry
  attempts, enabling within-round learning.
parent_skill: attune:mission-orchestrator
category: workflow-orchestration
estimated_tokens: 180
---

# Reflexion Buffer

## Purpose

When a phase fails and damage-control triggers a retry,
the agent retries blind. This module maintains an
episodic memory of what was tried, what failed, and why,
so each retry sees the full failure history and avoids
repeating the same mistakes.

Based on the Reflexion pattern (Shinn et al., NeurIPS
2023): verbal self-critiques stored in a buffer provide
reinforcement across attempts without fine-tuning.

## Buffer Structure

Each phase maintains its own buffer. Entries accumulate
across retry attempts within a single iteration-governor
round.

```json
{
  "phase": "execute",
  "max_attempts": 3,
  "entries": [
    {
      "attempt": 1,
      "action": "Ran integration test suite after T012",
      "result": "Timeout after 120s on test_api_auth",
      "diagnosis": "Auth mock server not started before test invocation",
      "adjustment": "Start mock server in setup fixture, add health check before test run"
    }
  ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `phase` | string | Current phase name |
| `max_attempts` | int | Retry cap (from damage-control) |
| `entries` | array | One entry per failed attempt |
| `entries[].attempt` | int | Attempt number (1-indexed) |
| `entries[].action` | string | What was tried (concise) |
| `entries[].result` | string | What happened (error, output) |
| `entries[].diagnosis` | string | Root cause analysis |
| `entries[].adjustment` | string | Concrete change for next try |

## Context Injection Format

Before each retry, inject the full buffer into the
phase prompt. The retry MUST see all prior failures,
not just the most recent.

```
## Reflexion Buffer (Phase: {phase}, Attempt {N}/{max})

### Attempt 1 -- FAILED
**Action**: {action}
**Result**: {result}
**Diagnosis**: {diagnosis}
**Adjustment**: {adjustment}
```

Repeat the block for each prior attempt. One heading
block, no redundant framing.

## Integration with Phase Routing

The buffer hooks into the error handling path defined
in `modules/phase-routing.md`, step 6:

```
Phase fails
  |
  1. Classify error (existing damage-control step)
  |
  2. Build reflexion entry
  |   Extract: action, result, diagnosis, adjustment
  |   Append to buffer
  |
  3. Check convergence (see below)
  |   If converged: escalate, skip retry
  |
  4. Inject buffer into retry context
  |   Prepend buffer block to phase prompt
  |
  5. Retry phase (existing damage-control step)
```

Steps 2-4 are new. Steps 1 and 5 are the existing
damage-control flow.

## Convergence Detection

If the buffer shows the same failure repeating, retrying
is pointless. Detect convergence and escalate instead.

**Algorithm**:

```
function is_converged(entries):
    if len(entries) < 2:
        return false

    last = entries[-1]
    prev = entries[-2]

    # Same error category repeating
    if similar(last.result, prev.result) and
       similar(last.diagnosis, prev.diagnosis):
        return true

    return false
```

**Similarity check**: Compare `result` and `diagnosis`
fields. If both share the same error type or message,
the attempts are converging. Exact string matching is
sufficient; the agent will reuse phrasing for identical
root causes.

**On convergence**: Skip remaining retries:

```
Reflexion buffer detected repeated failure pattern.

  Attempt {N-1}: {diagnosis}
  Attempt {N}:   {diagnosis}

Retrying is unlikely to help. Options:
  [A] Retry anyway (override convergence detection)
  [B] Skip this phase and continue
  [C] Abort mission
```

## Buffer Lifecycle

1. **Created**: When a phase begins execution. Empty
   buffer initialized with phase name and max_attempts.

2. **Populated**: On each phase failure, before retry.
   One entry appended per failed attempt.

3. **Persisted**: Written to mission-state.json under
   the phase object on phase completion (success or
   exhaustion) for post-mission analysis.

4. **Cleared**: When the next phase begins. Prior phase
   buffers remain in mission-state.json.

### State Schema Addition

Add `reflexion_buffer` to each phase entry in
mission-state.json (same schema as the buffer structure
above). An empty `entries` array means the phase
succeeded on first attempt.

## Integration with Ralph Wiggum

When `ralph-wiggum:ralph-loop` is active, each
rejection becomes a reflexion entry:

- `action`: the completion claim
- `result`: "Rejected by ralph-loop: {reason}"
- `diagnosis`: extracted from ralph's feedback
- `adjustment`: derived from ralph's specific ask

The buffer is injected into the next ralph iteration,
preventing the agent from repeating incomplete work
that ralph already rejected.

## Self-Critique Quality

The diagnosis field must contain a root cause, not a
restatement of the error.

- **Bad**: "The test failed." (restates the result)
- **Good**: "Auth mock not initialized before test
  runner started. Setup fixture creates the mock but
  does not wait for its health endpoint."

If the root cause is unclear, say so: "Root cause
unclear. Possible: resource contention, missing async
await, or flaky external dependency." An honest "I do
not know" beats a fabricated diagnosis.
