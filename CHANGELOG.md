# Changelog

All notable changes to the Claude Night Market plugin ecosystem are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-01-02

### Added

- **Conserve: Static Analysis Integration** - Complete bloat-detector skill with 5 modules
  - **New Module**: `static-analysis-integration.md` - Bridges Tier 1 heuristics to Tier 2 tool-based detection
    - **Python Tools**: Vulture (programmatic API), deadcode (auto-fix), autoflake (import cleanup)
    - **JavaScript/TypeScript**: Knip CLI integration with JSON parsing, tree-shaking detection
    - **Multi-Language**: SonarQube Web API for cyclomatic complexity and duplication metrics
    - **Features**: Auto-detection of available tools, graceful fallback to heuristics, confidence boosting
  - **Total Bloat Detection Coverage**: 2,423 lines across 5 modules
    - `quick-scan.md` (237 lines) - Heuristic detection
    - `git-history-analysis.md` (276 lines) - Staleness and churn metrics
    - `code-bloat-patterns.md` (638 lines) - 5 duplication types, language-specific patterns
    - `documentation-bloat.md` (634 lines) - Readability metrics, 4 similarity algorithms
    - `static-analysis-integration.md` (638 lines) - Tool integration **← NEW**
  - **Validation**: All tests pass, hub-spoke pattern maintained, proper frontmatter

- **Memory Palace: Knowledge Corpus Integration** - Research queue processing and storage
  - **Queue System**: Staging area for research sessions with evaluation rubric
  - **Knowledge Entry**: `codebase-bloat-detection.md` - Comprehensive bloat detection research
    - 43 sources across static analysis, git history, documentation metrics
    - Memory palace format with spatial encoding and cross-references
    - Score: 87/100 (Evergreen threshold: 80+)
  - **Queue Processing**: Automated vetting, approval, and archival workflow
  - **Integration**: Research findings directly applied to conserve plugin implementation

- **Attune Plugin (v1.2.0)** - Full-cycle project development from ideation to implementation
  - **New Commands**:
    - `/attune:brainstorm` - Brainstorm project ideas using Socratic questioning (integrates superpowers)
    - `/attune:specify` - Create detailed specifications from brainstorm session (integrates spec-kit)
    - `/attune:plan` - Plan architecture and break down into tasks (integrates superpowers)
    - `/attune:init` - Initialize new project with complete development infrastructure
    - `/attune:execute` - Execute implementation tasks systematically (integrates superpowers)
    - `/attune:upgrade` - Add or update configurations in existing projects
    - `/attune:validate` - Validate project structure against best practices
  - **New Agents**:
    - `project-architect` - Guides full-cycle workflow from brainstorming through planning
    - `project-implementer` - Executes implementation with TDD discipline and progress tracking
  - **New Skills**:
    - `project-brainstorming` - Socratic ideation and problem space exploration
    - `project-specification` - Specification creation workflow
    - `project-planning` - Architecture design and task breakdown
    - `project-execution` - Systematic implementation with tracking
    - `project-init` - Interactive project initialization workflow with language detection
    - `makefile-generation` - Generate language-specific Makefiles with standard targets
    - `workflow-setup` - Configure GitHub Actions workflows for CI/CD
    - `precommit-setup` - Set up pre-commit hooks for code quality enforcement
  - **Supported Languages**:
    - **Python**: uv-based dependency management, pytest, ruff, mypy, pre-commit hooks
    - **Rust**: cargo builds, clippy, rustfmt, CI workflows
    - **TypeScript/React**: npm/pnpm/yarn, vite, jest, eslint, prettier
  - **Features**:
    - Hybrid template + dynamic generation approach
    - Non-destructive initialization (prompts before overwriting)
    - Git initialization with comprehensive .gitignore
    - GitHub Actions workflows (test, lint, typecheck/build)
    - Pre-commit hooks configuration
    - Makefile with development targets (help, test, lint, format, build, clean)
    - Project structure creation (src/, tests/, README.md)
    - Version fetching for GitHub Actions and dependencies
    - Project validation with detailed scoring
  - **Phase 1 (Complete)**: Python-only MVP
  - **Phase 2 (Complete)**: Multi-language support (Rust, TypeScript)
  - **Phase 3 (Complete)**: Advanced features (version fetching, validation)
  - **Phase 4 (Complete)**: Integration features
    - `/attune:upgrade` - Add missing configs to existing projects with status reporting
    - Custom template locations (~/.claude/attune/templates/, .attune/templates/, $ATTUNE_TEMPLATES_PATH)
    - Plugin project initialization (attune + abstract integration)
    - Reference project template synchronization (auto-update from simple-resume, skrills)
    - Template composition and override system
  - **Templates Based On**: Reference projects (simple-resume, skrills, importobot)

