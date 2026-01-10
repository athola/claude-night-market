# Changelog

All notable changes to the Claude Night Market plugin ecosystem are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Conjure: GeminiQuotaTracker Inheritance Refactoring** - Reduced code duplication through leyline.QuotaTracker base class
  - **Code Reduction**: 287 → 255 lines (-32 lines, -11.1% reduction)
  - **Inherited Methods**: 11 methods now inherited from `leyline.QuotaTracker` base class
    - `record_request()`, `get_quota_status()`, `can_handle_task()`, `get_current_usage()`
    - `_load_usage()`, `_save_usage()`, `_cleanup_old_data()`, `estimate_file_tokens()`
  - **Preserved Features**: Gemini-specific token estimation (tiktoken + heuristic fallback)
  - **Backward Compatibility**: 100% compatible with existing dict-based configuration
  - **Documentation**: Complete technical guide at `plugins/conjure/docs/quota-tracking.md`
  - **Testing**: All functionality verified (instantiation, quota checking, token estimation, file handling)
  - **Dependencies**: Added `leyline>=1.0.0` for base class inheritance
  - **See Also**: ADR-0002 for architecture decision rationale

- **Methodology Curator Skill** - Surface expert frameworks before creating OR evaluating skills/hooks/agents
  - **New Skill**: `methodology-curator` - Curates proven methodologies from domain masters
    - **Concept**: Based on skill-from-masters approach - ground work in battle-tested frameworks
    - **Creation Workflow**: Surfaces experts → select/blend methodologies → create methodology brief → handoff to create-skill
    - **Evaluation Workflow**: Identify domain → gap analysis vs masters → targeted improvements
    - **Pure Markdown**: No external dependencies, installs with plugin
  - **Domain Modules** (6 domains, 1500+ lines of curated expertise):
    - `instruction-design.md` - Mager (behavioral objectives), Bloom (taxonomy), Gagné (9 events), Sweller (cognitive load), Clark (evidence-based)
    - `code-review.md` - Google Engineering, Fowler (refactoring), Feathers (legacy code), Wiegers (peer reviews), Gee (practical review)
    - `debugging.md` - Zeller (scientific debugging), Agans (9 rules), Spinellis (effective debugging), Miller (debugging questions), Regehr (systems debugging)
    - `testing.md` - Kent Beck (TDD), Freeman/Pryce (GOOS), Meszaros (xUnit patterns), Feathers (legacy testing), Bach/Bolton (exploratory)
    - `knowledge-management.md` - Luhmann (Zettelkasten), Ahrens (smart notes), Bush (memex), Allen (GTD), Forte (PARA/Second Brain)
    - `decision-making.md` - Munger (mental models), Kahneman (System 1/2), Klein (RPD), Duke (thinking in bets), Dalio (principles)
  - **Integration**: Works with `/create-skill`, `/create-hook`, brainstorming workflows
  - **Extensible**: Template provided for adding new domain modules

- **Subagent Auto-Compaction Documentation** - Claude Code 2.1.1+ discovery
  - **New Section**: `conserve:context-optimization/modules/subagent-coordination` - Auto-compaction at ~160k tokens
  - **Model Optimization Guide**: Added context management section for long-running subagents
  - **Log Signature**: Documented `compact_boundary` system message format for debugging
  - **Design Patterns**: State preservation strategies for compaction-aware agent design
  - **Context Thresholds**: Documented warning zones (80%, 90%) and trigger point (~160k)

### Fixed

- **hooks.json validation error**: Fixed abstract plugin hooks.json matcher format - changed from object `{"toolName": "Skill"}` to string `"Skill"` per Claude Code SDK requirements
- **#25**: Optimized architecture-paradigms skill to index/router pattern (28.5% reduction)
- **#26**: Modularized optimizing-large-skills skill (38% reduction)
- **#27**: Split large command files with 72% average reduction (bulletproof-skill, validate-hook, pr-review)
- **#28**: Consolidated abstract module bloat to docs/examples/ directory
- **#29**: Optimized agent files with 62% reduction in mcp-subagents
- **#30**: Enhanced JSON escaping with complete control character handling in imbue hooks
- **#31**: Added logging to PyYAML warnings for better CI/CD visibility
- **#32**: Added comprehensive delegation error path tests (12 new test methods)
- **#33**: Added wrapper base validation tests and implemented detect_breaking_changes()
- **#93**: Merged README-HOOKS.md into docs/guides/skill-observability-guide.md
- **#94**: Consolidated conjure CHANGELOG to reference main CHANGELOG
- **#95**: Renamed /pr to /prepare-pr with expanded Mandatory Post-Implementation Protocol workflow

