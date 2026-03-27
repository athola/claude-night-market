---
description: Hard limits on file reads before implementation to prevent token waste
alwaysApply: true
---

**Cap discovery reads before implementing!**

When implementing features, fixes, or refactors, limit
how many files you read before starting to write code.
Reading "one more file for context" is the #1 cause of
token waste — 68 tool calls burning 50k tokens on a
single turn.

**Read budgets by task type:**

| Task | Max Reads | Then |
|------|-----------|------|
| Implement from spec/requirements | 8 files | Start writing |
| Bug fix (known location) | 5 files | Start fixing |
| Refactor (known scope) | 1 per file changed | Start refactoring |
| Open exploration | 15 files | Report findings |

**What counts toward the budget:**

- Each `Read` tool call = 1 read
- Each `Grep` with `output_mode: "content"` = 1 read
- `Grep` with `files_with_matches` = free (returns paths only)
- `Glob` = free (returns paths only)
- `Read` with `offset`/`limit` targeting <50 lines = 0.5 reads

**Read order (most valuable first):**

1. The spec, requirements, or issue being implemented
2. The file(s) you will modify
3. Imports/interfaces those files depend on
4. Stop. Start writing.

**If you think you need more context:**

- Ask the user. Do not read more files.
- Say: "I've read N files and have enough context to
  start. Should I read more, or proceed?"

**Override: user-only, explicit.**

These limits can ONLY be exceeded when the user
explicitly requests deeper exploration. Examples:

- "Read more files" / "explore the codebase"
- "Read the whole module" / "understand everything"
- "I want you to be thorough, read what you need"
- "ultrathink" / "explore deeply" / "deep dive"
- "take your time and understand the full context"

**These are NOT overrides (do not self-authorize):**

| Thought | Reality |
|---------|---------|
| "I need more context" | You have enough. Start writing. |
| "One more file to be safe" | Safety = fewer tokens wasted. |
| "This is complex, I should read more" | Complex tasks need focused reads, not more reads. |
| "I want to understand the full picture" | Implement what you know. Ask if stuck. |
| "Let me check how X is used elsewhere" | Grep for filenames (free). Read only if critical. |

**Why this rule exists:**

Users report 60%+ of their daily quota consumed in a
single turn due to unbounded discovery reads. The model
over-indexes on "read before writing" guidance and reads
30-60+ files for tasks requiring 3-5. This rule makes
the budget explicit and the override user-controlled.
