---
description: Draft a Conventional Commit message for staged changes using the commit-messages skill.
---

# Draft a Conventional Commit Message

To draft a commit message, load the required skills in order:

1. Run `Skill(sanctum:git-workspace-review)` to capture repository status and diffs, completing its `TodoWrite` items.
2. Run `Skill(sanctum:commit-messages)` and create its `TodoWrite` items (type selection, drafting, etc.).

## Workflow
- **FIRST: Validate code quality** with `make format && make lint` - fix all issues before proceeding
- Use the skill checklist to gather evidence: `git status -sb`, `git diff --cached --stat`, and `git diff --cached`.
- Determine the appropriate Conventional Commit type/scope and note any breaking changes.
- Write the message to `{0|commit_msg.txt}` using the required format:
  ```
  <type>(<scope>): <subject>

  <body>

  <footer>
  ```
  (Scope and footer are optional; wrap body lines at 72 characters.)
- After writing, preview the file so the user can copy and paste it.

## CRITICAL: Never Bypass Quality Gates
**NEVER use `git commit --no-verify` or `-n`**. Pre-commit hooks exist to enforce code quality. If hooks fail, fix the issues - don't bypass them.

## Manual Execution
If a skill cannot be loaded, follow these steps:
- **Run code quality checks FIRST**: `make format && make lint`
- Fix any linting/formatting errors before proceeding
- Manually run the Git preflight commands (`pwd`, `git status -sb`, `git diff --cached --stat`, `git diff --cached`) to gather context.
- Follow the Conventional Commit format to choose a type/scope, draft the subject/body/footer, and write only the commit message to `{0|commit_msg.txt}`.
- Preview the file contents when finished.
- **NEVER commit with `--no-verify`** - always let pre-commit hooks run to validate quality.
