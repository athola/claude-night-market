---
description: Sync plugin.json files with disk contents (commands, skills, agents, hooks)
usage: /update-plugins [plugin-name] [--dry-run] [--fix]
---

# Update Plugin Registrations

Audit plugin.json files against actual disk contents and fix registration gaps.

## Arguments

- `plugin-name` - Optional: specific plugin to audit (default: all plugins)
- `--dry-run` - Show discrepancies without making changes (default behavior)
- `--fix` - Automatically update plugin.json files to add/remove registrations

## What It Does

### Phase 1: Registration Audit
1. Scans each plugin directory for commands, skills, agents, hooks on disk
2. Compares with plugin.json registrations
3. Reports discrepancies: missing registrations, stale entries
4. Optionally fixes by updating plugin.json files with proper sorting

### Phase 2: Plugin Quality Review

Triggers `/plugin-review --tier branch` on affected plugins.
Runs quick quality gates (test, lint, typecheck, registration)
on changed plugins and side-effect checks on related plugins.

### Phase 2-4 (On-Demand Modules)

These modules contain full procedural details: format
templates, commands, TodoWrite naming conventions, and
auto-issue creation procedures.

- See `update-plugins/modules/phase2-performance.md` for
  skill-review and performance analysis
- See `update-plugins/modules/phase3-meta-eval.md` for
  recursive quality validation
- See `update-plugins/modules/phase4-queue.md` for knowledge
  queue promotion checks

## Workflow

Execute the Python script with the provided arguments:

```bash
# Audit all plugins (dry run - show discrepancies only)
python3 plugins/sanctum/scripts/update_plugin_registrations.py --dry-run

# Audit specific plugin
python3 plugins/sanctum/scripts/update_plugin_registrations.py parseltongue --dry-run

# Fix all plugins (update plugin.json files)
python3 plugins/sanctum/scripts/update_plugin_registrations.py --fix

# Fix specific plugin
python3 plugins/sanctum/scripts/update_plugin_registrations.py abstract --fix
```

## Command Flags

| Flag | Purpose |
|------|---------|
| `--dry-run` | Show discrepancies without fixing (default) |
| `--fix` | Update plugin.json files |
| `--skip-meta-eval` | Skip meta-evaluation check |
| `--skip-queue` | Skip knowledge queue check |
| `--no-auto-issues` | Don't auto-create GitHub issues |

## Prerequisites

This command requires the sanctum plugin's Python scripts. Before running,
verify the script exists:

```bash
# Check if running in night-market repo
if [[ -f "plugins/sanctum/scripts/update_plugin_registrations.py" ]]; then
  echo "Sanctum scripts available - command will work"
else
  echo "ERROR: This command only works in the claude-night-market repository"
  echo "The update_plugin_registrations.py script is not available in this project."
  exit 1
fi
```

**For non-night-market projects**: This command is night-market-specific.
Use `claude plugin update <plugin>@<marketplace>` to update individual plugins.

## Script Features

- Smart filtering: Excludes module directories,
  __pycache__, test files, __init__.py
- Nested path handling: Detects and reports stale nested registrations
- Alphabetical sorting: Maintains consistent ordering in plugin.json
- Safe by default: Dry-run mode unless --fix is specified
- Enriched output: Orphaned modules show inline descriptions from file content

## Discrepancy Types

| Type | Meaning | Action |
|------|---------|--------|
| Missing | File on disk, not in plugin.json | Add registration |
| Stale | In plugin.json, not on disk | Remove or investigate |
| Path mismatch | Wrong path format | Correct path |

## When To Use

- After adding new commands, skills, agents, or hooks
- During version bumps to ensure completeness
- As part of PR preparation (`/pr` workflow)
- When capabilities-reference.md seems out of sync
- Periodically (weekly/monthly) to catch performance
  degradation early
- After major refactors to ensure no regressions in skill
  stability

## When NOT To Use

- Simple changes that don't need the full workflow
- Work already completed through another sanctum command

## Improvement Integration Loop

Phases 1-4 create a continuous feedback loop:
registration audit surfaces gaps, performance analysis
identifies degradation, meta-evaluation enforces quality,
and queue checks prevent knowledge loss.
See the phase modules for details.

## Integration

This command complements:

- `/plugin-review` - Tiered quality review (invoked as
  Phase 2)
- `/update-docs` - Updates documentation after plugin
  changes
- `/update-version` - Bumps versions after significant
  changes
- `/validate-plugin` - Validates overall plugin structure
- `pensive:skill-review` - Analyzes skill performance
  metrics (invoked in Phase 2 module)
- `/skill-logs` - Surfaces recent failures (invoked in
  Phase 2 module)
- `/fix-workflow` - Implements improvements for identified
  issues
- `memory-palace:knowledge-intake` - Evaluates queue items
  (Phase 4)

## See Also

- `abstract:validate-plugin-structure` - Full plugin
  validation
- `capabilities-reference.md` - Central capability listing
- `pensive:skill-review` - Performance analysis and
  recommendations
- `/skill-logs` - Execution history and failure patterns
- `/fix-workflow` - Workflow improvement retrospectives
- `memory-palace:knowledge-intake` - Queue evaluation
  criteria