### Changed

- **MECW Optimization**: Commands now use modular architecture with progressive loading pattern
  - Large skill modules moved to docs/examples/ for comprehensive guides
  - Stub files provide quick reference with links to detailed documentation
  - Total reduction: 70-79% in command files, 28-62% in skill files
- **Documentation Structure**: Comprehensive guides now centralized in docs/examples/ with categorization:
  - `docs/examples/hook-development/` - Hook types, security patterns
  - `docs/examples/skill-development/` - Authoring best practices, evaluation methodology
- **Testing Coverage**: Added 12+ new test methods for error paths and validation edge cases

## [1.2.3] - 2026-01-08

### Added

- **Error Handling Documentation** - Comprehensive guide for error handling across the ecosystem
  - **New Guide**: `docs/guides/error-handling-guide.md` with implementation patterns
  - **Error Classification**: Standardized system (E001-E099: Critical, E010-E099: Recoverable, E020-E099: Warnings)
  - **Plugin-Specific Patterns**: Detailed scenarios for abstract, conserve, memory-palace, parseltongue, sanctum
  - **Integration**: Connected to leyline:error-patterns for shared infrastructure
  - **Best Practices**: Recovery strategies, testing patterns, monitoring and alerting

- **Conjure Quota Tracking Documentation** - Technical implementation details
  - **New Guide**: `plugins/conjure/docs/quota-tracking.md` for Gemini API quota management
  - **Architecture Details**: Inheritance structure from leyline.QuotaTracker
  - **Token Estimation**: Multi-tier strategy (tiktoken + heuristic fallback)
  - **Usage Patterns**: CLI interface, hook integration, backward compatibility
  - **Performance**: Computational complexity, memory usage, testing patterns

- **Documentation Consolidation** - Merged ephemeral reports into permanent docs
  - **Error Handling Enhancement Report**: Consolidated into `docs/guides/error-handling-guide.md`
  - **GeminiQuotaTracker Refactoring Report**: Consolidated into `plugins/conjure/docs/quota-tracking.md`
  - **ADR-0002**: Already exists for quota tracker refactoring architecture decision
  - **Removed**: Temporary report files from worktrees

- **Branch Name Version Validation** - `/pr-review` now enforces branch name version consistency
  - **BLOCKING check**: If branch contains version (e.g., `skills-improvements-1.2.2`), it MUST match marketplace/project version
  - **Prevents incomplete version bumps**: Catches cases where branch naming indicates 1.2.2 but files still show 1.2.1
  - **Clear error messages**: Suggests either updating version files OR renaming branch to match
  - Supports all project types: Claude marketplace, Python, Node, Rust

- **Claude Code 2.1.0 Compatibility** - Full support for new frontmatter features and behaviors
  - **Skill Hot-Reload**: Skills now auto-reload without session restart
  - **Context Forking**: `context: fork` runs skills in isolated sub-agent context
  - **Agent Field**: `agent: agent-name` specifies agent type for skill execution
  - **Frontmatter Hooks**: Define PreToolUse/PostToolUse/Stop hooks in skill/agent/command frontmatter
  - **Once Hooks**: `once: true` executes hook only once per session
  - **YAML-Style allowed-tools**: Cleaner list syntax instead of comma-separated strings
  - **Wildcard Permissions**: `Bash(npm *)`, `Bash(* install)`, `Bash(git * main)`
  - **Skill Visibility**: `user-invocable: false` hides skills from slash command menu
  - **Agent Disabling**: `Task(AgentName)` syntax for disabling specific agents

- **Documentation Updates** - Comprehensive 2.1.0 feature documentation
  - **Plugin Development Guide**: New section covering all 2.1.0 frontmatter fields
  - **Common Workflows Guide**: Added 2.1.0 features section with examples (moved to `book/src/getting-started/common-workflows.md`)
  - **Skill Authoring Skill**: Updated frontmatter examples with 2.1.0 fields
  - **Hook Authoring Skill**: Added frontmatter hooks, `once: true`, and event types
  - **Documentation Consolidation**: Moved large guides to book/ for better organization
    - Common Workflows (722 lines), Function Extraction Guidelines (571 lines), Migration Guide (507 lines)
    - Archived temporary research and implementation reports to `docs/archive/2026-01-*/`
    - All documentation now complies with size guidelines (docs/ ≤ 500 lines, book/ ≤ 1000 lines)

