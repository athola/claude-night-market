---
name: execute
description: Execute implementation tasks systematically with progress tracking and checkpoint validation
---

# Attune Execute Command

Execute implementation plan systematically with task tracking, checkpoint validation, and progress reporting.

## Usage

```bash
# Start execution from plan
/attune:execute

# Execute specific task
/attune:execute --task TASK-003

# Resume from checkpoint
/attune:execute --resume

# Execute specific phase
/attune:execute --phase "Phase 1"
```

## What This Command Does

1. **Loads implementation plan** from planning phase
2. **Invokes execution agent** with superpowers integration
3. **Executes tasks** in dependency order with checkpoints
4. **Tracks progress** and updates task status
5. **Validates completion** against acceptance criteria
6. **Reports progress** with metrics and blockers

## Integration with Superpowers

When superpowers plugin is available:
- Uses `Skill(superpowers:executing-plans)` for systematic execution
- Uses `Skill(superpowers:systematic-debugging)` for issue resolution
- Uses `Skill(superpowers:verification-before-completion)` for validation

Without superpowers:
- Falls back to attune's native execution agent
- Provides similar checkpoint-based approach
- Validates task completion systematically

## Workflow

```bash
# 1. Load implementation plan
# Read docs/implementation-plan.md

# 2. Invoke execution agent
Agent(attune:project-implementer)

# 3. Execute tasks in dependency order:
#    For each task:
#      - Check dependencies complete
#      - Execute implementation
#      - Run tests
#      - Validate acceptance criteria
#      - Update progress tracker

# 4. Report progress
#    - Tasks completed/total
#    - Blockers and risks
#    - Next actions

# 5. Save execution state
#    - .attune/execution-state.json
```

## Execution Phases

### Phase 1: Preparation

**Actions**:
- Load implementation plan
- Validate project initialized (run /attune:init if needed)
- Check dependencies installed
- Review task dependency graph

**Output**: Execution plan with ordered task list

### Phase 2: Task Execution Loop

**For each task in order**:

```markdown
1. **Pre-execution**:
   - Verify dependencies complete
   - Review acceptance criteria
   - Create feature branch (if needed)

2. **Implementation**:
   - Write code following spec
   - Run tests continuously (TDD)
   - Document as you go

3. **Validation**:
   - All acceptance criteria met?
   - Tests passing?
   - Code review ready?

4. **Checkpoint**:
   - Mark task complete
   - Update progress tracker
   - Identify blockers
```

### Phase 3: Progress Reporting

**Metrics Tracked**:
- Tasks completed vs. total
- Tasks in progress
- Blocked tasks
- Estimated completion percentage
- Velocity (tasks/day)

**Reports Generated**:
- Daily standup summary
- Sprint progress report
- Blocker identification
- Risk assessment updates

## Arguments

- `--task <task-id>` - Execute specific task (e.g., TASK-003)
- `--phase <phase-name>` - Execute specific phase
- `--resume` - Resume from last checkpoint
- `--dry-run` - Preview execution without applying changes
- `--parallel` - Execute independent tasks in parallel (advanced)

## Examples

### Example 1: Full Execution

```bash
/attune:plan
/attune:init --lang python
/attune:execute
```

**Session Output**:
```
🚀 Executing Implementation Plan

Plan: docs/implementation-plan.md
Total tasks: 40
Current sprint: Sprint 1 (Foundation)

─────────────────────────────────────
Phase 1: Foundation (10 tasks)
─────────────────────────────────────

[✓] TASK-001: Initialize Project Structure
    ├─ Created project with /attune:init
    ├─ All tests passing
    └─ Duration: 45 minutes

[▶] TASK-002: Database Schema Design
    ├─ Creating migration: migrations/001_initial.sql
    ├─ Running: alembic revision --autogenerate
    └─ Progress: 60%

Checkpoint: 1/10 tasks complete (10%)
Next: Complete TASK-002, start TASK-003
Blockers: None
```

### Example 2: Execute Specific Task

