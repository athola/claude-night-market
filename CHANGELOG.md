# Changelog

All notable changes to the Claude Night Market plugin ecosystem are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.2] - 2026-01-22

### Enhanced - Claude Code 2.1.14+ Compatibility (conserve)

- **Parallel subagents**: Added version compatibility note to `mcp-coordination.md` documenting improved stability with Claude Code 2.1.14+ memory fixes
- **Continuation-agent**: Benefits from upstream memory leak fix for long-running sessions (stream resources now properly cleaned up after shell commands)
- **MECW guidance unchanged**: Our 50% quality threshold is independent of the 65%→98% blocking fix (quality vs operational limits)

## [1.3.1] - 2026-01-21

### Added - Hookify v1.1.0 (hookify)

- **block-destructive-git rule**: Blocks dangerous git commands that cause irreversible data loss
  - `git reset --hard` - Destroys all uncommitted changes
  - `git checkout -- .` - Discards all unstaged changes
  - `git clean -fd` - Permanently deletes untracked files
  - `git stash drop` - Permanently deletes stashed changes
  - `git branch -D` - Force-deletes branches (even unmerged)
  - `git reflog expire` / `git gc --prune` - Destroys recovery points
- **warn-risky-git rule**: Warns about git operations that modify history
  - `git reset` (soft/mixed) - Moves HEAD, may unstage files
  - `git checkout <branch> -- <file>` - Replaces file from another branch
  - `git rebase -i` / `git rebase --onto` - Rewrites commit history
  - `git cherry-pick/merge/am --abort` - Discards in-progress operations
- **Recovery-first guidance**: Each blocked command shows diagnostic commands to review changes before discarding
- **Safer alternatives**: Comprehensive alternative workflows (stash, backup branches, selective operations)

### Removed - Command Deduplication (sanctum)

- **Removed `sanctum:skill-review`** - Duplicate of `pensive:skill-review` and `abstract:skill-auditor`
  - `pensive:skill-review` handles runtime metrics (execution counts, stability gaps)
  - `abstract:skill-auditor` handles static quality analysis
  - Updated cross-references in `update-plugins.md` and `skill-logs.md`

### Added - Attune v1.2.0 War Room (attune)

- **`/attune:war-room` command**: Convene expert panel for strategic decisions
- **`Skill(attune:war-room)`**: Full deliberation skill with 7 phases
- **Expert panel**: 7 specialized AI roles (Supreme Commander, Chief Strategist, etc.)
- **Deliberation phases**: Intel, Assessment, COA Development, Red Team, Voting, Premortem, Synthesis
- **Merkle-DAG anonymization**: Contributions anonymized during deliberation, unsealed after decision
- **Borda count voting**: Rank-based aggregation for fair expert voting
- **Escalation logic**: Automatic escalation from lightweight to full council on complexity
- **War Room Modules**:
  - `modules/expert-roles.md` - Expert panel configuration and invocation patterns
  - `modules/deliberation-protocol.md` - Phase definitions and flow control
  - `modules/merkle-dag.md` - Anonymization and integrity verification
- **Strategeion**: Dedicated Memory Palace chamber for war council sessions
- **Conjure delegation**: Expert dispatch via conjure delegation framework

### Added - War Room Multi-LLM Deliberation (attune/conjure)

- **War Room framework** - Multi-LLM expert council for strategic decisions
  - 7 deliberation phases: Intel, Assessment, COA Development, Red Team, Voting, Premortem, Synthesis
  - Expert panel: Supreme Commander (Opus), Chief Strategist (Sonnet), Intelligence Officer (Gemini Pro), Field Tactician (GLM-4.7), Scout (Qwen Turbo), Red Team Commander (Gemini Flash), Logistics Officer (Qwen Max)
  - Lightweight mode (3 experts) with auto-escalation to full council (7 experts)
  - Merkle-DAG anonymization: contributions anonymized during deliberation, unsealed after decision
  - Borda count voting for fair expert aggregation

- **`war_room_orchestrator.py`** (conjure) - Async orchestration engine
  - Parallel expert dispatch with timeout handling
  - Session persistence to Strategeion (Memory Palace war chamber)
  - Graceful degradation on expert failures
  - Full test coverage (17 tests)

- **War Room skill and command** (attune)
  - `Skill(attune:war-room)` - Full deliberation skill
  - `/attune:war-room` - Command interface with options: `--full-council`, `--delphi`, `--resume`
  - Modular design: expert-roles, deliberation-protocol, merkle-dag modules

