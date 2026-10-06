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
last_updated: 2026-10-06
---

## Synopsis

Most harness releases add capability nobody has to act on. A few change
the meaning of syntax already written down, and those are the ones that
break plugins quietly. This entry keeps the second kind.

Covers 2.1.80 through 2.1.291. Later ranges append here rather than
starting a new entry, which keeps the accumulated list in one place.

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

## 2.1.221 to 2.1.289

Recorded 2026-10-04. The 2.1.101 to 2.1.219 rows the first pass left out
are folded in where they still bind.

### Fields the harness reads, ignores, or reads differently

| Version | Change | Consequence here |
|---------|--------|------------------|
| 2.1.259 | Skill and command `model:` honored interactively, for the rest of the turn | A `model: sonnet` hint downgrades an Opus or Fable session mid-mission |
| 2.1.267 | `effort:` on skills, commands and agents honored on pinned-effort models | Effort pins now take effect everywhere |
| docs | Plugin agents ignore `permissionMode`, `hooks`, `mcpServers`, `initialPrompt`. The tool field is `tools` | `allowed-tools` left agents with every tool, and agent `hooks:` never ran |
| 2.1.271 | Agent `omitClaudeMd` | Prompt-complete agents can skip the CLAUDE.md files |
| 2.1.248 | Agent `experimental.cacheTtl` (`5m`, `1h`) | Per-agent prompt cache TTL |
| 2.1.218 | `context: fork` skills run in the background. `background: false` opts out | Result timing changes for every fork skill |
| 2.1.252 | An agent's `model:` beats `CLAUDE_CODE_SUBAGENT_MODEL`. `_FORCE=1` restores the old order | The env var is a default, not an override |
| 2.1.286 | A project or user skill named `verify` runs before commits | Name collision is behavior |

### Tools and defaults that moved

| Version | Change | Consequence here |
|---------|--------|------------------|
| 2.1.233, 2.1.268 | TodoWrite and Task tools off on Opus 4.8+, Sonnet 5+, Fable 5+ unless `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` | Exit criteria cannot require a TodoWrite call |
| 2.1.278 | TaskOutput removed. Read the task's output file instead | `taskOutputMaxChars` is inert |
| 2.1.271 | Monitor watches always time out (30 min, 10 in `-p`). `persistent` is gone | Long watches re-arm |
| 2.1.232 | Interactive subagent spawns run in the background, with fork mode on | The session reaches Stop while a subagent works. Stop input lists it in `background_tasks` |
| 2.1.271 | Workflow guideline `medium` lowered from 15 agents to 10, `small` the default on Pro | Pinned guideline counts move with it |
| 2.1.284 | Sessions start in auto mode when no mode is configured | Pin `permissions.defaultMode` where it matters |
| 2.1.257 | Project-level `defaultMode: bypassPermissions` ignored | Bypass belongs in user or managed settings |

### Hooks

| Version | Change | Consequence here |
|---------|--------|------------------|
| 2.1.121 | PostToolUse `updatedToolOutput` replaces a tool result | A hook can shrink output instead of appending to it |
| 2.1.248 | Stdout that starts with `{` and is not JSON is a hook error | Hooks print `json.dumps` only |
| 2.1.251 | `PreModelSwitch`, `PostModelSwitch`. SessionStart resume carries staleness and re-cache cost | 33 events at 2.1.289 |
| 2.1.280 | Agent-type hooks no longer run on PermissionRequest | Use command or http hooks there |
| 2.1.281 | `claude plugin validate` warns on unquoted `${CLAUDE_PLUGIN_ROOT}` | Quote it or use exec form `args` |
| 2.1.288 | PreToolUse and PermissionRequest fail closed when matching fails | A broken matcher now blocks |

### Plugin tooling

| Version | Addition |
|---------|----------|
| 2.1.259 | `claude plugin validate --json` |
| 2.1.261 | `/skill-doctor`: unused skills and their context cost |
| 2.1.269 | `claude plugin eval`: scored eval suites against a no-plugin baseline (billed runs) |
| 2.1.283 | `/doctor prompt-audit` for prompting written for older models |
| 2.1.285 | `claude plugin configure` for `userConfig` values |
| 2.1.258 | Symlinked component paths, and paths leaving the plugin, refused |

### Mods (2.1.287)

A plugin's `hooks/hooks.json` may name one TypeScript module under
`modules`, beside or instead of `hooks`. The module exports
`register(on, options)` and hooks events such as `tool.call`,
`prompt.compose`, `session.append`, `turn.step` and `ui.render`. It can
draw panes and a band above the prompt, register commands and tools,
and keep state. Command hooks run alongside it and are not deprecated.
Mods are unsandboxed, can be switched off remotely, and are blocked for
marketplace plugins where an organization sets `allowManagedModsOnly`.
`claude plugin test` runs a mod's `*.test.ts` files.

A mod that answers `tool.call` itself keeps plugin PreToolUse hooks from
running. This repo's mods observe and draw only, for that reason.

## 2.1.290

Recorded 2026-10-05 from https://code.claude.com/docs/en/changelog.

| Change | Consequence here |
|--------|------------------|
| Teammate `agent_id` in Agent results is the agent ID; `name@team` moved to `teammate_id`. `TeammateIdle` no longer fires from a teammate's subagents or forks | conjure's health-monitoring module documents the new field and scope |
| `tool.check` events carry `agentId`; mod `tool.check` reads `ceiling` | No mod here hooks `tool.check` |
| `claude plugin validate --json` lists gating-site hooks and their `.catch` (`gatingHooks`) | The conserve and egregore mods register no gating hook |
| Bash asks before `pyright` and more `ps` forms | conserve's PermissionRequest hook auto-approves neither |
| Skill and command `!` blocks refuse raw control characters | None found in this repo's skills |
| WebFetch reports text past 100,000 characters and takes `offset`; interactive WebSearch refills at 100 calls/hour | No skill here quotes either limit |
| `CLAUDE_CODE_DISABLE_ATTACHMENTS` cannot be set from repository settings | Not set here |
| Async Stop hook with an unquoted script path under a spaced folder looped | All 72 plugin-root hook paths here are quoted |

## 2.1.291

Recorded 2026-10-06. Two regression fixes: cloud sessions dropping
permission-prompt answers (from 2.1.290), and a session's last messages
lost on quit (from 2.1.288). Nothing a plugin configures or ships is
affected.

## Open questions this does not answer

- Which of this repo's hook files use a single-segment `if:` pattern.
  The changelog states the rule, not the call sites.
- Whether any behavior here is reversible by configuration.
- Whether the mods API keeps its shape. Its declaration file calls it
  early access and says it may change between releases.

## How to refresh

Run `Skill(night-market-model-and-harness-updates)`. It diffs the
installed version against `.claude/upstream-baseline.json` and reads
the changelog as a mandatory source, so the next range lands here with
its own delta rather than a re-reading of this one.
