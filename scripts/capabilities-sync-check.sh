#!/usr/bin/env bash
# capabilities-sync-check.sh - Verify capabilities docs match plugin registrations
# Used by: make docs-sync-check
# Exit non-zero if discrepancies found
# Requires: jq
# Compatible with bash 3.2+ (no associative arrays)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CAPS_REF="$REPO_ROOT/book/src/reference/capabilities-reference.md"
PLUGINS_DIR="$REPO_ROOT/plugins"

if [ ! -f "$CAPS_REF" ]; then
  echo "ERROR: capabilities-reference.md not found at $CAPS_REF"
  exit 1
fi

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required but not installed"
  exit 1
fi

errors=0
missing_entries=()
extra_entries=()

# Use temp files instead of associative arrays (bash 3.2 compat)
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

reg_skills="$tmpdir/skills"
reg_commands="$tmpdir/commands"
reg_agents="$tmpdir/agents"
: > "$reg_skills"
: > "$reg_commands"
: > "$reg_agents"

for plugin_json in "$PLUGINS_DIR"/*/.claude-plugin/plugin.json; do
  [ -f "$plugin_json" ] || continue
  plugin_name=$(jq -r '.name' "$plugin_json")

  # Skills
  while IFS= read -r skill_path; do
    [ -z "$skill_path" ] && continue
    skill_name=$(basename "$skill_path")
    echo "$skill_name	$plugin_name" >> "$reg_skills"
  done < <(jq -r '.skills[]? // empty' "$plugin_json")

  # Commands
  while IFS= read -r cmd_path; do
    [ -z "$cmd_path" ] && continue
    cmd_name=$(basename "$cmd_path" .md)
    echo "$cmd_name	$plugin_name" >> "$reg_commands"
  done < <(jq -r '.commands[]? // empty' "$plugin_json")

  # Agents
  while IFS= read -r agent_path; do
    [ -z "$agent_path" ] && continue
    agent_name=$(basename "$agent_path" .md)
    echo "$agent_name	$plugin_name" >> "$reg_agents"
  done < <(jq -r '.agents[]? // empty' "$plugin_json")
done

# Extract documented entries from capabilities reference
# Use awk instead of sed for BSD/GNU portability
doc_skills=$(awk '/^### All Skills/{f=1;next} /^### /{f=0} f && /^\| `/{gsub(/^\| `|`.*$/,"",$0); print}' "$CAPS_REF")
doc_commands=$(awk '/^### All Commands/{f=1;next} /^### /{f=0} f && /^\| `/{gsub(/^\| `|`.*$/,"",$0); print}' "$CAPS_REF" \
  | sed 's|^/||; s|^[a-z-]*:||')
doc_agents=$(awk '/^### All Agents/{f=1;next} /^### /{f=0} f && /^\| `/{gsub(/^\| `|`.*$/,"",$0); print}' "$CAPS_REF")

echo "=== Capabilities Sync Check ==="
echo ""

# Check skills
echo "--- Skills ---"
while IFS=$'\t' read -r skill plugin; do
  [ -z "$skill" ] && continue
  if ! echo "$doc_skills" | grep -Fqx "$skill"; then
    missing_entries+=("SKILL: $skill ($plugin) - registered but NOT in docs")
    ((errors++)) || true
  fi
done < "$reg_skills"
while IFS= read -r doc_skill; do
  [ -z "$doc_skill" ] && continue
  if ! grep -q "^${doc_skill}	" "$reg_skills"; then
    extra_entries+=("SKILL: $doc_skill - in docs but NOT registered in any plugin.json")
    ((errors++)) || true
  fi
done <<< "$doc_skills"

# Check commands
echo "--- Commands ---"
while IFS=$'\t' read -r cmd plugin; do
  [ -z "$cmd" ] && continue
  if ! echo "$doc_commands" | grep -Fqx "$cmd"; then
    missing_entries+=("COMMAND: $cmd ($plugin) - registered but NOT in docs")
    ((errors++)) || true
  fi
done < "$reg_commands"
while IFS= read -r doc_cmd; do
  [ -z "$doc_cmd" ] && continue
  if ! grep -q "^${doc_cmd}	" "$reg_commands"; then
    extra_entries+=("COMMAND: $doc_cmd - in docs but NOT registered in any plugin.json")
    ((errors++)) || true
  fi
done <<< "$doc_commands"

# Check agents
echo "--- Agents ---"
while IFS=$'\t' read -r agent plugin; do
  [ -z "$agent" ] && continue
  if ! echo "$doc_agents" | grep -Fqx "$agent"; then
    missing_entries+=("AGENT: $agent ($plugin) - registered but NOT in docs")
    ((errors++)) || true
  fi
done < "$reg_agents"
while IFS= read -r doc_agent; do
  [ -z "$doc_agent" ] && continue
  if ! grep -q "^${doc_agent}	" "$reg_agents"; then
    extra_entries+=("AGENT: $doc_agent - in docs but NOT registered in any plugin.json")
    ((errors++)) || true
  fi
done <<< "$doc_agents"

# Report results
echo ""
if [ ${#missing_entries[@]} -gt 0 ]; then
  echo "MISSING from docs (registered in plugin.json but not documented):"
  for entry in "${missing_entries[@]}"; do
    echo "  - $entry"
  done
  echo ""
fi

if [ ${#extra_entries[@]} -gt 0 ]; then
  echo "EXTRA in docs (documented but not registered in any plugin.json):"
  for entry in "${extra_entries[@]}"; do
    echo "  - $entry"
  done
  echo ""
fi

# Summary
total_skills=$(wc -l < "$reg_skills" | tr -d ' ')
total_commands=$(wc -l < "$reg_commands" | tr -d ' ')
total_agents=$(wc -l < "$reg_agents" | tr -d ' ')
echo "Summary: $total_skills skills, $total_commands commands, $total_agents agents registered"

if [ "$errors" -gt 0 ]; then
  echo "FAILED: $errors discrepancies found"
  exit 1
else
  echo "PASSED: All capabilities are in sync"
  exit 0
fi
