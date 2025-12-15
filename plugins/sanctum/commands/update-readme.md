---
description: Update README content using the git-workspace-review and update-readme skills with language-aware exemplar mining.
---

# Update README Content

To edit the README, load the required skills in order:

1. Run `Skill(sanctum:git-workspace-review)` to capture the change context and complete its `TodoWrite` items.
2. Run `Skill(sanctum:update-readme)` and follow its checklist (context, exemplar research, content consolidation, verification).

## Workflow
- Use notes from the preflight to understand recent changes that affect the README.
- Research language-aware README exemplars via web search for the project's primary language.
- Consolidate README sections with internal documentation links and reproducible evidence.
- Apply project writing guidelines and verify that all links and code examples work.

## Manual Execution
If a skill cannot be loaded, follow these steps:
- Manually gather the Git context (`pwd`, `git status -sb`, `git diff --stat`).
- Review the current README structure and update sections based on recent changes.
- Verify all links and examples before finalizing.
