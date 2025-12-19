# Phase 2: Task Planning

Analyze issue dependencies and create structured task breakdown.

## Dependency Analysis

Identify which issues can be worked in parallel:

```python
def analyze_dependencies(issues):
    """
    Identify which issues can be worked in parallel.
    """
    independent = []
    dependent = []

    for issue in issues:
        if issue.has_no_blockers(issues):
            independent.append(issue)
        else:
            dependent.append({
                'issue': issue,
                'blocked_by': issue.get_blockers(issues)
            })

    return independent, dependent
```

## Task Breakdown

For each issue, generate tasks following `superpowers:writing-plans` structure:

```markdown
## Issue #42: Add user authentication

### Task 1: Create auth middleware
- [ ] Implement JWT validation
- [ ] Add route protection decorator
- [ ] Write unit tests

### Task 2: Add login endpoint
- [ ] Create POST /auth/login
- [ ] Implement password verification
- [ ] Return JWT on success
- [ ] Write integration tests
```

## Initialize TodoWrite

Create todos for all tasks across all issues:

```
- [ ] Issue #42 - Task 1: Create auth middleware
- [ ] Issue #42 - Task 2: Add login endpoint
- [ ] Issue #43 - Task 1: Fix validation bug
```

## Dependency Graph Example

```
Dependency Graph:
  #42: Independent
  #43: Independent
  #44: Depends on #42

Parallel Batch 1: Issues #42, #43
Sequential Phase: Issue #44
```

## Next Phase

After planning, proceed to [parallel-execution.md](parallel-execution.md) to dispatch subagents.
