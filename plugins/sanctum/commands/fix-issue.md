---
name: fix-issue
description: Fix GitHub issues using subagent-driven-development with parallel execution where appropriate
usage: /fix-issue <issue-number | issue-url | space-delimited-list> [--dry-run] [--parallel] [--no-review]
extends: "superpowers:subagent-driven-development"
---

# Fix GitHub Issue(s)

Retrieves GitHub issue content and uses subagent-driven-development to systematically address the requirements, executing tasks in parallel where dependencies allow.

## Key Features

- **Flexible Input**: Single issue number, GitHub URL, or space-delimited list
- **Parallel Execution**: Independent tasks run concurrently via subagents
- **Quality Gates**: Code review between task groups
- **Fresh Context**: Each subagent starts with clean context for focused work

## When to Use

- Addressing one or more GitHub issues systematically
- Issues with well-defined acceptance criteria
- When you want automated task breakdown and parallel execution
- When issues contain multiple independent requirements

## Workflow

### Phase 1: Issue Discovery

1. **Parse Input Arguments**

   Accepts any of these formats:
   ```bash
   # Single issue number
   /fix-issue 42

   # GitHub issue URL
   /fix-issue https://github.com/owner/repo/issues/42

   # Multiple issues (space-delimited)
   /fix-issue 42 43 44

   # Mixed formats
   /fix-issue 42 https://github.com/owner/repo/issues/43
   ```

2. **Retrieve Issue Content**

   For each issue, fetch the full content:
   ```bash
   # By number (uses current repo)
   gh issue view 42 --json title,body,labels,assignees,comments

   # By URL (extracts owner/repo/number)
   gh issue view https://github.com/owner/repo/issues/42 --json title,body,labels,assignees,comments
   ```

3. **Extract Requirements**

   From each issue body, identify:
   - **Acceptance Criteria**: Checkboxes, "should", "must" statements
   - **Technical Requirements**: Code references, API specs, constraints
   - **Test Expectations**: Expected behavior, edge cases
   - **Dependencies**: Related issues, blocking items

### Phase 2: Task Planning

4. **Analyze Issue Dependencies**

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

5. **Create Task Breakdown**

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

6. **Initialize TodoWrite**

   Create todos for all tasks across all issues:
   ```
   - [ ] Issue #42 - Task 1: Create auth middleware
   - [ ] Issue #42 - Task 2: Add login endpoint
   - [ ] Issue #43 - Task 1: Fix validation bug
   ```

### Phase 3: Parallel Execution

7. **Group Independent Tasks**

   Identify tasks that can run concurrently:
   - Tasks from different files
   - Tasks with no shared state
   - Tasks that don't modify same code paths

8. **Dispatch Parallel Subagents**

   For independent tasks, dispatch concurrently:
   ```
   Task tool (general-purpose) [PARALLEL]:
     description: "Issue #42 - Task 1: Create auth middleware"
     prompt: |
       You are implementing Task 1 from Issue #42.

       Issue context:
       [Issue body and requirements]

       Your job:
       1. Implement exactly what the task specifies
       2. Follow TDD - write failing test first
       3. Implement until tests pass
       4. Verify no regressions
       5. Commit your work with conventional commit format

       Report: Implementation summary, test results, files changed
   ```

   ```
   Task tool (general-purpose) [PARALLEL]:
     description: "Issue #43 - Task 1: Fix validation bug"
     prompt: |
       You are implementing Task 1 from Issue #43.
       [Same structure as above]
   ```

9. **Await Parallel Results**

   Collect results from all parallel subagents before proceeding.

### Phase 4: Quality Gates

10. **Batch Code Review**

    After parallel batch completes, review all changes:
    ```
    Task tool (superpowers:code-reviewer):
      description: "Review parallel batch: Issues #42, #43"
      prompt: |
        Review changes from parallel implementation batch.

        Issues addressed:
        - #42 Task 1: Auth middleware
        - #43 Task 1: Validation fix

        BASE_SHA: [sha before batch]
        HEAD_SHA: [current sha]

        Focus on:
        - Correct implementation per issue requirements
        - No conflicts between parallel changes
        - Test coverage adequate
        - No security vulnerabilities introduced
    ```

11. **Handle Review Feedback**

    - **Critical Issues**: Fix immediately via follow-up subagent
    - **Important Issues**: Fix before next batch
    - **Minor Issues**: Note for later

### Phase 5: Sequential Tasks

12. **Execute Dependent Tasks**

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

13. **Review After Each Sequential Task**

    Following subagent-driven-development pattern.

### Phase 6: Completion

14. **Final Review**

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

15. **Update Issue Status**

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

16. **Finish Development**

    Use `superpowers:finishing-a-development-branch` to:
    - Verify all tests pass
    - Present merge options
    - Execute chosen completion path

## Options

- `--dry-run`: Analyze issues and show planned tasks without executing
- `--parallel`: Force parallel execution (skip dependency analysis)
- `--no-review`: Skip code review between tasks (not recommended)
- `--close`: Automatically close issues when fixed

## Examples

### Example 1: Single Issue

