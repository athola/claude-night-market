# War Room Specification: Overview

**Version**: 1.0.0-draft
**Date**: 2026-01-20
**Status**: Draft - Pending Review
**Branch**: war-room-brainstorm-1.3.1

---

## Document Index

This specification is split into multiple files for maintainability:

| Document | Contents |
|----------|----------|
| [Overview](war-room-spec-overview.md) | Executive summary, design decisions (this file) |
| [Architecture](war-room-spec-architecture.md) | System components, data flow, Strategeion |
| [Expert Panel](war-room-spec-experts.md) | Expert roles, invocation patterns, escalation |
| [Protocol](war-room-spec-protocol.md) | Deliberation phases, prompt templates |
| [Data Structures](war-room-spec-data.md) | Merkle-DAG, aggregation, session persistence |
| [Integration](war-room-spec-integration.md) | Conjure, commands, skills, hooks |
| [Implementation](war-room-spec-implementation.md) | Phases, success criteria, references |

---

## Executive Summary

The War Room is a multi-LLM deliberation system for pressure-based decision making. It orchestrates multiple AI experts (via conjure delegation) to analyze problems from diverse perspectives, challenge assumptions through adversarial review, and synthesize optimal approaches under the guidance of a Supreme Commander.

### Core Philosophy

> "The trick is that there is no trick. The power of intelligence stems from our vast diversity, not from any single, perfect principle."
> — Marvin Minsky, *Society of Mind*

The War Room draws from:
- **Sun Tzu**: Intelligence gathering through specialized agents
- **Clausewitz**: Acknowledging friction and fog in decision-making
- **Robert Greene**: Unity of command with participatory input
- **MDMP**: Structured course-of-action development and wargaming
- **Karpathy's LLM Council**: Anonymized peer review and chairman synthesis
- **Gary Klein**: Premortem analysis for failure mode identification

---

## Design Decisions Summary

| Decision | Selected Option |
|----------|-----------------|
| **Integration Point** | B+C: Separate `/attune:war-room` command + `Skill(attune:war-room)`, with hook option (D) for future gated auto-trigger |
| **Expert Panel** | Lightweight by default; Supreme Commander escalates to full council when justified |
| **Deliberation Rounds** | Two-round default; Delphi-style for high-stakes |
| **Anonymization** | Merkle-tree DAG with hash-masked attribution until decision finalized |
| **Aggregation** | Hybrid: voting to narrow to top 2-3, then Chairman synthesis; meritocracy override available |
| **Red Team Timing** | After all COAs generated + Premortem on selected approach |
| **Token Budget** | No cap; quality over cost; delegate lower-level thinking to cheaper models |
| **Session Persistence** | File-based JSON + Strategeion (war palace) in memory-palace |
| **Conjure Integration** | New `war_room_orchestrator.py` composing `delegation_executor` calls |
| **Failure Handling** | Graceful degradation with logged gaps |
| **Execution Permissions** | All conjured agents run with dangerous permissions (bypass permission prompts) |
| **Hook Auto-Trigger** | Hybrid: complexity score + user settings + keyword detection |

---

## Execution Permissions

### Dangerous Mode for All Experts

All conjured/delegated agents run with **dangerous permissions** to avoid interactive permission prompts that would block automated deliberation. This is safe because:

1. Experts are invoked with specific, audited prompts
2. Output is captured and reviewed by Supreme Commander before action
3. No file modifications occur during deliberation (read-only analysis)
4. Session is fully logged for audit

### Invocation Commands

| Service | Standard | Dangerous Mode (Required) |
|---------|----------|---------------------------|
| **Gemini** | `gemini -p "..."` | `gemini -p "..."` (no auth prompts) |
| **Qwen** | `qwen -p "..."` | `qwen -p "..."` (no auth prompts) |
| **GLM-4.7** | `claude-glm -p "..."` | `claude-glm --dangerously-skip-permissions -p "..."` |
| **Alias** | `ccg` | `ccgd` |

### GLM-4.7 Configuration

GLM-4.7 uses a dedicated configuration at `~/.claude-glm/`:

```bash
# ~/.local/bin/claude-glm script sets:
export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
export ANTHROPIC_AUTH_TOKEN="<zai-api-key>"
export ANTHROPIC_MODEL="glm-4.7"
export ANTHROPIC_SMALL_FAST_MODEL="glm-4.5-air"
export CLAUDE_HOME="$HOME/.claude-glm"
```

**Invocation for War Room**:
```bash
# Preferred: alias with dangerous permissions
ccgd -p "Expert prompt here"

# Fallback: explicit command (if alias not configured)
claude-glm --dangerously-skip-permissions -p "Expert prompt here"
```

---

**Next**: See [Architecture](war-room-spec-architecture.md) for system components and data flow.
