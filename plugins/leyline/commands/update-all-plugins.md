---
name: update-all-plugins
description: Update every installed Claude Code plugin from all marketplaces without manual selection.
usage: /update-all-plugins
---

# Update All Plugins

One-shot command that upgrades every installed plugin from all configured marketplaces. This command reads the installed plugins configuration and updates each plugin individually using the correct marketplace format.

## When to Use
- After receiving marketplace-wide security fixes or compatibility updates
- Before running regression suites that depend on latest plugins
- To avoid manually updating each plugin individually
- When you want to ensure all plugins are at their latest versions

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

3. **Report results**
   - Counts total plugins checked, updated, and already latest
   - Lists specific plugins that were updated with version changes
   - Reports any failures with error messages
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
- A restart of Claude Code is required after updates to apply changes
- The command will continue updating even if some plugins fail
- Updates are applied at the user scope by default

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
