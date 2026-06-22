---
name: commit-messages
description: Generates conventional commit messages from staged changes. Use when committing and needing a well-formatted message. Do not use for full PR prep; use pr-prep.
alwaysApply: false
category: artifact-generation
tags:
- git
- commit
- conventional-commits
tools: []
complexity: low
model_hint: fast
estimated_tokens: 350
---

# Conventional Commit Workflow

## When To Use

- Generating conventional commit messages from staged changes

## When NOT To Use

- Full PR preparation: use sanctum:pr-prep
- Amending existing commits: use git directly

## Steps

1. **Gather context** (run in parallel):
   - `git status -sb`
   - `git diff --cached --stat`
   - `git diff --cached`
   - `git log --oneline -5`
   - When sem is available (see `leyline:sem-integration`):
     `sem diff --staged --json` for entity-level changes

   If nothing is staged, tell the user and stop.

   When sem output is available, use entity names
   (function, class, method) in the commit subject and
   body instead of parsing raw diff hunks. For example,
   "add function validate_webhook_url" instead of
   "add validation logic to notify.py".

2. **Classify**: Pick type (`feat`, `fix`, `docs`, `refactor`,
   `test`, `chore`, `style`, `perf`, `ci`) and optional scope.

3. **Draft the message**:
   - **Subject**: `<type>(<scope>): <imperative summary>` (50 chars max)
   - **Body**: What and why, wrapped at 72 chars
   - **Footer**: BREAKING CHANGE or issue refs

4. **Slop check**: reject these words and replace with plain
   alternatives:

   | Reject | Use instead |
   |--------|-------------|
   | leverage, utilize | use |
   | seamless | smooth |
   | comprehensive | complete |
   | robust | solid |
   | facilitate | enable |
   | streamline | simplify |
   | optimize | improve |
   | delve | explore |
   | multifaceted | varied |
   | pivotal | key |
   | intricate | detailed |

   Also reject: "it's worth noting", "at its core",
   "in essence", "a testament to"

4a. **Character-level slop check**: load `shared/output-hygiene.md`
   (Contract A) and strip these markers. Inline fallback if that
   module is absent:

   | Marker | Replace with |
   |--------|--------------|
   | `"+"` as a prose conjunction | `and` (keep `+` in versions/code) |
   | em-dash `—` | colon, period, comma, or rewrite |
   | `--` as prose punctuation | colon or rewrite |
   | arrows `->` / `→` as connectors | `to` / `into` |
   | smart quotes `“ ” ‘ ’` | straight `"` and `'` |

4b. **Subject-matter check** (Contract B): describe the change by its
   reader-facing effect. Name neither the AI origin nor the specific
   marker removed. Do NOT write `remove AI slop`, `de-slop`,
   `AI-generated content`, `AI phrasing`, `replace em-dashes`, or
   `remove smart quotes`. Test: if the subject only makes sense as "I
   cleaned up AI output", rewrite it. For example `docs: clarify the
   setup section`, not `style: replace em-dashes with colons`.

5. **Write** to `./commit_msg.txt` and preview.

## Rules

- NEVER use `git commit --no-verify` or `-n`
- Write for humans, not to impress
- If pre-commit hooks fail, fix the issues

## Exit Criteria

- [ ] `commit_msg.txt` written to the working directory containing
      the drafted conventional commit message
- [ ] Subject line follows `<type>(<scope>): <summary>` format and
      is at most 50 characters
- [ ] Slop word check passes: none of the banned words (leverage,
      utilize, seamless, comprehensive, robust, etc.) appear in the
      message
- [ ] Character-level check passes: no em-dashes, no `+` as prose
      conjunction, no smart quotes, no `->` as prose connector
- [ ] If nothing is staged, skill halts immediately and reports
      "nothing staged" without producing a commit message
