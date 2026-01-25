---
name: session-management
description: |
  Triggers: session, resume, rename, checkpoint
  Manage Claude Code sessions with naming, checkpointing, and resume strategies.
  Use when: organizing long-running work, creating debug checkpoints, managing PR reviews
category: workflow
tags: [session, resume, checkpoint, debugging]
tools: [Bash]
complexity: low
estimated_tokens: 400
version: 1.3.5
---

# Session Management

## Overview

Claude Code supports named sessions for better workflow organization. Use this skill to manage complex, long-running work across multiple sessions.

## Available Commands

| Command | Description |
|---------|-------------|
| `/rename` | Name the current session |
| `/resume` | Resume a previous session (REPL) |
| `claude --resume <name>` | Resume from terminal |

## Workflow Patterns

### 1. Debugging Sessions

Name debug sessions for easy resumption:

```
# Start debugging
/rename debugging-auth-issue

# ... work on the issue ...

# If you need to pause, session is auto-saved
# Resume later:
claude --resume debugging-auth-issue
```

### 2. Feature Development Checkpoints

Create checkpoints during long feature work:

```
# After completing milestone 1
/rename feature-x-milestone-1

# Continue in new session
# Reference old session if needed
```

### 3. PR Review Sessions

For complex PR reviews that span multiple sittings:

```
# Start review
/rename pr-review-123

# Take breaks without losing context
# Resume:
claude --resume pr-review-123
```

### 4. Investigation Sessions

When investigating issues that may require research:

```
# Start investigation
/rename investigate-memory-leak

# Pause to gather more info externally
# Resume with full context:
claude --resume investigate-memory-leak
```

## Resume Screen Features

The `/resume` screen provides:

- **Grouped forked sessions**: See related sessions together
- **Keyboard shortcuts**:
  - `P` - Preview session content
  - `R` - Rename a session
- **Recent sessions**: Sorted by last activity

## Best Practices

### Naming Conventions

Use descriptive, hyphenated names:

| Pattern | Example | Use Case |
|---------|---------|----------|
| `debugging-<issue>` | `debugging-auth-401` | Bug investigation |
| `feature-<name>-<milestone>` | `feature-search-v2` | Feature development |
| `pr-review-<number>` | `pr-review-156` | PR reviews |
| `investigate-<topic>` | `investigate-perf` | Research |
| `refactor-<area>` | `refactor-api-layer` | Refactoring work |

### When to Name Sessions

Name sessions when:
- Work will span multiple days
- You might need to pause unexpectedly
- The session contains valuable context
- You want to reference it later

### Session Cleanup

Unnamed sessions are eventually garbage collected. Named sessions persist longer. Periodically clean up old named sessions you no longer need.

## Integration with Sanctum

Combine session management with other Sanctum skills:

1. **Before starting**: Run `Skill(sanctum:git-workspace-review)` to capture context
2. **Name the session**: `/rename <descriptive-name>`
3. **Work**: Use appropriate skills for the task
4. **Resume if needed**: `claude --resume <name>`

## Troubleshooting

### Session Not Found

If a named session isn't appearing in `/resume`:
- Check for typos in the name
- Sessions may expire after extended inactivity
- Use `/resume` screen to browse available sessions

### Lost Context After Resume

If context seems incomplete after resuming:
- Use `/catchup` to refresh git state
- Re-run `Skill(sanctum:git-workspace-review)` if needed

## See Also

- `/catchup` - Refresh context from git changes
- `/clear` - Start fresh session
- `Skill(sanctum:git-workspace-review)` - Capture repo context