```bash
/fix-issue 42

# Output:
Fetching issue #42...
Title: Add user authentication
Requirements identified: 4
Tasks generated: 3

Executing Task 1/3: Create auth middleware
  [Subagent working...]
  Complete: 5 tests passing, 2 files changed

Reviewing Task 1...
  Strengths: Good test coverage, follows patterns
  Issues: None

Executing Task 2/3: Add login endpoint
  [Subagent working...]
  ...

Final Review: All requirements met
Issue #42 marked as fixed
```

### Example 2: Multiple Issues (Parallel)

```bash
/fix-issue 42 43 44

# Output:
Fetching issues #42, #43, #44...
Analyzing dependencies...

Dependency Graph:
  #42: Independent
  #43: Independent
  #44: Depends on #42

Parallel Batch 1: Issues #42, #43
  [2 subagents running in parallel...]
  #42 Task 1: Complete (auth middleware)
  #43 Task 1: Complete (validation fix)

Batch Review...
  All changes valid, no conflicts

Sequential Phase: Issue #44
  Task 1: Complete (depends on #42)

Final Review: All requirements met
Issues #42, #43, #44 marked as fixed
```

### Example 3: Dry Run

```bash
/fix-issue 42 43 --dry-run

# Output:
DRY RUN - No changes will be made

Issue #42: Add user authentication
  Tasks:
    1. Create auth middleware (independent)
    2. Add login endpoint (depends on Task 1)
    3. Add logout endpoint (depends on Task 1)

Issue #43: Fix validation bug
  Tasks:
    1. Fix email validation (independent)
    2. Add validation tests (depends on Task 1)

Execution Plan:
  Parallel Batch 1: #42-Task1, #43-Task1
  Review Gate
  Parallel Batch 2: #42-Task2, #42-Task3, #43-Task2
  Review Gate
  Final Review

Estimated subagent invocations: 7
```

## Integration

### Required Skills

- **superpowers:subagent-driven-development**: Core execution pattern
- **superpowers:writing-plans**: Task breakdown structure
- **superpowers:test-driven-development**: Subagents follow TDD
- **superpowers:requesting-code-review**: Quality gates between tasks

### Sanctum Skills Used

- **git-workspace-review**: Pre-flight workspace check
- **commit-messages**: Conventional commit formatting

### GitHub CLI Commands

```bash
# Fetch issue details
gh issue view <number> --json title,body,labels,comments

# Add comment
gh issue comment <number> --body "message"

# Close issue
gh issue close <number> --comment "reason"

# Get current repo
gh repo view --json nameWithOwner -q .nameWithOwner
```

## Error Handling

### Issue Not Found

```bash
Error: Issue #42 not found
Verify:
  - Issue exists in current repository
  - You have access to the repository
  - Issue number is correct
```

### Subagent Failure

```bash
Error: Subagent failed on Issue #42 Task 2
Cause: Test failures after implementation

Options:
  1. Dispatch fix subagent (recommended)
  2. Skip task and continue
  3. Abort workflow

[Selecting option 1...]
Dispatching fix subagent...
```

### Merge Conflicts

```bash
Warning: Parallel changes created conflicts
Files: src/auth/middleware.ts

Resolution:
  1. Pausing parallel execution
  2. Resolving conflicts via dedicated subagent
  3. Resuming after resolution
```

## Best Practices

### Before Running

1. Ensure clean working directory (`git status` shows no changes)
2. Pull latest from remote
3. Verify GitHub CLI is authenticated (`gh auth status`)
4. Review issues briefly to confirm they're ready for implementation

### During Execution

1. Monitor subagent progress via TodoWrite
2. Don't manually edit files while subagents are working
3. Let code reviews complete before proceeding
4. Address Critical issues immediately

### After Completion

1. Review final changes before merging
2. Verify all tests pass
3. Update issue comments with implementation notes
4. Create PR if working on branch

## Configuration

```yaml
fix_issue:
  # Execution settings
  parallel_execution: true
  max_parallel_subagents: 3

  # Review settings
  review_between_batches: true
  review_after_each_task: false  # Batch review is more efficient

  # Issue handling
  auto_close_issues: false
  add_completion_comments: true

  # Commit settings
  commit_per_task: true
  commit_message_format: "conventional"
```

## Troubleshooting

### Subagent Not Following Issue Requirements

```bash
Problem: Subagent implemented feature differently than specified
Solution: Re-dispatch with more explicit prompt including:
  - Exact acceptance criteria from issue
  - Code examples if provided
  - Links to related files
```

### Too Many Parallel Conflicts

```bash
Problem: Multiple subagents modifying same files
Solution: Use --no-parallel or manually group tasks to avoid overlap
```

### Review Taking Too Long

```bash
Problem: Code review subagent taking excessive time
Solution: Split large batches into smaller groups
```

## Notes

- Requires GitHub CLI authentication
- Works best with well-structured issues (clear acceptance criteria)
- Parallel execution significantly speeds up multi-issue workflows
- Code review gates catch integration issues early
- Each subagent has fresh context, avoiding pollution from previous tasks
