# Post-Implementation Workflow Hooks Design

**Date:** 2025-12-07
**Status:** Approved
**Plugin:** sanctum

## Overview

Hooks that inject mandatory workflow instructions to Claude, ensuring documentation, testing, and demonstration targets are updated after feature implementations or plan executions.

## Problem Statement

When completing feature implementations or executing plans, Claude should automatically run:
1. `/sanctum:update-docs` - Update documentation
2. `/abstract:make-dogfood` - Update Makefile demonstration targets
3. `/sanctum:update-readme` - Update README
4. `/sanctum:update-tests` - Review and update tests

Without explicit reminders, these steps may be skipped.

## Design

### Hook 1: SessionStart - Governance Injection

**Purpose:** Inject non-negotiable workflow instructions at session start.

**Event:** `SessionStart`

**Output:** Injects governance policy as additional context that Claude carries through the session.

**Framing:** Uses policy language (not suggestions) to resist override attempts from other prompts, skills, or hooks.

### Hook 2: Stop - Verification Safeguard

**Purpose:** Warn if post-implementation commands weren't run when they should have been.

**Event:** `Stop`

**Behavior:** Lightweight check that reminds about the protocol. Cannot block (Stop hooks are informational), but provides final reminder.

## Security Considerations

| Threat | Mitigation |
|--------|------------|
| Override by other hooks | SessionStart runs early, frames context |
| Skills bypassing workflow | Governance framing, not suggestion |
| Context loss in long sessions | Stop hook provides backup reminder |
| User requesting skip | Users have authority; hook doesn't block legitimate overrides |

## Implementation

### File Structure

```
plugins/sanctum/hooks/
├── hooks.json                      # Hook registration
├── post_implementation_policy.py   # SessionStart hook
└── verify_workflow_complete.py     # Stop hook (optional safeguard)
```

### Hook Registration (hooks.json)

```json
{
  "SessionStart": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/hooks/post_implementation_policy.py",
          "timeout": 5
        }
      ]
    }
  ]
}
```

## Commands Triggered

1. `/sanctum:update-docs` - Documentation updates
2. `/abstract:make-dogfood` - Makefile demonstration targets
3. `/sanctum:update-readme` - README updates
4. `/sanctum:update-tests` - Test review and updates

## Success Criteria

- Claude receives governance instructions at session start
- Instructions persist through session regardless of other context
- Post-implementation workflow becomes automatic behavior
