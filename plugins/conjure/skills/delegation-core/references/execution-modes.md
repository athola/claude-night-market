# Execution Modes: Selection Guide

Criteria for choosing between single-session, subagents, and
agent-team execution modes.

## Purpose

Execution modes determine how Claude coordinates work across
multiple tasks or agents. The right mode balances parallelism
with coordination overhead, ensuring efficient execution without
excessive context switching or communication complexity.

## Quick Selection

| Scenario | Mode | Why |
|----------|------|-----|
| One file, sequential changes | single-session | No parallelism benefit |
| Multiple files, no dependencies | subagents | Parallelism helps |
| Multiple files, shared interfaces | agent-team | Need coordination |
| User will iterate with feedback | single-session | Easy to adjust |
| Independent research tasks | subagents | Report back only |

## When to Use Each Mode

**Use single-session when**:

- Tasks are sequential (each depends on previous)
- Heavy same-file editing (no coordination needed)
- User wants to iterate with feedback
- Complexity is low, quick iteration matters

**Use subagents when**:

- Tasks are independent (no shared mutable state)
- Files don't overlap (clear ownership)
- Work is research or exploration
- Parallel execution saves significant time

**Use agent-team when**:

- Tasks have shared interfaces that need coordination
- Work spans multiple files with cross-dependencies
- Real-time coordination would prevent conflicts
- Mission complexity is critical (Level 3)

## Getting Started

1. List your tasks and their dependencies
2. Check file overlap: do tasks touch the same files?
3. Check interface coordination: do tasks share APIs/contracts?
4. Apply the decision flowchart below
5. If agent-team, enable experimental feature first

## Why This Pattern

The wrong execution mode creates problems:

- **Single-session for parallel tasks**: Wastes time, no parallelism
- **Subagents for same-file edits**: Conflicts, wasted coordination
- **Agent-team for independent tasks**: Overhead exceeds benefit

The selection criteria are derived from observing what works:
independent tasks benefit from parallelism, but coordination
overhead grows faster than linear. The break-even point is
roughly 3+ independent files for subagents, and 5+ coordinated
files for agent-team.

This pattern emerged from watching agent teams struggle with
file conflicts that could have been avoided with the right mode.

## Mode Definitions

### Single-Session

**How it works**: Claude works through tasks sequentially within
one conversation session.

**Characteristics**:

- No agent spawning overhead
- Full context maintained throughout
- Easy to adjust course mid-execution
- Limited parallelism

**Best for**:

- Sequential tasks where each depends on the previous
- Heavy same-file editing (no coordination needed)
- Low complexity work
- Quick iterations with user feedback

**Example**:

```
Tasks:
  1. Fix bug in parser.py
  2. Update tests for parser.py
  3. Update documentation

Mode: single-session (all tasks touch same files sequentially)
```

### Subagents

**How it works**: Claude spawns independent subagents that work
on tasks in parallel and report results back to the coordinator.

**Characteristics**:

- True parallelism for independent tasks
- Each subagent has isolated context
- Coordinator synthesizes results
- Workers don't communicate with each other

**Best for**:

- Parallel tasks with clear boundaries
- Tasks that don't share mutable state
- Research or exploration tasks
- Independent file modifications

**Example**:

```
Tasks:
  1. Analyze src/api/ for error handling patterns
  2. Analyze src/db/ for error handling patterns
  3. Analyze src/utils/ for error handling patterns

Mode: subagents (independent analysis, report back to coordinator)
```

### Agent-Team

**How it works**: Claude creates a team of agents that can
communicate with each other directly, not just through the
coordinator.

**Characteristics**:

- Full peer-to-peer communication
- Shared workspace awareness
- Can coordinate on shared interfaces
- Higher coordination overhead

**Best for**:

- Parallel tasks with shared interfaces
- Work requiring real-time coordination
- Complex multi-component changes
- Critical missions (Station 3)

**Example**:

```
Tasks:
  1. Implement frontend component A
  2. Implement frontend component B
  3. Integrate A and B with shared state
  4. Write integration tests for A+B

Mode: agent-team (A and B need to coordinate on shared state)
```

**Note**: Agent-team mode is experimental. Enable with:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## Selection Decision Matrix

