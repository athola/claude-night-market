# Claude Night Market

Claude Night Market provides a suite of 15 plugins for Claude Code, focusing on git operations, code review, and specification-driven development. These plugins operate as a modular system where you can install only what you need.

## Architecture

The plugins are organized in layers. **Domain Experts** like `pensive` (code review) and `minister` (issue tracking) provide high-level skills. These rely on the **Utility Layer** for tasks like token conservation (`conserve`), which in turn build upon the **Foundation Layer** for core mechanics like permissions (`sanctum`). The **Meta Layer** (`abstract`) handles cross-plugin validation.

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

## Design Philosophy

The system uses shallow dependencies to keep token usage low. Plugins load progressively, meaning the system prompt only grows when you actively use a feature. We prioritize specifications over implementation, requiring a clear plan before generating code.

## Claude Code Capabilities

This marketplace uses Claude Code 2.1.0+ features to improve the developer experience. Skills automatically hot-reload when edited, allowing for rapid iteration. Context forking runs risky operations in isolation. Frontmatter hooks allow skills to execute logic at specific lifecycle points, and wildcard permissions reduce the frequency of approval prompts for trusted tools.

## Integration

These plugins are designed to work alongside [superpowers](https://github.com/obra/superpowers), which provides the foundational TDD and debugging skills. While Night Market plugins handle the workflow and process, superpowers handles the low-level execution and analysis.

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
