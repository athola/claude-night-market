# Claude Night Market

**Supercharge your Claude Code with specialized plugins for real software engineering workflows.**

Claude Night Market is a curated ecosystem of plugins that extend Claude Code with production-ready skills, commands, and agents—from git workflows and code review to spec-driven development and architecture planning.

> **Works standalone. Even better with [superpowers](https://github.com/obra/superpowers).**
> Superpowers provides foundational methodology skills (TDD, debugging, code review patterns) that enhance these plugins significantly.

## Why Night Market?

| Without Plugins | With Night Market |
|-----------------|-------------------|
| Generic git commands | `/pr` - Smart PR prep with scope checking |
| Manual code review | `/full-review` - Multi-discipline review orchestration |
| Ad-hoc specifications | `/speckit-specify` - Spec-driven development workflow |
| Context lost between sessions | `/catchup` - Quick context recovery |
| Repetitive boilerplate | `/attune:init` - Project scaffolding with best practices |

## Quick Start

```bash
# 1. Add the marketplace
/plugin marketplace add athola/claude-night-market

# 2. Install plugins you need
/plugin install sanctum@claude-night-market    # Git workflows
/plugin install pensive@claude-night-market    # Code review
/plugin install spec-kit@claude-night-market   # Spec-driven dev

# 3. Start using
/pr                                            # Prepare a pull request
/full-review                                   # Run code review
Skill(sanctum:git-workspace-review)            # Invoke a skill
```

**That's it.** See [Installation Guide](book/src/getting-started/installation.md) for recommended plugin sets and troubleshooting.

## What's Included

**14 plugins** organized in layers, each building on foundations below:

```
┌─────────────────────────────────────────────────────────────────┐
│  Domain Specialists                                             │
│  archetypes · pensive · parseltongue · memory-palace            │
│  spec-kit · minister · attune · scry                            │
├─────────────────────────────────────────────────────────────────┤
│  Utility Layer                                                  │
│  conserve (resource optimization) · conjure (LLM delegation)    │
├─────────────────────────────────────────────────────────────────┤
│  Foundation Layer                                               │
│  imbue (workflows) · sanctum (git ops) · leyline (infra)        │
├─────────────────────────────────────────────────────────────────┤
│  Meta Layer                                                     │
│  abstract (plugin infrastructure)                               │
└─────────────────────────────────────────────────────────────────┘
```

### Highlights

| Plugin | What It Does | Key Commands |
|--------|--------------|--------------|
| **sanctum** | Git workflows, PR prep, commit messages | `/pr`, `/commit-msg`, `/fix-issue` |
| **pensive** | Code review toolkit (API, architecture, bugs) | `/full-review`, `/architecture-review` |
| **spec-kit** | Specification-driven development | `/speckit-specify`, `/speckit-plan` |
| **conserve** | Codebase health and bloat detection | `/bloat-scan`, `/unbloat` |
| **attune** | Project scaffolding and initialization | `/attune:init`, `/attune:brainstorm` |
| **parseltongue** | Python development suite | `/analyze-tests`, `/run-profiler` |
| **archetypes** | Architecture paradigm selection | 13 architecture guides |
| **memory-palace** | Knowledge management | `/palace`, `/garden` |

See [Capabilities Reference](book/src/reference/capabilities-reference.md) for all 100+ skills, 75+ commands, and 25+ agents.

## Who Is This For?

- **Solo developers** wanting structured workflows without the overhead
- **Teams** standardizing on Claude Code practices
- **Plugin authors** building on proven patterns
- **Anyone** tired of reinventing git workflows, code review checklists, and project scaffolding

## Documentation

| Resource | Description |
|----------|-------------|
| [**Getting Started**](book/src/getting-started/README.md) | Installation and first steps |
| [**Quick Start Guide**](book/src/getting-started/quick-start.md) | Common workflow recipes |
| [**Plugin Catalog**](book/src/plugins/README.md) | Detailed plugin documentation |
| [**Capabilities Reference**](book/src/reference/capabilities-reference.md) | Complete skill/command listing |
| [**Tutorials**](book/src/tutorials/README.md) | Step-by-step guides |

## Optional: LSP Integration

Plugins default to LSP (Language Server Protocol) for semantic code navigation when available. LSP provides faster, more accurate results than grep-based search.

```bash
# Enable LSP in Claude Code
export ENABLE_LSP_TOOLS=1

# Install cclsp MCP server
npx cclsp@latest setup
```

See [LSP Setup Guide](plugins/abstract/docs/claude-code-compatibility.md) for language server installation and configuration.

## Extending Night Market

Want to build your own plugins?

```bash
# Scaffold a new plugin
make create-plugin NAME=my-plugin

# Validate structure
make validate

# Run quality checks
make lint && make test
```

See [Plugin Development Guide](docs/plugin-development-guide.md) for patterns, quality standards, and contribution guidelines.

## System Prompt Budget

The ecosystem fits within Claude Code's 15K character budget. All 160+ skills and commands load without configuration.

- **Current usage**: ~14,800 characters (98.7% of budget)
- **Budget enforcement**: Pre-commit hook prevents regression

See [Budget Optimization](docs/budget-optimization-dec-2025.md) for details.

## Philosophy

- **Modular**: Shallow dependency chains, single responsibility
- **Progressive**: Load only what you need
- **Composable**: Plugins designed to work together
- **Spec-driven**: Define what before implementing how

## Contributing

See [CONTRIBUTING](docs/plugin-development-guide.md#contributing) for guidelines. Each plugin maintains its own tests and documentation.

## License

[MIT](LICENSE)
