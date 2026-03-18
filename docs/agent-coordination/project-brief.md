# Agent Coordination Architecture -- Project Brief

## Problem Statement

The claude-night-market framework dispatches subagents for
complex tasks (code review, auditing, research), but
three failure modes consistently degrade output quality:

1. **Parent skim-reading**: When multiple subagents return
   results simultaneously, the parent agent processes them
   under growing context pressure.
   It filters, summarizes, and drops detail from the
   synthesized report.
   The user receives a shallow composite instead of the
   deep analysis each subagent actually produced.

2. **Subagent corner-cutting**: Subagents under completion
   pressure truncate their work to "finish."
   Even well-prompted agents skip edge cases, collapse
   findings into summaries, and present superficial
   conclusions rather than evidence-backed analysis.

3. **Hub-and-spoke bottleneck**: All coordination flows
   through the parent agent.
   Subagents cannot share discoveries, coordinate work
   boundaries, or build on each other's findings.
   The parent becomes both coordinator and quality gate,
   overloading its context with orchestration overhead.

### Root Cause: Context Rot

These symptoms trace to a well-documented architectural
property of transformer-based attention.
Research from Chroma (2025) testing 18 frontier models
found that *every model* degrades at *every context
length increment* -- not just near capacity limits.
Key findings:

- At 20K tokens, signal-to-noise ratio drops to ~2.5%
  (500 relevant tokens among 20,000 total)
- Models attend strongly to beginning and end of context,
  poorly to the middle (U-shaped attention curve)
- Doubling task duration quadruples failure rates
  (non-linear degradation)
- Coding agents spend over 60% of their first turn
  just retrieving context (Cognition/Devin measurement)
- Anthropic's multi-agent research showed 90.2%
  improvement over single-agent Opus 4 by isolating
  search into subagents with independent context windows

Larger context windows do not solve this.
A 1M window full of stale tool outputs performs worse
than 200K of structured, relevant state.

## Proposed Solution Areas

### S1: Tiered Audit Strategy (Sequential-First)

**Instead of**: Spawning 4-8 agents to audit the whole
codebase simultaneously.

**Do this**: Audit git history first (lightweight, bounded),
then selectively deep-dive into flagged areas.
Full codebase audit is gated behind a high tier requiring
explicit justification.

Inspired by RepoAudit (ICLR 2025), which processes one
function at a time with bounded exploration depth (max 4
calling levels), achieving 65.5% precision on repos
averaging 251K lines.
Sequential-then-selective beats parallel-everything.

**Approach**: Three tiers of escalating scope:

- **Tier 1 -- Git history audit**: `git log`, `git diff`,
  blame analysis.
  Identifies what changed, who changed it, and why.
  Fast, bounded, low context cost.
- **Tier 2 -- Targeted area audit**: Deep-dive into
  specific files/modules flagged by Tier 1.
  One area at a time, sequential, full detail preserved.
- **Tier 3 -- Full codebase audit**: Only when Tiers 1-2
  insufficient.
  Requires explicit user approval.
  Uses dedicated window sessions, not subagents.

### S2: File-Based Inter-Agent Communication

**Instead of**: Hub-and-spoke where all results flow
through the parent agent's context.

**Do this**: Agents write findings to structured files.
Other agents (or the parent) read selectively.
The parent's context stays clean.

Inspired by the GitHub-based orchestrator pattern where
6 specialized agents coordinate through trigger files
(`triggers/{agent}.trigger`) and response files
(`responses/{agent}.response`) with structured prefixes
(DONE, ISSUE, LABEL-UPDATED, PR).

**Approach**: Shared workspace directory (`.coordination/`):

```
.coordination/
  tasks.json          # Shared task list with states
  agents/
    reviewer.findings  # Structured output per agent
    auditor.findings
    tester.findings
  handoffs/
    reviewer-to-tester.md  # Explicit handoff context
  summary.md           # Synthesized by coordinator last
```

Key properties:
- Each agent writes to its own file (no conflicts)
- Parent reads selectively (only what it needs to
  synthesize)
- Full detail preserved in files even if parent
  summarizes
- User can read raw findings directly
- Debuggable: exact files visible, no opaque context

### S3: Three-Tier Agent Memory Architecture

**Instead of**: Vector-search-everything (2023 approach)
or context-window-as-memory.

**Do this**: Tiered memory by urgency, with agents
curating their own context deliberately.

Inspired by the "Why Your Agent's Memory Architecture
Is Probably Wrong" (DEV Community, 2026) and the
ICLR 2026 MemAgents workshop proposal.

**Approach**:

- **Hot tier**: Single `memory.md` per agent, 200-line
  hard limit.
  Current priorities, active warnings, next actions.
  Loaded at session start.
- **Warm tier**: Topic files pulled on demand.
  Agent deliberately retrieves based on current task.
- **Cold tier**: Searchable archive.
  Monthly summaries, historical records.
  Accessed only when investigating past decisions.

The 200-line constraint forces prioritization and
prevents unbounded context growth.
Agents control what they remember, not a retrieval
algorithm.

### S4: Auto-Role Assignment per Codebase Area

**Instead of**: Generic agents dispatched with ad-hoc
prompts containing whatever context the parent remembers.

**Do this**: Map codebase areas to specialist agent
configurations that auto-load relevant context.

Inspired by the agent orchestrator pattern where
"specialized agents with focused context significantly
outperform generalist agents" and OpenCode's agent.md
blueprint approach.

**Approach**: Directory-based agent registry:

