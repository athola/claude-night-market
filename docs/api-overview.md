# API Overview

*Updated: 2026-01-23*
*Original Source: API_REVIEW_REPORT.md (API Surface Inventory)*

## API Surface Summary

Claude Night Market consists of 16 plugins that provide CLI commands, Python packages, and skill-based APIs. These tools support a range of workflows, from code review to knowledge management.

## API Inventory

The ecosystem includes 109 CLI commands, 122 modular skills, 40 specialized agents, and 7 Python packages with public APIs. We also maintain 16 execution hooks.

| Plugin | Version | Commands | Skills | Agents | Python Package | CLI Entry |
|--------|---------|----------|--------|--------|----------------|-----------|
| abstract | 1.3.5 | 18 | 13 | 5 | Yes | abstract-skills |
| archetypes | 1.3.5 | 0 | 14 | 0 | No | - |
| attune | 1.3.5 | 8 | 10 | 2 | No | - |
| conjure | 1.3.5 | 0 | 3 | 0 | No | - |
| conserve | 1.3.5 | 5 | 10 | 5 | No | - |
| hookify | 1.3.5 | 5 | 2 | 0 | No | - |
| imbue | 1.3.5 | 3 | 11 | 1 | No | - |
| leyline | 1.3.5 | 2 | 12 | 0 | Yes | - |
| memory-palace | 1.3.5 | 5 | 7 | 4 | Yes | - |
| minister | 1.3.5 | 3 | 2 | 0 | Yes | - |
| parseltongue | 1.3.5 | 3 | 4 | 4 | No | - |
| pensive | 1.3.5 | 11 | 11 | 3 | Yes | - |
| sanctum | 1.3.5 | 20 | 15 | 9 | Yes | - |
| scribe | 1.3.5 | 5 | 4 | 3 | No | - |
| scry | 1.3.5 | 2 | 4 | 1 | No | - |
| spec-kit | 1.3.5 | 9 | 4 | 3 | Yes | - |

## Plugin Details

### Abstract (v1.3.5)
Validation and analysis framework for the ecosystem. Includes commands for creating and validating skills, hooks, and plugins (`validate-plugin`, `create-skill`). Skills focus on governance, authoring, and evaluation, including `skills-eval` and `performance-optimization`.

### Archetypes (v1.3.5)
Reference library for architecture paradigms. Contains 14 skills covering patterns like hexagonal architecture, microservices, and event-driven design.

### Attune (v1.3.5)
Project initialization and architecture templates. Streamlines the setup of new projects with `arch-init` and `init`.

### Conjure (v1.3.5)
Cross-model delegation. Skills like `gemini-delegation` and `qwen-delegation` route tasks to specific models based on capability.

### Conserve (v1.3.5)
Context window usage and resource management. Commands like `analyze-growth` and `optimize-context` help developers understand token consumption. Skills include `context-optimization`, `clear-context`, and `resource-management`.

### Hookify (v1.3.5)
Hook development utilities and templates. Commands help create, test, and manage execution hooks across the ecosystem.

### Imbue (v1.3.5)
Structured review workflows. Offers commands for feature reviews and catchups (`feature-review`, `catchup`). Skills include `evidence-logging`, `proof-of-work`, and `scope-guard`.

### Leyline (v1.3.5)
Shared patterns and utilities library. Allows for bulk plugin updates via `reinstall-all-plugins`. Skills cover authentication, error handling, and testing standards.

### Memory-Palace (v1.3.5)
Knowledge management organization. Commands like `garden` and `palace` help users navigate and structure information. Skills focus on knowledge intake and retrieval.

### Minister (v1.3.5)
Governance and project initiative tracking. Uses skills like `governance-tracking` and `tracker-comment` to maintain project oversight.

### Parseltongue (v1.3.5)
Python development utilities. Includes tools for analyzing tests and profiling performance (`analyze-tests`, `run-profiler`). Skills support async programming and packaging.

### Pensive (v1.3.5)
Code review and analysis framework. Provides specific review commands for various languages and domains, such as `api-review`, `rust-review`, and `bug-review`.

### Sanctum (v1.3.5)
Git workflow automation. Handles tasks from commit message generation to PR reviews. Commands include `fix-pr`, `merge-docs`, and `update-dependencies`.

### Scribe (v1.3.5)
Documentation generation and content authoring utilities. Commands help create and maintain documentation across plugins.

### Scry (v1.3.5)
Terminal and browser session recording. Supports creating media assets with commands like `record-browser` and `record-terminal`.

### Spec-Kit (v1.3.5)
Specification-driven development. Offers a suite of commands for planning, specifying, and implementing features based on strict requirements.

## API Quality Assessment

We enforce documentation and type safety using `ruff`, `mypy`, and `bandit`. All plugins adhere to a standard directory structure to ensure discovery. Our current focus is on normalizing command naming across plugins and clarifying export patterns for cross-plugin dependencies.

## Related Documents

- [API Updates](api-updates.md) - Changelog and documentation progress
- [API Consistency Plan](plans/2025-12-06-api-consistency.md)
- [Medium-Term Initiatives](plans/2025-12-06-medium-term-initiatives.md)
