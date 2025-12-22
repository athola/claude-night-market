# Phases 5-6: Completion

Execute sequential tasks and finalize the workflow.

## Phase 5: Sequential Tasks

For tasks with dependencies, execute sequentially:

```
Task tool (general-purpose):
  description: "Issue #42 - Task 2: Add login endpoint"
  prompt: |
    You are implementing Task 2 from Issue #42.

    This task depends on completed Task 1 (auth middleware).

    [Task requirements]

    Verify Task 1's middleware works before building on it.
```

Review after each sequential task following the subagent-driven-development pattern.

## Phase 6: Final Review

Dispatch comprehensive review of all changes:

```
Task tool (superpowers:code-reviewer):
  description: "Final review: Issues #42, #43, #44"
  prompt: |
    Review complete implementation for issues: #42, #43, #44

    Verify:
    - All acceptance criteria met
    - Tests comprehensive and passing
    - No regressions introduced
    - Code quality meets standards
    - Documentation updated if needed
```

## Update Issue Status

For each completed issue:

```bash
# Add completion comment
gh issue comment 42 --body "Fixed in commit $(git rev-parse --short HEAD)

Changes:
- Implemented auth middleware
- Added login endpoint
- Added comprehensive tests

Ready for review."

# Optionally close issue
gh issue close 42 --comment "Completed via automated fix workflow"
```

## Finish Development

Use `superpowers:finishing-a-development-branch` to:

- Verify all tests pass
- Present merge options
- Execute chosen completion path

## Example Final Output

```
Final Review: All requirements met

Issues Summary:
  #42: 3 tasks completed, all tests passing
  #43: 2 tasks completed, all tests passing
  #44: 1 task completed, all tests passing

Issues #42, #43, #44 marked as fixed
Ready for PR creation
```