- **Phase 3: Strategeion persistence**
  - Enhanced session persistence with organized subdirectories
  - `intelligence/` - Scout and Intel Officer reports
  - `battle-plans/` - COA documents from all experts
  - `wargames/` - Red Team challenges and premortem analyses
  - `orders/` - Final Supreme Commander decision
  - Session archiving to `campaign-archive/{project}/{date}/`
  - MerkleDAG reconstruction on session load

- **Phase 4: Delphi mode and hook triggers**
  - `convene_delphi()` - Iterative convergence until expert agreement
  - Convergence scoring based on Borda count spread
  - Hook auto-trigger detection with keyword analysis
  - Configurable complexity threshold (default 0.7)

## [1.3.0] - 2026-01-19

### Added - Scribe Plugin

- **New scribe plugin** - Documentation quality and AI-generated content detection
  - `doc-verifier` agent - Multi-pass documentation QA with AI slop detection
  - AI slop pattern detection: marketing speak, buzzwords, excessive enthusiasm
  - Quality checks: completeness, accuracy, consistency, examples, clarity
  - Multi-tier review: quick scan → detailed analysis → slop detection
  - Integration with `/sanctum:pr-review` and `/sanctum:update-docs` workflows

### Enhanced - Sanctum Workflows

- **Scribe integration** - Documentation review in PR and doc update workflows
  - `/pr-review` now includes scribe's doc-verifier for documentation changes
  - `/update-docs` invokes scribe for AI-generated content detection
  - Hooks.json indirect reference resolution in plugin auditor
  - Zellij session detection for smarter notifications
  - GitHub API PATCH method for PR description updates

### Enhanced - Plugin Quality Tools

- **Conserve plugin** - AI hygiene auditing and duplication detection
  - AI-generated bloat patterns module
  - Duplicate detection script for codebase hygiene
  - AI hygiene auditor agent for proactive quality checks
  - Agent psychosis and codebase hygiene documentation

- **Memory Palace** - Knowledge corpus validation and semantic memory
  - ACE Playbook semantic memory integration
  - Knowledge corpus validation script with automated testing
  - Cargo cult programming prevention documentation

### Documentation

- Added scribe plugin documentation to book
- Updated capability references with scribe agents, commands, and skills
- Enhanced plugin domain specialists section
- Updated sanctum PR workflow and README update documentation

## [1.2.9] - 2026-01-16

### Added - PermissionRequest Hook (conserve)

- **`permission_request.py` hook** - Workflow automation via auto-approve/deny (Claude Code 2.0.54+)
  - Auto-approve safe patterns: `ls`, `cat`, `head`, `tail`, `grep`, `rg`, `find`, `git status/log/diff`
  - Auto-deny dangerous patterns: `rm -rf /`, `sudo`, `curl | bash`, `git push --force main`
  - Security model: denylist checked first, then allowlist, unknown shows dialog
  - Issue #55: PermissionRequest hooks for workflow automation

- **`test_permission_request.py`** - Test coverage for hook patterns
  - Dangerous pattern detection tests
  - Safe pattern approval tests
  - Unknown command dialog tests

### Added - Session Management Skill (sanctum)

