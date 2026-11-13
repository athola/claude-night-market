---
name: agent-teams
description: "Running the War Room panel as a Claude Code agent team: when it helps, team configuration, deliberation flow, fallback to conjure, and cost."
---

### Overview

When `--agent-teams` is specified (or auto-selected for Full Council / Delphi modes), the War Room uses Claude Code Agent Teams instead of sequential conjure delegation. Each expert runs as a persistent teammate with bidirectional messaging. Experts deliberate in real time instead of through batch request/response cycles.

**Requires**: Claude Code 2.1.32+, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, tmux installed.

### When Agent Teams Helps

| Mode | Without Agent Teams | With Agent Teams | Benefit |
|------|-------------------|-----------------|---------|
| Express | Sonnet direct call | N/A (overkill) | None: skip |
| Lightweight | 3 sequential delegations | N/A (overhead exceeds benefit) | None: skip |
| Full Council | 7 sequential/parallel delegations | 7 teammates with live inbox messaging | Experts can **react** to each other's COAs in real-time |
| Delphi | Multiple delegation rounds | Persistent team iterates until convergence | No re-invocation cost per round, and state persists across rounds |

**Rule of thumb**: Use agent teams only for Full Council and Delphi modes. Lightweight and Express modes don't generate enough inter-expert traffic to justify the coordination overhead.

### Team Configuration

```bash
# War Room agent team structure
Team: war-room-{session-id}
  Lead: supreme-commander (Opus) — orchestrates phases, final synthesis
  Teammates:
    chief-strategist (Sonnet) — approach generation
    intel-officer (Sonnet) — deep context analysis
    field-tactician (Sonnet) — implementation feasibility
    scout (Haiku) — rapid reconnaissance
    red-team (Sonnet) — adversarial challenge
    logistics (Haiku) — resource estimation
```

Note: In agent teams mode, all teammates run as Claude Code instances (Opus/Sonnet/Haiku). External LLM experts (Gemini, Qwen, GLM) are not used because agent teams requires the Claude CLI. The trade-off is losing model diversity but gaining real-time inter-expert messaging.

### Deliberation Flow with Agent Teams

1. **Lead creates team** → spawns teammates in tmux panes
2. **Phase 1 (Intel)**: Lead assigns intel tasks to scout and intel-officer via inbox
3. **Phase 3 (COA)**: Lead broadcasts situation assessment. Teammates develop COAs independently, and messaging allows clarifying questions mid-development
4. **Phase 4 (Red Team)**: Red-team teammate receives all COAs and posts challenges. Other teammates can **respond to challenges in real-time**
5. **Phase 5 (Voting)**: Lead broadcasts ballot, and teammates rank via inbox messages
6. **Phase 6 (Premortem)**: All teammates receive selected COA and can build on each other's failure scenarios
7. **Phase 7 (Synthesis)**: Lead collects all artifacts, produces decision
8. **Phase 8 (Discussion Publishing)**: After the
   Supreme Commander Decision document is finalized,
   you MUST execute `modules/discussion-publishing.md`
   to publish the decision to GitHub Discussions.
   Publishing is the default. The user can decline
   with "n". See the "Discussion Publishing (REQUIRED)"
   section below for the full step-by-step workflow.

### Falling Back to Conjure Delegation

If agent teams fails (tmux unavailable, team creation error), the War Room automatically falls back to standard conjure delegation. The deliberation protocol is identical: only the execution backend differs.

### Cost Considerations

Agent teams is significantly more token-intensive than conjure delegation (each teammate maintains its own context window). Use only when the coordination value justifies the cost, typically Delphi mode where multiple rounds of revision make persistent teammates worthwhile.