## [1.1.2] - 2026-01-01

### Added

- **Conserve: Bloat Detection & Remediation** - Full codebase cleanup workflow
- **Codebase-wide AI Slop Cleanup** - Systematic removal of AI-generated language patterns
  - Removed ~628 instances of vague AI slop words across 356 files
  - Replaced "comprehensive" with context-specific terms (detailed/deep/thorough/full)
  - Replaced "ensures/ensure" with precise verbs (validates/verify/maintains)
  - Replaced "robust" with "production-grade" or "solid"
  - Replaced marketing language (powerful/seamless/leverage/utilize) with plain terms
  - Affected all file types: Markdown (487 instances), Python (91), Shell/YAML/Makefiles (50)
  - No functional changes, purely stylistic improvements for clarity
  - **New Commands**:
    - `/bloat-scan` - Progressive bloat detection (3 tiers: quick scan, targeted analysis, deep audit)
    - `/unbloat` - Safe bloat remediation with interactive approval and automatic backups
  - **New Agents**:
    - `bloat-auditor` - Orchestrates bloat detection scans and generates prioritized reports
    - `unbloat-remediator` - Executes safe deletions, refactorings, and consolidations with rollback support
  - **New Skill**:
    - `bloat-detector` - Detection algorithms for dead code, God classes, documentation duplication, and dependency bloat
  - **Detection Capabilities**:
    - Tier 1 (2-5 min): Heuristic-based detection using git history (no external tools required)
    - Tier 2 (10-20 min): Static analysis integration (Vulture, Knip) with anti-pattern detection
    - Tier 3 (30-60 min): Deep audit with cyclomatic complexity and cross-file redundancy
  - **Safety Features**:
    - Automatic backup branches before any changes
    - Interactive approval workflow with dry-run mode
    - Test verification after each change with auto-rollback on failure
    - Reversible git operations (git rm/git mv)
  - **Benefits**: 10-20% context reduction on average, identifies technical debt hotspots

## [1.1.1] - 2025-12-30

### Added

- **Project-level agent configuration**: Added `.claude/agents/` with main-thread agent definitions
  - `plugin-developer.md` - Default agent for night-market plugin development (set in `.claude/settings.json`)
  - `code-review-mode.md` - Evidence-based code review sessions with imbue/pensive integration
  - `documentation-mode.md` - Documentation-focused workflows with sanctum integration
  - Enables consistent multi-session agent configuration across all project work
  - Automatic agent loading when starting sessions in project directory

- **LSP setup guidance in main README**: Quick start guide for Language Server Protocol integration
  - Added "Recommended Setup: LSP Integration" section prominently in README
  - Step-by-step setup instructions (enable environment variable, install language servers, verify)
  - Comparison table showing LSP advantages (900x performance, 90% token reduction)
  - List of plugins benefiting from LSP (pensive, sanctum, conserve)
  - Graceful degradation explanation (grep fallback when LSP unavailable)
  - Reference to detailed compatibility documentation

- **Claude Code compatibility reference**: New documentation tracking version-specific features and fixes
  - `plugins/abstract/docs/claude-code-compatibility.md` - Detailed compatibility matrix
  - Version support matrix for ecosystem compatibility
  - Migration guides for Claude Code version upgrades
  - Testing checklist for compatibility verification

### Documentation

