---
name: doc-updates
description: |
  Update documentation files based on recent changes while enforcing project
  writing guidelines.

  Triggers: documentation update, docs update, ADR, docstrings, writing guidelines,
  readme update, documentation maintenance

  Use when: updating documentation after code changes, enforcing writing guidelines,
  maintaining ADRs, updating docstrings

  DO NOT use when: README-specific updates - use update-readme instead.
  DO NOT use when: consolidating ephemeral docs - use doc-consolidation.

  Use this skill for general documentation updates.
category: artifact-generation
tags: [documentation, readme, adr, docstrings, writing]
tools: [Read, Write, Edit, Bash, TodoWrite]
complexity: medium
estimated_tokens: 900
progressive_loading: true
modules:
  - adr-patterns
dependencies:
  - sanctum:shared
  - sanctum:git-workspace-review
  - imbue:evidence-logging
---

# Documentation Update Workflow

## When to Use
Use this skill when code changes require updates to the README, plans, wikis, or docstrings.
Run `Skill(sanctum:git-workspace-review)` first to capture the change context.

## Required TodoWrite Items
1. `doc-updates:context-collected`
2. `doc-updates:targets-identified`
3. `doc-updates:edits-applied`
4. `doc-updates:guidelines-verified`
5. `doc-updates:preview`

## Step 1: Collect Context (`context-collected`)
- Ensure `Skill(sanctum:git-workspace-review)` has been run.
- Use its notes to understand the delta.
- Identify the features or bug fixes that need documentation updates.

## Step 2: Identify Targets (`targets-identified`)
- List the relevant files from the scope (e.g., README.md, wiki entries, docstrings).
- Prioritize user-facing documentation first, then supporting plans and specifications.
- When architectural work is planned, confirm whether an Architecture Decision Record (ADR) already exists in `wiki/architecture/` (or wherever ADRs are located).
- Add missing ADRs to the target list before any implementation begins.

## Step 3: Apply Edits (`edits-applied`)
- Update each file with grounded language: explain what changed and why.
- Reference specific commands, filenames, or configuration options where possible.
- For docstrings, use the imperative mood and keep them concise.
- For ADRs, see `modules/adr-patterns.md` for complete template structure, status flow, immutability rules, and best practices.

## Step 4: Enforce Guidelines (`guidelines-verified`)
- Re-read the project's style rules (no filler phrases, avoid abstract adjectives, etc.).
- Ensure the balance between bullet points and paragraphs matches the guidance.
- Remove emojis and checkmarks; replace them with text equivalents.

## Step 5: Preview Changes (`preview`)
- Show diffs for each edited file (`git diff <file>` or `rg` snippets).
- Summarize remaining TODOs or follow-ups.

## Exit Criteria
- All `TodoWrite` items are completed and documentation is updated.
- New ADRs, if any, are in `wiki/architecture/` (or the established ADR directory) with the correct status and links to related work.
- Guidelines are satisfied, and the content does not sound AI-generated.
- Files are staged or ready for review.
