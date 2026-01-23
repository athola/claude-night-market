# Tasks Integration Exploration - January 2026

**Purpose**: Evaluate Claude Code 2.1.16+ Tasks system for potential plugin integration
**Date**: 2026-01-23
**Status**: Research Complete - Integration Recommended

## Executive Summary

Claude Code 2.1.16 introduced a **proper user-facing Tasks system** with dedicated tools for creating, tracking, and managing tasks with dependency support. This is a significant opportunity to enhance our workflow plugins.

**Key Finding**: The Tasks system provides exactly what we need for state management:
- Persistent task state across sessions
- Dependency tracking between tasks
- Shared task lists across Claude Code instances
- Background task execution with output retrieval

**Recommendation**: Integrate Tasks system into attune and spec-kit for improved state management, while maintaining file-based fallback for non-Claude Code environments.

## Tasks System Overview

### Available Tools

| Tool | Description | Use Case |
|:-----|:------------|:---------|
| **TaskCreate** | Creates a new task in the task list | Start tracking implementation tasks |
| **TaskList** | Lists all tasks with their current status | Progress dashboards, resume detection |
| **TaskGet** | Retrieves full details for a specific task | Check dependencies, get context |
| **TaskUpdate** | Updates task status, dependencies, or details | Mark complete, add blockers |
| **TaskOutput** | Retrieves output from a background task | Get results from parallel subagents |

### Key Features

#### 1. Shared Task Lists Across Sessions

```bash
# Session 1 - Start implementation
export CLAUDE_CODE_TASK_LIST_ID="attune-project-xyz"
claude

# Session 2 - Different terminal, same project
export CLAUDE_CODE_TASK_LIST_ID="attune-project-xyz"
claude
# Both sessions see the same task list!
```

**Benefit**: Multiple Claude Code sessions can coordinate on the same implementation plan.

#### 2. Dependency Tracking

Tasks can define prerequisites that must complete first:

```
Task: TASK-003 - Implement user authentication
Dependencies: [TASK-001, TASK-002]
Status: blocked (waiting on dependencies)
```

**Benefit**: Automatic task ordering without manual tracking.

#### 3. Background Task Execution

Tasks can run in the background and be retrieved later:

```
# Start long-running task
TaskCreate: "Run full test suite" (background: true)

# Continue other work...

# Later, retrieve results
TaskOutput: "task-abc123"
```

**Benefit**: Parallel execution without blocking the main workflow.

## Integration Opportunities

### Plugin: attune

**Current State**: `.attune/execution-state.json` with custom format

**Tasks Integration**:

```markdown
# /attune:execute with Tasks

1. On start: TaskCreate for each implementation task
   - Set dependencies based on plan
   - Store task IDs in .attune/task-mapping.json (for reference)

2. During execution: TaskUpdate as tasks complete
   - Update status: pending → in_progress → complete
   - Add evidence references

3. On resume: TaskList to check current state
   - Find incomplete tasks
   - Verify dependencies met

4. Benefits:
   - Native UI visibility in VS Code
   - Persistent across session restarts
   - Dependencies automatically enforced
```

**Design Decisions**:

1. **Lazy TaskCreate**: Create tasks as you reach them, not upfront
   - More flexible when plans change mid-execution
   - Reduces wasted tasks if execution stops early
   - Better reflects actual progress

2. **Ask User on Ambiguity**: When task boundaries are unclear, prompt for input
   - "This change touches auth and payments. Create separate tasks or one combined task?"
   - "Dependencies unclear between TASK-003 and TASK-004. Which should run first?"
   - Keeps user in control of task granularity

**Migration Strategy**:

