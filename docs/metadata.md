# Plugin Metadata Convention

## Overview

This marketplace uses a dual-manifest system to support both Claude Code's official plugin schema and extended marketplace-specific metadata.

## File Structure

Each plugin has two manifest files in its `.claude-plugin/` directory:

### plugin.json (Official Schema)
The standard Claude Code plugin manifest with only officially supported fields:

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Plugin description",
  "commands": ["./commands/example.md"],
  "keywords": ["keyword1", "keyword2"],
  "author": {
    "name": "Author Name",
    "url": "https://github.com/author"
  },
  "license": "MIT"
}
```

**Supported Fields:**
- `name` (required, kebab-case)
- `version` (semantic versioning)
- `description`
- `commands` (paths must start with `./`)
- `agents`
- `hooks`
- `mcpServers`
- `keywords`
- `author` (object with `name`, `email`, `url`)
- `homepage`
- `repository`
- `license`

### metadata.json (Extended Marketplace Schema)
Additional metadata useful for the marketplace but not part of the official Claude Code schema:

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "main": "skills",
  "skills": [
    "skills/skill-one",
    "skills/skill-two"
  ],
  "dependencies": {
    "other-plugin": ">=1.0.0"
  },
  "provides": {
    "capabilities": ["capability1", "capability2"],
    "patterns": ["pattern1", "pattern2"],
    "tools": ["tool1", "tool2"]
  },
  "claude": {
    "skill_prefix": "plugin-name",
    "auto_load": false,
    "categories": {
      "category": "Description"
    },
    "sdk_compatibility": {
      "version": "2024.1",
      "features": ["feature1", "feature2"]
    }
  }
}
```

**Extended Fields:**
- `main` - Primary entry point type (e.g., "skills", "commands")
- `skills` - List of skill paths without `./` prefix
- `dependencies` - Plugin dependencies with version constraints
- `provides` - Structured capabilities the plugin provides
- `claude` - Claude Code-specific configuration
  - `skill_prefix` - Prefix for skill names
  - `auto_load` - Whether to load automatically
  - `categories` - Plugin categorization
  - `sdk_compatibility` - SDK version and feature requirements
  - `agent_integration` - Agent system capabilities

## Why Two Files?

The dual-manifest system exists because `plugin.json` must strictly adhere to Claude Code's official schema to pass validation and installation checks. In contrast, `metadata.json` allows us to preserve rich, marketplace-specific metadata—such as skill dependencies and structured capabilities—without triggering validation errors. Marketplace tooling is designed to read both files, providing enhanced features while ensuring full compatibility with the official plugin system.

## Migration Notes

When updating plugins, keep `plugin.json` minimal and compliant with the official standards. Move any extended metadata fields into `metadata.json` and verify the results by running the official `claude plugin validate` command. Both manifest files must maintain consistent version numbers to ensure the marketplace tooling can correctly resolve dependencies and capabilities.
