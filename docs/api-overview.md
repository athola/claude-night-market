# API Overview

*Updated: 2026-03-20*
*Original Source: API_REVIEW_REPORT.md (API Surface Inventory)*

## API Surface Summary

Claude Night Market consists of 18 plugins that provide
CLI commands, Python packages, and skill-based APIs.
These tools support a range of workflows, from code
review to knowledge management.

## API Inventory

The ecosystem includes 109 CLI commands, 142 modular
skills, 47 specialized agents, and 9 Python packages
with public APIs. We also maintain 25 execution hooks.

| Plugin | Version | Commands | Skills | Agents | Python Package | CLI Entry |
|--------|---------|----------|--------|--------|----------------|-----------|
| abstract | 1.6.7 | 18 | 11 | 5 | Yes | abstract-skills |
| archetypes | 1.6.7 | 0 | 14 | 0 | No | - |
| attune | 1.6.7 | 10 | 13 | 2 | No | - |
| conjure | 1.6.7 | 0 | 4 | 0 | No | - |
| conserve | 1.6.7 | 4 | 11 | 5 | No | - |
| egregore | 1.6.7 | 5 | 4 | 2 | No | - |
| hookify | 1.6.7 | 6 | 2 | 0 | No | - |
| imbue | 1.6.7 | 3 | 10 | 1 | No | - |
| leyline | 1.6.7 | 3 | 17 | 0 | Yes | - |
| memory-palace | 1.6.7 | 5 | 6 | 4 | Yes | - |
| minister | 1.6.7 | 3 | 2 | 0 | Yes | - |
| parseltongue | 1.6.7 | 3 | 4 | 4 | No | parseltongue |
| pensive | 1.6.7 | 12 | 12 | 4 | Yes | - |
| sanctum | 1.6.7 | 18 | 14 | 9 | Yes | - |
| scribe | 1.6.7 | 3 | 4 | 3 | Yes | - |
| scry | 1.6.7 | 2 | 4 | 1 | No | - |
| spec-kit | 1.6.7 | 10 | 3 | 3 | Yes | - |
| tome | 1.7.0 | 4 | 7 | 4 | No | - |

## Plugin Details

### Abstract (v1.6.7)
Validation and analysis framework for the ecosystem.
Includes commands for creating and validating skills, hooks,
and plugins (`validate-plugin`, `create-skill`).
Skills focus on governance, authoring, and evaluation, including `skills-eval`,
`rules-eval`, and `modular-skills`.
A daily learning aggregation hook generates LEARNINGS.md
and promotes findings to GitHub Issues or Discussions based on severity.

### Archetypes (v1.6.7)
Reference library for architecture paradigms.
Contains 14 skills covering patterns like hexagonal architecture,
microservices, and event-driven design.

### Attune (v1.6.7)
Project initialization, architecture templates, and strategic decision-making.
Commands include `arch-init`, `init`,
`war-room` (multi-expert deliberation with optional agent teams execution for
Full Council and Delphi modes),
and `mission` (unified lifecycle orchestrator with state detection
and session recovery).

### Conjure (v1.6.7)
Cross-model delegation and multi-agent coordination.
Skills like `gemini-delegation`
and `qwen-delegation` route tasks to specific models,
while `agent-teams` coordinates parallel Claude Code agents through a
filesystem-based protocol.

### Conserve (v1.6.7)
Context window usage and resource management.
Commands like `bloat-scan`
and `optimize-context` help developers understand token consumption.
Skills include `context-optimization`, `clear-context`,
and `cpu-gpu-performance`.

### Hookify (v1.6.7)
Behavioral rules engine with markdown-based configuration.
Commands convert Python hooks to declarative rules (`from-hook`),
manage rule catalogs (`install`, `list`),
and configure rule activation (`configure`).

### Imbue (v1.6.7)
Structured review workflows. Offers commands for catchups,
structured reviews, and stewardship health checks
(`catchup`, `structured-review`, `stewardship-health`).
Skills include `proof-of-work`, `scope-guard`,
`rigorous-reasoning`, and `latent-space-engineering`.

### Leyline (v1.6.7)
Shared patterns and utilities library.
Allows for bulk plugin updates via `reinstall-all-plugins`.
Skills cover authentication,
error handling (including agent crash recovery via `error-patterns`),
testing standards, cross-platform git forge detection via `git-platform`,
4-tier risk routing via `risk-classification`, stewardship principles,
and a `deferred-capture` contract for unified deferred-item filing.

