# Plugin Metadata Convention

## Overview

This marketplace uses a dual-manifest system. We support the official Claude Code schema while tracking extended metadata needed for our specific tooling.

## File Structure

Each plugin maintains two manifest files in its `.claude-plugin/` directory.

### plugin.json (Official Schema)
This file strictly follows the Claude Code plugin schema. It contains only officially supported fields to ensuring validation passes.

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
This file captures metadata that the marketplace needs but the official schema rejects.

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

We split metadata because the official `plugin.json` validator is strict. Including extra fields causes installation to fail. By keeping `plugin.json` clean and moving rich metadata like dependencies and capabilities to `metadata.json`, we get the best of both worlds: full compatibility with Claude Code and the enhanced features required by our marketplace.

## Migration Notes

Keep `plugin.json` minimal. Move any field not in the official schema to `metadata.json`. Always run `claude plugin validate` to verify compliance. Ensure version numbers match in both files so tooling allows correct dependency resolution.
