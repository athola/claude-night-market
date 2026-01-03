---
name: pr-prep
description: |
  Prepare a pull request by validating the workspace, running quality gates,
  summarizing changes, and drafting the PR template.

  Triggers: PR preparation, pull request, quality gates, PR template, PR summary,
  branch preparation, merge request

  Use when: preparing PRs for submission, running quality gates, drafting
  PR descriptions and templates

  DO NOT use when: reviewing existing PRs - use pr-review instead.
  DO NOT use when: just generating commit messages - use commit-messages.

  Use this skill for PR preparation.
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
- Confirm `Skill(sanctum:git-workspace-review)` has been completed.
- If new changes were staged since running it, rerun that skill.

## Step 2: Run Quality Gates (`quality-gates`)
- Execute formatting, linting, and tests using project commands (e.g., `make fmt`, `make lint`, `make test`).
- If commands differ, note what was run.
- Resolve failures before continuing.
- If a task cannot run locally, state why and what alternative validation was done.
- **See `modules/quality-gates.md`** for language-specific commands and failure handling.

## Step 3: Summarize Changes (`changes-summarized`)
- Use the notes from `Skill(sanctum:git-workspace-review)` and `git diff --stat origin/main...HEAD` to understand the scope.
- Skim diffs for key points.
- Group them into 2-4 bullets highlighting the "why" and "what".
- Note breaking changes, migrations, or documentation updates.

## Step 4: Document Testing (`testing-documented`)
- List each test and command that was run and its result.
- Include manual verification steps if relevant.
- If tests were skipped, explain the mitigation plan.

## Step 5: Draft the PR (`pr-drafted`)
- Fill out the standard template with Summary, Changes, Testing, and Checklist sections.
- Add issue references, screenshots, or follow-up TODOs.
- **See `modules/pr-template.md`** for template structure and examples.

## Output Instructions
- Write the final PR description to the provided path.
- After writing, print the file path and show its contents.

## Notes
- Never include tool or AI attribution in the PR text.
- If new changes are required mid-process, rerun quality gates.
- This skill focuses on preparation; creating the PR (push and open) happens outside this workflow.
