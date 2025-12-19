# Troubleshooting

Common issues and solutions when using fix-issue.

## Error: Issue Not Found

```bash
Error: Issue #42 not found
Verify:
  - Issue exists in current repository
  - You have access to the repository
  - Issue number is correct
```

## Error: Subagent Failure

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

## Warning: Merge Conflicts

```bash
Warning: Parallel changes created conflicts
Files: src/auth/middleware.ts

Resolution:
  1. Pausing parallel execution
  2. Resolving conflicts via dedicated subagent
  3. Resuming after resolution
```

## Subagent Not Following Requirements

```bash
Problem: Subagent implemented feature differently than specified
Solution: Re-dispatch with more explicit prompt including:
  - Exact acceptance criteria from issue
  - Code examples if provided
  - Links to related files
```

## Too Many Parallel Conflicts

```bash
Problem: Multiple subagents modifying same files
Solution: Use --no-parallel or manually group tasks to avoid overlap
```

## Review Taking Too Long

```bash
Problem: Code review subagent taking excessive time
Solution: Split large batches into smaller groups
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
