---
description: Prepare a PR description using the pr-prep skill.
---

# Prepare a PR Description

To draft a PR description, load the required skills in order:

1. Run `Skill(sanctum:git-workspace-review)` to capture repository status and diffs, completing its `TodoWrite` items.
2. Run `Skill(sanctum:pr-prep)` and create its `TodoWrite` items (quality gates, summaries, testing, PR draft) as you progress.

## Workflow
Follow the skill's checklist to:
- Review `git status -sb` and confirm staged work.
- Run the project's formatting, linting, and test commands (e.g., `make fmt`, `make lint`, `make test`).
- Summarize key changes and testing results.
- Fill out the PR template with Summary, Changes, Testing, and Checklist sections.
- Write the final description to `{0|pr_description.md}` (or the provided destination) and preview the file contents when finished.

## Manual Execution
If a skill cannot be loaded, follow these steps:
- Manually gather repository status and diffs (`pwd`, `git status -sb`, `git diff --stat`, `git diff`) and run the necessary quality gates.
- Summarize the changes and testing, fill out the PR template, write it to the destination file, and show the preview.
