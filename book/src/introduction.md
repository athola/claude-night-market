# Welcome to Claude Night Market

A collection of Claude Code plugins for software engineering workflows.

Claude Night Market provides plugins for Claude Code to support software engineering workflows. It includes skills, commands, agents, and hooks for development tasks.

## What You'll Find Here

This documentation covers installation, a plugin catalog, tutorials, API references, and achievements to track your progress.

## Plugin Architecture

The marketplace is organized into layers, each building on the foundations below:

```
+------------------+
|  Domain Experts  |  archetypes, pensive, parseltongue, memory-palace, spec-kit, minister
+------------------+
        |
+------------------+
|  Utility Layer   |  conservation, conjure
+------------------+
        |
+------------------+
| Foundation Layer |  imbue, sanctum, leyline
+------------------+
        |
+------------------+
|   Meta Layer     |  abstract
+------------------+
```

## Philosophy

We prioritize modular design with shallow dependencies and single responsibility. Plugins load progressively, so users only pay for what they use. Development is spec-driven, prioritizing specifications before implementation.

## Claude Code 2.1.0+ Compatibility

This marketplace leverages new Claude Code 2.1.0 features:

| Feature | Benefit |
|---------|---------|
| **Skill Hot-Reload** | Edit skills without restarting sessions |
| **Context Forking** | Run skills in isolated context with `context: fork` |
| **Frontmatter Hooks** | Lifecycle hooks scoped to skills/agents |
| **Wildcard Permissions** | Flexible patterns like `Bash(npm *)` |
| **YAML allowed-tools** | Cleaner list syntax for tool permissions |

See the [Plugin Development Guide](../docs/plugin-development-guide.md#claude-code-210-features) for detailed documentation.

## Quick Example

```bash
# Add the marketplace
/plugin marketplace add athola/claude-night-market

# Install a plugin
/plugin install sanctum@claude-night-market

# Use a command
/pr

# Invoke a skill
Skill(sanctum:git-workspace-review)
```

## Recommended Companion: Superpowers

Many skills work effectively with [superpowers](https://github.com/obra/superpowers) skills. While plugins work standalone, superpowers provides foundational methodology skills (TDD, debugging, code review patterns).

```bash
# Add superpowers marketplace
/plugin marketplace add obra/superpowers

# Install superpowers
/plugin install superpowers@superpowers-marketplace
```

## Next Steps

Head to the [Getting Started](getting-started/index.html) section to install your first plugin.
