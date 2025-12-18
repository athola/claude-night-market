# Changelog

All notable changes to the Claude Night Market plugin ecosystem are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2025-12-18

### Added

- **Conservation hooks**: Session-start integration that automatically loads optimization guidance
- **Conservation bypass modes**: `CONSERVATION_MODE` environment variable (quick/normal/deep)
- **Sanctum fix-issue command**: New workflow for addressing GitHub issues
- **Sanctum session notifications**: `session_complete_notify.py` hook for session completion alerts
- **Minister plugin**: Officially added to marketplace (project management with GitHub integration)

### Changed

- **Documentation overhaul**: Expanded `docs/capabilities-reference.md` with complete skill, command, agent, and hook listings for all plugins
- **Conservation README**: Added session start integration docs, bypass modes table, and threshold guidelines
- **Plugin versions**: All plugins bumped to 1.0.1 or 1.0.2 for consistency
- **Skill modules**: Refined content across abstract, conservation, imbue, leyline, pensive, sanctum, and spec-kit

### Improved

- **Context optimization**: Comprehensive updates to MECW patterns and monitoring across conservation and leyline
- **Skill authoring docs**: Enhanced persuasion principles, TDD methodology, and anti-rationalization modules
- **Hook authoring**: Updated security patterns and performance guidelines

## [1.0.1] - 2025-12-18

### Fixed

- **Security scanning**: Exclude `.venv` and non-code directories from Bandit and other security scans
- **Hook portability**: Improved cross-platform hook execution

### Changed

- **Scope-guard modularization**: Broke down scope-guard into smaller, focused modules
- **Workflow-improvement**: Added workflow-improvement capability to sanctum
- **Plugin versions**: Updated versions across all plugins

### Technical

- Merged from PR #24

## [1.0.0] - 2025-12-15

### Added

- **Initial release** of the Claude Night Market plugin ecosystem
- **11 plugins**: abstract, archetypes, conjure, conservation, imbue, leyline, memory-palace, parseltongue, pensive, sanctum, spec-kit
- **Core infrastructure**: Skills, commands, agents, and hooks framework
- **Documentation**: README, capabilities reference, and per-plugin documentation

### Plugins Overview

| Plugin | Purpose |
|--------|---------|
| abstract | Meta-skills infrastructure for plugin development |
| archetypes | Architecture paradigm selection (14 paradigms) |
| conjure | Intelligent delegation to external LLMs |
| conservation | Resource optimization and context management |
| imbue | Workflow methodologies and review scaffolding |
| leyline | Storage patterns and data persistence |
| memory-palace | Spatial memory techniques (method of loci) |
| parseltongue | Language detection and multi-language support |
| pensive | Code review toolkit (7 specialized skills) |
| sanctum | Git operations and workspace management |
| spec-kit | Specification-driven development |

### Technical

- Merged from PR #8
- Commit: bd7d2ce

[1.0.2]: https://github.com/athola/claude-night-market/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/athola/claude-night-market/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/athola/claude-night-market/releases/tag/v1.0.0
