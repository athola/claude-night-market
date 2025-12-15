---
name: pr-prep
description: Prepare a pull request by validating the workspace, running quality gates, summarizing changes, and drafting the PR template.
category: artifact-generation
tags: [git, pr, pull-request, quality-gates, testing]
tools: [Bash, Write, TodoWrite]
complexity: medium
estimated_tokens: 1000
progressive_loading: true
modules:
  - quality-gates.md
  - pr-template.md
dependencies:
  - sanctum:shared
  - sanctum:git-workspace-review
  - imbue:evidence-logging
  - imbue:structured-output
---

# Pull Request Preparation Workflow

## When to Use
Use this skill to stage work and produce a PR summary/description.
Run `Skill(sanctum:git-workspace-review)` first so the repository state and diffs are already captured.

## Required TodoWrite Items
Create `TodoWrite` items for each of these steps before you start:
1. `pr-prep:workspace-reviewed`
2. `pr-prep:quality-gates`
3. `pr-prep:changes-summarized`
4. `pr-prep:testing-documented`
5. `pr-prep:pr-drafted`

Mark them as complete as each section is finished.

## Step 1: Review Workspace (`workspace-reviewed`)
- Confirm `Skill(sanctum:git-workspace-review)` has been completed (branch, status, staged set).
- If new changes were staged since running it, rerun that skill before continuing.

## Step 2: Run Quality Gates (`quality-gates`)
- Execute formatting, linting, and tests using project commands (e.g., `make fmt`, `make lint`, `make test`).
- If commands differ, note what you ran.
- Capture any failures and resolve them before continuing.
- If something cannot run locally, state why and what alternative validation was done.
- **See `modules/quality-gates.md`** for language-specific commands and failure handling patterns.

## Step 3: Summarize Changes (`changes-summarized`)
- Use the notes from `Skill(sanctum:git-workspace-review)` plus `git diff --stat origin/main...HEAD` (if needed) to understand the scope.
- Skim detailed diffs for key points.
- Group them into 2-4 bullets highlighting the "why" and "what".
- Note breaking changes, migrations, or documentation updates that were made or remain.

## Step 4: Document Testing (`testing-documented`)
- List each test and command that was run and its result (pass/fail).
- Include manual verification steps if relevant (e.g., "verified CLI status command locally").
- If tests were skipped (e.g., due to an environment constraint), explain the mitigation plan.

## Step 5: Draft the PR (`pr-drafted`)
- Fill out the standard template with Summary, Changes, Testing, and Checklist sections.
- Add issue references, screenshots, or follow-up TODOs where useful.
- **See `modules/pr-template.md`** for detailed template structure, examples, and best practices.

## Output Instructions
- Write the final PR description to the path provided by the prompt (e.g., `{0|pr_description.md}`).
- After writing, print the file path and show its contents so reviewers can copy and paste it.

## Notes
- Never include tool or AI attribution in the PR text.
- If new changes are required mid-process, rerun the necessary quality gates.
- This skill focuses on preparation; creating the PR (push and open) happens outside this workflow.
