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

5. **Slop check**: the message must NOT contain:
   leverage, utilize, seamless, comprehensive, robust, facilitate,
   streamline, delve, multifaceted, pivotal, intricate, optimize,
   nuanced, furthermore, moreover, revolutionize, elevate, unlock,
   "it's worth noting", "at its core", "in essence", "a testament to"

   If found, replace with plain words (use, smooth, complete, solid,
   enable, simplify, improve, explore, varied, key, detailed).

5a. **Character-level slop check**: load
   `shared/output-hygiene.md` (Contract A) and strip these from the
   message. Inline fallback if that module is absent:

   - `"+"` used as a prose conjunction becomes `and`
     (`parser + validator` becomes `parser and validator`). Keep `+`
     in version strings, math, and code.
   - em-dash `—` becomes a colon, period, comma, or a rewrite.
   - `--` used as prose punctuation becomes a colon or a rewrite.
   - arrows `->` and `→` used as connectors become `to` or `into`.
   - smart quotes `“ ” ‘ ’` become straight `"` and `'`.

5b. **Subject-matter check** (Contract B): describe the change by its
   reader-facing effect. Name neither the AI origin nor the specific
   marker removed. Do NOT write `remove AI slop`, `de-slop`,
   `AI-generated content`, `AI phrasing`, `replace em-dashes`,
   `remove smart quotes`, or similar. Test: if the subject only makes
   sense as "I cleaned up AI output", rewrite it. For example
   `docs: clarify the setup section`, not `style: replace em-dashes
   with colons`.

6. **Write** the message to `./commit_msg.txt` and preview it.

## Rules

- **NEVER** use `git commit --no-verify` or `-n`.
- Write for humans. "fix auth bug" beats "streamline authentication
  optimization."
