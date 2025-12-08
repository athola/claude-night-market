---
description: Bump project versions using the git-workspace-review and version-updates skills.
---

# Bump Project Versions

Before changing any version numbers, load the required skills in order:

1. Run `Skill(sanctum:git-workspace-review)` to capture repository status and diffs, completing its `TodoWrite` items.
2. Run `Skill(sanctum:version-updates)` and follow its checklist (context, targets, edits, docs, verification).

## Workflow
- Determine the desired version (the default bump is a patch). If the user passed an explicit version, record it before editing files.
- Update all relevant configuration files, changelog entries, and README/docs references.
- Run any required tests or builds, then show the resulting `git diff` to confirm the changes.

## Manual Execution
If a skill cannot be loaded, follow these steps:
- Manually gather `git status -sb` and the list of files containing version strings.
- Apply the version bump, update documentation, and verify with tests and diffs before summarizing the outcome.
