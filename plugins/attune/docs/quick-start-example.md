# Quick Start Example

Complete walkthrough of using Attune's full-cycle workflow to build a CLI tool.

## Project: Task Tracker CLI

**Goal**: Build a simple CLI tool to track tasks with local storage.

## Step 1: Brainstorm (/attune:brainstorm)

```bash
/attune:brainstorm --domain "CLI tool"
```

**Session Highlights**:

```
🧠 Brainstorming: CLI Tool Project

Problem Definition:
→ What problem are you solving?
  "Developers need quick task tracking without leaving terminal"

→ Who experiences this problem?
  "Developers, command-line users, DevOps engineers"

→ What existing solutions?
  "Todoist (web-based), Things (GUI), GitHub issues (heavyweight)"

Constraints:
→ Technical: Must work offline, fast startup (< 100ms)
→ Resources: Solo developer, 1 week timeline
→ Integration: Bonus if integrates with git branches

Approaches Generated:
1. JSON file storage (Simple, fast, limited features)
2. SQLite database (More features, query capability)
3. Plain text files (Ultra-simple, grep-able)
4. Git-based storage (Versioned, branch-aware)

Selected: **SQLite database** (Approach 2)
Rationale: Good balance of simplicity and features, fast enough, room to grow
```

**Output**: `docs/project-brief.md`

```markdown
# Task Tracker CLI - Project Brief

## Problem Statement
Command-line users need quick task tracking without context switching to web or GUI applications.

## Goals
1. Sub-100ms startup for quick capture
2. Offline-first (no network dependencies)
3. Simple CLI interface (add, list, done, delete)
4. Integration with git branches (bonus)

## Constraints
- Solo developer, 1 week timeline
- Must work on Linux/macOS/Windows
- Minimal dependencies

## Selected Approach: SQLite Database
**Rationale**: Provides query capability for filtering, fast enough for CLI use, single file storage

**Trade-offs Accepted**:
- Slightly slower than plain text (acceptable for < 10k tasks)
- Requires SQLite (usually pre-installed)

## Next Steps
1. Create specification with commands and storage schema
2. Plan architecture (CLI framework, database layer)
3. Initialize Python project
4. Implement systematically
```

## Step 2: Specify (/attune:specify)

```bash
/attune:specify
```

**Generated Specification** (excerpt):

```markdown
# Task Tracker CLI - Specification v0.1.0

## Functional Requirements

### FR-001: Add Task

**Description**: Add a new task to the tracker

**Acceptance Criteria**:
- [ ] Given task description, when running `task add "Fix bug"`, then task is created with ID
- [ ] Given task with description, when added, then display "Added task #1: Fix bug"
- [ ] Given empty description, when adding, then display error "Task description required"

**Priority**: High
**Estimated Effort**: S

### FR-002: List Tasks

**Description**: Display all pending tasks

**Acceptance Criteria**:
- [ ] Given tasks exist, when running `task list`, then show tasks with ID and description
- [ ] Given no tasks, when listing, then display "No tasks found"
- [ ] Given completed tasks, when listing, then hide by default (show with --all flag)

**Priority**: High
**Estimated Effort**: S

### FR-003: Complete Task

**Description**: Mark task as completed

**Acceptance Criteria**:
- [ ] Given task ID, when running `task done 1`, then mark task complete and remove from list
- [ ] Given invalid ID, when completing, then display error "Task not found"
- [ ] Given already completed task, when completing again, then display "Task already complete"

**Priority**: High
**Estimated Effort**: S

## Non-Functional Requirements

### NFR-001: Performance
- Startup time < 100ms for database with < 1000 tasks
- List command < 50ms

### NFR-002: Usability
- Command syntax matches common CLI patterns (git-like)
- Clear error messages
- Help text with `--help`

## Technical Constraints

**Language**: Python 3.10+
**Database**: SQLite
**CLI Framework**: Click or Typer
**Testing**: pytest
```

## Step 3: Plan (/attune:blueprint)

```bash
/attune:blueprint
```

**Generated Plan** (excerpt):

```markdown
# Task Tracker CLI - Implementation Plan

## Architecture

### System Overview

Simple layered architecture:
```
┌─────────────────┐
│   CLI Layer     │  Command parsing, output formatting
│   (Click)       │
├─────────────────┤
│ Business Logic  │  Task operations, validation
├─────────────────┤
│  Data Access    │  SQLite operations
├─────────────────┤
│   Database      │  SQLite file
│  (tasks.db)     │
└─────────────────┘
```

### Components

#### Component: CLI Layer
**Responsibility**: Parse commands and format output
**Technology**: Click (simple, well-documented)
**Files**: `src/task_tracker/cli.py`

#### Component: Task Service
**Responsibility**: Business logic for task operations
**Technology**: Pure Python
**Files**: `src/task_tracker/service.py`

#### Component: Database
**Responsibility**: Persistent storage
**Technology**: SQLite with SQLAlchemy ORM
**Files**: `src/task_tracker/models.py`, `src/task_tracker/database.py`

### Data Model

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    completed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_tasks_completed ON tasks(completed);
```

## Task Breakdown

### TASK-001: Initialize Project (30 min, P0)
- Use `/attune:project-init --lang python`
- Set up project structure
- Configure pyproject.toml with Click dependency

### TASK-002: Database Models (45 min, P0)
**Dependencies**: TASK-001
- Create `models.py` with Task model
- Create `database.py` with session management
- Tests: model creation, persistence

### TASK-003: Task Service (60 min, P0)
**Dependencies**: TASK-002
- Implement `add_task(description)`
- Implement `list_tasks(include_completed=False)`
- Implement `complete_task(task_id)`
- Tests: all operations with edge cases

