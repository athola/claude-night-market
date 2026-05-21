# Claude Night Market

[![Version](https://img.shields.io/badge/version-1.9.7-blue)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Plugins](https://img.shields.io/badge/plugins-23-orange)](book/src/plugins/)
[![Skills](https://img.shields.io/badge/skills-187-teal)](book/src/reference/capabilities-reference.md)
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
187 skills, 129 slash commands, and 55 agents.
Each plugin installs independently.

<p align="center">
  <img src="assets/gifs/skills-showcase.gif" alt="Night Market skills in action" width="720">
</p>

## Highlights

- **TDD by default.** `imbue` enforces failing-test-first via
  PreToolUse hooks; CONSTITUTION.md encodes rules that override any
  conflicting skill.
- **Layered architecture.** Four internal layers (Foundation,
  Utility, Domain, Meta) prevent dependency cycles. Install only
  what you need.
- **Multi-LLM delegation.** `conjure` routes tasks to Gemini and
  Qwen with cheapest-capable model selection.
- **AI-slop guards.** `scribe:slop-detector` runs four layers of
  checks (P0 critical patterns, document economy, sentence-level
  slop, evidence-backed claims) before docs ship.
- **Cross-session state.** Task lists, sessions, and decisions
  persist via `CLAUDE_CODE_TASK_LIST_ID` and GitHub Discussions.

## Contents

- [Quick Start](#quick-start)
- [Trust and Safety](#trust-and-safety)
- [Architecture](#architecture) (plugin catalog, layer model)
- [Common Workflows](#common-workflows)
- [Requirements](#requirements)
- [What's New](#whats-new)
- [Plugin Development](#plugin-development)
- [Documentation](#documentation)
- [Stewardship](#stewardship) · [Contributing](#contributing) ·
  [Acknowledgements](#acknowledgements) · [License](#license)

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

## Trust and Safety

> ⚠️ Plugins run inside your Claude Code session and can read or
> edit your repo, run shell commands, and call external services.
> **Review any plugin before installing it.**

Night Market ships three lines of defense, but none replace your
own review:

- **TDD gates** (`imbue`): a PreToolUse hook blocks implementation
  writes that lack a corresponding failing test.
- **Destructive-command blockers** (`conserve`): auto-approve safe
  commands while halting `rm -rf`, `git push --force`,
  `git reset --hard`, and similar.
- **Additive-bias audits** (`leyline:additive-bias-defense`): every
  diff is checked for unjustified additions before commit.

See [STEWARDSHIP.md](STEWARDSHIP.md) for the maintenance contract
and [CONSTITUTION.md](CONSTITUTION.md) for the immutable rules
that override any conflicting skill or hook.

## Architecture

23 internal plugins in four layers, plus external
plugins from the superpowers-marketplace.
Arrows show dependency direction (A --> B means
A depends on B). Dashed arrows mark optional
complements.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/architecture-dark.svg">
  <img alt="Plugin architecture: 5 layers (External, Meta, Domain, Utility, Foundation) with 23 plugins" src="assets/architecture-light.svg">
</picture>

<sub>Source: <a href="assets/architecture.d2">assets/architecture.d2</a>; regenerate with <code>d2 assets/architecture.d2 assets/architecture-light.svg</code></sub>

### Plugin Catalog

| Plugin | Layer | Description | Skills | Cmds |
|--------|-------|-------------|:------:|:----:|
| **abstract** | Meta | Skill authoring, hook development, evaluation frameworks, escalation governance, hook scope guidance | 15 | 18 |
| **leyline** | Foundation | Auth flows (GitHub/GitLab/AWS), quota management, error patterns, markdown formatting, Discussions retrieval, damage-control, stewardship, trust verification, injection detection, deferred-capture contracts, additive-bias defense | 22 | 3 |
| **sanctum** | Foundation | Git workflows, commit messages, PR prep, docs updates, version management, sessions, deferred-item capture | 18 | 20 |
| **imbue** | Foundation | TDD enforcement, proof-of-work validation, scope guarding, additive-bias auditing, rigorous reasoning, vow enforcement | 13 | 5 |
| **conserve** | Utility | Context optimization, bloat detection, context mapping, CPU/GPU monitoring, token conservation, filter-first log debugging | 13 | 5 |
| **conjure** | Utility | Delegation framework for routing tasks to external LLMs (Gemini, Qwen) with cheapest-capable model selection | 4 | 0 |
| **hookify** | Utility | Behavioral rules engine with markdown configuration and hook-to-rule conversion | 2 | 6 |
| **egregore** | Utility | Autonomous agent orchestrator with parallel worktrees, agent specialization, cross-item learning, and crash recovery | 4 | 5 |
| **herald** | Utility | Shared notification library: GitHub issue alerts, webhook support (Slack, Discord, generic) | 0 | 0 |
| **oracle** | Utility | ONNX Runtime inference daemon for ML-enhanced plugin capabilities over localhost HTTP | 1 | 1 |
| **pensive** | Domain | Code review, architecture review, bug hunting, blast radius analysis, performance hotspots, Makefile audits, NASA Power of 10 | 14 | 13 |
| **attune** | Domain | Project lifecycle: brainstorm, specify, plan, interactive plan review, initialize, execute, war-room, dorodango polishing | 13 | 10 |
| **spec-kit** | Domain | Spec-driven development: specifications, task generation, implementation | 3 | 10 |
| **parseltongue** | Domain | Python: testing, performance, async patterns, packaging | 4 | 3 |
| **minister** | Domain | GitHub issue management, label taxonomy, initiative tracking, DORA delivery metrics | 3 | 3 |
| **memory-palace** | Domain | Spatial knowledge organization, digital garden curation, PR review capture | 7 | 5 |
| **archetypes** | Domain | Architecture paradigm selection (hexagonal, CQRS, microservices, etc.) | 14 | 0 |
| **gauntlet** | Domain | Codebase learning through knowledge extraction, challenges, code knowledge graph, and spaced repetition | 7 | 6 |
| **phantom** | Domain | Computer use: screenshot capture, mouse/keyboard control, autonomous desktop agent | 1 | 1 |
| **scribe** | Domain | Documentation, AI slop detection, SICO voice extraction, style transfer, session replay | 11 | 9 |
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

## Requirements

- **Claude Code** 2.1.16+ (2.1.32+ for agent teams, 2.1.38+ for
  security features, 2.1.85+ latest tested)
- **Python 3.9+** for hooks (macOS ships 3.9.6). Plugin packages may
  target 3.10+ via virtual environments, but all hook code must be
  3.9-compatible. See the [Plugin Development Guide][dev-guide]
  for compatibility rules.

## What's New

**1.9.7:** `conserve` adds the `log-debugging-hygiene` module
and `/filter-log` command. On the committed
`intake_queue.jsonl` fixture, `tail -n 100` beats lossless log
compression by 25 percentage points; the module documents a
three-tier workflow (filter first, then compact-output flags,
then compression as fallback) anchored on that reproducible
benchmark. An invariant test prevents future regression by
asserting the plugin's runtime deps stay free of bundled
compressors, and hypothesis-based property tests verify tier-1
outputs remain literal subsets of the input. See
[CHANGELOG](CHANGELOG.md#197---2026-05-18) for the full entry.

**1.9.6:** adds `minister:dora-metrics` for computing the
four DORA delivery-performance metrics (deployment frequency,
lead time for changes, change failure rate, median time to
restore service) from GitHub PR and deployment data,
classifying results into Elite / High / Medium / Low tiers
from the Accelerate research (#487). `gauntlet` gains an in-loop
variation provider that runs deterministically inside Claude
Code, so challenge wording can vary without spawning a sibling
Claude through the Anthropic SDK (#464). `memory-palace`
deduplication validates `importance_score` bounds `[0, 100]`
before any cache or on-disk mutation. `tome:research` is now
registered as a dispatchable agent so other plugins can invoke
it through the Agent tool (#465). Test and documentation
backfills land across `minister`, `tome`, `sanctum`, `imbue`,
`pensive`, `archetypes`, and `abstract`.

**1.9.5:** bugfix-only batch closing 24 review findings
from PR #417. Imbue hooks are hardened against false
positives and edge cases; imbue test reliability is
improved across `proof-of-work`, `scope-guard`, and
related skills; cross-plugin refactors retire dead code
in `parseltongue`, `pensive`, `scribe`, and `tome`; the
`abstract` plugin gains policy and feature work tied to
issues #453 through #462. No new public APIs; full test
suites pass (imbue 635, leyline 656 at 89.58% coverage,
abstract 2186 with 3 xfailed).

**1.9.4:** the AI-slop playbook is now wired
across the ecosystem. `scribe:slop-detector` gains seven modules
(identity-and-voice leaks, hallucination detection, stub handling,
document economy, empirical baseline calibration, evidence-backed
claims, anti-goals) and a `cleanup-workflow` that walks editors
through Layer 0 to Layer 3 remediation; `pensive:rust-review`
adds four Rust-specific slop modules. A new top-level
[CONSTITUTION.md](CONSTITUTION.md) codifies AI-hygiene guardrails
as supreme rules. `leyline` ships a `git_platform` Python wrapper
for cross-platform `gh api` calls and a `bootstrap` helper that
eliminates ad-hoc `sys.path` manipulation in plugin scripts.
`abstract` adds a `hook-scope-guide` skill for choosing
plugin / project / global scope. Three quality refinement waves
closed 24 review findings across eight plugins.

**1.9.3 and earlier:** inclusive-defaults policy, `safe-defaults`
hookify bundle, TDD-by-default in `speckit-tasks`. See the
[Changelog](CHANGELOG.md) for the full history.

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

Per-plugin documentation is in `book/src/plugins/`
(one page per plugin).

## Stewardship

Every plugin is entrusted to the community. Five principles guide how
we maintain and improve the ecosystem: steward (not own), multiply (not
merely preserve), be faithful in small things, serve those who come
after, and think seven iterations ahead.

Each plugin README includes a Stewardship section with specific
improvement opportunities. Run `/stewardship-health` to view per-plugin
health dimensions.

See [STEWARDSHIP.md](STEWARDSHIP.md) for the full manifesto and
[CONSTITUTION.md](CONSTITUTION.md) for the immutable rules
(AI disclosure, additive-bias defense, TDD gates, slop-scan
gates) that override any conflicting skill or hook.

## Contributing

Each plugin maintains its own tests and documentation. Run `make test`
at the repo root to execute all plugin test suites. See the
[Plugin Development Guide][dev-guide] for contribution guidelines.

## Acknowledgements

Night Market stands on the shoulders of upstream work:

- [Anthropic Claude Code][claude-code]: the agentic coding tool
  this marketplace extends.
- [github/spec-kit][spec-kit-upstream]: the `spec-kit` plugin syncs
  with upstream v0.5.0 for spec-driven development.
- [obra/superpowers][superpowers-upstream]: Night Market integrates
  with superpowers v5.0.7 for foundational workflow methodology.
  See the [Superpowers Integration Guide][superpowers-doc].
- [QAInsights/Quillx][quillx]: three of five Quillx patterns adapted
  into Night Market plugins (see the badge near the top).

Per-plugin attributions are in each plugin's `pyproject.toml` and
documentation. See [STEWARDSHIP.md](STEWARDSHIP.md) for the
maintenance contract that governs how upstream changes flow in.

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
[spec-kit-upstream]: https://github.com/github/spec-kit
[superpowers-upstream]: https://github.com/obra/superpowers
[superpowers-doc]: book/src/reference/superpowers-integration.md
[quillx]: https://github.com/QAInsights/Quillx
