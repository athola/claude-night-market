#!/usr/bin/env bash
# capabilities-sync-check.sh - Verify capabilities docs match plugin registrations
# Used by: make docs-sync-check
# Exit non-zero if discrepancies found
# Requires: bash 4+ (associative arrays), jq

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

# Collect all registered capabilities from plugin.json files
declare -A registered_skills
declare -A registered_commands
declare -A registered_agents

for plugin_json in "$PLUGINS_DIR"/*/.claude-plugin/plugin.json; do
  [ -f "$plugin_json" ] || continue
  plugin_name=$(jq -r '.name' "$plugin_json")

  # Skills: extract directory basename from paths like "./skills/foo-bar"
  while IFS= read -r skill_path; do
    [ -z "$skill_path" ] && continue
    skill_name=$(basename "$skill_path")
    registered_skills["$skill_name"]="$plugin_name"
  done < <(jq -r '.skills[]? // empty' "$plugin_json")

  # Commands: extract filename stem from paths like "./commands/foo-bar.md"
  while IFS= read -r cmd_path; do
    [ -z "$cmd_path" ] && continue
    cmd_name=$(basename "$cmd_path" .md)
    registered_commands["$cmd_name"]="$plugin_name"
  done < <(jq -r '.commands[]? // empty' "$plugin_json")

  # Agents: extract filename stem from paths like "./agents/foo-bar.md"
  while IFS= read -r agent_path; do
    [ -z "$agent_path" ] && continue
    agent_name=$(basename "$agent_path" .md)
    registered_agents["$agent_name"]="$plugin_name"
  done < <(jq -r '.agents[]? // empty' "$plugin_json")
done

# Extract documented entries from the capabilities reference markdown tables
# Skills section: between "### All Skills" and the next "###"
doc_skills=$(sed -n '/^### All Skills/,/^### /{/^| `/{s/^| `\([^`]*\)`.*/\1/p}}' "$CAPS_REF")
# Commands section: strip leading / and plugin: namespace prefix so
# /tome:research -> research, /commit-msg -> commit-msg
doc_commands=$(sed -n '/^### All Commands/,/^### /{/^| `/{s/^| `\([^`]*\)`.*/\1/p}}' "$CAPS_REF" \
  | sed 's|^/||; s|^[a-z-]*:||')
# Agents section
doc_agents=$(sed -n '/^### All Agents/,/^### /{/^| `/{s/^| `\([^`]*\)`.*/\1/p}}' "$CAPS_REF")

echo "=== Capabilities Sync Check ==="
echo ""

# Check skills
echo "--- Skills ---"
for skill in "${!registered_skills[@]}"; do
  if ! echo "$doc_skills" | grep -qx "$skill"; then
    missing_entries+=("SKILL: $skill (${registered_skills[$skill]}) - registered but NOT in docs")
    ((errors++)) || true
  fi
done
while IFS= read -r doc_skill; do
  [ -z "$doc_skill" ] && continue
  if [ -z "${registered_skills[$doc_skill]+x}" ]; then
    extra_entries+=("SKILL: $doc_skill - in docs but NOT registered in any plugin.json")
    ((errors++)) || true
  fi
done <<< "$doc_skills"

# Check commands
echo "--- Commands ---"
for cmd in "${!registered_commands[@]}"; do
  if ! echo "$doc_commands" | grep -qx "$cmd"; then
    missing_entries+=("COMMAND: $cmd (${registered_commands[$cmd]}) - registered but NOT in docs")
    ((errors++)) || true
  fi
done
while IFS= read -r doc_cmd; do
  [ -z "$doc_cmd" ] && continue
  if [ -z "${registered_commands[$doc_cmd]+x}" ]; then
    extra_entries+=("COMMAND: $doc_cmd - in docs but NOT registered in any plugin.json")
    ((errors++)) || true
  fi
done <<< "$doc_commands"

# Check agents
echo "--- Agents ---"
for agent in "${!registered_agents[@]}"; do
  if ! echo "$doc_agents" | grep -qx "$agent"; then
    missing_entries+=("AGENT: $agent (${registered_agents[$agent]}) - registered but NOT in docs")
    ((errors++)) || true
  fi
done
while IFS= read -r doc_agent; do
  [ -z "$doc_agent" ] && continue
  if [ -z "${registered_agents[$doc_agent]+x}" ]; then
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
total_skills=${#registered_skills[@]}
total_commands=${#registered_commands[@]}
total_agents=${#registered_agents[@]}
echo "Summary: $total_skills skills, $total_commands commands, $total_agents agents registered"

if [ "$errors" -gt 0 ]; then
  echo "FAILED: $errors discrepancies found"
  exit 1
else
  echo "PASSED: All capabilities are in sync"
  exit 0
fi
