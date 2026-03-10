# Hook Types Overview

Claude Code hook lifecycle events and their use cases. Hooks intercept specific moments in the session to inject context, validate actions, or transform outputs.

## Quick Reference (Claude Code 2.1.50)

### Lifecycle Hooks
- **Setup**: One-time plugin initialization
- **SessionStart**: Session initialization, context setup
- **SessionEnd**: Session cleanup, metrics collection
- **Stop**: Graceful shutdown, final logging

### Tool Execution Hooks
- **PreToolUse**: Validation, logging, state management
- **PostToolUse**: Result processing, metrics, cleanup
- **PostToolUseFailure**: Error handling, fallback (2.1.20+)

### Permission Hooks
- **PermissionRequest**: Auto-approve/deny patterns

### Communication Hooks
- **UserPromptSubmit**: Input validation, routing
- **Notification**: System notification forwarding (2.1.20+)

### Agent Coordination Hooks
- **SubagentStart**: Track agent spawns (2.1.20+)
- **SubagentStop**: Collect results, cleanup
- **TeammateIdle**: Work assignment (2.1.33+).
  Supports `{"continue": false}` to stop teammate
  (2.1.69+).
- **TaskCompleted**: Task chaining (2.1.33+).
  Supports `{"continue": false}` to stop teammate
  (2.1.69+).

### Configuration Hooks
- **ConfigChange**: React to settings changes (2.1.49+)
- **InstructionsLoaded**: Augment instructions (2.1.33+)

### Context Hooks
- **PreCompact**: Preserve critical context before compaction

### Worktree Hooks (2.1.50+, plugin fix 2.1.69+)
- **WorktreeCreate**: Initialize worktree state.
  Command-only (no Python SDK callback, no matchers).
  Must print absolute worktree path on stdout.
  Plugin-registered hooks were silently ignored before
  2.1.69; now they fire correctly.
- **WorktreeRemove**: Cleanup worktree state.
  Command-only (no Python SDK callback, no matchers).
  Receives `worktree_path` in input. Cannot block
  removal. Plugin-registered hooks were silently
  ignored before 2.1.69; now they fire correctly.

### HTTP Hooks (2.1.63+)

Hooks can POST JSON to a URL instead of running shell
commands. Use `"type": "http"` with a `"url"` field.
The hook POSTs the standard hook input as JSON and
expects a standard hook response JSON body. Useful for
enterprise/sandboxed environments where shell execution
is restricted. See `Skill(abstract:hook-authoring)` for
full configuration details.

### Hook Event Fields: agent_id and agent_type (2.1.69+)

All hook events now include an `agent_id` field for
subagent sessions and an `agent_type` field for both
subagent sessions and `--agent` invocations. Use these
fields to distinguish which agent triggered the hook
and to implement agent-specific hook logic.

```json
{
  "session_id": "sess_abc",
  "hook_event_name": "PreToolUse",
  "agent_id": "backend@my-team",
  "agent_type": "implementer",
  "tool_name": "Bash",
  "tool_input": { "command": "make test" }
}
```

Status line hooks also gain a `worktree` field
(2.1.69+) containing `name`, `path`, `branch`, and
`originalRepoDir` when running in a `--worktree`
session.

### Cron Scheduling Tools (2.1.71+)

Three new built-in tools for session-scoped scheduled
tasks: `CronCreate`, `CronList`, and `CronDelete`.
Hooks can match on these tool names in `PreToolUse`
and `PostToolUse` events. The `/loop` command uses
`CronCreate` internally.

- `CronCreate`: Schedule a recurring or one-shot task
  with a 5-field cron expression and prompt
- `CronList`: List all scheduled tasks with IDs
- `CronDelete`: Cancel a task by ID

A session can hold up to 50 scheduled tasks. Recurring
tasks auto-expire after 3 days. Disable the scheduler
entirely with `CLAUDE_CODE_DISABLE_CRON=1`.

### Bash Auto-Approval Expansion (2.1.71+)

Added to the default bash auto-approval allowlist:
`fmt`, `comm`, `cmp`, `numfmt`, `expr`, `test`,
`printf`, `getconf`, `seq`, `tsort`, and `pr`. These
are standard POSIX text/math utilities that execute
without permission prompts. Hooks using
`PermissionRequest` should account for these commands
no longer triggering permission events.

### Heredoc Permission Fix (2.1.71+)

Compound bash commands containing heredoc commit
messages no longer trigger false-positive permission
prompts. This fixes the common pattern:

```bash
git commit -m "$(cat <<'EOF'
feat: my commit message
EOF
)"
```

Previously this could prompt for permission even when
`Bash(git commit *)` was in the allow list.

### Security: Workspace Trust (2.1.51+)

Hook commands that emit `statusLine` or `fileSuggestion`
now require workspace trust acceptance in interactive
mode. Untrusted hooks cannot execute these commands
until the user has accepted workspace trust. If your
hook outputs status line updates or file suggestions,
test it in both trusted and untrusted workspace contexts.

## Hook Selection Guide

| Use Case | Recommended Hook | Why |
|----------|------------------|-----|
| Log all tool calls | PreToolUse | Captures before execution |
| Track execution time | Pre + PostToolUse | Measure duration |
| Validate inputs | UserPromptSubmit | Before processing |
| Handle tool errors | PostToolUseFailure | Error-specific handling |
| Auto-approve tools | PermissionRequest | Bypass permission dialog |
| Initialize session | SessionStart | One-time setup |
| Cleanup resources | SessionEnd/Stop | Guaranteed cleanup |
| Multi-agent coordination | TeammateIdle/TaskCompleted | Agent team workflows |
| React to config | ConfigChange | Settings-driven behavior |

## See Complete Guide

The comprehensive hook types guide includes:
- Detailed lifecycle diagrams
- Complete code examples for each hook type
- Advanced patterns and combinations
- Performance considerations
- Migration guides

See `Skill(abstract:hook-authoring)` for the full hook development guide and examples.
