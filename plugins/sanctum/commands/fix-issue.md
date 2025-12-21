---
name: fix-issue
description: Fix GitHub issues using subagent-driven-development with parallel execution where appropriate
usage: /fix-issue <issue-number | issue-url | space-delimited-list> [--dry-run] [--parallel] [--no-review]
---

# Fix GitHub Issue(s)

Fix one or more GitHub issues using subagent-driven-development methodology.

## Usage

```bash
# Single issue
/fix-issue 42

# Multiple issues (analyzes dependencies, runs in parallel where possible)
/fix-issue 42 43 44

# GitHub URL
/fix-issue https://github.com/owner/repo/issues/42

# Preview without executing
/fix-issue 42 --dry-run
```

## Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Analyze and show planned tasks without executing |
| `--parallel` | Force parallel execution (skip dependency analysis) |
| `--no-review` | Skip code review between tasks (not recommended) |
| `--close` | Automatically close issues when fixed |

## Workflow

1. Load `Skill(sanctum:fix-issue)` for detailed workflow guidance
2. Follow the six phases: Discovery, Planning, Parallel Execution, Quality Gates, Sequential Tasks, Completion
3. Each phase has TodoWrite checkpoints for progress tracking

## What It Does

1. **Discovers** issue requirements from GitHub
2. **Plans** task breakdown with dependency analysis
3. **Executes** independent tasks in parallel via subagents
4. **Reviews** code between task batches
5. **Completes** sequential tasks and updates issues

## Required Skills

This command uses `Skill(sanctum:fix-issue)` which depends on:

- **superpowers:subagent-driven-development**: Core execution pattern
- **superpowers:writing-plans**: Task breakdown structure
- **superpowers:test-driven-development**: Subagents follow TDD
- **superpowers:requesting-code-review**: Quality gates between tasks
- **superpowers:finishing-a-development-branch**: Finalization

## Examples

### Fix Single Issue

```bash
/fix-issue 42

# Fetches issue #42, creates tasks, executes with TDD, reviews, updates issue
```

### Fix Multiple Issues in Parallel

```bash
/fix-issue 42 43 44

# Analyzes dependencies between issues
# Runs independent tasks in parallel
# Sequences dependent tasks appropriately
```

### Dry Run Preview

```bash
/fix-issue 42 --dry-run

# Shows planned tasks without executing
# Useful for reviewing scope before committing
```
