# API Overview

*Consolidated: 2025-12-07*
*Original Source: API_REVIEW_REPORT.md (API Surface Inventory)*

## Plugin API Surface Summary

The Claude Night Market ecosystem contains 11 plugins with diverse API surfaces including CLI commands, Python packages, and skill-based APIs.

## API Inventory

| Plugin | Version | Commands | Skills | Agents | Python Package | CLI Entry |
|--------|---------|----------|--------|--------|----------------|-----------|
| abstract | 2.1.0 | 10 | 6 | 3 | Yes | abstract-skills |
| archetypes | 1.0.0 | 0 | 15 | 0 | No | - |
| conjure | 1.1.0 | 0 | 3 | 0 | Yes | - |
| conservation | 2.0.0 | 2 | 4 | 1 | Yes | - |
| imbue | 2.0.0 | 2 | 5 | 1 | Yes | - |
| leyline | 1.0.0 | 0 | 8 | 0 | Yes | - |
| memory-palace | 2.0.0 | 4 | 5 | 4 | Yes | - |
| parseltongue | 2.0.0 | 4 | 4 | 3 | Yes | - |
| pensive | 3.0.0 | 8 | 8 | 3 | Yes | - |
| sanctum | 3.0.0 | 7 | 8 | 3 | Yes | - |
| spec-kit | 3.0.0 | 9 | 3 | 3 | Yes | - |

## API Types

| Type | Count | Description |
|------|-------|-------------|
| CLI Commands | 46 | Slash commands across plugins |
| Skills | 69 | Skill definitions with modular loading |
| Agents | 24 | Specialized agents |
| Python Packages | 9 | Packages with public APIs |
| Hooks | 15 | Pre/post execution hooks |

## Plugin Details

### Abstract (v2.1.0)
Plugin validation and analysis framework.

**Commands**: `analyze-skill`, `analyze-hook`, `validate-plugin`, `create-skill`, `create-hook`, `create-command`, `estimate-tokens`, `context-report`, `hooks-eval`, `skills-eval`

**Skills**: `skill-authoring`, `skills-eval`, `modular-skills`, `hook-authoring`, `hooks-eval`, `shared-patterns`

### Archetypes (v1.0.0)
Architecture paradigm reference library.

**Skills**: 15 architecture paradigm skills (hexagonal, microservices, event-driven, etc.)

### Conjure (v1.1.0)
Cross-model delegation framework.

**Skills**: `delegation-core`, `gemini-delegation`, `qwen-delegation`

### Conservation (v2.0.0)
Context window and resource management.

**Commands**: `optimize-context`, `analyze-growth`

**Skills**: `context-optimization`, `mcp-code-execution`, `optimizing-large-skills`, `performance-monitoring`

### Imbue (v2.0.0)
Structured review workflows.

**Commands**: `catchup`, `full-review`

**Skills**: `catchup`, `diff-analysis`, `evidence-logging`, `review-core`, `structured-output`

### Leyline (v1.0.0)
Shared patterns and utilities library.

**Skills**: `authentication-patterns`, `error-patterns`, `evaluation-framework`, `mecw-patterns`, `progressive-loading`, `pytest-config`, `quota-management`, `service-registry`

### Memory Palace (v2.0.0)
Knowledge management and organization.

**Commands**: `palace`, `garden`, `navigate`, (4 total)

**Skills**: `digital-garden-cultivator`, `knowledge-intake`, `knowledge-locator`, `memory-palace-architect`, `session-palace-builder`

### Parseltongue (v2.0.0)
Python development utilities.

**Commands**: `analyze-tests`, `check-async`, `run-profiler`, (4 total)

**Skills**: `python-async`, `python-packaging`, `python-performance`, `python-testing`

### Pensive (v3.0.0)
Code review and analysis framework.

**Commands**: `review`, `api-review`, `architecture-review`, `bug-review`, `makefile-review`, `math-review`, `rust-review`, `test-review`

**Skills**: `api-review`, `architecture-review`, `bug-review`, `makefile-review`, `math-review`, `rust-review`, `test-review`, `unified-review`

### Sanctum (v3.0.0)
Git workflow automation.

**Commands**: `catchup`, `commit-msg`, `pr`, `update-docs`, `update-readme`, `update-tests`, `update-version`

**Skills**: `commit-messages`, `doc-updates`, `file-analysis`, `git-workspace-review`, `pr-prep`, `test-updates`, `update-readme`, `version-updates`

### Spec-Kit (v3.0.0)
Specification-driven development.

**Commands**: `speckit.analyze`, `speckit.checklist`, `speckit.clarify`, `speckit.constitution`, `speckit.implement`, `speckit.plan`, `speckit.specify`, `speckit.startup`, `speckit.tasks`

**Skills**: `spec-analyzer`, `task-generator`, `implementation-executor`

## API Quality Assessment

### Strengths
- Universal documentation coverage (100% README, docstrings)
- Standardized plugin structure
- Consistent quality tooling (ruff, mypy, bandit)

### Areas for Improvement
- Versioning consistency
- Command naming patterns (kebab-case vs dot-notation)
- API export patterns
- Cross-plugin integration documentation

## Related Documents

- [API Consistency Plan](plans/2025-12-06-api-consistency.md)
- [Medium-Term Initiatives](plans/2025-12-06-medium-term-initiatives.md)
