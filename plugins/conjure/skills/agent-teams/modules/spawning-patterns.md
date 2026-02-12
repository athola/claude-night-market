---
name: spawning-patterns
description: tmux-based agent spawning, CLI identity flags, and pane management
parent_skill: conjure:agent-teams
category: delegation-framework
estimated_tokens: 200
---

# Spawning Patterns

## Overview

Each teammate runs as an independent `claude` CLI process in a tmux split pane. The team lead spawns teammates via `tmux split-window`, passing identity flags so each agent knows its role within the team.

## Required Environment Variables

```bash
export CLAUDECODE=1
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

These are set automatically by the spawner before launching each teammate.

### Nested Session Guard (Claude Code 2.1.39+)

Claude Code 2.1.39 added a guard that prevents launching `claude` inside another `claude` session. Agent teams are **unaffected** because:
- tmux `split-window` creates an independent shell environment
- The `CLAUDECODE=1` env var is set explicitly per pane, not inherited from a parent session
- The guard targets accidental recursive invocations, not intentional team spawning

If you encounter the guard unexpectedly, ensure you're using tmux or iTerm2 pane splitting (not subshell invocations like `claude -p "..." | ...` within an existing session).

## CLI Identity Flags

```bash
claude \
  --agent-id "backend@my-team" \
  --agent-name "backend" \
  --team-name "my-team" \
  --agent-color "#FF6B6B" \
  --agent-role "implementer" \
  --parent-session-id "$LEAD_SESSION_ID" \
  --agent-type "general-purpose" \
  --model sonnet
```

| Flag | Format | Description |
|------|--------|-------------|
| `--agent-id` | `<name>@<team>` | Unique agent identifier |
| `--agent-name` | string | Human-readable name |
| `--team-name` | string | Team this agent belongs to |
| `--agent-color` | hex color | Visual distinction in tmux |
| `--parent-session-id` | string | Links to lead agent's session |
| `--agent-type` | string | Role type (e.g., `general-purpose`) |
| `--agent-role` | string | Crew role: `implementer`, `researcher`, `tester`, `reviewer`, `architect` (default: `implementer`) |
| `--model` | string | Model selection: `sonnet`, `opus`, `haiku` (2.1.39+ correctly qualifies for Bedrock/Vertex/Foundry) |
| `--plan-mode-required` | flag | Optional: enforce planning mode |

## Agent ID Format

The agent-id follows the pattern `<name>@<team-name>`, creating a unique namespace:
- `backend@refactor-team`
- `frontend@refactor-team`
- `reviewer@code-review`

## tmux Pane Management

### Spawning

```bash
# Split current window horizontally, run claude in new pane
tmux split-window -h "CLAUDECODE=1 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 \
  claude --agent-id backend@my-team --agent-name backend ..."
```

The spawner captures the new pane ID from tmux and stores it in the team config's member entry (`tmux_pane_id` field).

### Color Assignment

Colors are assigned from a palette based on member index:
```
["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"]
```

### Killing a Pane

```bash
tmux kill-pane -t <pane_id>
```

Used during force-kill and graceful shutdown after approval.

## iTerm2 Alternative

Agent Teams also supports iTerm2 with the `it2` CLI as an alternative to tmux. The coordination protocol (files, messages, tasks) is identical — only the terminal multiplexer differs.

## Agent Name Validation

- Must match `^[A-Za-z0-9_-]+$`
- Under 64 characters
- Cannot be `team-lead` (reserved for the lead agent)
- Must be unique within the team

## Spawning Sequence

1. Validate agent name (uniqueness, format)
2. Assign color from palette
3. Create `TeammateMember` with metadata (model, type, cwd)
4. Register member in team config (atomic write)
5. Create empty inbox file for the agent
6. Send initial prompt to agent's inbox via messaging protocol
7. Execute `tmux split-window` with full CLI flags
8. Capture and store `tmux_pane_id` in member config

## Graceful Shutdown Protocol

1. Lead sends `shutdown_request` message with unique request ID
2. Teammate receives request, finishes current work
3. Teammate sends `shutdown_response` approving the shutdown
4. Lead calls `process_shutdown_approved` to clean up pane and config
