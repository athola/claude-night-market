---
description: Draft a Conventional Commit message for staged changes. Analyzes diffs, classifies change type, and formats scope/body.
model_hint: fast
---

# Draft a Conventional Commit Message

Run these git commands to gather context, then draft the message.

## Steps

1. **Gather context** (run in parallel):
   - `git status -sb`
   - `git diff --cached --stat`
   - `git diff --cached`
   - `git log --oneline -5`

2. **If nothing is staged**, tell the user and stop.

3. **Classify the change**: Pick a type from `feat`, `fix`, `docs`,
   `refactor`, `test`, `chore`, `style`, `perf`, `ci`.
   Pick an optional scope from the changed directory or module.

4. **Draft the message** in this format:
   ```
   <type>(<scope>): <imperative summary, ≤50 chars>

   <body: what and why, wrapped at 72 chars>

   <footer: BREAKING CHANGE or issue refs, if any>
   ```

5. **Slop check** -- the message must NOT contain:
   leverage, utilize, seamless, comprehensive, robust, facilitate,
   streamline, delve, multifaceted, pivotal, intricate, optimize,
   nuanced, furthermore, moreover, revolutionize, elevate, unlock,
   "it's worth noting", "at its core", "in essence", "a testament to"

   If found, replace with plain words (use, smooth, complete, solid,
   enable, simplify, improve, explore, varied, key, detailed).

6. **Write** the message to `./commit_msg.txt` and preview it.

## Rules

- **NEVER** use `git commit --no-verify` or `-n`.
- Write for humans. "fix auth bug" beats "streamline authentication
  optimization."
