# Claude Night Market

**Claude Code plugins for software engineering workflows.**

Claude Night Market extends Claude Code with skills, commands, and agents for git workflows, code review, spec-driven development, and architecture planning.

> **Note:** These plugins function independently but use [superpowers](https://github.com/obra/superpowers) for TDD and debugging.

> **Claude Code 2.1.0+:** This marketplace leverages new features including skill hot-reload, frontmatter hooks, `context: fork`, wildcard permissions, and YAML-style `allowed-tools`. See [Plugin Development Guide](docs/plugin-development-guide.md#claude-code-210-features) for details.

> **Skill Observability:** Track skill execution with continual learning metrics. memory-palace stores execution memories automatically, while pensive provides `/skill-review` for analyzing metrics and stability gaps. See [Skill Observability Guide](docs/guides/skill-observability-guide.md) for details.

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
Skill(sanctum:git-workspace-review)            # Invoke a skill (if Skill tool available)
```

> **Note:** If the `Skill` tool is unavailable, read skill files directly: `Read plugins/{plugin}/skills/{skill-name}/SKILL.md` and follow the instructions.

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
| **pensive** | Code review, shell auditing, skill metrics | `/full-review`, `/shell-review`, `/skill-review` |
| **spec-kit** | Specification-driven development | `/speckit-specify`, `/speckit-plan` |
| **minister** | GitHub issue management | `/create-issue`, `/close-issue`, `/status` |
| **conserve** | Codebase health and bloat detection | `/bloat-scan`, `/unbloat` (saved 70k+ tokens) |
| **attune** | Project scaffolding | `/attune:init`, `/attune:brainstorm` |
| **parseltongue** | Python development tools | `/analyze-tests`, `/run-profiler` |
| **archetypes** | Architecture paradigm selection | 13 architecture guides |
| **memory-palace** | Knowledge management | `/palace`, `/garden`, `/skill-logs` |
| **hookify** | Behavioral rules without config | `/hookify`, `/hookify:list` |

See [Capabilities Reference](book/src/reference/capabilities-reference.md) for all 106 skills, 85 commands, and 35 agents.

## Audience

The Night Market helps developers who want automated workflows and teams standardizing Claude Code practices. Plugin authors can build on standard patterns, while maintainers benefit from automated PR preparation and scaffolding.

## Common Workflows

See [**Common Workflows Guide**](book/src/getting-started/common-workflows.md) for when and how to use commands, skills, and agents:

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

**Browse 106 skills** across all plugins, examine their structure, and combine them into workflows.

**What you'll learn:**
- Browse and discover skills across 16 plugins
- Examine skill frontmatter, metadata, and structure
- Use `abstract:plugin-validator` to check quality
- Chain skills into complex workflows

[→ Full Tutorial](docs/tutorials/skills-showcase.md) (90 seconds, beginner-friendly)

---

## Documentation

| Resource | Description |
|----------|-------------|
| [**Getting Started**](book/src/getting-started/README.md) | Installation and first steps |
| [**Common Workflows**](book/src/getting-started/common-workflows.md) | When to use commands/skills/agents |
| [**Quick Start Guide**](book/src/getting-started/quick-start.md) | Common workflow recipes |
| [**Plugin Catalog**](book/src/plugins/README.md) | Detailed plugin documentation |
| [**Capabilities Reference**](book/src/reference/capabilities-reference.md) | Complete skill/command listing |
| [**Tutorials**](book/src/tutorials/README.md) | Step-by-step guides |
| [**Advanced Guides**](docs/guides/README.md) | In-depth guides for complex topics |
| [**Skills Separation Guide**](docs/guides/development-vs-runtime-skills-separation.md) | Separating dev skills from runtime agent skills ([Quick Ref](docs/guides/skills-separation-quickref.md)) |
| [**Quality Gates**](docs/quality-gates.md) | Code quality system and pre-commit hooks |
| [**Error Handling**](docs/guides/error-handling-guide.md) | Error classification and recovery patterns |
| [**Optimization Patterns**](docs/optimization-patterns.md) | Bloat reduction methodology (70k+ tokens saved) |
| [**Data Extraction Pattern**](docs/guides/data-extraction-pattern.md) | Separating embedded data into YAML |
| [**Documentation Standards**](docs/guides/documentation-standards.md) | Line limits and debloating methodology |
| [**Testing Guide**](docs/testing-guide.md) | Testing patterns and troubleshooting |
| [**Performance Guide**](docs/performance/README.md) | Hook optimization and benchmarking |
| [**LSP Integration**](docs/guides/lsp-native-support.md) | Language Server Protocol setup and verification |

## LSP Integration

### LSP Support (Recommended)

LSP (Language Server Protocol) enables **symbol-aware search**, which is faster than text search. Available in Claude Code v2.0.74+.

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
LSP finds references in ~50ms (vs ~45s for text search), uses fewer tokens, and is more accurate.

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

The ecosystem operates within Claude Code's 15K character budget. All 226 capabilities (106 skills, 85 commands, 35 agents) load without configuration. Current usage is approximately 14,800 characters, enforced by a pre-commit hook.

See [Budget Optimization](docs/budget-optimization-dec-2025.md) for details.

## Philosophy

Night Market plugins are modular with shallow dependencies. They load progressively, so you only pay for what you use. Development prioritizes specifications before implementation.

## Contributing

See [CONTRIBUTING](docs/plugin-development-guide.md#contributing) for guidelines. Each plugin maintains its own tests and documentation.

## License

[MIT](LICENSE)
