# Capabilities Sync Module

Synchronizes plugin.json registrations with capabilities reference documentation.

## Purpose

Detects drift between:
- **Source of truth**: `plugins/*/.claude-plugin/plugin.json` files
- **Documentation**: `book/src/reference/capabilities-reference.md` and related files

## When Loaded

This module is loaded during Step 4.75 (after plugins-synced, before accuracy-verified).

## Sync Targets

| Source | Documentation Target |
|--------|---------------------|
| `plugin.json.skills[]` | `book/src/reference/capabilities-reference.md` (Skills table) |
| `plugin.json.commands[]` | `book/src/reference/capabilities-reference.md` (Commands table) |
| `plugin.json.agents[]` | `book/src/reference/capabilities-reference.md` (Agents table) |
| `hooks/hooks.json` | `book/src/reference/capabilities-reference.md` (Hooks table) |
| Plugin existence | `book/src/plugins/{plugin}.md` |
| Plugin in layer | `book/src/plugins/{layer}-layer.md` |
| Plugin in SUMMARY | `book/src/SUMMARY.md` |

## Detection Script

```bash
#!/bin/bash
# capabilities-sync-check.sh
# Run from repo root

echo "=== Capabilities Sync Report ==="
echo ""

# Temporary files for comparison
REGISTERED_SKILLS=$(mktemp)
DOCUMENTED_SKILLS=$(mktemp)
REGISTERED_COMMANDS=$(mktemp)
DOCUMENTED_COMMANDS=$(mktemp)
REGISTERED_AGENTS=$(mktemp)
DOCUMENTED_AGENTS=$(mktemp)

# Extract registered skills from plugin.json files
for pjson in plugins/*/.claude-plugin/plugin.json; do
  plugin=$(basename $(dirname $(dirname "$pjson")))
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
  jq -r --arg p "$plugin" '.agents[]? | sub("^\\./agents/"; "") | sub("\\.md$"; "") | "\($p):\(.)"' "$pjson" 2>/dev/null
done | sort -u > "$REGISTERED_AGENTS"

# Extract documented agents
grep -E "^\| \`[a-z-]+\` \|" book/src/reference/capabilities-reference.md 2>/dev/null | \
  sed -n '/All Agents/,/All Hooks/p' | \
  grep -E "^\| \`" | \
  awk -F'|' '{gsub(/[`\[\] ]/, "", $2); gsub(/ /, "", $3); print $3":"$2}' | \
  sort -u > "$DOCUMENTED_AGENTS"

# Report differences
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

# Check for missing plugin pages in book
echo ""
echo "### Plugin Pages"
for plugin in plugins/*/; do
  name=$(basename "$plugin")
  if [ ! -f "book/src/plugins/${name}.md" ]; then
    echo "  - Missing: book/src/plugins/${name}.md"
  fi
done

# Check SUMMARY.md includes all plugins
echo ""
echo "### SUMMARY.md"
for plugin in plugins/*/; do
  name=$(basename "$plugin")
  if ! grep -q "plugins/${name}.md" book/src/SUMMARY.md 2>/dev/null; then
    echo "  - Missing from SUMMARY: ${name}"
  fi
done

# Cleanup
rm -f "$REGISTERED_SKILLS" "$DOCUMENTED_SKILLS" "$REGISTERED_COMMANDS" "$DOCUMENTED_COMMANDS" "$REGISTERED_AGENTS" "$DOCUMENTED_AGENTS"
```

## Workflow Integration

### Step 4.75: Sync Capabilities Documentation (`capabilities-synced`)

After `plugins-synced` (Step 4.5), run capabilities sync:

```bash
# Quick check for capabilities drift
bash plugins/sanctum/skills/doc-updates/modules/capabilities-sync-check.sh
```

**If discrepancies found:**

1. **Missing skills/commands/agents**: Generate table entries
2. **Extra in docs**: Verify if removed or renamed
3. **Missing plugin pages**: Create from template
4. **Missing from SUMMARY**: Add to appropriate layer

### Auto-Generation Templates

#### Skill Entry
```markdown
| `{skill-name}` | [{plugin}](../plugins/{plugin}.md) | {description from SKILL.md frontmatter} |
```

#### Command Entry
```markdown
| `/{plugin}:{command}` | {plugin} | {description from command.md frontmatter} |
```

#### Agent Entry
```markdown
| `{agent-name}` | {plugin} | {description from agent.md frontmatter} |
```

#### Hook Entry
```markdown
| `{hook-file}` | {plugin} | {type} | {description} |
```

## Feature-to-Documentation Mapping

Generic mapping pattern for any repository:

```yaml
# .claude/doc-sync.yaml (example config)
mappings:
  # Plugin ecosystem pattern
  - source: "plugins/*/.claude-plugin/plugin.json"
    extract: ["skills", "commands", "agents"]
    targets:
      - path: "book/src/reference/capabilities-reference.md"
        section_pattern: "### All {type}s"
      - path: "book/src/plugins/{plugin}.md"
        section_pattern: "## {type}s"

  # Generic feature pattern
  - source: "src/features/*/manifest.json"
    extract: ["exports", "apis"]
    targets:
      - path: "docs/api-reference.md"
        section_pattern: "## {feature} API"
```

## Exit Criteria

- All registered capabilities appear in documentation
- No orphaned documentation entries (items removed from plugin.json)
- All plugins have book pages
- SUMMARY.md is complete
