# Scope Guard Integration with Superpowers

This document explains how to integrate scope-guard with the superpowers brainstorm→plan→execute workflow.

## Automatic Integration (Default)

**The imbue plugin now includes automatic scope-guard hooks.** When imbue is installed:

1. **SessionStart hook** - Injects scope-guard quick reference into every session
   - Shows worthiness formula and thresholds
   - Warns if branch is in Yellow/Red zone at session start

2. **UserPromptSubmit hook** - Monitors thresholds on every prompt
   - Checks lines, commits, days, new files
   - Alerts in Yellow/Red zone with specific warnings

**No configuration needed** - hooks activate automatically when imbue plugin is installed.

## Integration Approach

Since superpowers skills live in a separate repository, we integrate via:
1. **Automatic hooks** that inject scope-guard awareness (now default)
2. **Keyword triggers** in scope-guard that auto-activate after brainstorming/planning
3. **Manual invocation** at workflow checkpoints

## Option 1: Auto-Trigger via Keywords (Recommended)

The scope-guard skill includes activation patterns that trigger when:
- Keywords like "scope", "feature", "implement", "add", "extend" appear
- Brainstorming or planning context is detected
- Branch metrics approach thresholds

**No configuration needed** - Claude will naturally invoke scope-guard when relevant.

## Option 2: Add to Session Start Hook

Add to your `~/.claude/hooks/session-start.sh`:

```bash
#!/bin/bash
# Run scope-guard threshold check at session start for long-running branches

# Only check if we're in a git repo with uncommitted work
if git rev-parse --git-dir > /dev/null 2>&1; then
    DAYS_ON_BRANCH=$(( ($(date +%s) - $(git log -1 --format=%ct $(git merge-base main HEAD 2>/dev/null) 2>/dev/null || echo $(date +%s))) / 86400 ))

    if [ "$DAYS_ON_BRANCH" -gt 3 ]; then
        echo "scope-guard: Branch is $DAYS_ON_BRANCH days old. Consider running threshold check."
    fi
fi
```

## Option 3: Pre-PR Hook Installation

Copy the threshold check hook to your project:

```bash
# Copy hook to project
cp plugins/imbue/hooks/pre_pr_scope_check.sh .git/hooks/pre-push

# Or install globally
mkdir -p ~/.claude/hooks
cp plugins/imbue/hooks/pre_pr_scope_check.sh ~/.claude/hooks/
```

## Option 4: Manual Checkpoint Prompts

Add these prompts to your workflow:

### After Brainstorming
```
Before we document this design, let me use scope-guard to evaluate the proposed features.
Skill(imbue:scope-guard)
```

### Before Finalizing Plans
```
Before finalizing this implementation plan, let me check scope-guard thresholds.
Skill(imbue:scope-guard)
```

### During Long Branches
```
This branch has been active for a while. Let me run the scope-guard threshold check.
```

## Claude Code Settings Integration

Add to your `.claude/settings.json` to auto-remind:

```json
{
  "customInstructions": {
    "sessionReminders": [
      "After brainstorming sessions, invoke imbue:scope-guard to evaluate features",
      "Before finalizing plans, check branch thresholds with scope-guard"
    ]
  }
}
```

## Workflow Checkpoints

| Workflow Stage | Scope Guard Action |
|----------------|-------------------|
| End of brainstorming | Score all proposed features |
| Before plan finalization | Compare against backlog, check budget |
| Mid-implementation (Yellow threshold) | Review scope, consider splitting |
| Pre-PR (Red threshold) | Justify or defer items to backlog |

## Environment Variables

Customize thresholds via environment:

```bash
export SCOPE_GUARD_GREEN_LINES=1000
export SCOPE_GUARD_YELLOW_LINES=1500
export SCOPE_GUARD_RED_LINES=2000
export SCOPE_GUARD_GREEN_FILES=8
export SCOPE_GUARD_YELLOW_FILES=12
export SCOPE_GUARD_RED_FILES=15
export SCOPE_GUARD_GREEN_COMMITS=15
export SCOPE_GUARD_YELLOW_COMMITS=25
export SCOPE_GUARD_RED_COMMITS=30
```
