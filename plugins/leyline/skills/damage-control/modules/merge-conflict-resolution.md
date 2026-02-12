---
name: merge-conflict-resolution
description: Post-execution conflict detection, resolution protocol, and prevention via file-level conflict analysis
parent_skill: leyline:damage-control
category: infrastructure
estimated_tokens: 250
---

# Merge Conflict Resolution

## Post-Execution Conflict Detection

After parallel agents complete their work, the lead agent checks for conflicts before merging:

```bash
# Check for conflicts between agent branches
git merge --no-commit --no-ff <agent-branch>
# If exit code != 0, conflicts exist

# List conflicting files
git diff --name-only --diff-filter=U
```

**Conflict indicators:**
- Git merge conflicts (overlapping edits to same file regions)
- Semantic conflicts (no git conflict but incompatible changes — e.g., two agents both rename a function differently)
- Import conflicts (both agents add imports that collide or duplicate)

## Resolution Protocol

### Step 1: Stop Affected Agents

Immediately halt agents working on related files to prevent further divergence.

```
Lead → broadcast: "CONFLICT DETECTED in [file list].
  All agents touching these files: STOP and await resolution."
```

### Step 2: Lead Resolves

The lead agent (or human, for CRITICAL tasks) resolves conflicts:

1. **Identify conflict scope**: List all conflicting files and affected tasks
2. **Determine priority**: Which agent's changes take precedence based on task dependencies
3. **Merge manually**: Apply changes in dependency order
4. **Verify**: Run tests to confirm merged result is correct
5. **Commit resolution**: Single commit with clear message documenting the merge

```bash
git add <resolved-files>
git commit -m "fix: resolve merge conflict between [agent-1] and [agent-2]

Conflicting files: [list]
Resolution: Kept [agent-1] changes for [reason],
integrated [agent-2] changes with modifications."
```

### Step 3: Resume Agents

After resolution, notify agents to pull latest and continue:

```
Lead → affected agents: "Conflicts resolved. Pull latest from main.
  Your remaining tasks are unaffected."
```

## Prevention via File-Level Conflict Analysis

Before dispatching parallel tasks, analyze for potential conflicts:

### Pre-Dispatch Conflict Matrix

```markdown
| Task | Files Modified | Conflict Risk |
|------|---------------|---------------|
| T001 | src/api/users.py, tests/test_users.py | - |
| T002 | src/api/orders.py, tests/test_orders.py | - |
| T003 | src/api/users.py, src/models/user.py | CONFLICT with T001 |
```

**Rules:**
- Tasks touching the **same file**: NEVER parallel (sequential or same agent)
- Tasks touching **files in same module**: Check for shared imports/types
- Tasks touching **different modules**: Safe for parallel execution
- Tasks modifying **shared config files**: Sequential only (e.g., `pyproject.toml`, `package.json`)

References patterns from `sanctum:do-issue/modules/parallel-execution.md` for conflict analysis.

### Conflict-Aware Task Assignment

When the lead assigns tasks:
1. Build file-modification map from task descriptions
2. Identify overlapping file sets
3. Group conflicting tasks to same agent (sequential execution)
4. Dispatch non-conflicting groups to separate agents (parallel execution)

## Semantic Conflict Detection

Git won't catch semantic conflicts. After merging, run:

1. **Type checking**: Catch incompatible type changes
2. **Lint**: Catch duplicate imports, unused variables from removed code
3. **Test suite**: Catch behavioral conflicts
4. **Import analysis**: Verify no circular dependencies introduced

If semantic conflicts found, treat as a new merge conflict and re-enter resolution protocol.
