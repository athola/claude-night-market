---
name: plan-before-large-dispatch
enabled: true
event: prompt
action: warn
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: (audit|analyze|research|review|comprehensive|deep.?dive|full.?scan|evaluate).*(codebase|plugin|skill|architecture|system|repo)
---

**Plan mode required for large agent dispatch!**

Tasks involving comprehensive analysis, audits, or
research across the codebase typically require 4+
parallel agents. Before dispatching:

**MUST get user alignment first.** There are two
compliant paths, and the second one did not exist when
this rule was written:

1. `EnterPlanMode`: design the agent strategy, specify
   the agent roster, the scope per agent and the output
   contract, and get approval before launching agents.
2. A **Workflow script**. The script is the plan, in a
   form that executes. It carries its own user gate: a
   workflow only runs when the user asks for one, by
   name or with the `ultracode` keyword, so the
   alignment this rule exists to force is still forced.

Pick path 2 when the shape is known before the work
(fan out, verify, synthesize, migrate a list). Pick
path 1 when the roster has to adapt to what the first
agents find.

**What the script provides, that the plan asks for:**

| This rule demands | A workflow provides |
|-------------------|---------------------|
| Agent roster | the `agent()` calls |
| Scope per agent | each call's prompt |
| Output contract | `schema`, validated at the tool-call layer, with model retry on mismatch |
| Result integration | the script body |
| Failure strategy | failed agents return `null`; a throwing stage drops that item |
| Worktree isolation decision | `isolation: "worktree"` per agent |

Results also stay in script variables rather than in
the session, which is the direct answer to the context
overflow this rule was written to prevent.

**Constraints that come with path 2:**

- Never start a workflow unasked. A quoted tip is not
  a request.
- Subagents in a workflow run in `acceptEdits` and
  inherit the tool allowlist, whatever the session's
  permission mode. Scope their prompts accordingly.
- The `ultracode` keyword does not fire from headless
  routes (`-p`, SDK without a human-origin stamp,
  scheduled prompts, webhooks), so nothing in egregore
  or a night run starts one implicitly.
- A script has no filesystem and no shell. A workflow
  may find, rank and structure. It cannot be the step
  that proves a test passed.
- No module loading. A script containing `import()`
  fails before the run starts, so work needing a
  library belongs inside an agent's task.

Full analysis, with the source for each claim:
`reports/dynamic-workflows-integration-2026-08-23.md`
(machine-local; `reports/` is gitignored).

**The spend posture is pinned, not inherited:**

`.claude/settings.json` sets `workflowSizeGuideline`
to `medium`, which asks for fewer than 15 agents when
Claude writes a workflow. That is also the built-in
default, so the agent count Claude aims for does not
move. Pinning it does change one thing: a guideline
you choose replaces the default 25-agent threshold on
the advisory `Large workflow` warning, so that warning
fires here at 15 rather than 25. The pin is written
down so a change to the default cannot silently resize
the four workflows this repo ships, whose agent counts
were sized against it. The key needs Claude Code
v2.1.219 or later. Before that the effective
guideline is `unrestricted`.

Two things follow from pinning it in a settings file:

- A settings file takes precedence over `/config`,
  and the `/config` row is hidden while one supplies
  a value. `/config workflowSizeGuideline=small` will
  not take while this file sets the key.
- The guideline is advice to the model, not a cap.
  The runtime bounds are what actually hold: up to
  16 concurrent agents, fewer on fewer CPUs, and
  1,000 per run.

`ultracode` is deliberately left unset. Setting it
would have Claude plan a workflow for every
substantive task, which is the unasked start the
first constraint above forbids.

The guideline sizes a run before it starts. Nothing
in it measures what a run cost, so pair it with
`Skill(conserve:agent-expenditure)` afterward.

**Prefer tiered audit over full-codebase dispatch:**

- Default to Tier 1 (git history) first
- Escalate to Tier 2 (targeted areas) only for flagged
  modules
- Tier 3 (full codebase) requires explicit user approval
- Reference: `pensive:tiered-audit` skill

**Agent Dispatch Plan template:**

| # | Agent | Model | Scope | Output Contract |
|---|-------|-------|-------|-----------------|
| 1 | type | model | what it investigates | required_sections, min_evidence, strictness |

**Every dispatch MUST include an output contract:**

```yaml
output_contract:
  required_sections: [summary, findings, evidence]
  min_evidence_count: 3
  strictness: normal  # strict / normal / lenient
```

Agents without contracts will not have their output
validated. See `imbue:proof-of-work/modules/output-contracts`
for the full schema and templates.

**Worktree isolation decision:**

- Agents modifying **overlapping files**: use
  `isolation: "worktree"` for ALL of them
- Agents modifying **disjoint files**: skip isolation
- **Never mix** worktree and direct agents on the
  same file set (silent data loss)
- After dispatch: verify with `git worktree list`
  and `git diff --stat`

Reference: `do-issue/modules/parallel-execution.md`
(Worktree Isolation section)

**Why this rule exists:**

- 4+ agents without a plan -> lost observability,
  context overflow, wasted compute
- Research agents produce large outputs ->
  continuation agents lose state
- Without user alignment, agents may investigate
  the wrong dimensions
- Without output contracts, agents cut corners and
  produce unverifiable findings
- Agents can delete files and fail to recreate
  replacements (verify outputs exist)

**Threshold:** 1-3 agents can dispatch directly.
4+ agents require plan mode.

**References:**

- `plugins/sanctum/skills/do-issue/modules/parallel-execution.md`
- `plugins/imbue/skills/proof-of-work/modules/output-contracts.md`
- `plugins/pensive/skills/tiered-audit/SKILL.md`