| Factor | Single-Session | Subagents | Agent-Team |
|--------|----------------|-----------|------------|
| Task dependencies | Sequential | Independent | Interdependent |
| File overlap | Heavy | None/Light | Moderate |
| Parallelism benefit | Low | High | High |
| Coordination need | N/A | Low | High |
| Complexity | Low | Medium | High |
| Risk level | Any | Station 0-2 | Station 2-3 |

## Selection Flowchart

```
START
  │
  ├─ Do tasks share mutable files? ──────────────── YES ─┐
  │                                                      │
  │                                                      ├─→ Single-Session
  │                                                      │
  ├─ Do tasks need to coordinate with each other? ─ YES ─┤
  │                                                      │
  │                                                      ├─→ Agent-Team
  │                                                      │   (if enabled)
  ├─ Are tasks independent? ─────────────────────── YES ─┤
  │                                                      │
  │                                                      ├─→ Subagents
  │                                                      │
  └─ Otherwise ──────────────────────────────────────────→ Single-Session
```

## Mode Compatibility

### Subagents + Worktrees

For parallel tasks with potential file conflicts, combine
subagents with git worktrees:

```
Agent A: worktree/feature-a/
Agent B: worktree/feature-b/

Each agent works in isolated worktree, results merged later.
```

### Agent-Team + Shared Workspace

Agent-team mode works best when agents share awareness of:

- File modifications (who's editing what)
- Interface contracts (agreed APIs)
- Progress state (what's done, what's blocked)

## Mode Transitions

You can transition between modes mid-mission:

1. **Single-session → Subagents**: Spawn agents for independent
   research phases
2. **Subagents → Single-session**: Consolidate findings and
   implement sequentially
3. **Agent-team → Subagents**: Simplify if coordination proves
   unnecessary

Never transition away from agent-team mid-task if agents are
actively coordinating.

## Examples

### Example 1: Feature Research (Subagents)

```
Mission: Research best practices for implementing rate limiting

Tasks:
  1. Research rate limiting algorithms
  2. Research Redis-based rate limiting
  3. Research rate limiting in similar frameworks

Mode: subagents
Rationale: Independent research tasks, no file modifications
```

### Example 2: Bug Fix (Single-Session)

```
Mission: Fix null pointer exception in user service

Tasks:
  1. Locate the bug
  2. Write a failing test
  3. Fix the bug
  4. Verify test passes

Mode: single-session
Rationale: Sequential tasks in same file, quick iteration
```

### Example 3: API + Frontend (Agent-Team)

```
Mission: Implement user preferences feature

Tasks:
  1. Create API endpoints for preferences
  2. Create database schema
  3. Build frontend preferences UI
  4. Write integration tests

Mode: agent-team
Rationale: Tasks 1-3 need to coordinate on data structure,
task 4 depends on 1-3
```

## Anti-Patterns

### Anti-Pattern 1: Subagents for Same-File Edits

```
# BAD: Two agents editing same file
Agent A: Modify src/api.py (add endpoint)
Agent B: Modify src/api.py (fix bug)

# GOOD: Single-session
Claude: Modify src/api.py (add endpoint, then fix bug)
```

### Anti-Pattern 2: Single-Session for Independent Research

```
# BAD: Sequential research
1. Research Redis rate limiting (15 min)
2. Research Memcached rate limiting (15 min)
3. Compare results

# GOOD: Parallel subagents
Agent A: Research Redis (15 min)
Agent B: Research Memcached (15 min)
Coordinator: Compare (5 min)
Total: 20 min vs 35 min
```

### Anti-Pattern 3: Agent-Team Without Coordination Need

```
# BAD: Agent-team for truly independent tasks
Agent A: Fix typo in README.md
Agent B: Fix typo in CONTRIBUTING.md

# GOOD: Subagents or single-session
These don't need to coordinate. Agent-team adds overhead.
```

## Integration with Squadron Composition

See `../agent-teams/references/squadron-composition.md` for:

- Team sizing by mission complexity
- Role definitions (Admiral, Captain, Red-cell)
- File ownership rules

## Source

Adapted from [Nelson](https://github.com/harrymunro/nelson) by
Harry Munro, used under MIT license.
