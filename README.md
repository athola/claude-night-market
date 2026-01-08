# Claude Night Market

**Claude Code plugins for software engineering workflows.**

Claude Night Market extends Claude Code with skills, commands, and agents for git workflows, code review, spec-driven development, and architecture planning.

> **Note:** These plugins function independently but use [superpowers](https://github.com/obra/superpowers) for TDD and debugging.

> **Claude Code 2.1.0+:** This marketplace leverages new features including skill hot-reload, frontmatter hooks, `context: fork`, wildcard permissions, and YAML-style `allowed-tools`. See [Plugin Development Guide](docs/plugin-development-guide.md#claude-code-210-features) for details.

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

**15 plugins** organized in layers, each building on foundations below:

```mermaid
flowchart TB
    classDef domainClass fill:#e8f4f8,stroke:#2980b9,stroke-width:2px,color:#2c3e50
    classDef utilityClass fill:#f8f4e8,stroke:#f39c12,stroke-width:2px,color:#2c3e50
    classDef foundationClass fill:#f4e8f8,stroke:#8e44ad,stroke-width:2px,color:#2c3e50
    classDef metaClass fill:#e8f4e8,stroke:#27ae60,stroke-width:2px,color:#2c3e50

    subgraph Domain["Domain Specialists"]
        direction LR
        D1[archetypes]:::domainClass
        D2[pensive]:::domainClass
        D3[parseltongue]:::domainClass
        D4[memory-palace]:::domainClass
        D5[spec-kit]:::domainClass
        D6[minister]:::domainClass
        D7[attune]:::domainClass
        D8[scry]:::domainClass
    end

    subgraph Utility["Utility Layer"]
        direction LR
        U1[conserve]:::utilityClass
        U2[conjure]:::utilityClass
        U3[hookify]:::utilityClass
    end

    subgraph Foundation["Foundation Layer"]
        direction LR
        F1[imbue]:::foundationClass
        F2[sanctum]:::foundationClass
        F3[leyline]:::foundationClass
    end

    subgraph Meta["Meta Layer"]
        direction LR
        M1[abstract]:::metaClass
    end

    Domain ==> Utility ==> Foundation ==> Meta
```

### Highlights

| Plugin | What It Does | Key Commands |
|--------|--------------|--------------|
| **sanctum** | Git workflows, PR prep, commit messages | `/pr`, `/commit-msg`, `/fix-issue` |
| **pensive** | Code review toolkit (API, architecture, bugs) | `/full-review`, `/architecture-review` |
| **spec-kit** | Specification-driven development | `/speckit-specify`, `/speckit-plan` |
| **minister** | Project management and GitHub integration | `/create-issue`, `/close-issue`, `/status` |
| **conserve** | Codebase health and bloat detection | `/bloat-scan`, `/unbloat` |
| **attune** | Project scaffolding and initialization | `/attune:init`, `/attune:brainstorm` |
| **parseltongue** | Python development suite | `/analyze-tests`, `/run-profiler` |
| **archetypes** | Architecture paradigm selection | 13 architecture guides |
| **memory-palace** | Knowledge management | `/palace`, `/garden` |
| **hookify** | Zero-config behavioral rules | `/hookify`, `/hookify:list` |

See [Capabilities Reference](book/src/reference/capabilities-reference.md) for all 107 skills, 81 commands, and 34 agents.

## Audience

The Night Market serves developers seeking automated workflows and teams standardizing Claude Code practices. Plugin authors can build on standard patterns, while maintainers benefit from automated PR preparation and scaffolding.

## Common Workflows

See [**Common Workflows Guide**](docs/common-workflows.md) for when and how to use commands, skills, and agents:

| Workflow | What to Use | Example |
|----------|-------------|---------|
| Initialize project | `/attune:arch-init` | `attune:arch-init --name my-api` |
| Review a PR | `/full-review` | Run multi-discipline code review |
| Fix PR feedback | `/fix-pr` | Address review comments |
| Prepare a PR | `/pr` + `/sanctum:update-*` | Quality gates before merge |
| Create GitHub issue | `/create-issue` | Interactive issue creation with templates |
| Catch up on changes | `/catchup` | Context recovery after break |
| Write specifications | `/speckit-specify` | Spec-driven development |
| Debug issues | `Skill(superpowers:debugging)` | Systematic root cause analysis |

## Demos

### Skills Showcase Tutorial

![Skills Showcase Demo](assets/gifs/skills-showcase.gif)

**Discover 107 skills** across all plugins, understand their structure, and see how they compose into powerful development workflows.

**What you'll learn:**
- Browse and discover skills across 15 plugins
- Examine skill frontmatter, metadata, and structure
- Use `abstract:plugin-validator` to check quality
- See how skills chain into complex workflows

[→ Full Tutorial](docs/tutorials/skills-showcase.md) (90 seconds, beginner-friendly)

---

## Documentation

| Resource | Description |
|----------|-------------|
| [**Getting Started**](book/src/getting-started/README.md) | Installation and first steps |
| [**Common Workflows**](docs/common-workflows.md) | When to use commands/skills/agents |
| [**Quick Start Guide**](book/src/getting-started/quick-start.md) | Common workflow recipes |
| [**Plugin Catalog**](book/src/plugins/README.md) | Detailed plugin documentation |
| [**Capabilities Reference**](book/src/reference/capabilities-reference.md) | Complete skill/command listing |
| [**Tutorials**](book/src/tutorials/README.md) | Step-by-step guides |
| [**Quality Gates**](docs/quality-gates.md) | Code quality system and pre-commit hooks |
| [**Testing Guide**](docs/testing-guide.md) | Testing patterns and troubleshooting |
| [**Performance Guide**](docs/performance/README.md) | Hook optimization and benchmarking |
| [**LSP Integration**](docs/guides/lsp-native-support.md) | Language Server Protocol setup and verification |

## LSP Integration

### ✅ LSP Support (Recommended)

LSP (Language Server Protocol) provides **symbol-aware search** with 900x performance improvement over text search (50ms vs 45s for reference finding). Available in Claude Code v2.0.74+.

**Setup (Settings-Level Configuration):**

Add to `~/.claude/settings.json`:

```json
{
  "env": {
    "ENABLE_LSP_TOOL": "1"
  }
}
```

Then install language servers:

```bash
# Install language servers
npm install -g pyright typescript-language-server typescript
rustup component add rust-analyzer  # For Rust projects

# Install Claude Code LSP plugins (official)
/plugin install pyright-lsp@claude-plugins-official       # Python
/plugin install typescript-lsp@claude-plugins-official    # TypeScript/JavaScript
/plugin install rust-analyzer-lsp@claude-plugins-official # Rust
```

**Verification:**

```bash
# Run diagnostic script
./scripts/lsp-diagnostic.sh

# Or manually verify
claude
> "Find all references to AsyncAnalysisSkill"  # Triggers LSP
```

**Benefits:**
LSP support improves performance by 900x for semantic queries compared to text search (50ms vs 45s). It reduces token usage by 90% for reference finding and improves accuracy through symbol awareness.

See [LSP Native Support Guide](docs/guides/lsp-native-support.md) for troubleshooting and advanced usage.

## Extending Night Market

To build your own plugins:

```bash
# Scaffold a new plugin
make create-plugin NAME=my-plugin

# Validate structure
make validate

# Run quality checks
make lint && make test

# Or use quality scripts directly
./scripts/run-plugin-lint.sh my-plugin
./scripts/run-plugin-tests.sh my-plugin
./scripts/check-all-quality.sh --report
```

See [Plugin Development Guide](docs/plugin-development-guide.md) for patterns and contribution guidelines, or [Quality Gates](docs/quality-gates.md) for the three-layer quality system.

## System Prompt Budget

The ecosystem operates within Claude Code's 15K character budget. All 222 capabilities (107 skills, 81 commands, 34 agents) load without configuration. Current usage is approximately 14,800 characters (98.7% of budget), enforced by a pre-commit hook to prevent regression.

See [Budget Optimization](docs/budget-optimization-dec-2025.md) for details.

## Philosophy

We prioritize modular design with shallow dependency chains and single responsibility. Plugins load progressively, ensuring users only pay for what they use. Development is spec-driven, prioritizing specifications before implementation.

## Contributing

See [CONTRIBUTING](docs/plugin-development-guide.md#contributing) for guidelines. Each plugin maintains its own tests and documentation.

## License

[MIT](LICENSE)