- **Claude Code 2.0.74 compatibility**: Updated documentation and agent capabilities for latest release
  - **LSP (Language Server Protocol) Tool**: **Now the preferred default** for code navigation and analysis
    - Added detailed LSP integration patterns section to compatibility documentation
    - Updated `plugins/pensive/agents/code-reviewer.md` with LSP-enhanced review capabilities
    - Updated `plugins/pensive/agents/architecture-reviewer.md` with semantic architecture analysis
    - Updated `plugins/pensive/agents/rust-auditor.md` with rust-analyzer integration
    - Updated `plugins/sanctum/commands/update-docs.md` with LSP documentation verification
    - Updated `plugins/sanctum/skills/doc-updates/SKILL.md` with LSP accuracy checking
    - Updated `plugins/conserve/skills/context-optimization/modules/mecw-principles.md` with LSP token optimization
    - Documented 900x performance improvement for reference finding (50ms vs 45s)
    - Language support: TypeScript, Rust, Python, Go, Java, Kotlin, C/C++, PHP, Ruby, C#, PowerShell, HTML/CSS
    - **Strategic Positioning**: LSP is now the **default/preferred** approach across all plugins
      - Pensive agents default to LSP for code review, architecture analysis, Rust audits
      - Sanctum commands default to LSP for documentation verification
      - Conserve skills recommend LSP for token optimization
      - Grep positioned as fallback when LSP unavailable
      - Recommendation: Enable `ENABLE_LSP_TOOLS=1` permanently in environment
  - **Security Fix - allowed-tools enforcement**: Documented critical security bug fix
    - Created "Tool Restriction Patterns" section in compatibility documentation
    - Documented previous bug: `allowed-tools` restrictions were NOT being enforced (< 2.0.74)
    - Documented fix: Tool restrictions now properly applied (2.0.74+)
    - Added security patterns for read-only analysis, safe execution, and untrusted input processing
    - Audit results: No current plugins use `allowed-tools` (verified via ecosystem scan)
    - Added best practices for tool restriction design
  - **Improved /context visualization**: Documented enhanced context monitoring
    - Updated `plugins/conserve/skills/context-optimization/modules/mecw-principles.md`
    - Skills/agents now grouped by source plugin
    - Better visibility into plugin-level context consumption
    - Sorted token counts for optimization
    - Improved MECW compliance monitoring
  - **Terminal setup improvements**: Documented extended terminal support
    - Added support for Kitty, Alacritty, Zed, Warp terminals
    - Enhanced cross-platform compatibility
  - **User Experience**: Documented UX improvements
    - ctrl+t shortcut in /theme to toggle syntax highlighting
    - Syntax highlighting info in theme picker
    - macOS keyboard shortcut improvements (opt vs alt display)
  - **Bug Fixes**: Documented resolved issues
    - Fixed visual bug in /plugins discover selection indicator
    - Fixed syntax highlighting crash
    - Fixed Opus 4.5 tip incorrectly showing

