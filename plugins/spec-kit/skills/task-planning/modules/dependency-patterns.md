# Task Dependency Patterns

## Overview

Dependencies define task execution order and identify parallelization opportunities. Proper dependency modeling prevents race conditions and validates components exist before they're used.

## Dependency Types

### Sequential Dependencies

**Definition**: Task B cannot start until Task A completes

**When to Use**:
- Task B modifies output from Task A
- Task B requires interfaces/types defined in Task A
- Task B tests functionality implemented in Task A
- Tasks affect the same file(s)

**Example**:
```markdown
### T002 - Define Task data model
**Dependencies**: T001
**Files**: src/models/task.py

### T003 - Implement task validation
**Dependencies**: T002
**Files**: src/models/task.py, src/validators/task.py
```

**Reasoning**: Task validation requires the Task model to exist first. Both affect task.py, requiring sequential execution.

### Parallel Dependencies [P]

**Definition**: Tasks can execute concurrently with no conflicts

**When to Use**:
- No shared dependencies beyond a common foundation
- Operate on different files
- Independent feature implementations
- Separate test suites

**Marker**: Suffix task with `[P]`

**Example**:
```markdown
### T004 - Implement user authentication [P]
**Dependencies**: T001
**Files**: src/services/auth.py, tests/test_auth.py

### T005 - Implement task storage [P]
**Dependencies**: T001
**Files**: src/services/storage.py, tests/test_storage.py
```

**Reasoning**: Both depend on T001 setup but operate on different files and can run concurrently.

### Fan-Out Pattern

**Definition**: Multiple tasks depend on single foundation task

**Pattern**:
```
T001 (Foundation)
    ├─> T002 [P]
    ├─> T003 [P]
    └─> T004 [P]
```

**Use Case**: After creating data models, implement multiple independent services

**Example**:
```markdown
### T001 - Define API schemas
**Dependencies**: None
**Files**: src/types/api.ts

### T002 - Implement user endpoints [P]
**Dependencies**: T001
**Files**: src/routes/users.ts

### T003 - Implement task endpoints [P]
**Dependencies**: T001
**Files**: src/routes/tasks.ts

### T004 - Implement project endpoints [P]
**Dependencies**: T001
**Files**: src/routes/projects.ts
```

### Fan-In Pattern

**Definition**: Single task depends on multiple prerequisites

**Pattern**:
```
T002 [P] ─┐
T003 [P] ─┼─> T005
T004 [P] ─┘
```

**Use Case**: Integration task requiring multiple components

**Example**:
```markdown
### T002 - Implement auth service [P]
**Dependencies**: T001
**Files**: src/services/auth.py

### T003 - Implement storage service [P]
**Dependencies**: T001
**Files**: src/services/storage.py

### T004 - Implement notification service [P]
**Dependencies**: T001
**Files**: src/services/notifications.py

### T005 - Integrate services in workflow
**Dependencies**: T002, T003, T004
**Files**: src/workflow/coordinator.py
```

## File Coordination Rules

### Same-File Modification

**Rule**: Tasks modifying the same file must execute sequentially

**Example**:
```markdown
### T006 - Add base Task class
**Files**: src/models/task.py

### T007 - Add Task validation methods
**Dependencies**: T006
**Files**: src/models/task.py
```

**Reasoning**: Prevents merge conflicts and validates clean incremental changes.

### Same-Directory Independence

**Rule**: Tasks creating different files in same directory can run in parallel

**Example**:
```markdown
### T008 - Create user model [P]
**Files**: src/models/user.py

### T009 - Create task model [P]
**Files**: src/models/task.py
```

**Reasoning**: No file conflicts, different models, independent implementations.

### Test-Implementation Pairing

**Rule**: Implementation and its tests are typically sequential

**Example**:
```markdown
### T010 - Implement resolver logic
**Files**: src/services/resolver.py

### T011 - Add resolver integration tests
**Dependencies**: T010
**Files**: tests/integration/test_resolver.py
```

**Reasoning**: Can't test what doesn't exist yet.

**Exception**: TDD approach might reverse this (write test first).

## Task ID Conventions

### Numbering Format

**Pattern**: `TNNN` where NNN is zero-padded number

**Examples**:
- `T001` - First task
- `T023` - Twenty-third task
- `T100` - Hundredth task

**Rules**:
- Always zero-pad to 3 digits minimum
- Sequential numbering across phases
- No gaps in sequence
- Don't reuse IDs

### Ordering Strategy

**By Phase First**:
```markdown
T001 through T003: Phase 1
T004 through T010: Phase 2
T011 through T025: Phase 3
T026 through T030: Phase 4
T031 through T035: Phase 5
```

**Benefit**: Clear phase boundaries, easy to identify task phase

## Dependency Declaration Format

### Single Dependency
```markdown
**Dependencies**: T001
```

### Multiple Dependencies
```markdown
**Dependencies**: T001, T003, T007
```

### No Dependencies
```markdown
**Dependencies**: None
```

## Common Dependency Patterns

### Linear Chain
```
T001 -> T002 -> T003 -> T004
```
Use when each task builds directly on previous task.

### Independent Parallel
```
T001
    ├─> T002 [P]
    ├─> T003 [P]
    └─> T004 [P]
```
Use when multiple features share only initial setup.

### Diamond Pattern
```
        T001
       /          \
T002 [P]    T003 [P]
       \          /
        T004
```
Use when parallel work converges for integration.

### Layered Dependencies
```
Phase 2: T001, T002, T003
           ↓         ↓         ↓
Phase 3: T004 depends on all Phase 2
```
Use when foundation must be complete before next phase.

## Validation Rules

- [ ] Every task has explicit dependency field
- [ ] No circular dependencies
- [ ] Parallel tasks [P] have no file conflicts
- [ ] Sequential tasks on same file are ordered
- [ ] All referenced task IDs exist
- [ ] Tasks reference dependencies from earlier phases
