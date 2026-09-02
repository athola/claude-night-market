---
name: git-workspace-review
description: Verifies workspace state and staged changes as a read-only preflight. Use before commits or PRs to confirm staged set is clean and correct.
alwaysApply: false
category: workspace-ops
tags:
- git
- preflight
- status
- diff
- staged
tools: []
complexity: low
model_hint: fast
estimated_tokens: 500
modules:
- modules/git-commands.md
hooks:
  PreToolUse:
  - matcher: Bash
    command: "# Log git analysis commands\nif jq -r '.tool_input.command // empty' | grep -qE\
      \ \"git (status|diff|log|show|branch)\"; then\n  echo \"[skill:git-workspace-review]\
      \ Git analysis initiated: $(date)\" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/skill-audit.log\n\
      fi\n"
    once: true
  Stop:
  - command: 'echo "[skill:git-workspace-review] === Analysis completed at $(date)
      ===" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/skill-audit.log

      '
role: library
---
# Git Workspace Review

## When NOT To Use

- Writing the commit message (use `sanctum:commit-messages`)
- Running the full pre-PR gate (use `sanctum:pr-prep`)

## Verification

Run `git status` after review to verify workspace state matches expectations.

## Testing

Run `pytest plugins/sanctum/tests/test_git_workspace_review.py` to validate review workflow.

## Usage

Use this skill before workflows that depend on repository state, such as commit message generation, PR preparation, or release notes. Run it once per session or whenever staged changes are modified.

## Required Progress Tracking

1. `git-review:repo-confirmed`
2. `git-review:status-overview`
3. `git-review:code-quality-check`
4. `git-review:diff-stat`
5. `git-review:diff-details`

Mark each item as complete as you finish the corresponding step.

## Step 1: Confirm Repository (`repo-confirmed`)

Run `pwd` to confirm you are in the correct repository directory. Execute `git status -sb` to view the current branch and short status, then capture the branch name and upstream information.

## Step 2: Review Status Overview (`status-overview`)

Analyze the `git status -sb` output for staged and unstaged changes. Stage or unstage files so that subsequent workflows operate on the intended diff.

## Step 3: Check Code Quality (`code-quality-check`)

Run `make lint` from the repository root to validate code quality
before committing. It formats with ruff, applies the per-plugin check
with autofix, and runs bandit, so no separate format step is needed.
The root Makefile defines no `format` target, and the plugin Makefiles
that define one only apply inside their own directory.

Fix any errors immediately. Do not bypass pre-commit hooks with
`--no-verify`. This check identifies issues early and avoids
late-stage pipeline failures.

## Step 4: Review Diff Statistics (`diff-stat`)

Run `git diff --cached --stat` for staged changes (or
`git diff --stat` for unstaged work). Note the number of
files modified and identify hotspots with large insertion
or deletion counts.

When sem is available (see `leyline:sem-integration`),
also run `sem diff --format plain --staged` to display an entity-level
summary alongside the stat output. This shows which
functions, classes, and methods changed rather than just
line counts.

## Step 5: Review Detailed Diff (`diff-details`)

Run `git diff --cached` to examine the actual changes. For unstaged work, use `git diff`. Identify key themes, such as Makefile adjustments or new skill additions, to provide context for downstream summaries.

## Exit Criteria

Complete all progress tracking items. You should have a clear understanding of modified files and areas, and the correct work should be staged. Subsequent workflows can then rely on this context without re-executing git commands.

## Supporting Modules

- [Git commands reference](modules/git-commands.md) - diff, status, branch operations for sanctum workflows

## Troubleshooting

If pre-commit hooks block a commit, resolve the reported issues instead
of using `--no-verify`. `make lint` fixes styling automatically and
surfaces the logical failures that remain. If merge conflicts occur, use
`git merge --abort` to return to a clean state before retrying.
