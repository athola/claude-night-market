# Claude Night Market

[![Version](https://img.shields.io/badge/version-1.8.2-blue)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Plugins](https://img.shields.io/badge/plugins-23-orange)](book/src/plugins/)
[![Skills](https://img.shields.io/badge/skills-167-teal)](book/src/reference/capabilities-reference.md)
[![Claude Code](https://img.shields.io/badge/Claude_Code-2.1.16%2B-purple)](https://code.claude.com/docs/en/overview)
[![GitHub Stars](https://img.shields.io/github/stars/athola/claude-night-market?style=social)](https://github.com/athola/claude-night-market)
[![Quillx: 3/5 Adapted](https://img.shields.io/badge/Quillx-3%2F5%20Adapted-blue)](https://github.com/QAInsights/Quillx)

**A plugin marketplace for Claude Code, Anthropic's
agentic coding tool.**

Night Market extends Claude Code with 23 plugins
covering git workflows, code review, spec-driven
development, architecture selection, codebase
visualization, autonomous agents, multi-LLM delegation,
ML-enhanced scoring, and multi-source research.
167 skills, 148 slash commands, and 51 agents.
Each plugin installs independently.

<p align="center">
  <img src="assets/gifs/skills-showcase.gif" alt="Night Market skills in action" width="720">
</p>

## Quick Start

Requires **Claude Code 2.1.16+** and **Python 3.9+** for hooks.
See [Requirements](#requirements) for details.

```bash
# Add the marketplace
/plugin marketplace add athola/claude-night-market

# Install plugins you need
/plugin install sanctum@claude-night-market    # Git workflows
/plugin install pensive@claude-night-market    # Code review
/plugin install spec-kit@claude-night-market   # Spec-driven dev

# Use them
/prepare-pr                                    # Prepare a pull request
/full-review                                   # Run code review
```

**Alternative:** Install via npx with
`npx skills add athola/claude-night-market` (installs all plugins at once).

After installation, run `claude --init` for one-time setup.

> **Note:** If the `Skill` tool is unavailable, read skill files directly
> at `plugins/{plugin}/skills/{skill-name}/SKILL.md`.

### opkg (OpenPackage)

```bash
# Install specific plugins
opkg i gh@athola/claude-night-market --plugins sanctum
opkg i gh@athola/claude-night-market --plugins pensive,conserve

# Plugins that depend on shared runtime skills (e.g. attune, conjure)
# automatically pull packages/core as a dependency
```

See the [Installation Guide](book/src/getting-started/installation.md)
for detailed setup options.

## Architecture

23 internal plugins in four layers, plus external
plugins from the superpowers-marketplace.
Arrows show dependency direction (A --> B means
A depends on B).

```mermaid
flowchart TB
    classDef domain fill:#e8f4f8,stroke:#2980b9,stroke-width:2px,color:#2c3e50
    classDef utility fill:#f8f4e8,stroke:#f39c12,stroke-width:2px,color:#2c3e50
    classDef foundation fill:#f4e8f8,stroke:#8e44ad,stroke-width:2px,color:#2c3e50
    classDef meta fill:#e8f4e8,stroke:#27ae60,stroke-width:2px,color:#2c3e50
    classDef ext fill:#f5f5f5,stroke:#95a5a6,stroke-width:1px,stroke-dasharray: 5 5,color:#7f8c8d
    classDef standalone fill:#fafafa,stroke:#bdc3c7,stroke-width:1px,color:#95a5a6

    subgraph External["External · superpowers-marketplace"]
        direction LR
        SP[superpowers]:::ext
        SPC[superpowers-chrome]:::ext
        SPD[superpowers-dev]:::ext
        SPL[superpowers-lab]:::ext
    end

    subgraph Domain["Domain Specialists"]
        attune:::domain
        pensive:::domain
        scribe:::domain
        spec-kit:::domain
        memory-palace:::domain
        minister:::domain
        parseltongue:::domain
        tome:::domain
        gauntlet:::domain
        phantom:::domain
        archetypes:::domain
        cartograph:::domain
        scry:::domain
    end

    subgraph Utility["Utility Layer"]
        conserve:::utility
        conjure:::utility
        hookify:::utility
        egregore:::utility
        herald:::utility
        oracle:::utility
    end

    subgraph Foundation["Foundation Layer"]
        leyline:::foundation
        imbue:::foundation
        sanctum:::foundation
    end

    subgraph Meta["Meta Layer"]
        abstract:::meta
    end

    %% Domain --> Foundation
    attune --> imbue & sanctum & leyline
    pensive --> imbue & leyline
    scribe --> leyline & pensive & scry
    spec-kit --> imbue & sanctum
    memory-palace --> leyline & sanctum
    parseltongue --> leyline
    minister --> leyline
    tome --> leyline

    %% Domain --> Domain
    attune --> spec-kit

    %% Utility --> Foundation
    conserve --> leyline & imbue
    conjure --> leyline
    hookify --> leyline
    egregore --> sanctum & conserve

    %% Meta --> Foundation + Domain
    abstract --> leyline & imbue & sanctum & pensive

    %% External (dashed = complements, not hard dependency)
    SP -.-> imbue & sanctum & attune
```

### Plugin Catalog

| Plugin | Layer | Description | Skills | Cmds |
|--------|-------|-------------|:------:|:----:|
| **abstract** | Meta | Skill authoring, hook development, evaluation frameworks, escalation governance | 12 | 18 |
| **leyline** | Foundation | Auth flows (GitHub/GitLab/AWS), quota management, error patterns, markdown formatting, Discussions retrieval, damage-control, stewardship, trust verification, injection detection, deferred-capture contracts | 21 | 3 |
| **sanctum** | Foundation | Git workflows, commit messages, PR prep, docs updates, version management, sessions, deferred-item capture | 14 | 46 |
| **imbue** | Foundation | TDD enforcement, proof-of-work validation, scope guarding, rigorous reasoning | 10 | 3 |
| **conserve** | Utility | Context optimization, bloat detection, CPU/GPU monitoring, token conservation | 12 | 4 |
| **conjure** | Utility | Delegation framework for routing tasks to external LLMs (Gemini, Qwen) with cheapest-capable model selection | 4 | 0 |
| **hookify** | Utility | Behavioral rules engine with markdown configuration and hook-to-rule conversion | 2 | 6 |
| **egregore** | Utility | Autonomous agent orchestrator with parallel worktrees, agent specialization, cross-item learning, and crash recovery | 4 | 5 |
| **herald** | Utility | Shared notification library: GitHub issue alerts, webhook support (Slack, Discord, generic) | 0 | 0 |
| **oracle** | Utility | ONNX Runtime inference daemon for ML-enhanced plugin capabilities over localhost HTTP | 1 | 1 |
| **pensive** | Domain | Code review, architecture review, bug hunting, blast radius analysis, Makefile audits, NASA Power of 10 | 13 | 12 |
| **attune** | Domain | Project lifecycle: brainstorm, specify, plan, initialize, execute, war-room, dorodango polishing | 13 | 10 |
| **spec-kit** | Domain | Spec-driven development: specifications, task generation, implementation | 3 | 10 |
| **parseltongue** | Domain | Python: testing, performance, async patterns, packaging | 4 | 3 |
| **minister** | Domain | GitHub issue management, label taxonomy, initiative tracking | 2 | 3 |
| **memory-palace** | Domain | Spatial knowledge organization, digital garden curation, PR review capture | 6 | 5 |
| **archetypes** | Domain | Architecture paradigm selection (hexagonal, CQRS, microservices, etc.) | 14 | 0 |
| **gauntlet** | Domain | Codebase learning through knowledge extraction, challenges, code knowledge graph, and spaced repetition | 6 | 6 |
| **phantom** | Domain | Computer use: screenshot capture, mouse/keyboard control, autonomous desktop agent | 1 | 1 |
| **scribe** | Domain | Documentation with AI slop detection, style learning, session replay, tech tutorials | 7 | 5 |
| **scry** | Domain | Terminal recordings (VHS), browser recordings (Playwright), GIF processing | 4 | 2 |
| **tome** | Domain | Multi-source research: code archaeology, community discourse, academic literature, TRIZ analysis | 7 | 4 |
| **cartograph** | Domain | Codebase visualization: architecture, data flow, dependency, call chains, community detection, class diagrams via Mermaid | 7 | 1 |

Full inventory:
[Capabilities Reference](book/src/reference/capabilities-reference.md).

### How the Layers Work

**Governance.** `imbue` enforces TDD via a PreToolUse hook that
verifies test files before allowing implementation writes.
Quality gates halt execution when tests fail.

**Security.** `leyline` manages OAuth flows with local token
caching. `conserve` auto-approves safe commands while blocking
destructive operations. `sanctum` isolates named sessions, and
agents can run in worktree isolation for parallel execution.

**Orchestration.** `egregore` manages autonomous agent lifecycles
with parallel worktree execution, agent specialization, cross-item
learning, and crash recovery via watchdog monitoring.

**Maintenance.** `/update-ci` reconciles pre-commit hooks and
GitHub Actions with code changes. `abstract` tracks skill
stability and auto-triggers improvement agents when degradation
is detected.

**Cross-session state.** `attune`, `spec-kit`, and `sanctum`
persist state across sessions via `CLAUDE_CODE_TASK_LIST_ID`.
GitHub Discussions serve as a second persistence layer for
decisions, war-room deliberations, and evergreen knowledge.

**Risk classification.** `leyline:risk-classification` provides
4-tier task gating (GREEN/YELLOW/RED/CRITICAL). RED and CRITICAL
tasks escalate to `war-room-checkpoint` for expert deliberation.

## Common Workflows

See the [Common Workflows Guide][workflows] for full details.

| Workflow | Command | What it does |
|----------|---------|-------------|
| Project lifecycle | `/attune:mission` | Routes through brainstorm, specify, plan, execute phases |
| Initialize project | `/attune:arch-init` | Architecture-aware scaffolding with language detection |
| Review a PR | `/full-review` | Multi-discipline code review in a single pass |
| Fix PR feedback | `/fix-pr` | Address review comments progressively |
| Implement issues | `/do-issue` | Issue resolution with parallel agent execution |
| Prepare a PR | `/prepare-pr` | Quality gates, linting, clean git state |
| Write specs | `/speckit-specify` | Specification-first development |
| Catch up on changes | `/catchup` | Context recovery from recent git history |
| Codebase cleanup | `/unbloat` | Bloat removal with progressive depth levels |
| Update CI/CD | `/update-ci` | Reconcile hooks and workflows with code changes |
| Strategic decisions | `/attune:war-room` | Expert routing with reversibility scoring |
| Refine code | `/refine-code` | Duplication, algorithm, and clean code analysis |

## What's New

See the [Changelog](CHANGELOG.md) for the full history.

## Requirements

- **Claude Code** 2.1.16+ (2.1.32+ for agent teams, 2.1.38+ for
  security features, 2.1.85+ latest tested)
- **Python 3.9+** for hooks (macOS ships 3.9.6). Plugin packages may
  target 3.10+ via virtual environments, but all hook code must be
  3.9-compatible. See the [Plugin Development Guide][dev-guide]
  for compatibility rules.

## Plugin Development

Create a new plugin:

```bash
make create-plugin NAME=my-plugin
make validate
make lint && make test
```

Plugin layout:

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json        # Metadata: skills, commands, agents, hooks
├── commands/               # Slash commands (markdown)
├── skills/                 # Agent skills (SKILL.md + modules/)
├── hooks/                  # Event handlers (Python, 3.9-compatible)
├── agents/                 # Specialized agent definitions
├── tests/                  # pytest suite
├── Makefile                # Build, test, lint targets
└── pyproject.toml          # Package config
```

See the [Plugin Development Guide][dev-guide] for structure requirements
and naming conventions. For LSP integration, see the
[LSP Guide](docs/guides/lsp-native-support.md).

## Documentation

- [Installation Guide](book/src/getting-started/installation.md) -
  setup, marketplace, post-install hooks
- [Quick Start](book/src/getting-started/quick-start.md) -
  first commands after installation
- [Common Workflows][workflows] - task-oriented usage guide
- [Plugin Development Guide][dev-guide] - creating and testing plugins
- [Capabilities Reference](book/src/reference/capabilities-reference.md) -
  full skill, command, and agent inventory
- [Tutorials](book/src/tutorials/README.md) -
  PR workflows, debugging, feature lifecycles
- [Architecture Decision Records](docs/adr/) -
  design rationale and trade-off documentation

Per-plugin documentation lives in `book/src/plugins/`
(one page per plugin).

## Stewardship

Every plugin is entrusted to the community. Five principles guide how
we maintain and improve the ecosystem: steward (not own), multiply (not
merely preserve), be faithful in small things, serve those who come
after, and think seven iterations ahead.

Each plugin README includes a Stewardship section with specific
improvement opportunities. Run `/stewardship-health` to view per-plugin
health dimensions.

See [STEWARDSHIP.md](STEWARDSHIP.md) for the full manifesto.

## Contributing

Each plugin maintains its own tests and documentation. Run `make test`
at the repo root to execute all plugin test suites. See the
[Plugin Development Guide][dev-guide] for contribution guidelines.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=athola/claude-night-market&type=Date)](https://star-history.com/#athola/claude-night-market&Date)

## Powered by Night Market

Using night-market plugins in your project? Add the badge:

```markdown
[![Powered by Night Market](https://img.shields.io/badge/powered_by-Night_Market-blueviolet)](https://github.com/athola/claude-night-market)
```

[![Powered by Night Market](https://img.shields.io/badge/powered_by-Night_Market-blueviolet)](https://github.com/athola/claude-night-market)

## License

[MIT](LICENSE)

[claude-code]: https://docs.anthropic.com/en/docs/build-with-claude/claude-code
[dev-guide]: docs/plugin-development-guide.md
[workflows]: book/src/getting-started/common-workflows.md
