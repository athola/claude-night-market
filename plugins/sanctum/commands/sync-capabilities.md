---
description: Detect and fix drift between plugin.json registrations and capabilities reference documentation
usage: /sync-capabilities [--fix] [--plugin <name>]
---

# Sync Capabilities

Compare plugin.json registrations (skills, commands, agents) against `book/src/reference/capabilities-reference.md` and report discrepancies. Optionally auto-generate missing entries.

## Arguments

- `--fix` - Auto-generate missing entries in capabilities-reference.md (default: report only)
- `--plugin <name>` - Check a specific plugin instead of all plugins

## What It Does

1. Reads all `plugins/*/.claude-plugin/plugin.json` files (or a single plugin if `--plugin` is specified)
2. Extracts registered skills, commands, and agents
3. Parses `book/src/reference/capabilities-reference.md` for documented entries
4. Reports discrepancies: missing from docs, extra in docs, stale entries
5. Checks for missing plugin book pages and SUMMARY.md entries
6. With `--fix`, generates table entries for missing items using templates

## Workflow

### Step 1: Run Detection Script

Execute the capabilities sync check from the repo root:

```bash
#!/bin/bash
# Run from repo root

PLUGIN_FILTER="${1:-}"  # Optional: specific plugin name

echo "=== Capabilities Sync Report ==="
echo ""

REGISTERED_SKILLS=$(mktemp)
DOCUMENTED_SKILLS=$(mktemp)
REGISTERED_COMMANDS=$(mktemp)
DOCUMENTED_COMMANDS=$(mktemp)
REGISTERED_AGENTS=$(mktemp)
DOCUMENTED_AGENTS=$(mktemp)

# Extract registered skills from plugin.json files
for pjson in plugins/*/.claude-plugin/plugin.json; do
  plugin=$(basename $(dirname $(dirname "$pjson")))
  [ -n "$PLUGIN_FILTER" ] && [ "$plugin" != "$PLUGIN_FILTER" ] && continue
  jq -r --arg p "$plugin" '.skills[]? | sub("^\\./skills/"; "") | "\($p):\(.)"' "$pjson" 2>/dev/null
done | sort -u > "$REGISTERED_SKILLS"

# Extract documented skills from capabilities-reference.md
grep -E "^\| \`[a-z-]+\` \|" book/src/reference/capabilities-reference.md 2>/dev/null | \
  sed -n '/All Skills/,/All Commands/p' | \
  grep -E "^\| \`" | \
  awk -F'|' '{gsub(/[`\[\] ]/, "", $2); gsub(/.*\(\.\.\/plugins\//, "", $3); gsub(/\.md\).*/, "", $3); print $3":"$2}' | \
  sort -u > "$DOCUMENTED_SKILLS"

# Extract registered commands
for pjson in plugins/*/.claude-plugin/plugin.json; do
  plugin=$(basename $(dirname $(dirname "$pjson")))
  [ -n "$PLUGIN_FILTER" ] && [ "$plugin" != "$PLUGIN_FILTER" ] && continue
  jq -r --arg p "$plugin" '.commands[]? | sub("^\\./commands/"; "") | sub("\\.md$"; "") | "/\($p):\(.)"' "$pjson" 2>/dev/null
done | sort -u > "$REGISTERED_COMMANDS"

# Extract documented commands
grep -E "^\| \`/" book/src/reference/capabilities-reference.md 2>/dev/null | \
  sed -n '/All Commands/,/All Agents/p' | \
  grep -E "^\| \`/" | \
  awk -F'|' '{gsub(/[`\[\] ]/, "", $2); gsub(/ /, "", $3); print $2}' | \
  sort -u > "$DOCUMENTED_COMMANDS"

# Extract registered agents
for pjson in plugins/*/.claude-plugin/plugin.json; do
  plugin=$(basename $(dirname $(dirname "$pjson")))
  [ -n "$PLUGIN_FILTER" ] && [ "$plugin" != "$PLUGIN_FILTER" ] && continue
  jq -r --arg p "$plugin" '.agents[]? | sub("^\\./agents/"; "") | sub("\\.md$"; "") | "\($p):\(.)"' "$pjson" 2>/dev/null
done | sort -u > "$REGISTERED_AGENTS"

# Extract documented agents
grep -E "^\| \`[a-z-]+\` \|" book/src/reference/capabilities-reference.md 2>/dev/null | \
  sed -n '/All Agents/,/All Hooks/p' | \
  grep -E "^\| \`" | \
  awk -F'|' '{gsub(/[`\[\] ]/, "", $2); gsub(/ /, "", $3); print $3":"$2}' | \
  sort -u > "$DOCUMENTED_AGENTS"

# Report
echo "### Skills"
echo "Missing from docs (registered but not documented):"
comm -23 "$REGISTERED_SKILLS" "$DOCUMENTED_SKILLS" | sed 's/^/  - /'
echo ""
echo "Extra in docs (documented but not registered):"
comm -13 "$REGISTERED_SKILLS" "$DOCUMENTED_SKILLS" | sed 's/^/  - /'

echo ""
echo "### Commands"
echo "Missing from docs:"
comm -23 "$REGISTERED_COMMANDS" "$DOCUMENTED_COMMANDS" | sed 's/^/  - /'
echo ""
echo "Extra in docs:"
comm -13 "$REGISTERED_COMMANDS" "$DOCUMENTED_COMMANDS" | sed 's/^/  - /'

echo ""
echo "### Agents"
echo "Missing from docs:"
comm -23 "$REGISTERED_AGENTS" "$DOCUMENTED_AGENTS" | sed 's/^/  - /'
echo ""
echo "Extra in docs:"
comm -13 "$REGISTERED_AGENTS" "$DOCUMENTED_AGENTS" | sed 's/^/  - /'

# Check for missing plugin pages
echo ""
echo "### Plugin Pages"
for plugin in plugins/*/; do
  name=$(basename "$plugin")
  [ -n "$PLUGIN_FILTER" ] && [ "$name" != "$PLUGIN_FILTER" ] && continue
  if [ ! -f "book/src/plugins/${name}.md" ]; then
    echo "  - Missing: book/src/plugins/${name}.md"
  fi
done

# Check SUMMARY.md
echo ""
echo "### SUMMARY.md"
for plugin in plugins/*/; do
  name=$(basename "$plugin")
  [ -n "$PLUGIN_FILTER" ] && [ "$name" != "$PLUGIN_FILTER" ] && continue
  if ! grep -q "plugins/${name}.md" book/src/SUMMARY.md 2>/dev/null; then
    echo "  - Missing from SUMMARY: ${name}"
  fi
done

rm -f "$REGISTERED_SKILLS" "$DOCUMENTED_SKILLS" "$REGISTERED_COMMANDS" "$DOCUMENTED_COMMANDS" "$REGISTERED_AGENTS" "$DOCUMENTED_AGENTS"
```

### Step 2: Review Output

Examine the sync report. Discrepancies fall into three categories:

| Type | Meaning | Action |
|------|---------|--------|
| Missing from docs | Registered in plugin.json but not in capabilities-reference.md | Add entry |
| Extra in docs | Documented but no matching plugin.json registration | Remove or investigate |
| Missing pages | Plugin exists but has no book page or SUMMARY entry | Create page |

### Step 3: Fix (with `--fix`)

When `--fix` is specified, auto-generate missing entries using these templates.

#### Skill Entry

Read the skill's `SKILL.md` frontmatter for the description, then insert:

```markdown
| `{skill-name}` | [{plugin}](../plugins/{plugin}.md) | {description from SKILL.md} |
```

#### Command Entry

Read the command's YAML frontmatter for the description, then insert:

```markdown
| `/{plugin}:{command}` | {plugin} | {description from command.md frontmatter} |
```

#### Agent Entry

Read the agent file's first heading or frontmatter for the description, then insert:

```markdown
| `{agent-name}` | {plugin} | {description from agent.md} |
```

Insert each new entry into the correct alphabetical position within the appropriate table in `capabilities-reference.md`.

### Step 4: Verify Fix

After applying fixes, re-run the detection script to confirm zero discrepancies:

```bash
# Re-run to verify
# Should show no "Missing from docs" entries
```

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

This command extracts the capabilities sync logic from `/update-docs` Phase 4.75 into a standalone operation. It uses the same detection script from `plugins/sanctum/skills/doc-updates/modules/capabilities-sync.md`.

Complements:
- `/update-plugins` - Syncs plugin.json with disk contents (the other direction)
- `/update-docs` - Full documentation update including capabilities sync
- `capabilities-reference.md` - The documentation target

## See Also

- `plugins/sanctum/skills/doc-updates/modules/capabilities-sync.md` - Detection logic module
- `book/src/reference/capabilities-reference.md` - Central capability listing
- `/update-plugins` - Plugin registration audit
