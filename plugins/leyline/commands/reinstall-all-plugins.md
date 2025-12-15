---
name: reinstall-all-plugins
description: Uninstall and reinstall all Claude Code plugins to refresh cache and resolve version mismatches.
usage: /reinstall-all-plugins [--generate-script]
---

# Reinstall All Plugins

Utility command that detects installed plugins and generates reinstallation commands. Use when plugins have cache corruption, version mismatches, or stale hook paths.

## Excluded Plugins

The following plugins are **automatically excluded** from reinstallation to prevent breaking the reinstall process:

- **hookify** — Removing this plugin during reinstall can break hook execution, causing the reinstall process itself to fail

These plugins will be listed separately in the output but no uninstall/install commands will be generated for them.

## Limitations

**IMPORTANT**: The `/plugin install` and `/plugin uninstall` commands are built-in Claude Code CLI commands that cannot be executed programmatically from within a session. This command provides two alternatives:

1. **Interactive Mode** (default): Generates copy-paste commands for you to run sequentially
2. **Script Mode** (`--generate-script`): Creates a shell script for terminal execution

## Workflow

### Step 1: Detect Installed Plugins

Read the plugin registry from filesystem:

```python
# Read: ~/.claude/plugins/installed_plugins_v2.json
# Parse the JSON and extract plugin identifiers and metadata
```

Use `Read("~/.claude/plugins/installed_plugins_v2.json")` to get the current plugin list.

### Step 2: Categorize Plugins

For each plugin, extract:
- **Identifier**: `{name}@{marketplace}` (e.g., `sanctum@claude-night-market`)
- **Scope**: `user` or `project`
- **isLocal**: Whether it's a local plugin (affects reinstall behavior)
- **Source marketplace**: For determining reinstall command

**Exclusion check**: Skip any plugin whose name matches the excluded list (e.g., `hookify`). These will be reported separately.

### Step 3: Generate Commands

**For Interactive Mode** — Present numbered commands:

```
Plugins detected: 12

To reinstall, run these commands in order:

# Step 1: Uninstall all plugins
/plugin uninstall sanctum@claude-night-market
/plugin uninstall spec-kit@claude-night-market
... (one per line)

# Step 2: Reinstall all plugins
/plugin install sanctum@claude-night-market
/plugin install spec-kit@claude-night-market
... (one per line)
```

**For Script Mode** (`--generate-script`) — Generate a bash script:

```bash
#!/bin/bash
# Generated reinstall script
# Run from terminal: bash /tmp/reinstall-plugins.sh
#
# NOTE: hookify is excluded to prevent breaking hook execution during reinstall

PLUGINS=(
  "sanctum@claude-night-market"
  "spec-kit@claude-night-market"
  # ... more plugins (hookify excluded)
)

echo "Uninstalling ${#PLUGINS[@]} plugins..."
echo "(hookify excluded to preserve hook execution)"
for plugin in "${PLUGINS[@]}"; do
  echo "  Uninstalling $plugin..."
  claude /plugin uninstall "$plugin" 2>/dev/null || echo "  Warning: $plugin uninstall may have failed"
done

echo ""
echo "Reinstalling ${#PLUGINS[@]} plugins..."
for plugin in "${PLUGINS[@]}"; do
  echo "  Installing $plugin..."
  claude /plugin install "$plugin" || echo "  ERROR: Failed to install $plugin"
done

echo ""
echo "Reinstall complete. Restart Claude Code to apply changes."
```

Write the script to `/tmp/reinstall-plugins.sh` and instruct user to run it.

### Step 4: Provide Guidance

After generating commands/script:
- Remind user to **restart Claude Code** after reinstallation
- Note any local plugins that require their source paths to still exist
- Warn about remote plugins that may have updated versions

## Implementation Notes

### Reading Plugin Registry

The authoritative source is `~/.claude/plugins/installed_plugins_v2.json`:

```json
{
  "version": 2,
  "plugins": {
    "plugin-name@marketplace": [{
      "scope": "user",
      "installPath": "/path/to/cache/...",
      "version": "1.0.0",
      "isLocal": true|false
    }]
  }
}
```

### DO NOT attempt:
- `Bash("claude plugins list")` — not available inside session
- `Command("/plugins list")` — not a real tool
- `SlashCommand("/plugin install X")` — only for custom commands, not built-ins

### DO use:
- `Read("~/.claude/plugins/installed_plugins_v2.json")` — filesystem access works
- `Write("/tmp/reinstall-plugins.sh", script)` — for script generation
- `AskUserQuestion` — to confirm before generating destructive commands

## Example Session

```
User: /reinstall-all-plugins

Claude: Reading plugin registry...

Found 21 installed plugins (1 excluded):

**Excluded from reinstall** (these plugins will NOT be touched):
- hookify@claude-code-plugins — Required for hook execution during reinstall

**Plugins to reinstall** (20):

| Plugin | Marketplace | Scope | Local |
|--------|-------------|-------|-------|
| sanctum | claude-night-market | user | ✓ |
| spec-kit | claude-night-market | user | ✓ |
| episodic-memory | superpowers-marketplace | user | ✗ |
| ... | ... | ... | ... |

To reinstall all plugins, copy and paste these commands one at a time:

**Uninstall Phase:**
/plugin uninstall sanctum@claude-night-market
/plugin uninstall spec-kit@claude-night-market
/plugin uninstall episodic-memory@superpowers-marketplace
...

**Install Phase:**
/plugin install sanctum@claude-night-market
/plugin install spec-kit@claude-night-market
/plugin install episodic-memory@superpowers-marketplace
...

After completing all commands, restart Claude Code to apply changes.
```

## Troubleshooting

### Plugin fails to reinstall
- **Local plugins**: Ensure source directory still exists at the original path
- **Remote plugins**: Check network connectivity; plugin may have been removed from marketplace
- **Version mismatch**: Try `/plugin install plugin@marketplace --force` if available

### Hooks still reference old paths
After reinstall, if hooks still fail:
1. Check `~/.claude/plugins/cache/` for stale directories
2. Manually remove orphaned cache entries
3. Restart Claude Code

### Need to preserve specific plugin versions
Before uninstalling, note the version in `installed_plugins_v2.json`. Remote plugins may update to latest on reinstall.