```bash
/attune:execute --task TASK-005
```

**Detailed Task Execution**:
```
📋 Executing TASK-005: Implement OAuth Flow

Dependencies: TASK-004 (Complete ✓)

Acceptance Criteria:
- [ ] GitHub OAuth app configured
- [ ] Login redirect to GitHub
- [ ] Callback handles tokens
- [ ] User session created
- [ ] Tests cover happy + error paths

Step 1/5: Configure GitHub OAuth App
→ Creating OAuth app in GitHub Settings...
→ Setting callback URL: http://localhost:8000/auth/callback
→ Storing client_id and client_secret in .env
✓ Complete

Step 2/5: Implement login endpoint
→ Creating backend/app/auth/oauth.py...
→ Writing tests/auth/test_oauth.py...
[Code implementation details...]
✓ Complete (tests passing)

Step 3/5: Implement callback handler
[... implementation ...]

Progress: 3/5 steps (60%)
Estimated completion: 30 minutes
```

### Example 3: Resume from Checkpoint

```bash
/attune:execute --resume
```

Loads state from `.attune/execution-state.json`:
```
🔄 Resuming Execution

Last checkpoint: 2026-01-02 14:30:22
Completed: 15/40 tasks (37.5%)
Last task: TASK-015 (Complete)
Next task: TASK-016

Resuming with TASK-016...
```

### Example 4: Phase-Specific Execution

```bash
/attune:execute --phase "Phase 2"
```

Executes only Phase 2 tasks (TASK-011 through TASK-030).

## Claude Code Tasks Integration (2.1.16+)

When running in Claude Code 2.1.16+, execution uses the native Tasks system:

### Automatic Features

- **Lazy Task Creation**: Tasks created in Claude Code as execution reaches them
- **Native UI Visibility**: Tasks visible in VS Code sidebar
- **Cross-Session State**: Resume execution across Claude Code sessions
- **Dependency Tracking**: Claude Code enforces task dependencies

### Task Creation Flow

```python
# TasksManager handles state with dual-mode support
from tasks_manager import TasksManager

manager = TasksManager(
    project_path=project_path,
    fallback_state_file=Path(".attune/execution-state.json"),
)

# Check for resume state
if manager.prompt_for_resume():
    resume_state = manager.detect_resume_state()
    # Continue from resume_state.next_task_id

# For each task in plan:
task_id = manager.ensure_task_exists(
    task_description,
    dependencies=task_dependencies,
)
# If task is ambiguous, user is prompted for decision
```

### User Prompts on Ambiguity

When task boundaries are unclear, you'll be asked:
- "This task touches multiple components. Create as single task or split?"
- "Potential circular dependency detected. Which task should run first?"

### Shared Task Lists

To share state across terminals:
```bash
export CLAUDE_CODE_TASK_LIST_ID="attune-myproject-execute"
claude
```

### File Fallback

For Claude Code <2.1.16 or non-Claude environments, falls back to:

## Execution State

Progress is saved to `.attune/execution-state.json`:

```json
{
  "plan_file": "docs/implementation-plan.md",
  "started_at": "2026-01-02T10:00:00Z",
  "last_checkpoint": "2026-01-02T14:30:22Z",
  "current_sprint": "Sprint 1",
  "current_phase": "Phase 1",
  "tasks": {
    "TASK-001": {
      "status": "complete",
      "started_at": "2026-01-02T10:05:00Z",
      "completed_at": "2026-01-02T10:50:00Z",
      "duration_minutes": 45,
      "acceptance_criteria_met": true,
      "tests_passing": true
    },
    "TASK-002": {
      "status": "in_progress",
      "started_at": "2026-01-02T14:00:00Z",
      "progress_percent": 60,
      "blocker": null
    }
  },
  "metrics": {
    "tasks_complete": 15,
    "tasks_total": 40,
    "completion_percent": 37.5,
    "velocity_tasks_per_day": 3.2,
    "estimated_completion_date": "2026-02-15"
  },
  "blockers": []
}
```