```python
# Dual-mode operation
def get_task_state():
    if claude_code_version >= "2.1.16":
        # Use native Tasks
        return TaskList()
    else:
        # Fallback to file-based state
        return load_json(".attune/execution-state.json")

# Lazy task creation with user confirmation
def ensure_task_exists(task_description, context):
    existing = TaskList()

    # Check if similar task already exists
    similar = find_similar_task(existing, task_description)
    if similar:
        return similar.id

    # Ambiguity check - ask user if unclear
    if is_ambiguous(task_description, context):
        user_choice = ask_user(
            f"About to create task: '{task_description}'\n"
            f"Options:\n"
            f"  1. Create as single task\n"
            f"  2. Split into subtasks\n"
            f"  3. Merge with existing task\n"
            f"Choice [1/2/3]?"
        )
        task_description = refine_based_on_choice(user_choice, task_description)

    return TaskCreate(task_description)
```

### Plugin: spec-kit

**Current State**: `.specify/tasks.md` (markdown format)

**Tasks Integration**:

```markdown
# /speckit-execute with Tasks

1. Generate tasks from specification
2. TaskCreate for each with:
   - Description from spec
   - Dependencies from analysis
   - Acceptance criteria in details

3. Execute tasks in dependency order
4. TaskOutput for parallel validation

Benefits:
- Task state survives spec regeneration
- Dependencies enforced by Claude Code
- Progress visible outside Claude session
```

### Plugin: sanctum

**Current State**: Ad-hoc task tracking in PR workflows

**Tasks Integration**:

```markdown
# /sanctum:fix-pr with Tasks

1. TaskCreate for each PR comment/fix
2. Set dependencies (e.g., lint before test)
3. TaskUpdate as fixes applied
4. Final TaskList for PR summary

Benefits:
- Clear audit trail
- Resume after session timeout
- Parallel fix attempts
```

### Plugin: conserve

**Opportunity**: Use TaskOutput for continuation agent coordination

```markdown
# Auto-clear with Tasks

1. Before handoff: TaskCreate with current state
2. Continuation subagent: TaskGet to restore context
3. On complete: TaskUpdate with results

Benefits:
- State doesn't depend on file writes
- Works with compaction
- Better subagent coordination
```

## Implementation Plan

### Phase 1: Proof of Concept (1 Week) - IN PROGRESS

**Goal**: Validate Tasks integration works with attune using lazy creation + user prompts

- [x] Create attune-tasks-poc branch
- [x] Implement lazy TaskCreate (create as you reach each task)
- [x] Implement ambiguity detection heuristics
- [x] Add user prompt for task boundary decisions
- [x] Implement TaskList for resume detection
- [x] Write BDD tests (24 tests, all passing)
- [ ] Test with real implementation workflow
- [ ] Measure: Does it improve reliability?

**Implementation**: `plugins/attune/scripts/tasks_manager.py`
**Tests**: `plugins/attune/tests/test_tasks_integration.py`

**Success Criteria**:
- [x] Tasks created just-in-time, not upfront
- [x] User prompted when task boundaries unclear
- [x] Claude Code 2.1.17 detected, Tasks available
- [x] Resume works after session restart
- [x] Dependencies enforce correct ordering

**Integration Test Results** (2026-01-23):
```
=== Test 1: File Fallback Mode ===
Created tasks: TASK-001, TASK-002, TASK-003
Tasks in state: 3
Can start TASK-002? False (blocked by dependency)
Can start TASK-001? True
After completing TASK-001, can start TASK-002? True

=== Test 2: Resume Detection ===
Has incomplete tasks: True
Next task: TASK-002
Completed: 1

=== Test 3: Ambiguity Detection ===
Cross-cutting detected: True (cross_cutting)
Simple task detected: True

=== All Integration Tests Passed! ===
```

### Phase 2: Production Integration (2-3 Weeks)

**Goal**: Full Tasks support in attune with fallback

- [ ] Implement dual-mode state management
- [ ] Add CLAUDE_CODE_TASK_LIST_ID to workflow
- [ ] Update documentation
- [ ] Add tests for both modes

**Deliverables**:
- Updated `/attune:execute` command
- Task mapping file format
- Migration guide

### Phase 3: Expand to Other Plugins (1 Month)

**Goal**: Tasks support across ecosystem

- [ ] spec-kit integration
- [ ] sanctum integration (PR workflows)
- [ ] conserve integration (continuation)
- [ ] Cross-plugin task coordination

