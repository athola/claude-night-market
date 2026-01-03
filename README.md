# Claude Night Market

**Claude Code plugins for software engineering workflows.**

Claude Night Market extends Claude Code with skills, commands, and agents for git workflows, code review, spec-driven development, and architecture planning.

> **Note:** These plugins work standalone but integrate with [superpowers](https://github.com/obra/superpowers) to add foundational skills like TDD and debugging.

## Comparison

| Standard Workflow | With Night Market |
|-------------------|-------------------|
| Generic git commands | `/pr` - PR preparation with scope checking |
| Manual code review | `/full-review` - Multi-discipline review orchestration |
| Ad-hoc specifications | `/speckit-specify` - Spec-driven development workflow |
| Context lost between sessions | `/catchup` - Context recovery |
| Manual setup | `/attune:init` - Project scaffolding with best practices |

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

**Next steps:** See [Installation Guide](book/src/getting-started/installation.md) for recommended plugin sets and troubleshooting.

## What's Included

**14 plugins** organized in layers, each building on foundations below:

```mermaid
flowchart TB
    subgraph Domain["🎯 Domain Specialists"]
        direction LR
        archetypes & pensive & parseltongue & memory-palace
        spec-kit & minister & attune & scry
    end
    subgraph Utility["🔧 Utility Layer"]
        direction LR
        conserve["conserve<br/>(resource optimization)"]
        conjure["conjure<br/>(LLM delegation)"]
    end
    subgraph Foundation["🏗️ Foundation Layer"]
        direction LR
        imbue["imbue<br/>(workflows)"]
        sanctum["sanctum<br/>(git ops)"]
        leyline["leyline<br/>(infra)"]
    end
    subgraph Meta["⚙️ Meta Layer"]
        abstract["abstract<br/>(plugin infrastructure)"]
    end

    Domain --> Utility --> Foundation --> Meta
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

## Target Audience

- **Developers** seeking structured, automated workflows.
- **Teams** standardizing Claude Code practices across projects.
- **Plugin authors** building on established architectural patterns.
- **Maintainers** automating repetitive tasks like PR preparation and scaffolding.

## Common Workflows

See [**Common Workflows Guide**](docs/common-workflows.md) for when and how to use commands, skills, and agents:

| Workflow | What to Use | Example |
|----------|-------------|---------|
| Initialize project | `/attune:arch-init` | `attune:arch-init --name my-api` |
| Review a PR | `/full-review` | Run multi-discipline code review |
| Fix PR feedback | `/fix-pr` | Address review comments |
| Prepare a PR | `/pr` + `/sanctum:update-*` | Quality gates before merge |
| Catch up on changes | `/catchup` | Context recovery after break |
| Write specifications | `/speckit-specify` | Spec-driven development |
| Debug issues | `Skill(superpowers:debugging)` | Systematic root cause analysis |

## Documentation

| Resource | Description |
|----------|-------------|
| [**Getting Started**](book/src/getting-started/README.md) | Installation and first steps |
| [**Common Workflows**](docs/common-workflows.md) | When to use commands/skills/agents |
| [**Quick Start Guide**](book/src/getting-started/quick-start.md) | Common workflow recipes |
| [**Script Integration**](docs/script-integration-pattern.md) | Programmatic tool calling patterns |
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

To build your own plugins:

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

The ecosystem operates within Claude Code's 15K character budget. All 160+ skills and commands load without configuration.

- **Current usage**: ~14,800 characters (98.7% of budget)
- **Enforcement**: A pre-commit hook prevents regression.

See [Budget Optimization](docs/budget-optimization-dec-2025.md) for details.

## Philosophy

- **Modular**: Shallow dependency chains and single responsibility.
- **Progressive**: Load only what is needed.
- **Composable**: Plugins designed to work together.
- **Spec-driven**: Prioritize specifications before implementation.

## Contributing

See [CONTRIBUTING](docs/plugin-development-guide.md#contributing) for guidelines. Each plugin maintains its own tests and documentation.

## License

[MIT](LICENSE)