- **`session-management` skill** - Named session workflows (Issue #57)
  - `/rename` - Name current session for later resumption
  - `/resume` - Resume previous sessions from REPL or terminal
  - Patterns: debugging sessions, feature checkpoints, PR reviews, investigations
  - Best practices: naming conventions, session cleanup

### Documentation

- Updated conserve README with Hooks section documenting PermissionRequest
- Updated sanctum README with session-management skill
- Added "Permission Automation" to main README Key Features

## [1.2.8] - 2026-01-15

### Added - Interactive Authentication System (leyline)

- **`interactive-auth.sh` module** - Centralized OAuth authentication for external services
  - Multi-service support: GitHub, GitLab, AWS, GCP, Azure
  - Token caching with 5-minute TTL, session persistence with 24-hour TTL
  - Interactive OAuth prompts with CI/CD detection and automatic fallback
  - Retry logic with exponential backoff (max 3 attempts)
  - Wrapper functions: `gh_with_auth`, `glab_with_auth`, `aws_with_auth`

- **`authentication-patterns` skill enhancements**
  - New `interactive-auth.md` module (634 lines) - comprehensive implementation guide
  - New `workflow-integration.md` examples - real-world integration patterns
  - New `README.md` quick-start guide (457 lines)
  - Shell test suite: 14 tests covering syntax, functions, caching, sessions

- **`docs/guides/authentication-integration.md`** - Implementation summary and usage guide

### Added - Anti-Cargo-Cult Framework (imbue)

- **`anti-cargo-cult.md` shared module** - Understanding verification protocols
  - The Five Whys of Understanding framework
  - Understanding Checklist for code review
  - Recovery Protocol for cargo cult code
  - Integration with proof-of-work and rigorous-reasoning skills

- **Fourth Iron Law: NO CODE WITHOUT UNDERSTANDING**
  - Added to `iron-law-enforcement.md` module
  - Integration with proof-of-work TodoWrite items
  - Expanded red flags for cargo cult patterns

- **Enhanced `red-flags.md`** (+184 lines)
  - New "Cargo Cult" Family section
  - AI suggestion patterns, best practice patterns
  - Copy-paste without understanding patterns

- **`rigorous-reasoning` cargo cult patterns** (+21 lines)
  - Cargo cult reasoning detection in conflict analysis
  - Pattern recognition for "best practice" and "everyone does it" justifications

- **Knowledge corpus**: `cargo-cult-programming-prevention.md` (memory-palace)

### Added - Test Coverage Improvements (leyline)

- **`test_tokens.py`** (+10 tests)
  - JSON/default ratio handling, OSError handling, directory walking
  - tiktoken encoder paths, file encoding success/error cases
  - Coverage: 60% → 94%

- **`test_quota_tracker.py`** (+15 tests)
  - Status levels (healthy/warning/critical), RPM/daily/token warnings
  - All `can_handle_task` edge cases, storage persistence, CLI modes
  - Coverage: 74% → 97%

- **`test_anti_cargo_cult.py`** (imbue) - 16 BDD tests
  - Module structure and content validation
  - Cross-skill integration verification
  - Red flags content validation

## [1.2.7] - 2026-01-14

### Added - New Skills (Issues #39, #40)

- **`imbue:workflow-monitor` skill (skeleton)** - Monitor workflow executions for errors and inefficiencies
  - Detection patterns for command failures, timeouts, retry loops, context exhaustion
  - Efficiency detection for verbose output, redundant reads, sequential vs parallel
  - Issue templates for automatic GitHub issue creation
  - Configuration: severity thresholds, auto-create toggle, efficiency metrics

- **`pensive:fpf-review` skill (skeleton)** - FPF (Functional Programming Framework) architecture review
  - Three-perspective analysis: Functional, Practical, Foundation
  - Feature inventory and capability gap identification
  - Performance assessment and usability evaluation
  - Pattern recognition and technical debt assessment
  - Structured report generation

- **`imbue:rigorous-reasoning` skill** - Prevent sycophantic reasoning through checklist-based analysis
  - Priority signals: no courtesy agreement, checklist over intuition, categorical integrity
  - Conflict analysis protocol with harm/rights checklist
  - Red flag self-monitoring for sycophantic patterns
  - Debate methodology for truth claims in contested territory
  - Modules: priority-signals, conflict-analysis, engagement-principles, debate-methodology, correction-protocol, incremental-reasoning, pattern-completion

### Added - Feature Review Tests (Issue #41)

- **`test_feature_review.py`** - 25 comprehensive tests for feature-review skill
  - Scoring framework tests: value/cost calculation, weighted scores, priority thresholds
  - Classification system tests: proactive/reactive, static/dynamic, 2x2 matrix
  - Kano classification tests: basic, performance, delighter categories
  - Tradeoff dimension tests: minimum dimensions, scale validation
  - Integration tests: issue title format, suggestion labels, backlog limits

### Fixed - Defensive .get() Usage (Issue #44)

- **`compliance.py`** - Consistent defensive dict access
  - Changed `self.rules["max_tokens"]` to `self.rules.get("max_tokens", 4000)`
  - Changed `self.rules["required_fields"]` to `self.rules.get("required_fields", [...])`
  - Added 3 tests: partial rules, malformed rules, empty rules file handling
  - Prevents KeyError when rules file is incomplete or malformed

### Enhanced - `/fix-pr` Workflow (Issues #46, #47, #48, #49)

- **Context budget tracking** (Issue #46)
  - Added context_budget configuration with warn/checkpoint/mandatory thresholds
  - Context usage warnings at 50%, 70%, 90%
  - Mandatory phases (3.5, 4, 6) that must not be skipped
  - Checkpoint/resume pattern documentation

- **Thread vs comment distinction** (Issue #47)
  - Added section 1.5: Review Feedback Type Detection
  - Decision tree for PRRT_* threads vs general comments vs aggregated reviews
  - Guidance for handling reviews without line-specific thread IDs

- **Triage output grouping** (Issue #48)
  - Added section 2.0: Triage Output Format
  - Four categories: Fix Now, This PR, Backlog, Skip
  - Actionable table format with IDs, issues, files, rationale

- **`--continue` flag** (Issue #49)
  - Resume from last incomplete phase
  - Phase completion markers for detection
  - Example resume scenarios

### Enhanced - `/update-docs` Output Examples (Issue #51)

- **Added Output Examples section** to update-docs.md
  - Consolidation Detection Output: untracked reports, bloated files tables
  - Accuracy Verification Output: version/count mismatch warnings
  - Style Violation Output: directory-specific rules, filler phrase detection

## [1.2.6] - 2026-01-13

### Added - Self-Improvement Patterns and Research (Issues #7, #37)

- **`/fix-workflow` enhanced with self-improvement patterns**
  - Added Phase 1.5: Reflexion (self-critique loop before implementation)
  - Added Plan-Do-Check-Act (PDCA) cycle to implementation phase
  - Added difficulty-aware orchestration (simple/medium/complex)
  - Added Phase 2: Outcome feedback loop for self-evolution
  - New `--difficulty auto|simple|complex` flag
  - Complexity scoring based on files affected, cross-plugin changes, prior failures

- **ACE Playbook research for memory-palace** (Issue #7)
  - Documented semantic deduplication patterns via FAISS (0.8 cosine threshold)
  - Captured Generator-Reflector-Curator triad architecture
  - Identified counter-based reinforcement pattern (helpful/harmful/neutral)
  - Recommended per-room semantic indices for domain isolation
  - Research document: `memory-palace/docs/knowledge-corpus/queue/ace-playbook-research.md`

### Added - Plugin Root Validation (Issue #34)

- **imbue_validator now warns about missing/invalid plugin roots**
  - Logs warning when plugin root directory doesn't exist
  - Logs warning when plugin root is empty
  - Logs warning when plugin lacks expected structure (no skills/ or plugin.json)
  - New properties: `root_exists`, `root_empty`, `has_valid_structure`
  - 4 new tests covering all notification scenarios

### Added - MECW Optimization Implemented (Issues #28, #29)

- **Module bloat consolidation executed**
  - `testing-hooks.md` reduced from 627 to 118 lines (81% reduction)
  - Examples archived to `docs/examples/hook-testing/comprehensive-examples.md`
  - Module now references archived examples via links
  - Token savings: ~500 lines per skill load

### Added - Counter-Based Reinforcement (ACE Enhancement)

- **`counter_reinforcement.py` module** - ACE Playbook semantic memory pattern
  - `ReinforcementCounter` class with helpful/harmful/neutral counters
  - `CounterReinforcementTracker` for entry-level tracking
  - `helpfulness_ratio` and `confidence_score` computed properties
  - `needs_review` detection for problematic entries
  - `should_deduplicate()` using 0.8 cosine similarity threshold
  - Export/import for persistence
  - 22 new tests with full coverage

### Added - Minister Label Management

- **`/update-labels` command** - Professional GitHub label taxonomy management
  - Creates type labels: `feature`, `bugfix`, `test`, `docs`, `refactor`, `performance`, `ci-cd`, `research`
  - Creates priority labels: `high-priority`, `medium-priority`, `low-priority`
  - Creates effort labels: `small-effort`, `medium-effort`, `large-effort`
  - Replaces catch-all `enhancement` label with specific types
  - Auto-classifies issues based on title patterns
  - Supports `--dry-run`, `--preserve`, `--repo` flags
  - Integrates with minister's issue lifecycle commands

### Added - Iron Law Interlock Enforcement

- **`iron-law-interlock.md` shared module** - Hard gate enforcement for creation workflows
  - Transforms Iron Law from advisory to structural enforcement
  - Provides mandatory checklist before Write tool invocation
  - Requires test file creation BEFORE implementation
  - Captures RED state evidence as precondition
  - Defines exemption categories (documentation, configuration, user-directed)
  - Located at `abstract/shared-modules/iron-law-interlock.md`

- **Updated `/create-command`** - Phase 0 now enforces Iron Law
  - Must create test file before command file
  - Must capture failing test evidence
  - Phase 6 added: GREEN state verification
  - TodoWrite items: `proof:iron-law-red`, `proof:iron-law-interlock-satisfied`, `proof:iron-law-green`

- **Updated `/create-skill`** - Phase -1 Iron Law interlock added
  - Blocking gate before methodology curation and brainstorming
  - Quick reference for test-first workflow
  - Links to full interlock documentation

- **Updated `/create-hook`** - Phase -1 Iron Law interlock added
  - Blocking gate before brainstorming
  - Quick reference for test-first workflow
  - Links to full interlock documentation

- **Updated `imbue:proof-of-work`** - Cross-skill module reference
  - Added link to iron-law-interlock shared module
  - Connects TDD enforcement with creation workflows

## [1.2.5] - 2026-01-11

### Added - Continuous Improvement Integration

- **/update-plugins Phase 2: Automatic improvement analysis** - Plugin maintenance now includes performance review
  - Invokes `/skill-review` to identify unstable skills (stability_gap > 0.3)
  - Queries `/skill-logs` for recent failures and patterns
  - Checks git history for recurring fixes (instability signals)
  - Generates prioritized improvement recommendations (Critical/Moderate/Low)
  - Creates TodoWrite items for actionable improvements
  - **No flags required** - improvement analysis runs by default after registration audit

- **/fix-workflow Phase 0: Improvement context gathering** - Retrospectives now leverage historical data
  - Queries skill execution metrics before starting analysis
  - Searches memory-palace review-chamber for related lessons
  - Analyzes git history for recurring patterns
  - Cross-references current friction with known failure modes
  - Prioritizes fixes for high stability_gap components
  - **Automatic by default** - no flags required

- **sanctum:workflow-improvement skill enhancements** - Step 0 context gathering
  - New TodoWrite item: `fix-workflow:context-gathered`
  - New TodoWrite item: `fix-workflow:lesson-stored`
  - Checks `/skill-logs` for recent failures in workflow components
  - Queries memory-palace for workflow-related lessons
  - Analyzes git commit patterns for recurring issues
  - Step 7: Close the loop by storing lessons for future reference
  - Metrics comparison template for before/after validation

- **Continuous improvement feedback loop** - Self-improving plugin ecosystem
  - `/update-plugins` identifies improvement opportunities
  - `/fix-workflow` implements improvements with historical context
  - Lessons stored in git history and memory-palace
  - Future runs reference past improvements
  - Reduces recurring issues through pattern learning

- **imbue:proof-of-work integration with improvement workflows** - Validation for continuous improvement
  - New section: "With Improvement Workflows (`/update-plugins`, `/fix-workflow`)"
  - `/update-plugins` Phase 2 validation examples with evidence format
  - `/fix-workflow` Phase 0 validation examples for data source verification
  - `/fix-workflow` Step 7 validation for measuring improvement impact
  - Updated triggers: "improvement validated", "workflow optimized", "performance improved"
  - Ensures improvement claims are backed by quantitative metrics

- **Test coverage for continuous improvement integration** - Comprehensive test suite
  - New test file: `plugins/sanctum/tests/test_continuous_improvement.py`
  - 8 test cases covering all integration points
  - Tests Phase 2 and Phase 0 documentation
  - Tests workflow-improvement skill enhancements
  - Tests proof-of-work integration
  - Tests CHANGELOG and documentation completeness
  - Tests infrastructure accessibility
  - All tests passing with 100% success rate

### Added - Claude Code 2.1.4 Compatibility (2026-01-11)

- **`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` environment variable** - Documented for CI/CD use cases
  - Disables auto-backgrounding and `Ctrl+B` shortcut
  - Useful for CI/CD pipelines, debugging, deterministic test environments
  - Does not affect Python subprocess spawning or asyncio tasks in hooks

### Added - Claude Code 2.1.3 Compatibility (2026-01-11)

- **Compatibility documentation for Claude Code 2.1.3** - Full documentation of new features and fixes
  - **Skills/Commands Merge**: Skills now appear in `/` menu alongside commands (no behavior change)
  - **Subagent Model Fix**: Model specified in agent frontmatter now respected during context compaction
  - **Web Search Fix**: Subagent web search now uses correct model
  - **Hook Timeout**: Extended from 60 seconds to 10 minutes (enables CI/CD and complex validation)
  - **Permission Diagnostics**: `/doctor` now detects unreachable permission rules
  - **Plan File Fix**: Fresh plan files after `/clear` commands
  - **ExFAT Compatibility**: Fixed skill duplicate detection on large inode filesystems

- **Updated hook-authoring skill** - Timeout guidance updated for 10-minute limit
  - Best practice: Aim for < 30s for typical hooks
  - Extended time available for CI/CD integration, complex validation, external APIs

- **Updated compatibility reference** - Version matrix includes 2.1.3+ as recommended
  - All 29 ecosystem agents verified to have `model:` specification (benefits from subagent fix)
  - No breaking changes - existing plugin.json structure remains valid

### Added - Claude Code 2.1.2 Compatibility (2026-01-11)

- **Agent-aware SessionStart hooks** - Hooks now leverage `agent_type` input field
  - `sanctum/hooks/post_implementation_policy.py` - Skips governance for review agents
  - `conserve/hooks/session-start.sh` - Abbreviated context for lightweight agents
  - `imbue/hooks/session-start.sh` - Minimal scope-guard for review/optimization agents
  - Pattern: Read JSON from stdin, check `agent_type`, customize context injection
  - Reduces context overhead by ~200-800 tokens for non-implementation agents

- **SessionStart input schema documentation** - Updated skill documentation
  - `abstract:hook-authoring` - Documents `agent_type`, `source`, `session_id` fields
  - `abstract:hook-scope-guide` - Explains agent-aware hook patterns
  - Includes Python and Bash examples for reading hook input

- **Large output persistence documentation** - Notes on behavior change
  - `conserve:context-optimization` - Documents disk-based output storage
  - Best practices for leveraging full output access without context bloat

- **`FORCE_AUTOUPDATE_PLUGINS` environment variable** - Documented for developers
  - Forces plugin auto-update even when main auto-updater disabled
  - Useful for CI/CD pipelines and controlled update rollouts

### Changed

- Hook input reading uses non-blocking patterns (`read -t 0.1` in bash)
- Backward compatible: gracefully handles missing stdin from older Claude Code versions

### Added - Iron Law TDD Enforcement (2026-01-11)

- **New `iron-law-enforcement.md` module** - Comprehensive TDD enforcement patterns
  - Defines the Iron Law: "NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST"
  - Prevents "Cargo Cult TDD" where tests validate pre-conceived implementations
  - Five enforcement levels: self-enforcement, adversarial verification, git history analysis, pre-commit hooks, coverage gates
  - Self-check protocol with red flags table for TDD violations
  - RED/GREEN/REFACTOR subagent pattern for adversarial verification
  - Git history audit commands to detect TDD compliance
  - Pre-commit hook template to block implementation-only commits
  - Three-pillar coverage requirements: line, branch, and mutation testing
  - Recovery protocols for Iron Law violations
  - Self-improvement loop: learn from violations, strengthen rules

- **Updated proof-of-work skill** - Integrated Iron Law enforcement
  - Added Iron Law section with self-check table
  - New TodoWrite items: `proof:iron-law-red`, `proof:iron-law-green`, `proof:iron-law-refactor`, `proof:iron-law-coverage`
  - Cross-referenced iron-law-enforcement.md module

- **Updated skill-authoring skill** - Extended Iron Law to all implementation work
  - Skills: No skill without documented Claude failure
  - Code: No implementation without failing test
  - Claims: No completion claim without evidence
  - Cross-referenced proof-of-work Iron Law module

- **Updated proof-enforcement.md** - Added Rule 4: Iron Law TDD Compliance
  - Blocks completion claims lacking TDD evidence
  - Checks for failing test evidence, design emergence, commit patterns
  - Includes recovery protocol for violations

- **Updated post_implementation_policy.py** - Strengthened governance injection
  - Added Iron Law self-check table to session start
  - Extended red flags with TDD-specific patterns
  - Added iron-law TodoWrite items to required protocol

- **Updated imbue session-start.sh** - Added Iron Law quick reference
  - Iron Law statement and self-check table
  - TDD TodoWrite items reminder

### Fixed - Proof-of-Work Enforcement Gap (2026-01-11)

- **Integrated proof-of-work into governance protocol** - `post_implementation_policy.py`
  - Proof-of-work is now STEP 1 (before doc updates)
  - Added red flag table to catch rationalization patterns
  - Requires TodoWrite items: `proof:solution-tested`, `proof:evidence-captured`

- **Added proof-of-work reminder to Stop hook** - `verify_workflow_complete.py`
  - End-of-session checklist now includes proof-of-work items
  - Warning if proof-of-work was skipped

- **Added proof-of-work to imbue session start** - `session-start.sh`
  - Quick reference table alongside scope-guard
  - Red flags table for common rationalization patterns

**Root Cause**: `proof-enforcement.md` was a design document referencing non-existent
`PreMessageSend` hook type. Implementation now uses available hooks (SessionStart, Stop)
to enforce proof-of-work discipline through governance injection and checklists

- **Cleaned up unsupported hook type reference** - `imbue/hooks/proof-enforcement.md`
  - Updated frontmatter to reference actual triggers (SessionStart, Stop)
  - Added Implementation Status section explaining actual enforcement mechanism
  - Updated Configuration section to reflect automatic enforcement
  - Preserved detection patterns as self-enforcement guidance

## [1.2.4] - 2026-01-10

### Added - Shell Review Skill and Security Guardrails (2026-01-10)

- **pensive:shell-review** - New skill for auditing shell scripts
  - Exit code analysis and error handling validation
  - POSIX portability checks (bash-specific vs portable constructs)
  - Safety pattern verification (quoting, word splitting, globbing)
  - Modular design with `exit-codes.md`, `portability.md`, `safety-patterns.md` modules
  - Integration with `imbue:evidence-logging` for structured findings

- **sanctum:security-pattern-check hook** - Context-aware security checking
  - Distinguishes code files from documentation (reduces false positives)
  - Detects patterns in context (ignores examples showing what NOT to do)
  - Checks for dynamic code execution, shell injection, SQL injection, hardcoded secrets
  - Configurable via `hooks.json` with environment variable overrides

- **Commit workflow guardrails** - Prevention of quality gate bypass
  - Added guardrails against `--no-verify` in commit-messages skill
  - Updated git-workspace-review to run `make format && make lint` proactively
  - Skills now block if code quality checks fail (no bypass allowed)

### Changed - Bloat Reduction Phases 6-9 (2026-01-10)

#### Phase 6: Pensive Code Refactoring (~2,400 tokens saved)
- Created shared utilities module (`pensive/utils/`)
  - `content_parser.py`: File parsing and snippet extraction utilities
  - `severity_mapper.py`: Centralized severity categorization
  - `report_generator.py`: Reusable markdown report formatting
- Enhanced `BaseReviewSkill` with shared helper methods
- Reduced code duplication across 4 review skills (rust, architecture, bug, makefile)

#### Phase 8: Examples Repository (~5,540 tokens saved)
- Created centralized `/examples/attune/` directory
- Moved large example files from plugin to examples directory
  - `microservices-example.md` (726 lines → 20 line stub)
  - `library-example.md` (699 lines → 18 line stub)
- Replaced with lightweight stub files that reference full content

#### Phase 9: Script Data Extraction - Complete (~10,192 tokens saved)
Applied systematic data extraction to 4 large Python scripts:

1. **seed_corpus.py** (1,117 → ~285 lines)
   - Extracted: `data/seed_topics.yaml` (topic catalog)
   - Savings: ~832 lines

2. **makefile_dogfooder.py** (793 → ~200 lines)
   - Extracted: `data/makefile_target_catalog.yaml` (target definitions)
   - Savings: ~593 lines

3. **template_customizer.py** (792 → ~130 lines)
   - Extracted: `data/architecture_templates.yaml` (480 lines of templates)
   - Savings: ~662 lines

4. **architecture_researcher.py** (641 → ~180 lines)
   - Extracted: `data/paradigm_decision_matrix.yaml` (decision logic)
   - Savings: ~461 lines

**Pattern**: Identify embedded data → Extract to YAML → Add load functions → Update scripts
**Result**: 3,343 → ~795 lines (76% code reduction)

**Total token savings (Phases 6-9)**: ~18,132 tokens
**Combined total (all phases)**: ~70,772 tokens (28-33% context reduction)

### Added

- **Skills Separation Guide** - Comprehensive guide for separating development skills from runtime agent skills
  - **Problem**: Namespace collision when using Claude Code to build AI agents (development skills vs runtime skills)
  - **New Guides**: 4 complementary resources (~16,300 words total)
    - `docs/guides/development-vs-runtime-skills-separation.md` - Full technical guide (11K words)
    - `docs/guides/skills-separation-quickref.md` - One-page quick reference
    - `docs/guides/skills-separation-diagram.md` - Visual diagrams (Mermaid + ASCII)
    - `docs/reddit-response-skills-separation.md` - Conversational response format
  - **4 Separation Patterns**: Physical directory, namespace prefixing, context forking, scoped loading
  - **SDK Integration**: Complete examples for composing system prompts from skill files
  - **Example Project**: TodoAgent with separated development (.claude/skills/) and runtime (src/agent/prompts/) namespaces
  - **Workflow Coverage**: 3-phase workflow (build, test, deploy) with context isolation
  - **Troubleshooting**: Common issues and solutions for namespace bleeding
  - **Integration**: References abstract, conserve, pensive, spec-kit plugins
  - **Updated**: README.md with link to Advanced Guides, docs/guides/README.md with new section
  - **Use Case**: Essential for anyone building AI agent applications with Claude Code assistance

- **Documentation Standards** - NEW guide codifying documentation debloating methodology
  - **New Guide**: `docs/guides/documentation-standards.md` enforces directory-specific line limits
  - **Directory Limits**: docs/=500 lines (strict reference), book/=1000 lines (lenient tutorial)
  - **Debloating Techniques**: Progressive disclosure, consolidation, cross-referencing, deletion
  - **Anti-Patterns**: Complete-guide files, verbose examples, redundant code, monolithic files
  - **Enforcement**: Pre-commit checks, monthly reviews, PR checklist
  - **Phase 5 Results**: Applied to 8 files, 3,421 lines saved (55% reduction, ~3,200 tokens)

- **Data Extraction Pattern Guide** - Comprehensive guide for separating data from code
  - **New Guide**: `docs/guides/data-extraction-pattern.md` documents the data-to-YAML refactoring pattern
  - **5-Step Process**: Identify → Extract → Deserialize → Update → Validate
  - **Real Examples**: 4 production refactorings from claude-night-market (seed_corpus, makefile_dogfooder, template_customizer, architecture_researcher)
  - **Results**: 75% average code reduction (3,343 → ~795 lines across 4 scripts)
  - **Benefits**: Non-programmer editable configs, cleaner diffs, runtime flexibility
  - **Best Practices**: YAML schema documentation, error handling, defaults, version migration
  - **Code Templates**: Production-ready examples with comprehensive error handling
  - **Integration**: References optimization-patterns.md and documentation-standards.md

- **Optimization Patterns** - Battle-tested methodology for context reduction
  - **New Guide**: `docs/optimization-patterns.md` captures systematic optimization approach
  - **8 Patterns**: Archive cleanup, hub-and-spoke docs, data extraction, shared utilities, examples repo, progressive disclosure, TODO audit, anti-pattern removal
  - **Proven Results**: 9 phases achieving 28-33% context reduction (~70,772 tokens saved)
  - **5 Principles**: Separation of concerns, DRY, progressive disclosure, maintainability, backwards compatibility
  - **Phase-Based Workflow**: Discovery → Analysis → Planning → Execution → Validation
  - **Metrics**: Token estimation formulas, success criteria, tracking templates
  - **Real-World Data**: Complete phase-by-phase breakdown with measurable impact
  - **Future Opportunities**: Automation, configuration management, pattern library

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

- **hooks.json validation errors**: Fixed hooks.json matcher format in abstract and memory-palace plugins - changed from object `{"toolName": "Skill"}` to string `"Skill"` per Claude Code SDK requirements
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
- **Bloat Report Updated**: bloat-scan-report-20260109.md now includes Phase 5 (~52,640 tokens total saved)

### Changed

- **Documentation Debloating (Phase 5)** - Enforced strict line limits across documentation files
  - **hook-types-comprehensive.md**: 748 → 147 lines (table-of-contents pattern)
  - **security-patterns.md**: 904 → 534 lines (consolidated redundant examples)
  - **authoring-best-practices.md**: 652 → 427 lines (removed verbosity)
  - **evaluation-methodology.md**: 653 → 377 lines (extracted implementations)
  - **error-handling-guide.md**: 580 → 316 lines (cross-referenced tutorial)
  - **Deleted outdated plans**: 2 historical files (1,685 lines)
  - **Total impact**: 6,222 → 1,801 lines (3,421 saved, ~3,200 tokens)
  - **Quality preserved**: All detail maintained via progressive disclosure

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
    - `/attune:upgrade-project` - Add or update configurations in existing projects
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
    - `/attune:upgrade-project` - Add missing configs to existing projects with status reporting
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
- **Commands restructured**: Eliminated duplicate command names across plugins (do-issue, reinstall-all-plugins)
- **Capabilities documentation**: Added feature-review and standardized hook types

### Fixed

- **Compliance**: Addressed PR #42 review feedback for skill assurance

## [1.0.3] - 2025-12-19

### Added

- **Imbue feature-review skill**: Evidence-based prioritization for feature requests and bug triage
- **Memory-palace PreToolUse hook**: Persist intake queue directly from hook for reliable queue management

### Changed

- **Sanctum do-issue command**: Modularized for better token efficiency
- **Imbue tests**: Test updates across review analyst, catchup, and skill modules

### Fixed

- **Sanctum fix-pr**: Removed emojis from example outputs for cleaner formatting
- **Lock files**: Updated across imbue, memory-palace, pensive, and spec-kit plugins

## [1.0.2] - 2025-12-18

### Added

- **Conservation hooks**: Session-start integration that automatically loads optimization guidance
- **Conservation bypass modes**: `CONSERVATION_MODE` environment variable (quick/normal/deep)
- **Sanctum do-issue command**: New workflow for addressing GitHub issues
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

[1.3.1]: https://github.com/athola/claude-night-market/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/athola/claude-night-market/compare/v1.2.9...v1.3.0
[1.2.5]: https://github.com/athola/claude-night-market/compare/v1.2.4...v1.2.5
[1.2.4]: https://github.com/athola/claude-night-market/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/athola/claude-night-market/compare/v1.2.1...v1.2.3
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
