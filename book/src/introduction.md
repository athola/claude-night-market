# Welcome to Claude Night Market

A collection of Claude Code plugins for software engineering workflows.

Claude Night Market provides plugins for Claude Code to support software engineering workflows. It includes skills, commands, agents, and hooks for development tasks.

## What You'll Find Here

This documentation covers:

- **Getting Started**: Installation, configuration, and your first plugin
- **Plugin Catalog**: Detailed documentation for each plugin in the marketplace
- **Tutorials**: Step-by-step guides for common workflows
- **Reference**: Complete API documentation and capability listings
- **Achievement System**: Track your learning progress with gamified milestones

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

The project follows four principles:

1. **Modular**: Shallow dependency chains with single responsibility
2. **Progressive**: Load only what is needed.
3. **Composable**: Plugins designed to work together.
4. **Spec-driven**: Prioritize specifications before implementation.

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
