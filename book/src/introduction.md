# Claude Night Market

Claude Night Market contains 16 plugins for Claude Code that automate git operations, code review, and specification-driven development. Each plugin operates independently, allowing you to install only the components required for your specific workflow.

## Architecture

The ecosystem uses a layered architecture to manage dependencies and token usage.

1.  **Domain Specialists**: Plugins like `pensive` (code review) and `minister` (issue tracking) provide high-level task automation.
2.  **Utility Layer**: Provides resource management services, such as token conservation in `conserve`.
3.  **Foundation Layer**: Implements core mechanics used across the ecosystem, including permission handling in `sanctum`.
4.  **Meta Layer**: `abstract` provides tools for cross-plugin validation and enforcement of project standards.

## Design Philosophy

The project prioritizes token efficiency through shallow dependency chains. Progressive loading ensures that plugin logic enters the system prompt only when a specific feature is active. We enforce a "specification-first" workflow, requiring a written design phase before code generation begins.

## Claude Code Integration

Plugins require Claude Code 2.1.0 or later to use features like:
- **Hot-reloading**: Skills update immediately upon file modification.
- **Context Forking**: Risky operations run in isolated context windows.
- **Lifecycle Hooks**: Frontmatter hooks execute logic at specific execution points.
- **Wildcard Permissions**: Pre-approved tool access reduces manual confirmation prompts.

## Integration with Superpowers

These plugins integrate with the [superpowers](https://github.com/obra/superpowers) marketplace. While Night Market handles high-level process and workflow orchestration, superpowers provides the underlying methodology for TDD, debugging, and execution analysis.

## Quick Start

```bash
# 1. Add the marketplace
/plugin marketplace add athola/claude-night-market

# 2. Install a plugin
/plugin install sanctum@claude-night-market

# 3. Use a command
/pr

# 4. Invoke a skill
Skill(sanctum:git-workspace-review)
```
