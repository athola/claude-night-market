# Subagent Fallback

Reader: a session running `/attune:mission` or `/attune:execute` whose
delegation returned `providers_exhausted`, or where conjure is not
installed.

The task still leaves the main session. It goes to a subagent on the
session's own model, through the host harness's own subagent tool. Work
inline only when the harness has no subagent tool.

## Pick the agent by phase

Execute tasks go to `attune:project-implementer`. Validate what returns
through the same TDD workflow as a delegated result: an implementation
that fails its RED test is rejected.

Review-phase tasks go to `general-purpose`. Scope, investigate, verify
and report tasks produce findings rather than code, and each finding is
validated by `Skill(imbue:proof-of-work)` evidence.

## Keep the session's model

Always pass `model` in Claude Code, set to the session's alias (`opus`,
`sonnet`, `haiku` or `fable`). The agent pins `sonnet`, and without the
override an Opus mission runs its tasks on Sonnet. Omitting the model is
not safe for `general-purpose` either. A configured
`CLAUDE_CODE_SUBAGENT_MODEL` replaces an omitted model. When the session
model has no alias, omit it and report which model the subagent ran on.

Two settings replace a passed model: `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`
set to `1`, and a mod that sets one in its `agent.spawn` hook. When
either is active, report the model the subagent used rather than the
session's.

The implementer also pins `effort: medium`. Where the harness accepts an
`effort` on the call, pass the session's level.

## Keep the work on the mission branch

The implementer runs with `isolation: worktree`. Unless
`worktree.baseRef` is `"head"`, that worktree starts from the
repository's default branch, and the task is built against code the
mission has not reached. Check the setting before dispatching. When it
is not `"head"`, send the task, its RED test and the TDD instruction to
`general-purpose` instead, which works in the mission's own tree.

When the task did run in a worktree, find its branch with
`git worktree list`. Merge the worktree branch into the mission branch
before validating, then remove the worktree.

## Panels and cost

A task with several seats, such as a war room or an expert panel, is a
different case. Per `plugins/attune/skills/war-room/SKILL.md`, a panel
that could not reach external models is not a panel. Run it labeled
single-model, or stop. Never report seats played by one model as
independent agreement.

With no CLI installed, this path runs on every eligible task. Batch small
tasks into one subagent. A fresh context for a one-line change costs more
than the isolation saves.

## Other harnesses

In Codex, OpenCode or another harness, use its subagent or task tool and
leave the model unchanged. OpenCode documents that a subagent runs on
the model of the agent that invoked it. Where a harness configuration
pins a different subagent model, report the model used.
