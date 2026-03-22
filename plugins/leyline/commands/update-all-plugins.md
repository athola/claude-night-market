---
name: update-all-plugins
description: Update all installed Claude Code plugins from all marketplaces.
usage: /update-all-plugins
---

# Update All Plugins

One-shot command that upgrades every installed plugin from all configured marketplaces and syncs memory palace knowledge. This command reads the installed plugins configuration, updates each plugin individually, and processes any queued research into palaces.

## When To Use
- After receiving marketplace-wide security fixes or compatibility updates
- Before running regression suites that depend on latest plugins
- To avoid manually updating each plugin individually
- When you want to validate all plugins are at their latest versions
- To process accumulated research from sessions into memory palaces

## When NOT To Use

- Project doesn't use the leyline infrastructure patterns
- Simple scripts without service architecture needs

## Workflow
The command executes the Python script at `scripts/update_all_plugins.py` which:

1. **Read installed plugins**
   - Parses `~/.claude/plugins/installed_plugins_v2.json`
   - Extracts plugin names and their marketplaces
   - Groups plugins by marketplace for efficient processing

2. **Update plugins by marketplace**
   - For each plugin, runs: `claude plugin update {plugin}@{marketplace}`
   - Handles update responses and tracks success/failure
   - Continues updating even if some plugins fail

3. **Sync memory palace knowledge** (if memory-palace is installed)
   - Processes `data/intake_queue.jsonl` into palaces
   - Matches queued research to existing palaces by domain/tags
   - Creates new entries in appropriate palace districts
   - Reports items processed and palaces updated

4. **Garden tending with palace check** (if memory-palace is installed)
   - Runs `garden tend --palaces` to check both garden plots and palace entries
   - Identifies stale/overgrown garden plots needing attention
   - Checks palace entries for staleness, low quality, duplicates
   - **Prompts for user approval before any cleanup operations**
   - Use `--apply` only after reviewing recommendations

5. **Report results**
   - Counts total plugins checked, updated, and already latest
   - Lists specific plugins that were updated with version changes
   - Reports any failures with error messages
   - Shows palace sync results (items processed, palaces updated)
   - Shows prune recommendations (if any)
   - Notes if restart is required for changes to take effect

## Implementation Notes
- The script reads the actual installed plugins configuration file
- Each plugin is updated with its full marketplace identifier: `{plugin}@{marketplace}`
- No `--all` flag exists for the native update command, so we iterate through each plugin
- The script handles both versioned plugins (e.g., "1.2.1") and commit-based plugins (e.g., "ddbd034ca35c")
- Output is formatted without emojis for better compatibility with different terminals

## Options
This command currently has no options. It updates all plugins from all marketplaces.

## Notes
- Requires network access to check for updates
- Use `/reload-plugins` (2.1.69+) to activate pending
  plugin changes without restarting Claude Code. For
  older versions, a full restart is still required.
- The command will continue updating even if some
  plugins fail
- Plugin installation status is now accurate in
  `/plugin` menu (2.1.70+). Previous versions could
  show plugins as inaccurately installed or report
  "not found in marketplace" on fresh startup.
- `/plugin uninstall` (2.1.71+) now disables
  project-scoped plugins in `.claude/settings.local.json`
  instead of modifying `.claude/settings.json`, so
  uninstalls don't affect teammates via version control
- Updates are applied at the user scope by default
- If updates fail with git timeout errors, set
  `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` (default: 120s,
  increased from 30s in 2.1.51)

## Auto-Update Configuration (2.0.70+)

Claude Code now supports per-marketplace auto-update toggles. This setting controls whether plugins from a marketplace update automatically when new versions are available.

To configure auto-updates for a specific marketplace:
1. Open Claude Code settings
2. Navigate to plugin marketplace settings
3. Toggle auto-update on/off per marketplace

**When to use this command vs auto-update**:
- **Auto-update**: Convenient for trusted marketplaces where you want latest versions automatically
- **This command**: Manual control when you want to review changes before updating, or to trigger updates on-demand across all marketplaces

Execute the update script:
```bash
python3 /home/alext/claude-night-market/plugins/leyline/scripts/update_all_plugins.py
```