### Phase 4: Advanced Patterns (2 Months)

**Goal**: Leverage full Tasks capabilities

- [ ] Parallel task execution in War Room
- [ ] Cross-session task sharing
- [ ] Task analytics and reporting
- [ ] Plugin interoperability via shared task lists

## User Interaction Patterns

### When to Ask the User

| Situation | Question | Default if No Response |
|-----------|----------|------------------------|
| Task boundary unclear | "Split into subtasks or keep combined?" | Keep combined |
| Dependency ambiguous | "Which task should complete first?" | Alphabetical order |
| Similar task exists | "Reuse existing task or create new?" | Reuse existing |
| Task scope creep | "This grew larger than expected. Split?" | Continue as-is |
| Blocker detected | "Skip, retry, or escalate?" | Escalate |

### Ambiguity Detection Heuristics

```python
def is_ambiguous(task_description, context):
    """Detect when user input would improve task quality."""

    # Multiple distinct components mentioned
    if count_distinct_components(task_description) > 2:
        return True

    # Cross-cutting concern (auth, logging, error handling)
    if mentions_cross_cutting(task_description):
        return True

    # Unclear dependency with existing tasks
    existing_tasks = TaskList()
    if has_circular_dependency_risk(task_description, existing_tasks):
        return True

    # Large estimated scope
    if estimated_tokens(task_description) > 5000:
        return True

    return False
```

### Example Interaction Flow

```
Executing: TASK-003 - Implement user authentication

[Ambiguity detected: This task touches both auth service and user model]

Question: This implementation spans multiple components:
  - Authentication service (src/auth/)
  - User model (src/models/user.py)
  - Session middleware (src/middleware/)

Options:
  1. Single task (all changes together)
  2. Split into 3 tasks with dependencies
  3. Let me specify the split

Your choice [1/2/3]: 2

Creating tasks:
  - TASK-003a: Update User model with auth fields
  - TASK-003b: Implement AuthService (depends on 003a)
  - TASK-003c: Add session middleware (depends on 003b)

Proceeding with TASK-003a...
```

## Trade-offs and Considerations

### Benefits of Tasks Integration

| Benefit | Impact |
|---------|--------|
| Native persistence | No file I/O, survives crashes |
| Dependency enforcement | Automatic, no manual tracking |
| VS Code visibility | Users see progress in UI |
| Cross-session sharing | Multiple terminals coordinate |
| Background execution | True parallelism |

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Claude Code version dependency | Dual-mode with file fallback |
| Tasks API changes | Version detection, abstraction layer |
| Token cost of TaskList calls | Cache task state, batch updates |
| Complexity increase | Phased rollout, extensive testing |

### When NOT to Use Tasks

- Simple single-session workflows
- Non-Claude Code environments (API, other tools)
- Very short tasks (overhead not worth it)
- Privacy-sensitive state (Tasks may be logged)

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `CLAUDE_CODE_TASK_LIST_ID` | Share tasks across sessions | `attune-project-xyz` |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` | Disable background execution | `1` |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Control auto-compaction timing | `85` |

## Recommended Naming Convention

For task list IDs:

```
{plugin}-{project-hash}-{workflow}

Examples:
- attune-abc123-execute
- speckit-def456-implement
- sanctum-ghi789-fix-pr
```

## Conclusion

**The Claude Code Tasks system is a significant enhancement that aligns perfectly with our plugin architecture.**

### Immediate Actions

1. **Start POC** with attune (highest complexity, most to gain)
2. **Document** task list ID conventions
3. **Test** background task execution for War Room

### Long-term Vision

A unified task management layer where:
- All plugins share a common task model
- Users see all implementation progress in one place
- Cross-plugin workflows coordinate via shared task lists
- State persists reliably across sessions and crashes

## Sources

- [Claude Code Settings - Tasks](https://code.claude.com/docs/en/settings)
- [Claude Code Changelog 2.1.16](https://code.claude.com/docs/en/changelog)
- [Subagents Documentation](https://code.claude.com/docs/en/sub-agents)
