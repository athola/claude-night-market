# Tasks Integration Guide

Claude Code 2.1.16+ provides a native Tasks system for state management. The `attune`, `spec-kit`, and `sanctum` plugins integrate with this system while maintaining file-based fallback for older versions.

## Tasks API Reference

| Tool | Purpose |
|------|---------|
| TaskCreate | Create a new task in the task list |
| TaskList | List all tasks with current status |
| TaskGet | Retrieve full details for a specific task |
| TaskUpdate | Update task status, dependencies, or details |
| TaskOutput | Retrieve output from a background task |

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `CLAUDE_CODE_TASK_LIST_ID` | Share tasks across sessions | `attune-project-xyz` |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` | Disable background execution | `1` |

## Task Completion Discipline

**CRITICAL**: Mark tasks complete IMMEDIATELY after finishing work:

1. Complete the work
2. Run `TaskUpdate(taskId: "X", status: "completed")`
3. Then move to next task

Do NOT batch task completions at the end—update status as you go. This ensures:
- Accurate progress tracking for users
- Proper state recovery if session ends unexpectedly
- Clear signal to other agents about task availability

## Design Patterns

### Lazy Task Creation

Tasks are created as you reach them, not upfront. This allows flexibility when plans change.

```python
def ensure_task_exists(task_description, context):
    existing = TaskList()
    similar = find_similar_task(existing, task_description)
    if similar:
        return similar.id
    return TaskCreate(task_description)
```

### Ambiguity Detection

When task boundaries are unclear, the system prompts for user decisions:
- Cross-cutting concerns (auth, logging, error handling)
- Multiple components affected
- Large estimated scope (>5000 tokens)

### Dual-Mode Operation

```python
def get_task_state():
    if claude_code_version >= "2.1.16":
        return TaskList()  # Native Tasks
    else:
        return load_json(".attune/execution-state.json")  # File fallback
```

## Implementation

See `plugins/attune/scripts/tasks_manager.py` for the full implementation.
