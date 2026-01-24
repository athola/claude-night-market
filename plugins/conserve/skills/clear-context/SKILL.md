---
name: clear-context
description: |
  Automatic context management with graceful handoff to continuation subagent.

  Triggers: context pressure, 80% threshold, auto-clear, context full,
  continuation, session state, checkpoint

  Use when: Context usage approaches 80% during long-running tasks.
  This skill enables automatic continuation without manual /clear.

  The key insight: Subagents have fresh context windows. By delegating
  remaining work to a continuation subagent, we achieve effective "auto-clear"
  without stopping the workflow.
category: conservation
token_budget: 200
progressive_loading: true

hooks:
  PreToolUse:
    - matcher: "Task"
      command: |
        echo "[skill:clear-context] Subagent delegation at $(date)" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/clear-context-audit.log
---

# Clear Context Skill

## Quick Start

When context pressure reaches critical levels (80%+), invoke this skill to:
1. Save current session state
2. Delegate continuation to a fresh subagent
3. Continue work without manual intervention

```
Skill(conserve:clear-context)
```

## When to Use

- **Proactively**: Before starting large multi-chained tasks
- **Reactively**: When context warning indicates 80%+ usage
- **Automatically**: Integrated into long-running workflows

## The Auto-Clear Pattern

Since `/clear` requires user action, we achieve automatic context clearing without interruption through **subagent delegation**:

```
Main Agent (high context)
    ↓
    Saves state to .claude/session-state.md
    ↓
    Spawns continuation subagent (fresh context)
    ↓
    Subagent reads state, continues work
```

## Thresholds

| Level | Threshold | Action |
|-------|-----------|--------|
| WARNING | 40% | Monitor, plan optimization |
| CRITICAL | 50% | Prepare for handoff |
| EMERGENCY | 80% | **Execute auto-clear now** |

**Configuration** (environment variables):
- `CONSERVE_EMERGENCY_THRESHOLD`: Override 80% default (e.g., `0.75` for 75%)
- `CONSERVE_SESSION_STATE_PATH`: Override `.claude/session-state.md` default

## Auto-Clear Workflow

### Step 1: Assess Current State

Before triggering auto-clear, gather:
- Current task/goal description
- Progress made so far
- Key decisions and rationale
- Files being actively worked on
- Open TodoWrite items

### Step 2: Save Session State

Write to `.claude/session-state.md` (or `$CONSERVE_SESSION_STATE_PATH`):

```markdown
# Session State Checkpoint
Generated: [timestamp]
Reason: Context threshold exceeded (80%+)

## Current Task
[What we're trying to accomplish]

## Progress Summary
[What's been done so far]

## Key Decisions
- Decision 1: [rationale]
- Decision 2: [rationale]

## Active Files
- path/to/file1.py - [status]
- path/to/file2.md - [status]

## Pending TodoWrite Items
- [ ] Item 1
- [ ] Item 2

## Continuation Instructions
[Specific next steps for the continuation agent]
```

### Step 3: Spawn Continuation Agent

Use the Task tool to delegate:

```
Task: Continue the work from session checkpoint

Instructions:
1. Read .claude/session-state.md for full context
2. Verify understanding of current task and progress
3. Continue from where the previous agent left off
4. If you also approach 80% context, repeat this handoff process

The session state file contains all necessary context to continue without interruption.
```

### Step 4: Graceful Exit

After spawning continuation agent:
- Report that handoff is complete
- Provide link to session state for reference
- Exit current task (subagent continues)

## Integration with Existing Hooks

This skill works with `context_warning.py` hook:

1. Hook fires on PreToolUse
2. At 80%+ threshold, hook injects emergency guidance
3. Guidance recommends invoking this skill
4. Skill executes auto-clear workflow

## Module Loading

For detailed session state format and examples:
```
Load module: session-state
```

## Self-Monitoring Pattern

For workflows that might exceed context, add periodic checks:

```python
# Pseudocode for context-aware workflow
def long_running_task():
    for step in task_steps:
        execute_step(step)

        # Check context after each major step
        if estimate_context_usage() > 0.80:
            invoke_skill("conserve:clear-context")
            return  # Continuation agent takes over
```

## Estimation Without CLAUDE_CONTEXT_USAGE

If the environment variable isn't available, estimate using:

1. **Turn count heuristic**: ~5-10K tokens per complex turn
2. **Tool invocation count**: Heavy tool use = faster context growth
3. **File read tracking**: Large files consume significant context

```python
def estimate_context_pressure():
    """Rough estimation when env var unavailable."""
    # Heuristics (tune based on observation)
    turns_weight = 0.02  # Each turn ~2% of typical context
    file_reads_weight = 0.05  # Each file read ~5%

    estimated = (turn_count * turns_weight) + (file_reads * file_reads_weight)
    return min(estimated, 1.0)
```

## Example: Brainstorm with Auto-Clear

```markdown
## Brainstorm Session with Context Management

1. Before starting, note current context level
2. Set checkpoint after each brainstorm phase:
   - Problem definition checkpoint
   - Constraints checkpoint
   - Approaches checkpoint
   - Selection checkpoint

3. If context exceeds 80% at any checkpoint:
   - Save brainstorm state
   - Delegate to continuation agent
   - Agent continues from checkpoint
```

## Best Practices

1. **Checkpoint Frequently**: During long tasks, save state at natural breakpoints
2. **Clear Instructions**: Continuation agent needs specific, actionable guidance
3. **Verify Handoff**: Ensure state file is written before spawning subagent
4. **Monitor Recursion**: Continuation agents can also hit limits - design for chaining

## Troubleshooting

### Continuation agent doesn't have full context
- Ensure session-state.md is comprehensive
- Include all relevant file paths
- Document implicit assumptions

### Subagent fails to continue properly
- Check that state file path is correct
- Verify file permissions
- Add more specific continuation instructions

### Context threshold not detected
- CLAUDE_CONTEXT_USAGE may not be set
- Use estimation heuristics as fallback
- Manual invocation always works
