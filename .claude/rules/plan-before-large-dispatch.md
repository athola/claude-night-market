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

**MUST enter plan mode first:**

1. `EnterPlanMode` -- design the agent strategy
2. Specify: agent roster, scope per agent, output
   contract
3. Get user approval before launching agents

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
