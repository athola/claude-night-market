# API Overview

*Updated: 2026-02-26*
*Original Source: API_REVIEW_REPORT.md (API Surface Inventory)*

## API Surface Summary

Claude Night Market consists of 16 plugins that provide CLI commands, Python packages, and skill-based APIs. These tools support a range of workflows, from code review to knowledge management.

## API Inventory

The ecosystem includes 96 CLI commands, 120 modular skills, 41 specialized agents, and 7 Python packages with public APIs. We also maintain 20 execution hooks.

| Plugin | Version | Commands | Skills | Agents | Python Package | CLI Entry |
|--------|---------|----------|--------|--------|----------------|-----------|
| abstract | 1.5.1 | 18 | 10 | 5 | Yes | abstract-skills |
| archetypes | 1.5.1 | 0 | 14 | 0 | No | - |
| attune | 1.5.1 | 10 | 12 | 2 | No | - |
| conjure | 1.5.1 | 0 | 4 | 0 | No | - |
| conserve | 1.5.1 | 4 | 10 | 5 | No | - |
| hookify | 1.5.1 | 6 | 2 | 0 | No | - |
| imbue | 1.5.1 | 2 | 9 | 1 | No | - |
| leyline | 1.5.1 | 2 | 12 | 0 | Yes | - |
| memory-palace | 1.5.1 | 5 | 6 | 4 | Yes | - |
| minister | 1.5.1 | 3 | 2 | 0 | Yes | - |
| parseltongue | 1.5.1 | 3 | 4 | 4 | No | - |
| pensive | 1.5.1 | 12 | 11 | 4 | Yes | - |
| sanctum | 1.5.1 | 17 | 14 | 9 | Yes | - |
| scribe | 1.5.1 | 3 | 3 | 3 | No | - |
| scry | 1.5.1 | 2 | 4 | 1 | No | - |
| spec-kit | 1.5.1 | 9 | 3 | 3 | Yes | - |

## Plugin Details

### Abstract (v1.5.1)
Validation and analysis framework for the ecosystem. Includes commands for creating and validating skills, hooks, and plugins (`validate-plugin`, `create-skill`). Skills focus on governance, authoring, and evaluation, including `skills-eval`, `rules-eval`, and `modular-skills`. A daily learning aggregation hook generates LEARNINGS.md and promotes findings to GitHub Issues or Discussions based on severity.

### Archetypes (v1.5.1)
Reference library for architecture paradigms. Contains 14 skills covering patterns like hexagonal architecture, microservices, and event-driven design.

### Attune (v1.5.1)
Project initialization, architecture templates, and strategic decision-making. Commands include `arch-init`, `init`, `war-room` (multi-expert deliberation with optional agent teams execution for Full Council and Delphi modes), and `mission` (unified lifecycle orchestrator with state detection and session recovery).

### Conjure (v1.5.1)
Cross-model delegation and multi-agent coordination. Skills like `gemini-delegation` and `qwen-delegation` route tasks to specific models, while `agent-teams` coordinates parallel Claude Code agents through a filesystem-based protocol.

### Conserve (v1.5.1)
Context window usage and resource management. Commands like `bloat-scan` and `optimize-context` help developers understand token consumption. Skills include `context-optimization`, `clear-context`, and `cpu-gpu-performance`.

### Hookify (v1.5.1)
Behavioral rules engine with markdown-based configuration. Commands convert Python hooks to declarative rules (`from-hook`), manage rule catalogs (`install`, `list`), and configure rule activation (`configure`).

### Imbue (v1.5.1)
Structured review workflows. Offers commands for catchups and structured reviews (`catchup`, `structured-review`). Skills include `proof-of-work`, `scope-guard`, and `rigorous-reasoning`.

### Leyline (v1.5.1)
Shared patterns and utilities library. Allows for bulk plugin updates via `reinstall-all-plugins`. Skills cover authentication, error handling (including agent crash recovery via `error-patterns`), testing standards, cross-platform git forge detection via `git-platform`, and 4-tier risk routing via `risk-classification`.

### Memory-Palace (v1.5.1)
Knowledge management organization. Commands like `garden` and `palace` help users navigate and structure information. Skills focus on knowledge intake and retrieval.

### Minister (v1.5.1)
GitHub issue management and initiative tracking. Commands include `create-issue`, `close-issue`, and `update-labels`. Skills provide release health gates and initiative pulse dashboards.

### Parseltongue (v1.5.1)
Python development utilities. Includes tools for analyzing tests and profiling performance (`analyze-tests`, `run-profiler`). Skills support async programming and packaging.

### Pensive (v1.5.1)
Code review and analysis framework. Provides specific review commands for various languages and domains, such as `api-review`, `rust-review`, and `bug-review`. Includes `safety-critical-patterns` for NASA Power of 10 rules adapted for robust code.

### Sanctum (v1.5.1)
Git workflow automation. Handles tasks from commit message generation to PR reviews with mandatory code quality analysis. Commands include `fix-pr`, `merge-docs`, and `update-dependencies`.

### Scribe (v1.5.1)
Documentation quality enforcement. Commands include `slop-scan` (AI content detection), `doc-polish` (interactive editing), and `doc-verify` (accuracy validation). Skills detect AI-generated content markers (`slop-detector`), learn writing styles (`style-learner`), and generate human-quality documentation (`doc-generator`).

### Scry (v1.5.1)
Terminal and browser session recording. Supports creating media assets with commands like `record-browser` and `record-terminal`.

### Spec-Kit (v1.5.1)
Specification-driven development. Offers a suite of commands for planning, specifying, and implementing features based on strict requirements.

## API Quality Assessment

We enforce documentation and type safety using `ruff`, `mypy`, and `bandit`. All plugins adhere to a standard directory structure to ensure discovery. Our current focus is on normalizing command naming across plugins and clarifying export patterns for cross-plugin dependencies.

## Related Documents

- [Plugin Development Guide](plugin-development-guide.md)
- [Skill Integration Guide](skill-integration-guide.md)
