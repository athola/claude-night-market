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

Tasks involving comprehensive analysis, audits, or research across the codebase typically require 4+ parallel agents. Before dispatching:

**MUST enter plan mode first:**
1. `EnterPlanMode` — design the agent strategy
2. Specify: agent roster, scope per agent, output contract
3. Get user approval before launching agents

**Agent Dispatch Plan template:**

| # | Agent Type | Model | Scope | Output Contract |
|---|-----------|-------|-------|-----------------|
| 1 | type | model | what it investigates | what it returns |

**Why this rule exists:**
- 4+ agents without a plan → lost observability, context overflow, wasted compute
- Research agents produce large outputs → continuation agents lose state
- Without user alignment, agents may investigate the wrong dimensions

**Threshold:** 1-3 agents can dispatch directly. 4+ agents require plan mode.

**Reference:** `plugins/sanctum/skills/do-issue/modules/parallel-execution.md`
