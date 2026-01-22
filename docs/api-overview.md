# API Overview

*Updated: 2026-01-14*
*Original Source: API_REVIEW_REPORT.md (API Surface Inventory)*

## API Surface Summary

Claude Night Market consists of 14 plugins that provide CLI commands, Python packages, and skill-based APIs. These tools support a range of workflows, from code review to knowledge management.

## API Inventory

The ecosystem includes 75 CLI commands, 104 modular skills, 32 specialized agents, and 13 Python packages with public APIs. We also maintain over 15 execution hooks.

| Plugin | Version | Commands | Skills | Agents | Python Package | CLI Entry |
|--------|---------|----------|--------|--------|----------------|-----------|
| abstract | 1.2.7 | 14 | 9 | 3 | Yes | abstract-skills |
| archetypes | 1.2.6 | 0 | 14 | 0 | No | - |
| conjure | 1.2.6 | 0 | 3 | 0 | Yes | - |
| conserve | 1.2.6 | 2 | 5 | 1 | Yes | - |
| imbue | 1.2.7 | 4 | 10 | 1 | Yes | - |
| leyline | 1.2.6 | 2 | 12 | 0 | Yes | - |
| memory-palace | 1.2.6 | 3 | 5 | 4 | Yes | - |
| minister | 1.2.6 | 0 | 2 | 0 | Yes | - |
| parseltongue | 1.2.6 | 3 | 4 | 3 | Yes | - |
| pensive | 1.2.7 | 9 | 11 | 3 | Yes | - |
| sanctum | 1.2.7 | 17 | 14 | 9 | Yes | - |
| scry | 1.2.6 | 2 | 4 | 0 | No | - |
| spec-kit | 1.2.6 | 9 | 4 | 3 | Yes | - |
| attune | 1.2.6 | 2 | 4 | 0 | Yes | - |

## Plugin Details

### Abstract (v1.2.7)
Provides the validation and analysis framework for the ecosystem. It includes commands for creating and validating skills, hooks, and plugins, such as `validate-plugin` and `create-skill`. Its skills focus on governance, authoring, and evaluation, including `skills-eval` and `performance-optimization`.

### Archetypes (v1.2.6)
Functions as a reference library for architecture paradigms. It contains 14 skills covering patterns like hexagonal architecture, microservices, and event-driven design.

### Conjure (v1.2.6)
Handles cross-model delegation. Its skills, such as `gemini-delegation` and `qwen-delegation`, enable tasks to be routed to specific models based on capability.

### Conserve (v1.2.6)
Manages context window usage and resources. Commands like `analyze-growth` and `optimize-context` help developers understand token consumption. Skills include `context-optimization` and `resource-management`.

### Imbue (v1.2.7)
Supports structured review workflows. It offers commands for feature reviews and catchups (`feature-review`, `catchup`). Skills include `evidence-logging`, `proof-of-work`, and `scope-guard`.

### Leyline (v1.2.6)
A library of shared patterns and utilities. It allows for bulk plugin updates via `reinstall-all-plugins`. Skills cover authentication, error handling, and testing standards.

### Memory-Palace (v1.2.6)
Organizes knowledge management. Commands like `garden` and `palace` help users navigate and structure information. Skills focus on knowledge intake and retrieval.

### Minister (v1.2.6)
Tracks governance and project initiatives. It uses skills like `governance-tracking` and `tracker-comment` to maintain project oversight.

### Parseltongue (v1.2.6)
Utilities for Python development. It includes tools for analyzing tests and profiling performance (`analyze-tests`, `run-profiler`). Skills support async programming and packaging.

### Pensive (v1.2.7)
A framework for code review and analysis. It provides specific review commands for various languages and domains, such as `api-review`, `rust-review`, and `bug-review`.

### Sanctum (v1.2.7)
Automates Git workflows. This plugin handles tasks from commit message generation to PR reviews. Commands include `fix-pr`, `merge-docs`, and `update-dependencies`.

### Scry (v1.2.6)
Utilities for recording terminal and browser sessions. It supports creating media assets with commands like `record-browser` and `record-terminal`.

### Spec-Kit (v1.2.6)
Facilitates specification-driven development. It offers a suite of commands for planning, specifying, and implementing features based on strict requirements.

### Attune (v1.2.6)
Templates for project initialization and architecture. It streamlines the setup of new projects with `arch-init` and `init`.

## API Quality Assessment

We enforce documentation and type safety using `ruff`, `mypy`, and `bandit`. All plugins adhere to a standard directory structure to ensure discovery. Our current focus is on normalizing command naming across plugins and clarifying export patterns for cross-plugin dependencies.

## Related Documents

- [API Updates](api-updates.md) - Changelog and documentation progress
- [API Consistency Plan](plans/2025-12-06-api-consistency.md)
- [Medium-Term Initiatives](plans/2025-12-06-medium-term-initiatives.md)
