---
name: git-catchup
description: A git repository catchup using the imbue catchup methodology.
usage: /git-catchup [baseline]
---

# Git Repository Catchup

To review changes, load the required skills in order:

1. Run `Skill(sanctum:git-workspace-review)` to capture the Git repository context (branch, status, diffs).
2. Run `Skill(imbue:catchup)` and work through its `TodoWrite` items (context confirmed, delta captured, insights extracted, follow-ups recorded).

## Methodology

The `imbue` catchup methodology applies to Git contexts as follows:

**Context Confirmation:**
- `pwd` confirms the repository location.
- `git status -sb` shows the branch and working tree state.
- `git rev-parse --abbrev-ref --symbolic-full-name @{u}` identifies the upstream branch.

**Delta Capture:**
- `git diff --stat ${BASE}...HEAD` for change metrics.
- `git diff --name-only ${BASE}...HEAD` for a file list.
- Prioritize source, configuration, and documentation files; skip cache and build outputs.

**Insight Extraction:**
- For each modified file, summarize the what, why, and any implications.
- Use `rg -n <pattern> <file>` for targeted searches.
- Defer deep analysis to specialized skills.

**Follow-up Recording:**
- Record tests to run, documentation to update, or reviewers to notify.
- Note any blockers that impede progress.

## Manual Execution

If skills cannot be loaded, run these commands manually:
```bash
pwd
git status -sb
git diff --stat main...HEAD  # Or an appropriate base
git diff --name-only main...HEAD
```

For each important file:
- Summarize what changed, why, and the implications.
- Note any tests needed or documentation to update.

Close with an overall summary and any follow-ups.
