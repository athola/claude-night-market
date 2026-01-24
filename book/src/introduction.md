# Claude Night Market

Claude Night Market contains 15 plugins for Claude Code, focusing on git operations, code review, and specification-driven development. Plugins operate independently, allowing partial installation.

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

Shallow dependencies reduce token usage. Progressive loading limits system prompt growth to active feature use. The workflow requires specifications before implementation.

## Claude Code Capabilities

Marketplace plugins use Claude Code 2.1.0+ features. Skills hot-reload on edit for rapid iteration. Context forking isolates risky operations. Frontmatter hooks execute logic at specific lifecycle points; wildcard permissions reduce approval prompts for trusted tools.

## Integration

These plugins work alongside [superpowers](https://github.com/obra/superpowers), which provides foundational TDD and debugging skills. Night Market plugins handle workflow and process; superpowers handles low-level execution and analysis.

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
