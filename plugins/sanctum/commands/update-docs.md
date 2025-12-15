---
description: Update project documentation using the git-workspace-review and doc-updates skills.
---

# Update Project Documentation

To edit documentation, load the required skills in order:

1. Run `Skill(sanctum:git-workspace-review)` to capture the change context and complete its `TodoWrite` items.
2. Run `Skill(sanctum:doc-updates)` and follow the checklist (context, targets, edits, guideline verification, preview).

## Workflow
- Use notes from the preflight to determine which files need updates (README, wiki entries, docstrings, etc.).
- Apply the project's writing guidelines (grounded language, imperative docstrings, no emojis or checkmarks).
- Summarize changes and show relevant diffs once edits are complete.

## Manual Execution
If a skill cannot be loaded, follow these steps:
- Manually gather the Git context (`pwd`, `git status -sb`, `git diff --stat`, `git diff`).
- Update each document using the guidelines listed above and preview the resulting diffs.
