# Welcome to Claude Night Market

A collection of Claude Code plugins for software engineering workflows.

Claude Night Market provides a curated ecosystem of plugins that enhance your Claude Code experience with specialized skills, commands, agents, and hooks for common development tasks.

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

The Claude Night Market is built on four principles:

1. **Modular**: Shallow dependency chains with single responsibility
2. **Progressive**: Load only what you need, when you need it
3. **Composable**: Plugins are designed to work together seamlessly
4. **Spec-driven**: Define what you want before implementing how

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

Many skills achieve their full potential when used alongside the [superpowers](https://github.com/obra/superpowers) skills. While all plugins work standalone, superpowers provides foundational methodology skills (TDD, debugging, code review patterns) that enhance workflows significantly.

```bash
# Add superpowers marketplace
/plugin marketplace add obra/superpowers

# Install superpowers
/plugin install superpowers@superpowers-marketplace
```

## Ready to Begin?

Head to the [Getting Started](getting-started/index.html) section to install your first plugin and start exploring the Night Market.
