---
name: validate-plugin
description: Validate Claude Code plugin structure, check plugin.json schema, verify path references, and ensure naming conventions. Use when creating new plugins, debugging plugin loading issues, verifying plugin modifications, or checking if a plugin is correctly structured.
usage: /validate-plugin [plugin-path]
---

# Validate Plugin Structure

This command validates a Claude Code plugin's structure against the official documentation requirements.

## Usage

```bash
# Validate current directory
/validate-plugin

# Validate specific plugin
/validate-plugin ~/claude-night-market/plugins/archetypes

# Validate relative path
/validate-plugin ../my-plugin
```

## What It Checks

The validator performs comprehensive checks:

### Critical Requirements
- `.claude-plugin/plugin.json` exists and is valid JSON
- Required `name` field is present
- Plugin name follows kebab-case convention
- Referenced files and paths exist
- Directories are in correct locations (not nested in `.claude-plugin/`)

### Warnings
- Path format (should be relative with `./`)
- Semantic versioning format
- Directory structure matches references

### Recommendations
- Recommended metadata fields (version, description, author, license)
- Enhanced Claude configuration options
- Skill frontmatter completeness

## Examples

### Validate Current Plugin

```bash
cd ~/claude-night-market/plugins/archetypes
/validate-plugin
```

### Batch Validate Multiple Plugins

```bash
for plugin in ~/claude-night-market/plugins/*; do
  /validate-plugin "$plugin"
done
```

## Implementation

Run the Python validation script:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-plugin.py "${1:-.}"
```
