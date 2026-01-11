---
description: Audit and sync plugin.json files with disk contents (commands, skills, agents, hooks)
usage: /update-plugins [plugin-name] [--dry-run] [--fix]
---

# Update Plugin Registrations

Audit plugin.json files against actual disk contents and fix registration gaps.

## Arguments

- `plugin-name` - Optional: specific plugin to audit (default: all plugins)
- `--dry-run` - Show discrepancies without making changes
- `--fix` - Automatically add missing registrations

## What It Does

1. **Scans each plugin directory** for commands, skills, agents, hooks on disk
2. **Compares with plugin.json** registrations
3. **Reports discrepancies**: missing registrations, stale entries, ordering issues
4. **Optionally fixes** by updating plugin.json files

## Workflow

```bash
# Audit all plugins (dry run)
/update-plugins --dry-run

# Fix a specific plugin
/update-plugins pensive --fix

# Full audit and fix
/update-plugins --fix
```

## Manual Execution

If the command is unavailable, run this audit script:

```bash
for plugin in plugins/*/; do
  name=$(basename "$plugin")
  pjson="$plugin/.claude-plugin/plugin.json"
  [ -f "$pjson" ] || continue

  echo "=== $name ==="

  # Commands
  echo "Commands in plugin.json:"
  jq -r '.commands[]? // empty' "$pjson" | sed 's|.*/||' | sort
  echo "Commands on disk:"
  ls "$plugin/commands/"*.md 2>/dev/null | xargs -I{} basename {} | sort

  # Skills
  echo "Skills in plugin.json:"
  jq -r '.skills[]? // empty' "$pjson" | sed 's|.*/||' | sort
  echo "Skills on disk:"
  ls -d "$plugin/skills"/*/ 2>/dev/null | xargs -I{} basename {} | sort

  echo ""
done
```

## Discrepancy Types

| Type | Meaning | Action |
|------|---------|--------|
| **Missing** | File on disk, not in plugin.json | Add registration |
| **Stale** | In plugin.json, not on disk | Remove or investigate |
| **Path mismatch** | Wrong path format | Correct path |

## Integration

This command complements:
- `/update-docs` - Updates documentation after plugin changes
- `/update-version` - Bumps versions after significant changes
- `/validate-plugin` - Validates overall plugin structure

## When to Use

- After adding new commands, skills, agents, or hooks
- During version bumps to ensure completeness
- As part of PR preparation (`/pr` workflow)
- When capabilities-reference.md seems out of sync

## See Also

- `abstract:validate-plugin-structure` - Full plugin validation
- `/update-docs` - Documentation updates
- `capabilities-reference.md` - Central capability listing