### Memory-Palace (v1.6.7)
Knowledge management organization.
Commands like `garden` and `palace` help users navigate
and structure information. Skills focus on knowledge intake and retrieval.

### Minister (v1.6.7)
GitHub issue management and initiative tracking.
Commands include `create-issue`, `close-issue`, and `update-labels`.
Skills provide release health gates and initiative pulse dashboards.

### Parseltongue (v1.6.7)
Python development utilities. Includes tools for analyzing tests
and profiling performance (`analyze-tests`, `run-profiler`).
Skills support async programming and packaging.

### Pensive (v1.6.7)
Code review and analysis framework.
Provides specific review commands for various languages
and domains, such as `api-review`, `rust-review`, and
`bug-review`. Includes `safety-critical-patterns` for
NASA Power of 10 rules and `tiered-audit` for
three-tier escalation analysis.

### Sanctum (v1.6.7)
Git workflow automation.
Handles tasks from commit message generation to PR reviews with mandatory code
quality analysis. Commands include `fix-pr`, `merge-docs`,
and `update-dependencies`. Hooks include a PostToolUse deferred-item watcher
and a Stop hook that sweeps the session ledger to file GitHub issues.

### Scribe (v1.6.7)
Documentation quality enforcement.
Commands include `doc-polish` (interactive editing),
`doc-generate` (documentation generation), and `style-learn` (style profiling).
AI content detection and accuracy validation are handled by the `slop-hunter`
and `doc-verifier` agents respectively.
Skills detect AI-generated content markers (`slop-detector`),
learn writing styles (`style-learner`),
and generate human-quality documentation (`doc-generator`).

### Scry (v1.6.7)
Terminal and browser session recording.
Supports creating media assets with commands like `record-browser`
and `record-terminal`.

### Spec-Kit (v1.6.7)
Specification-driven development.
Offers a suite of commands for planning, specifying,
and implementing features based on strict requirements.

### Egregore (v1.6.7)
Autonomous agent orchestrator for development lifecycles.
Commands include `summon` (spawn sessions), `dismiss`
(terminate), `status` (check progress),
`install-watchdog` and `uninstall-watchdog` (crash
recovery). Skills cover session spawning with budget
management (`summon`), pre-merge validation
(`quality-gate`), and watchdog lifecycle management.

### Tome (v1.7.0)
Multi-source research plugin for code archaeology,
community discourse, academic literature, and TRIZ
cross-domain analysis.
Commands include `research` (multi-source research),
`dig` (code archaeology), `cite` (citation management),
and `export` (output formatting).
Skills cover `code-search`, `discourse`, `papers`,
`synthesize`, and `triz` (cross-domain inventive
problem solving).

## API Quality Assessment

We enforce documentation and type safety using `ruff`, `mypy`, and `bandit`.
All plugins adhere to a standard directory structure to ensure discovery.
Our current focus is on normalizing command naming across plugins
and clarifying export patterns for cross-plugin dependencies.

## Enterprise Configuration (2.1.51+)

Managed settings can be deployed through multiple
channels:

| Platform | Mechanism | Path |
|----------|-----------|------|
| macOS | plist (MDM) | `com.anthropic.claudecode` domain |
| Windows | Registry | `HKLM\SOFTWARE\Policies\ClaudeCode` |
| All | File-based | See table below |

**File-based managed settings locations:**

| OS | Path |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/` |
| Linux/WSL | `/etc/claude-code/` |
| Windows | `C:\Program Files\ClaudeCode\` |

**Settings precedence** (highest to lowest):
1. Server-managed (remote)
2. MDM/OS-level policies (plist, HKLM registry)
3. File-based `managed-settings.json`
4. Command line arguments
5. Local project settings (`.claude/settings.local.json`)
6. Shared project settings (`.claude/settings.json`)
7. User settings (`~/.claude/settings.json`)

Managed-only settings (enforced by IT) include
`allowManagedPermissionRulesOnly`,
`allowManagedHooksOnly`, `allowManagedMcpServersOnly`,
`strictKnownMarketplaces`, `blockedMarketplaces`, and
`disableBypassPermissionsMode`.

## Related Documents

- [Plugin Development Guide](plugin-development-guide.md)
- [Skill Integration Guide](skill-integration-guide.md)
- [Plugin Dependencies](plugin-dependencies.md)
