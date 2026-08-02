---
id: claude-code-harness-deltas
title: Claude Code Harness Deltas Affecting Plugin Authors
maturity: growing
importance_score: 71
routing_type: both
tags:
  - claude-code
  - harness
  - hooks
  - permissions
  - plugins
  - migration
sources:
  - https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
related_artifacts:
  - .claude/skills/claude-code-plugin-reference/SKILL.md
  - .claude/upstream-baseline.json
  - .claude/skills/night-market-model-and-harness-updates/SKILL.md
  - docs/model-harness-updates/migrations/2026-08-02-harness-2-1-220.md
last_updated: 2026-08-02
---

## Synopsis

Most harness releases add capability nobody has to act on. A few change
the meaning of syntax already written down, and those are the ones that
break plugins quietly. This entry keeps the second kind, drawn from the
2.1.80 to 2.1.220 range.

Covers 2.1.80 through 2.1.220. Later ranges append here rather than
starting a new entry, so the accumulated list stays in one place.

## Changes that alter existing syntax

These reinterpret something already written. A plugin can keep working
by accident and fail later.

| Version | Change | Consequence |
|---------|--------|-------------|
| 2.1.214 | Hook `if:` single-segment `dir/**` matches only `<cwd>/dir` | A hook meant to fire at any depth needs `**/dir/**` |
| 2.1.213 | `Write(path)`, `NotebookEdit(path)`, `Glob(path)` permission rules warn | Only `Edit(path)` and `Read(path)` are consulted by file checks |
| 2.1.212 | `SessionStart` reports source `"fork"` | A hook branching on `source` takes the resume path for forks |
| 2.1.212 | Task tool `mode` parameter deprecated and ignored | Subagents inherit the parent's permission mode |
| 2.1.207 | Plugin option values ignored in project `.claude/settings.json` | Only user, `--settings`, and managed settings are honored |
| 2.1.206 | Agent names containing `:` rejected | The colon is reserved for plugin namespacing |

The `if:` change is the sharpest, because `deny` and `ask` permission
rules kept their any-depth behavior. The two syntaxes no longer agree,
so copying a pattern from one to the other silently changes its scope.

The permission-rule warning is worth stating plainly: a `Write(path)`
allow rule is not wrong syntax, it is inert. It parses, it loads, and it
never matches. That is the worst failure mode available to a permission
rule, because the author believes access was granted.

## Removals

| Version | Removed |
|---------|---------|
| 2.1.205 | `/agents` wizard; edit `.claude/agents/` directly |
| 2.1.183 | `TeamCreate` and `TeamDelete` tools |

## Additions worth knowing about

| Version | Addition |
|---------|----------|
| 2.1.220 | `DirectoryAdded` hook, fires on `/add-dir` mid-session |
| 2.1.218 | `Notification` hook for background agent events |
| 2.1.220 | Subagents nest to depth 3 by default, was 1 |
| 2.1.217 | Skills with `context: fork` run in background; opt out with `background: false` |
| 2.1.217 | Frontmatter booleans accept `yes`/`no`/`on`/`off`/`1`/`0` |
| 2.1.186 | Frontmatter keys accept kebab-case, snake_case, and camelCase |
| 2.1.183 | `Tool(param:value)` permission syntax, e.g. `Agent(model:opus)` |
| 2.1.216 | `${user_config.*}` rejected in shell-form plugin hook commands |

The 2.1.216 entry is a shell-injection fix, so a plugin relying on that
substitution in a shell-form command stops working rather than
degrading.

## Open questions this does not answer

- Which of this repo's hook files use a single-segment `if:` pattern.
  The changelog states the rule, not the call sites.
- Whether any behavior here is reversible by configuration.
- Anything after 2.1.220.

## How to refresh

Run `Skill(night-market-model-and-harness-updates)`. It diffs the
installed version against `.claude/upstream-baseline.json` and reads
the changelog as a mandatory source, so the next range lands here with
its own delta rather than a re-reading of this one.