## Progress Reports

### Daily Standup Report

Generated automatically:
```markdown
# Daily Standup - 2026-01-02

## Yesterday
- ✅ TASK-001: Initialize Project Structure (45 min)
- ✅ TASK-002: Database Schema Design (90 min)
- ✅ TASK-003: Implement Data Models (60 min)

## Today
- 🔄 TASK-004: Set up OAuth (60% complete)
- 📋 TASK-005: Implement Auth Middleware (planned)

## Blockers
- None

## Metrics
- Sprint progress: 15/40 tasks (37.5%)
- On track for Sprint 1 completion
```

### Sprint Progress Report

```markdown
# Sprint 1 Progress Report

**Dates**: Jan 3-16, 2026
**Goal**: Foundation - Working dev environment

## Completed (10 tasks)
- TASK-001 through TASK-010 ✓

## In Progress (2 tasks)
- TASK-011: Issue import logic (40%)
- TASK-012: GitHub webhook receiver (planning)

## Blocked (0 tasks)

## Burndown
- Day 1: 40 tasks remaining
- Day 5: 30 tasks remaining (on track)
- Estimated completion: Jan 15 (1 day early)

## Risks
- None identified

## Next Sprint Preview
- Phase 2: GitHub Integration (10 tasks)
```

## Task Execution Pattern

Each task follows this systematic pattern:

### 1. Pre-Execution Checks
```bash
# Verify dependencies
# Review acceptance criteria
# Ensure tests setup
```

### 2. Implementation (TDD)
```bash
# Write failing test (RED)
# Implement minimal code (GREEN)
# Refactor for quality (REFACTOR)
# Repeat until all criteria met
```

### 3. Validation
```bash
# Run all tests
# Check acceptance criteria
# Code quality check (lint, type check)
# Documentation updated
```

### 4. Checkpoint
```bash
# Mark task complete
# Update execution state
# Report progress
```

## Integration with Full Cycle

```
/attune:brainstorm    ← Generate project brief
      ↓
/attune:specify       ← Define requirements
      ↓
/attune:plan          ← Plan architecture and tasks
      ↓
/attune:init          ← Initialize project structure
      ↓
/attune:execute       ← You are here (implement systematically)
```

## Quality Gates

Before marking task complete, verify:
- ✅ All acceptance criteria met
- ✅ All tests passing (unit + integration)
- ✅ Code linted and type-checked
- ✅ Documentation updated
- ✅ No regression in other components

## Related Commands

- `/attune:plan` - Create implementation plan
- `/attune:init` - Initialize project structure
- `/attune:validate` - Validate project state
- `/speckit-implement` - Spec-kit implementation workflow (if available)

## Related Skills

- `Skill(attune:project-execution)` - Execution methodology
- `Skill(superpowers:executing-plans)` - Systematic execution (if available)
- `Skill(superpowers:systematic-debugging)` - Debug blockers (if available)
- `Skill(superpowers:test-driven-development)` - TDD workflow (if available)

## Agents

- `Agent(attune:project-implementer)` - Task execution agent

## Superpowers Integration

When superpowers is installed, this command automatically:
- Invokes `Skill(superpowers:executing-plans)` for execution framework
- Uses `Skill(superpowers:systematic-debugging)` for issue resolution
- Applies `Skill(superpowers:verification-before-completion)` for validation

Check if superpowers is available:
```bash
/plugin list | grep superpowers
```

Install superpowers:
```bash
/plugin marketplace add obra/superpowers
/plugin install superpowers@superpowers-marketplace
```

## Troubleshooting

**Blocked task**: Use systematic debugging
```bash
# Analyze blocker
# Document symptoms
# Hypothesize causes
# Test solutions
# Update plan if needed
```

**Test failures**: Return to TDD cycle
```bash
# Identify failing test
# Minimal fix to pass
# Refactor
# Continue
```

**Dependency issues**: Check task order
```bash
# Review dependency graph
# Ensure prerequisites complete
# May need to adjust plan
```
