---
name: fix-issue
description: Fix GitHub issues using subagent-driven-development with parallel execution where appropriate
usage: /fix-issue <issue-number | issue-url | space-delimited-list> [--dry-run] [--parallel] [--no-review]
extends: "superpowers:subagent-driven-development"
---

# Fix GitHub Issue(s)

Retrieves GitHub issue content and uses subagent-driven-development to systematically address requirements, executing tasks in parallel where dependencies allow.

## Key Features

- **Flexible Input**: Single issue number, GitHub URL, or space-delimited list
- **Parallel Execution**: Independent tasks run concurrently via subagents
- **Quality Gates**: Code review between task groups
- **Fresh Context**: Each subagent starts with clean context for focused work

## Quick Start

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

## Workflow Overview

| Phase | Description | Module |
|-------|-------------|--------|
| 1. Discovery | Parse input, fetch issues, extract requirements | [issue-discovery](modules/issue-discovery.md) |
| 2. Planning | Analyze dependencies, create task breakdown | [task-planning](modules/task-planning.md) |
| 3. Execution | Dispatch parallel subagents for independent tasks | [parallel-execution](modules/parallel-execution.md) |
| 4. Quality | Code review gates between task batches | [quality-gates](modules/quality-gates.md) |
| 5-6. Completion | Sequential tasks, final review, issue updates | [completion](modules/completion.md) |

## Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Analyze and show planned tasks without executing |
| `--parallel` | Force parallel execution (skip dependency analysis) |
| `--no-review` | Skip code review between tasks (not recommended) |
| `--close` | Automatically close issues when fixed |

## Required Skills

- **superpowers:subagent-driven-development**: Core execution pattern
- **superpowers:writing-plans**: Task breakdown structure
- **superpowers:test-driven-development**: Subagents follow TDD
- **superpowers:requesting-code-review**: Quality gates between tasks

## GitHub CLI Commands

```bash
# Fetch issue details
gh issue view <number> --json title,body,labels,comments

# Add completion comment
gh issue comment <number> --body "message"

# Close issue
gh issue close <number> --comment "reason"
```

## Configuration

```yaml
fix_issue:
  parallel_execution: true
  max_parallel_subagents: 3
  review_between_batches: true
  auto_close_issues: false
  commit_per_task: true
```

## Detailed Resources

- **Phase 1**: See [modules/issue-discovery.md](modules/issue-discovery.md) for input parsing and requirement extraction
- **Phase 2**: See [modules/task-planning.md](modules/task-planning.md) for dependency analysis
- **Phase 3**: See [modules/parallel-execution.md](modules/parallel-execution.md) for subagent dispatch
- **Phase 4**: See [modules/quality-gates.md](modules/quality-gates.md) for review patterns
- **Phase 5-6**: See [modules/completion.md](modules/completion.md) for finalization
- **Errors**: See [modules/troubleshooting.md](modules/troubleshooting.md) for common issues