- **Claude Code 2.0.73 compatibility**: Updated documentation for latest Claude Code release
  - **Session Forking**: Documented `--session-id` + `--fork-session` workflow patterns (2.0.73+)
    - Added detailed session forking patterns section to compatibility documentation
    - Documented use cases for sanctum (git workflows), imbue (parallel analysis), pensive (code reviews), memory-palace (knowledge intake)
    - Added best practices, naming conventions, and lifecycle management guidance
    - Created advanced patterns: decision tree exploration, experiment-driven development, parallel testing
    - Integration guidance with subagent delegation patterns
  - **Plugin Discovery**: Enhanced metadata best practices for search filtering (2.0.73+)
    - Plugin discover screen now supports search by name, description, marketplace
    - Recommendations for search-friendly plugin descriptions
    - Guidelines for descriptive keywords in plugin.json metadata
  - **Image Viewing**: Documented clickable [Image #N] links for media workflows (2.0.73+)
    - Updated scry plugin compatibility (media generation preview)
    - Updated imbue plugin compatibility (visual evidence artifacts)
    - Quick preview support for attached and generated images
  - **User Experience**: Documented UX improvements
    - alt-y yank-pop for kill ring history cycling
    - Improved /theme command and theme picker UI
    - Unified SearchBox across resume, permissions, and plugins screens
  - **Performance**: Fixed slow input history cycling and message submission race condition
  - **VSCode Extension**: Tab icon badges for pending permissions (blue) and unread completions (orange)

- **Claude Code 2.0.72 compatibility**: Updated documentation for latest Claude Code release
  - **Claude in Chrome (Beta)**: Documented native browser control integration
    - Complements scry plugin's Playwright-based browser recording
    - Added compatibility guidance to `plugins/scry/README.md`
    - Updated `plugins/scry/skills/browser-recording/SKILL.md` with Chrome integration notes
    - Updated `plugins/scry/commands/record-browser.md` with usage recommendations
    - Positioning: Native Chrome for interactive debugging, Playwright for automation/CI/CD
  - **User experience improvements**: Thinking toggle changed from Tab to Alt+T
  - **Performance improvements**: 3x faster @ mention file suggestions in git repositories
  - **Bug fixes**: `/context` command now respects custom system prompts in non-interactive mode

- **Claude Code 2.0.71 compatibility**: Updated documentation for Claude Code release
  - **Bash glob pattern support**: Documented fix for shell glob patterns (`*.txt`, `*.png`) in permission system
    - Updated `plugins/abstract/skills/hook-authoring/modules/hook-types.md`
    - Updated `plugins/abstract/skills/hook-authoring/modules/security-patterns.md`
    - Added migration guidance for removing glob pattern workarounds
  - **MCP server loading fix**: Documented fix for `.mcp.json` loading with `--dangerously-skip-permissions`
    - Enables fully automated CI/CD workflows with MCP servers
    - Updated hook authoring documentation with CI/CD examples
  - **New commands**: Documented `/config toggle` and `/settings` alias for configuration management

### Compatibility

- **Verified**: Tested with Claude Code 2.0.74
- **Recommended**: Claude Code 2.0.74+ for LSP integration, tool restrictions, and improved /context visualization
- **Notable Features**:
  - 2.0.74+: LSP tool, allowed-tools security fix, improved /context grouping
  - 2.0.73+: Session forking, plugin discovery, image viewing
  - 2.0.72+: Claude in Chrome integration
  - 2.0.71+: Bash glob patterns, MCP loading fix
  - 2.0.70+: Wildcard permissions, improved context accuracy
- **Minimum**: Claude Code 2.0.65+ for full feature support

## [1.1.0] - 2025-12-27

### Changed

- **Version alignment**: All plugins and the root workspace now report version 1.1.0
- **Spec-kit command naming**: Standardized to `/speckit-*` for naming consistency

### Documentation

- **API references**: Updated spec-kit command names and version tables to match 1.1.0

## [1.0.4] - 2025-12-22

### Added

- **Abstract skill assurance framework**: Reliable skill discovery and validation infrastructure
- **Compliance tests**: Trigger isolation and enforcement level tests for skill assurance

### Changed

- **Sanctum fix-pr**: Out-of-scope issue creation now mandatory for PR workflows
- **Commands restructured**: Eliminated duplicate command names across plugins (fix-issue, reinstall-all-plugins)
- **Capabilities documentation**: Added feature-review and standardized hook types

### Fixed

- **Compliance**: Addressed PR #42 review feedback for skill assurance

## [1.0.3] - 2025-12-19

### Added

- **Imbue feature-review skill**: Evidence-based prioritization for feature requests and bug triage
- **Memory-palace PreToolUse hook**: Persist intake queue directly from hook for reliable queue management

### Changed

- **Sanctum fix-issue command**: Modularized for better token efficiency
- **Imbue tests**: Test updates across review analyst, catchup, and skill modules

### Fixed

- **Sanctum fix-pr**: Removed emojis from example outputs for cleaner formatting
- **Lock files**: Updated across imbue, memory-palace, pensive, and spec-kit plugins

## [1.0.2] - 2025-12-18

### Added

- **Conservation hooks**: Session-start integration that automatically loads optimization guidance
- **Conservation bypass modes**: `CONSERVATION_MODE` environment variable (quick/normal/deep)
- **Sanctum fix-issue command**: New workflow for addressing GitHub issues
- **Sanctum session notifications**: `session_complete_notify.py` hook for session completion alerts
- **Minister plugin**: Officially added to marketplace (project management with GitHub integration)

### Changed

- **Documentation overhaul**: Expanded `book/src/reference/capabilities-reference.md` with complete skill, command, agent, and hook listings for all plugins
- **Conserve README**: Added session start integration docs, bypass modes table, and threshold guidelines
- **Plugin versions**: All plugins bumped to 1.0.2 for consistency
- **Skill modules**: Refined content across abstract, conserve, imbue, leyline, pensive, sanctum, and spec-kit

### Improved

- **Context optimization**: Updates to MECW patterns and monitoring across conserve and leyline
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
- **11 plugins**: abstract, archetypes, conjure, conserve, imbue, leyline, memory-palace, parseltongue, pensive, sanctum, spec-kit
- **Core infrastructure**: Skills, commands, agents, and hooks framework
- **Documentation**: README, capabilities reference, and per-plugin documentation

### Plugins Overview

| Plugin | Purpose |
|--------|---------|
| abstract | Meta-skills infrastructure for plugin development |
| archetypes | Architecture paradigm selection (14 paradigms) |
| conjure | Intelligent delegation to external LLMs |
| conserve | Resource optimization and context management |
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

[1.2.0]: https://github.com/athola/claude-night-market/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/athola/claude-night-market/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/athola/claude-night-market/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/athola/claude-night-market/compare/v1.0.4...v1.1.0
[1.0.4]: https://github.com/athola/claude-night-market/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/athola/claude-night-market/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/athola/claude-night-market/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/athola/claude-night-market/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/athola/claude-night-market/releases/tag/v1.0.0