### TASK-004: CLI Commands (60 min, P1)
**Dependencies**: TASK-003
- Implement `task add` command
- Implement `task list` command
- Implement `task done` command
- Tests: CLI integration tests

### TASK-005: Error Handling (30 min, P1)
**Dependencies**: TASK-004
- Add validation and error messages
- Handle database errors gracefully
- Tests: error cases

### TASK-006: Documentation (30 min, P2)
**Dependencies**: TASK-005
- Update README with usage examples
- Add docstrings
- Create simple user guide

## Timeline

**Day 1-2**: TASK-001 through TASK-003 (foundation and core logic)
**Day 3**: TASK-004 (CLI interface)
**Day 4**: TASK-005 through TASK-006 (polish and docs)
```

## Step 4: Initialize (/attune:project-init)

```bash
/attune:project-init --lang python --name task-tracker
```

**Output**:

```
✨ Initializing Python project: task-tracker

Created:
✓ .git/ (initialized repository)
✓ .gitignore (Python-specific)
✓ pyproject.toml (uv configuration)
✓ Makefile (development targets)
✓ .pre-commit-config.yaml (code quality hooks)
✓ src/task_tracker/__init__.py
✓ tests/__init__.py
✓ README.md
✓ .github/workflows/test.yml
✓ .github/workflows/lint.yml

Next steps:
1. cd task-tracker
2. make dev-setup     # Install dependencies
3. /attune:execute    # Start implementation
```

## Step 5: Execute (/attune:execute)

```bash
cd task-tracker
/attune:execute
```

**Execution Flow**:

```
🚀 Executing Implementation Plan

Loading: docs/implementation-plan.md
Total tasks: 6

─────────────────────────────────────
TASK-001: Initialize Project
─────────────────────────────────────

Already complete (project initialized with /attune:project-init)

✅ TASK-001: Complete (0 min - skipped)

─────────────────────────────────────
TASK-002: Database Models
─────────────────────────────────────

🔴 RED: Writing failing test

# tests/test_models.py
def test_create_task(db_session):
    task = Task(description="Test task")
    db_session.add(task)
    db_session.commit()
    assert task.id is not None
    assert task.description == "Test task"
    assert task.completed == False

Running: pytest tests/test_models.py::test_create_task
Result: FAILED (Task model not defined)

🟢 GREEN: Implementing minimal code

# src/task_tracker/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

# src/task_tracker/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

def init_db(db_path='tasks.db'):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

Running: pytest tests/test_models.py::test_create_task
Result: PASSED ✓

🔵 REFACTOR: Improving code quality

- Added type hints
- Added docstrings
- Extracted engine creation

Running: pytest tests/test_models.py
Result: All tests passing ✓

✅ TASK-002: Database Models (45 min)
    ├─ Tests: 3 passing
    ├─ Coverage: 95%
    └─ Next: TASK-003

─────────────────────────────────────
TASK-003: Task Service
─────────────────────────────────────

[Similar TDD workflow for service layer...]

✅ TASK-003: Task Service (55 min)
    ├─ Tests: 8 passing
    ├─ Coverage: 92%
    └─ Next: TASK-004

[Continue through TASK-004, TASK-005, TASK-006...]

─────────────────────────────────────
Summary
─────────────────────────────────────

✅ All tasks complete (6/6)
⏱️  Total time: 4.5 hours
📊 Final metrics:
    - Test coverage: 93%
    - Tests passing: 24/24
    - Code quality: All checks passing

🎉 Project ready for use!

Next steps:
1. Install: pip install -e .
2. Try: task add "My first task"
3. See: task --help
```

## Result

**Working CLI Tool** in 4.5 hours:

```bash
# Add tasks
$ task add "Write documentation"
Added task #1: Write documentation

$ task add "Review PR"
Added task #2: Review PR

# List tasks
$ task list
1. Write documentation
2. Review PR

# Complete task
$ task done 1
✓ Completed: Write documentation

$ task list
2. Review PR

# See all tasks
$ task list --all
1. Write documentation (completed)
2. Review PR
```

## Key Benefits

1. **Clear Requirements**: Specification prevented scope creep
2. **Systematic Execution**: TDD maintained quality from start
3. **Progress Tracking**: Knew exactly where we were at all times
4. **Quality Built-in**: 93% test coverage, all quality gates passing
5. **Fast Development**: 4.5 hours vs. typical 8-12 hours with rework

## Comparison: Traditional vs. Attune

### Traditional Ad-Hoc Development

```
Hour 1: Start coding CLI commands
Hour 2: Realize need database, refactor
Hour 3: Add features as ideas come up
Hour 4: Write some tests, find bugs
Hour 5: Debug issues, fix edge cases
Hour 6: Refactor messy code
Hour 7: Add error handling (should've been earlier)
Hour 8: Write documentation
Hour 9: Find more bugs in testing
Hour 10: Final fixes

Result: Working but messy code, incomplete tests, unclear requirements
```

### Attune Full-Cycle Development

```
Hour 1: Brainstorm and specify (clear requirements)
Hour 2: Plan architecture and tasks (clear roadmap)
Hour 3-4: Execute TASK-001 through TASK-003 (TDD, systematic)
Hour 4-5: Execute TASK-004 through TASK-006 (quality built-in)

Result: Clean code, 93% test coverage, clear architecture, extensible
```

**Time Saved**: ~50% (5 hours vs. 10 hours)
**Quality Gained**: Higher test coverage, clearer architecture, better docs
**Confidence Level**: High (systematic validation throughout)

## Try It Yourself

1. Pick a simple project idea
2. Run through the full workflow
3. Compare to your typical ad-hoc development
4. Share your results!
