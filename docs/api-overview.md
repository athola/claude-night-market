# API Overview

*Updated: 2025-12-26*
*Original Source: API_REVIEW_REPORT.md (API Surface Inventory)*

## API Surface Summary

The Claude Night Market ecosystem consists of 14 plugins providing CLI commands, Python packages, and skill-based APIs. These interfaces support workflows ranging from code review and git automation to knowledge management.

## API Inventory

| Plugin | Version | Commands | Skills | Agents | Python Package | CLI Entry |
|--------|---------|----------|--------|--------|----------------|-----------|
| abstract | 1.2.1 | 14 | 9 | 3 | Yes | abstract-skills |
| archetypes | 1.2.1 | 0 | 14 | 0 | No | - |
| conjure | 1.2.1 | 0 | 3 | 0 | Yes | - |
| conserve | 1.2.1 | 2 | 5 | 1 | Yes | - |
| imbue | 1.2.1 | 4 | 8 | 1 | Yes | - |
| leyline | 1.2.1 | 2 | 12 | 0 | Yes | - |
| memory-palace | 1.2.1 | 3 | 5 | 4 | Yes | - |
| minister | 1.2.1 | 0 | 2 | 0 | Yes | - |
| parseltongue | 1.2.1 | 3 | 4 | 3 | Yes | - |
| pensive | 1.2.1 | 8 | 9 | 3 | Yes | - |
| sanctum | 1.2.1 | 15 | 14 | 9 | Yes | - |
| scry | 1.2.1 | 2 | 4 | 0 | No | - |
| spec-kit | 1.2.1 | 9 | 4 | 3 | Yes | - |
| attune | 1.2.1 | 2 | 4 | 0 | Yes | - |

## API Types

| Type | Count | Description |
|------|-------|-------------|
| CLI Commands | 75 | Slash commands across plugins |
| Skills | 104 | Skill definitions with modular loading |
| Agents | 32 | Specialized agents |
| Python Packages | 13 | Packages with public APIs |
| Hooks | 15+ | Pre/post execution hooks |

## Plugin Details

### Abstract (v1.2.1)
Validation and analysis framework.

**Commands**: `analyze-hook`, `analyze-skill`, `bulletproof-skill`, `context-report`, `create-command`, `create-hook`, `create-skill`, `estimate-tokens`, `hooks-eval`, `make-dogfood`, `skills-eval`, `test-skill`, `validate-hook`, `validate-plugin`

**Skills**: `escalation-governance`, `hook-authoring`, `hooks-eval`, `makefile-dogfooder`, `modular-skills`, `performance-optimization`, `shared-patterns`, `skill-authoring`, `skills-eval`

### Archetypes (v1.2.1)
Architecture paradigm reference library.

**Skills**: 14 architecture paradigm skills (hexagonal, microservices, event-driven, etc.)

### Conjure (v1.2.1)
Cross-model delegation framework.

**Skills**: `delegation-core`, `gemini-delegation`, `qwen-delegation`

### Conserve (v1.2.1)
Context window and resource management.

**Commands**: `analyze-growth`, `optimize-context`

**Skills**: `context-optimization`, `mcp-code-execution`, `optimizing-large-skills`, `performance-monitoring`, `resource-management`

### Imbue (v1.2.1)
Structured review workflows.

**Commands**: `catchup`, `feature-review`, `review`, `structured-review`

**Skills**: `catchup`, `diff-analysis`, `evidence-logging`, `feature-review`, `review-core`, `scope-guard`, `shared`, `structured-output`

### Leyline (v1.2.1)
Shared patterns and utilities library.

**Commands**: `reinstall-all-plugins`, `update-all-plugins`

**Skills**: `authentication-patterns`, `error-patterns`, `evaluation-framework`, `mecw-patterns`, `progressive-loading`, `pytest-config`, `quota-management`, `service-registry`, `shared`, `storage-templates`, `testing-quality-standards`, `usage-logging`

### Memory-Palace (v1.2.1)
Knowledge management and organization.

**Commands**: `garden`, `navigate`, `palace`

**Skills**: `digital-garden-cultivator`, `knowledge-intake`, `knowledge-locator`, `memory-palace-architect`, `session-palace-builder`

### Minister (v1.2.1)
Governance and tracking plugin.

**Skills**: `governance-tracking`, `tracker-comment`

### Parseltongue (v1.2.1)
Python development utilities.

**Commands**: `analyze-tests`, `check-async`, `run-profiler`

**Skills**: `python-async`, `python-packaging`, `python-performance`, `python-testing`

### Pensive (v1.2.1)
Code review and analysis framework.

**Commands**: `api-review`, `architecture-review`, `bug-review`, `full-review`, `makefile-review`, `math-review`, `rust-review`, `test-review`

**Skills**: `api-review`, `architecture-review`, `bug-review`, `makefile-review`, `math-review`, `rust-review`, `shared`, `test-review`, `unified-review`

### Sanctum (v1.2.1)
Git workflow automation.

**Commands**: `commit-msg`, `fix-issue`, `fix-pr`, `fix-workflow`, `git-catchup`, `merge-docs`, `pr`, `pr-review`, `resolve-threads`, `update-dependencies`, `update-docs`, `update-readme`, `update-tests`, `update-tutorial`, `update-version`

**Skills**: `commit-messages`, `doc-consolidation`, `doc-updates`, `file-analysis`, `fix-issue`, `git-workspace-review`, `pr-prep`, `pr-review`, `shared`, `test-updates`, `tutorial-updates`, `update-readme`, `version-updates`, `workflow-improvement`

### Scry (v1.2.1)
Terminal and browser recording utilities.

**Commands**: `record-browser`, `record-terminal`

**Skills**: `browser-recording`, `gif-generation`, `media-composition`, `vhs-recording`

### Spec-Kit (v1.2.1)
Specification-driven development.

**Commands**: `speckit-analyze`, `speckit-checklist`, `speckit-clarify`, `speckit-constitution`, `speckit-implement`, `speckit-plan`, `speckit-specify`, `speckit-startup`, `speckit-tasks`

**Skills**: `shared`, `spec-writing`, `speckit-orchestrator`, `task-planning`

### Attune (v1.2.1)
Project initialization and architecture templates.

**Commands**: `arch-init`, `init`

**Skills**: `architecture-templates`, `project-initialization`, `research-integration`

## API Quality Assessment

We observe 100% README and docstring coverage across the ecosystem, supported by consistent quality tooling like `ruff`, `mypy`, and `bandit`. The plugin structure is standardized. However, opportunities for improvement exist in versioning consistency (currently aligned at 1.2.1), command naming patterns (mixing kebab-case and dot-notation), API export patterns, and the documentation for cross-plugin integration.

## Related Documents

- [API Updates](api-updates.md) - Changelog and documentation progress
- [API Consistency Plan](plans/2025-12-06-api-consistency.md)
- [Medium-Term Initiatives](plans/2025-12-06-medium-term-initiatives.md)
