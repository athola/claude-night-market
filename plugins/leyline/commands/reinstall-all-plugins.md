---
name: reinstall-all-plugins
description: Uninstall and reinstall all Claude Code plugins to refresh cache and resolve version mismatches.
usage: /reinstall-all-plugins [--list-only] [--generate-script] [--dry-run]
---

# Reinstall All Plugins

Utility command that detects installed plugins and reinstalls them. Use when plugins have cache corruption, version mismatches, or stale hook paths.

## Excluded Plugins

The following plugins are **automatically excluded** from reinstallation to prevent breaking the reinstall process:

- **hookify** — Removing this plugin during reinstall can break hook execution

## Modes

| Flag | Behavior |
|------|----------|
| (default) | Execute reinstall directly via Python script |
| `--list-only` | Generate copy-paste commands for manual execution |
| `--generate-script` | Generate `/tmp/reinstall-plugins.sh` for terminal execution |
| `--dry-run` | Show what would be done without executing |

## Execution

Run the reinstall script:

```bash
Bash("python3 /home/alext/claude-night-market/plugins/leyline/scripts/reinstall_all_plugins.py")
```

For list-only mode:
```bash
Bash("python3 /home/alext/claude-night-market/plugins/leyline/scripts/reinstall_all_plugins.py --list-only")
```

For script generation:
```bash
Bash("python3 /home/alext/claude-night-market/plugins/leyline/scripts/reinstall_all_plugins.py --generate-script")
```

For dry-run:
```bash
Bash("python3 /home/alext/claude-night-market/plugins/leyline/scripts/reinstall_all_plugins.py --dry-run")
```

## Output

The script will:
1. Read `~/.claude/plugins/installed_plugins.json` (or v2 format)
2. Categorize plugins (reinstallable vs excluded)
3. Uninstall each reinstallable plugin
4. Reinstall each plugin
5. Report success/failure summary

## After Reinstall

**Restart Claude Code** to apply the reinstalled plugins.

## Troubleshooting

### Plugin fails to reinstall
- **Local plugins**: validate source directory still exists
- **Remote plugins**: Check network connectivity
- **Version mismatch**: Plugin may have been removed
  from marketplace
- **Git timeout**: If reinstall fails with timeout errors
  on large repos or slow networks, increase the git
  timeout via environment variable:
  ```bash
  export CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=240000  # 4 minutes
  ```
  The default is 120s (increased from 30s in 2.1.51).

### Hooks still reference old paths
After reinstall, if hooks still fail:
1. Check `~/.claude/plugins/cache/` for stale directories
2. Manually remove orphaned cache entries
3. Restart Claude Code

### npm registry plugins (2.1.51+)
Plugins installed from npm sources now support custom
registries and specific version pinning. If your
organization uses a private npm registry, plugins can
be installed from it directly.
