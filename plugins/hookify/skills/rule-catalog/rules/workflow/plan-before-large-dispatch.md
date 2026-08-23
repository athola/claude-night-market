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

Planning before dispatching agents respects the context
window and the work that depends on coherent results.
(Foresight)

**Plan mode required for large agent dispatch!**

Tasks involving comprehensive analysis, audits, or research across the codebase typically require 4+ parallel agents. Before dispatching:

**MUST get user alignment first.** Two compliant paths:

1. `EnterPlanMode`: design the agent strategy, specify the roster, the scope per agent and the output contract, then get approval before launching.
2. A Workflow script. The script is the plan in executable form, and it carries its own user gate, because a workflow only runs when the user asks for one.

Pick path 2 when the shape is known before the work. Pick path 1 when the roster has to adapt to what the first agents find. A workflow never starts unasked, its subagents inherit the tool allowlist, and its script has no filesystem or shell, so it can find and rank but cannot prove a test passed. The docs say subagents always run in `acceptEdits`. Measured once on CLI 2.1.241 a subagent's edit still prompted from a manual-mode session, so do not rely on unattended completion.

**Agent Dispatch Plan template:**

| # | Agent Type | Model | Scope | Output Contract |
|---|-----------|-------|-------|-----------------|
| 1 | type | model | what it investigates | what it returns |

**Why this rule exists:**
- 4+ agents without a plan cost observability, overflow the context, and waste compute
- Research agents produce large outputs, so continuation agents lose state
- Without user alignment, agents may investigate the wrong dimensions

A workflow answers the first two directly: results stay in script variables instead of the session, and `schema` enforces the output contract at the tool-call layer.

**Threshold:** 1-3 agents can dispatch directly. 4+ agents require plan mode.

**Canonical copy:** `.claude/rules/plan-before-large-dispatch.md` in claude-night-market. This catalog entry is a condensed mirror; when they disagree, the canonical copy wins.

**Reference:** `plugins/sanctum/skills/do-issue/modules/parallel-execution.md`
