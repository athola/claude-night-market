---
name: version-updates
description: |
  Bump project versions across configs, docs, and changelog using
  git-workspace-review context.

  Triggers: version bump, semver, release version, changelog update, version
  update, package version, release preparation

  Use when: bumping project versions, updating changelogs, preparing releases,
  coordinating version changes across files

  DO NOT use when: just documentation updates - use doc-updates.
  DO NOT use when: full PR preparation - use pr-prep.

  Use this skill for version management and release preparation.
category: artifact-generation
tags: [version, release, changelog, semver, bump]
tools: [Read, Write, Edit, Bash, TodoWrite]
complexity: medium
estimated_tokens: 700
dependencies:
  - sanctum:shared
  - sanctum:git-workspace-review
---

# Version Update Workflow

## When to Use
Use this skill when preparing a release or bumping the project version.
Run `Skill(sanctum:git-workspace-review)` first to capture current changes.

## Required TodoWrite Items
1. `version-update:context-collected`
2. `version-update:target-files`
3. `version-update:version-set`
4. `version-update:docs-updated`
5. `version-update:verification`

## Step 1: Collect Context (`context-collected`)
- Confirm which version to apply (default: bump patch).
- If the prompt provides an explicit version, note it.
- validate `Skill(sanctum:git-workspace-review)` has already captured the repository status.

## Step 2: Identify Targets (`target-files`)
- List configuration files that store the version (e.g., `Cargo.toml`, `package.json`, `pyproject.toml`).
- Include changelog and README references that mention the version.

## Step 3: Update Versions (`version-set`)
- Update each target file with the new version.
- For semantic versions, follow `MAJOR.MINOR.PATCH` or the specified format.
- If the project supports multiple packages, document each update.

## Step 4: Update Documentation (`docs-updated`)
- Add or update changelog entries with today's date.
- Refresh README and docs references to mention the new version and any release notes.

## Step 5: Verification (`verification`)
- Run relevant builds or tests if version bumps require them (e.g., `cargo test`, `npm test`).
- Show `git status -sb` and `git diff` excerpts to confirm the version bumps.

## Output Instructions
- Summarize the files changed and the new version number.
- Mention follow-up steps, such as publishing or tagging, if applicable.