```
.claude/area-agents/
  plugins-abstract.md    # Agent config for plugins/abstract/
  plugins-egregore.md    # Agent config for plugins/egregore/
  plugins-conserve.md    # Agent config for plugins/conserve/
  hooks.md               # Agent config for hooks/
  book.md                # Agent config for book/
```

Each file contains:
- Codebase area ownership (glob patterns)
- Relevant architectural decisions and patterns
- Testing conventions for that area
- Common pitfalls and gotchas
- Preferred tools and review focus

When work targets a specific area, the matching agent
config is loaded automatically -- providing deep context
without manual prompt engineering.

### S5: Dedicated Window Sessions over Subagents

**Instead of**: Spawning many subagents within one
Claude Code session (shared context, corner-cutting
under completion pressure).

**Do this**: For complex multi-area work, use dedicated
Claude Code sessions (separate tmux panes or Agent Teams)
with file-based coordination.

Inspired by Claude Code Agent Teams (2026) which enables
direct mesh communication between independent sessions,
and the user's direct experience that separate windows
produce better results than subagents.

**Approach**:

- **Simple tasks (1-3 focused areas)**: Subagents are
  fine.
  Each gets a tight prompt with specific scope.
- **Complex audits (4+ areas)**: Use Agent Teams or
  dedicated tmux sessions.
  Each session gets full context window, no completion
  pressure from parent.
  Coordinate via `.coordination/` files.
- **Codebase-wide reviews**: Sequential, one area per
  session.
  Results accumulate in files.
  Final synthesis session reads all findings.

### S6: Output Contracts and Evidence Gates

**Instead of**: Trusting subagents to self-report
completion quality.

**Do this**: Define strict output contracts with
evidence requirements.
Validate outputs before accepting them.

Inspired by RepoAudit's dual validation (alignment +
feasibility), the imbue proof-of-work pattern, and
the observation that "most sub-agent failures stem from
invocation quality, not execution failures."

**Approach**:

- Every agent dispatch includes an output contract:
  required sections, minimum evidence count, specific
  artifacts expected.
- Validator pass checks contract compliance before
  results are accepted.
- Incomplete results trigger retry with specific
  feedback, not wholesale re-dispatch.
- Evidence tags (`[E1]`, `[E2]`) required for all
  claims.

## Research Sources

- [Context Rot: Why LLMs Degrade as Context Grows][1]
- [Multi-Agent Memory from a Computer Architecture
  Perspective][2]
- [Why Your Agent's Memory Architecture Is Probably
  Wrong][3]
- [Building an AI Agent Orchestrator: 6 Agents
  Coordinate Through GitHub][4]
- [Claude Code Sub-Agents: Parallel vs Sequential
  Patterns][5]
- [Claude Code Agent Teams: Complete Guide 2026][6]
- [RepoAudit: Autonomous LLM-Agent for Repository-Level
  Code Auditing][7]
- [Multi-Agent Collaboration Mechanisms: A Survey of
  LLMs][8]
- [Agent Communication Protocols: Comparing MCP, Cord,
  and Smolagents][9]
- [MemAgents: Memory for LLM-Based Agentic Systems
  (ICLR 2026 Workshop)][10]

[1]: https://www.morphllm.com/context-rot
[2]: https://arxiv.org/html/2603.10062
[3]: https://dev.to/agentteams/why-your-agents-memory-architecture-is-probably-wrong-55fc
[4]: https://dev.to/alprimak/building-an-ai-agent-orchestrator-how-6-specialized-agents-coordinate-through-github-55gk
[5]: https://claudefa.st/blog/guide/agents/sub-agent-best-practices
[6]: https://claudefa.st/blog/guide/agents/agent-teams
[7]: https://arxiv.org/html/2501.18160v1
[8]: https://arxiv.org/abs/2501.06322
[9]: https://www.sitepoint.com/agent-communication-protocols-comparing-mcp--cord--and-smolagents/
[10]: https://openreview.net/pdf?id=U51WxL382H

## Constraints

- **Branch budget**: Current branch is in RED ZONE
  (8753 lines, 28 commits).
  This initiative MUST target a new branch.
- **Python 3.9+**: All tooling must maintain
  compatibility.
- **Plugin architecture**: Solutions must fit the
  night-market plugin model (skills, agents, hooks,
  commands).
- **No new infrastructure**: File-based coordination
  preferred over databases, message queues, or external
  services.
- **Incremental adoption**: Each solution area (S1-S6)
  should be independently deployable.

## Success Criteria

1. Multi-agent audit reports preserve the detail level
   of individual agent findings (no skim-reading loss).
2. Subagent outputs pass evidence-gate validation before
   acceptance.
3. Codebase audits default to git-history-first (Tier 1)
   and require explicit escalation for full scans.
4. Agent coordination uses file-based communication,
   keeping the parent's context clean.
5. Codebase areas have auto-loaded specialist
   configurations.
6. Complex multi-area work defaults to dedicated sessions
   over subagents.

## Priority Order

1. **S1 (Tiered Audit)** + **S6 (Output Contracts)** --
   Highest impact, lowest implementation complexity.
   Addresses both skim-reading and corner-cutting directly.
2. **S2 (File-Based Communication)** -- Enables all other
   improvements by decoupling agent output from parent
   context.
3. **S4 (Auto-Role Assignment)** -- Leverages existing
   plugin infrastructure and agent.md patterns.
4. **S3 (Three-Tier Memory)** -- Extends existing
   conserve and memory-palace patterns.
5. **S5 (Dedicated Sessions)** -- Depends on Agent Teams
   maturity; manual tmux approach works today.
