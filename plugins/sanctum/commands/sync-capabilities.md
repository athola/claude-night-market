---
description: Detect and fix drift between plugin.json registrations and capabilities reference documentation
usage: /sync-capabilities [--fix] [--plugin <name>]
---

# Sync Capabilities

Compare plugin.json registrations (skills, commands, agents) against `book/src/reference/capabilities-reference.md` and report discrepancies. Optionally auto-generate missing entries.

## Arguments

- `--fix` - Auto-generate missing entries in capabilities-reference.md (default: report only)
- `--plugin <name>` - Check a specific plugin instead of all plugins

## Workflow

The detection script, the discrepancy types, and the entry templates
are kept in one module:
`plugins/sanctum/skills/doc-updates/modules/capabilities-sync.md`.
Read that module, then:

1. Run its **Detection Script** from the repo root.
2. With `--plugin <name>`, keep only the report lines that name
   `<name>`. The script checks every plugin, and this filter is
   applied to its output.
3. With `--fix`, add each missing entry using the module's
   **Auto-Generation Templates**, in alphabetical order within its
   table in `book/src/reference/capabilities-reference.md`.
4. Re-run the check until it reports zero discrepancies.
   `make docs-sync-check` runs the CI version,
   `scripts/capabilities-sync-check.sh`, and exits 1 on any
   discrepancy.

## Examples

```bash
# Report all discrepancies (dry run, default)
/sync-capabilities

# Check only the sanctum plugin
/sync-capabilities --plugin sanctum

# Auto-fix missing entries across all plugins
/sync-capabilities --fix

# Fix a specific plugin's missing entries
/sync-capabilities --fix --plugin abstract
```

## When To Use

- After adding new skills, commands, or agents to a plugin
- During PR preparation to verify documentation is current
- After `/update-plugins` to sync docs with registration changes
- Periodically to catch documentation drift

## When NOT To Use

- During `/update-docs` (which already includes capabilities sync as Phase 4.75)
- For plugin.json registration issues (use `/update-plugins` instead)

## Integration

`/update-docs` runs the same check as Phase 4.75. Complements:

- `/update-plugins`: syncs plugin.json with disk contents (the other
  direction)
- `/update-docs`: full documentation update including capabilities
  sync

## See Also

- `plugins/sanctum/skills/doc-updates/modules/capabilities-sync.md` - Detection logic module
- `book/src/reference/capabilities-reference.md` - Central capability listing
- `/update-plugins` - Plugin registration audit