- **Skill Observability System** (Issue #69) - Phases 4-5: Continual learning metrics and PreToolUse integration
  - **PreToolUse Hook**: `skill_tracker_pre.py` captures skill start time and invocation context
  - **PostToolUse Enhancement**: `skill_tracker_post.py` now calculates accurate duration and continual metrics
  - **Continual Learning Metrics**: Avalanche-style evaluation per skill execution
    - **Stability Gap Detection**: Automatic identification of performance inconsistency (avg - worst accuracy)
    - **Per-iteration metrics**: worst_case_accuracy, average_accuracy, avg_duration_ms
    - **Execution History**: Persistent tracking in `~/.claude/skills/logs/.history.json`
    - **Real-time Alerts**: stderr warnings when stability_gap > 0.3
  - **Skill Memory Storage**: memory-palace now handles all skill execution memory
    - Automatic tracking of every skill invocation across all plugins
    - JSONL log storage per plugin/skill/day with searchable history
    - Command: `/skill-logs` - view and manage skill execution memories
  - **Skill Review**: pensive now handles skill performance analysis
    - Commands: `/skill-review` - analyze skill metrics and stability gaps
    - Commands: `/skill-history` - view recent skill executions with context
    - Integration reference: `docs/guides/skill-observability-guide.md`

- **Parseltongue: Python Linter Agent** - Strict linting enforcement without bypassing checks
  - **New Agent**: `python-linter` - Expert agent for fixing lint errors properly
    - **Core Principle**: FIX, DON'T IGNORE - never add per-file-ignores to bypass lint checks
    - **Supported Rules**: E (pycodestyle), W (warnings), F (pyflakes), I (isort), B (bugbear), C4 (comprehensions), UP (pyupgrade), S (bandit), PL (pylint), D (pydocstyle)
    - **Common Fixes**: D205 (docstring format), E501 (line length), PLR2004 (magic values), PLC0415 (import location), PLR0915 (function length)
    - **Workflow**: Understand rule → fix actual code → refactor if needed → verify passes
  - **Only Acceptable Ignores**: `__init__.py` F401 (re-exports), `tests/**` S101/PLR2004/D103

### Changed

- **Agents Updated** - Added lifecycle hooks to key agents
  - `pensive:code-reviewer`: PreToolUse and Stop hooks for audit logging
  - Escalation configuration added to agents

- **Skill Patterns** - Updated skill patterns in documentation
  - YAML-style allowed-tools shown as preferred syntax
  - Wildcard permission patterns documented
  - Lifecycle hooks demonstrated in skill frontmatter

- **Agents Updated with Hooks** - Added lifecycle hooks to more agents
  - `sanctum:pr-agent`: PreToolUse, PostToolUse, Stop hooks for quality gate audit
  - `sanctum:git-workspace-agent`: PreToolUse hook for read-only validation
  - `conserve:context-optimizer`: PreToolUse, PostToolUse, Stop hooks for audit logging
  - `sanctum:commit-agent`: PreToolUse (Bash, Read), PostToolUse (Bash), Stop hooks for commit audit logging
  - `sanctum:dependency-updater`: PreToolUse (Bash, Write|Edit), PostToolUse (Bash), Stop hooks with security warnings
  - `pensive:architecture-reviewer`: PreToolUse (Read|Grep|Glob), PostToolUse (Bash), Stop hooks for review tracking
  - `pensive:rust-auditor`: PreToolUse (Bash, Grep), PostToolUse (Bash), Stop hooks for unsafe code audit trail

- **Commands Updated with Hooks** - Added lifecycle hooks to high-frequency user-facing commands
  - `/update-dependencies` (sanctum): PreToolUse (Task), Stop hooks with security-critical operation tracking and dry-run mode detection
  - `/pr` (sanctum): PreToolUse (Skill|Task), PostToolUse (Bash), Stop hooks tracking code review options and quality gates
  - `/bloat-scan` (conserve): PreToolUse (Task), Stop hooks tracking scan level and focus area for technical debt metrics

- **Skills Updated with Hooks** - Added lifecycle hooks to critical workflow skills
  - `pr-prep` (sanctum): PreToolUse (Bash), PostToolUse (Write), Stop hooks tracking quality gates and PR template generation
  - `git-workspace-review` (sanctum): PreToolUse (Bash), Stop hooks for git analysis tracking
  - `context-optimization` (conserve): PreToolUse (Read), PostToolUse (Bash), Stop hooks for context pressure monitoring

### Added

- **Frontmatter Validation Tests** - 33 new tests for Claude Code 2.1.0 validation
  - `TestValidate210Fields`: 19 tests for context, hooks, permissions, allowed-tools
  - `TestHas210Features`: 9 tests for feature detection
  - `TestAllHookEventTypes`: 2 tests for hook event validation
  - `TestConstantDefinitions`: 3 tests for constant verification
  - All 62 frontmatter tests pass (was 29, now 62)

- **Base Module Tests** - 25 new tests for abstract.base module
  - `TestSetupImports`: Backwards compatibility verification
  - `TestHasFrontmatterFile`: File reading with error handling
  - `TestFindMarkdownFiles`: Directory traversal and recursion
  - `TestAbstractScript`: Class initialization and lazy loading

### Removed

- **pensieve plugin** - Consolidated into memory-palace and pensive for better integration
  - **Memory storage** (hooks, logging) moved to memory-palace - uses existing observability infrastructure
  - **Review capabilities** (metrics, history) moved to pensive - extends code review toolkit
  - **No functionality lost** - all features preserved with better integration
  - **Migration path**: `/pensieve:metrics` → `/pensive:skill-review`, `/pensieve:history` → `/pensive:skill-history`

## [1.2.1] - 2026-01-05

### Added

- **Tutorials: Skills Showcase** - Interactive demo of skill discovery and usage
  - **New Tutorial**: Visual GIF demonstration of claude-night-market skill capabilities
    - **Skill Discovery**: Browse and count 105+ skills across all plugins
    - **Skill Anatomy**: Examine frontmatter, metadata, and structure
    - **Skill Validation**: Use `abstract:plugin-validator` to check quality
    - **Workflow Composition**: See how skills chain into complex workflows
    - **Dual Documentation**: Concise docs and detailed book chapter
  - **Assets**: VHS tape (`assets/tapes/skills-showcase.tape`) and generated GIF
  - **Integration**: Added to README demos section, book SUMMARY, and tutorials overview
  - **Target Audience**: Beginners learning the skill system, plugin developers understanding architecture

- **Minister: Issue Creation Command** - Complete GitHub issue lifecycle management
  - **New Command**: `/create-issue` - Create GitHub issues with formatting and reference links
    - **Interactive Template Mode**: Guided prompts for bug reports, feature requests, documentation
    - **Smart References**: Auto-fetch and format related issue/PR/doc links
    - **Cross-Repository**: Create issues in any accessible repository
    - **Label Management**: Apply multiple labels with validation
    - **Project Integration**: Auto-add to GitHub Projects v2
    - **Minister Tracker**: Optional auto-capture to project tracker
  - **Complements**: `/close-issue` command for full issue lifecycle coverage
  - **Integration**: Works with minister's initiative tracking and status dashboards

- **Quality Infrastructure** - Three-layer quality system for code standards
  - **New Scripts**:
    - `scripts/run-plugin-lint.sh` - Plugin-specific linting (all or changed plugins)
    - `scripts/run-plugin-typecheck.sh` - Plugin-specific type checking
    - `scripts/run-plugin-tests.sh` - Plugin-specific test execution
    - `scripts/check-all-quality.sh` - Comprehensive quality check with optional report
  - **Documentation**:
    - `docs/quality-gates.md` - Three-layer quality system documentation
    - `docs/testing-guide.md` - Testing patterns and troubleshooting
  - **Pre-Commit Integration**: Hooks run plugin-specific checks on changed files only
  - **Coverage**: ~400+ tests across 10 plugins with automated enforcement

### Changed

- **Pre-commit hooks enhanced** - Plugin-specific lint/typecheck/test hooks for changed plugins
- **README updated** - Added Quality Gates and Testing Guide to documentation table

### Fixed

- **Spec-Kit: Test Fixture Completion** - Fixed 3 skipped parametrized tests in task planning
  - **Fixture Update**: Completed `valid_task_list` fixture with phases 2-4 (Core Implementation, Integration, Polish)
  - **Test Coverage**: All 184 spec-kit tests now passing (previously 181 passed, 3 skipped)
  - **Phase Structure**: Added 8 new tasks across 3 phases with proper dependencies and time estimates
  - **Format Compliance**: Ensured time estimates match regex pattern and action verb requirements
  - **Documentation**: Updated testing guide to reflect spec-kit's 184 tests (up from ~60)

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
      - Recommendation: Enable `ENABLE_LSP_TOOL=1` permanently in environment
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

[1.2.1]: https://github.com/athola/claude-night-market/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/athola/claude-night-market/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/athola/claude-night-market/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/athola/claude-night-market/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/athola/claude-night-market/compare/v1.0.4...v1.1.0
[1.0.4]: https://github.com/athola/claude-night-market/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/athola/claude-night-market/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/athola/claude-night-market/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/athola/claude-night-market/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/athola/claude-night-market/releases/tag/v1.0.0
