# Capabilities Reference

Quick lookup table of all skills, commands, agents,
and hooks in the Claude Night Market.

**For full flag documentation and workflow examples**:
See [Capabilities Reference Details](capabilities-reference-details.md).

## Quick Reference Index

### All Skills (Alphabetical)

| Skill | Plugin | Description |
|-------|--------|-------------|
| `agent-expenditure` | [conserve](../plugins/conserve.md) | Per-agent token usage tracking |
| `agent-teams` | [conjure](../plugins/conjure.md) | Coordinate Claude Code Agent Teams through filesystem-based protocol |
| `api-review` | [pensive](../plugins/pensive.md) | API surface evaluation |
| `architecture-aware-init` | [attune](../plugins/attune.md) | Architecture-aware project initialization with research |
| `architecture-paradigm-client-server` | [archetypes](../plugins/archetypes.md) | Client-server communication |
| `architecture-paradigm-cqrs-es` | [archetypes](../plugins/archetypes.md) | CQRS and Event Sourcing |
| `architecture-paradigm-event-driven` | [archetypes](../plugins/archetypes.md) | Asynchronous communication |
| `architecture-paradigm-functional-core` | [archetypes](../plugins/archetypes.md) | Functional Core, Imperative Shell |
| `architecture-paradigm-hexagonal` | [archetypes](../plugins/archetypes.md) | Ports & Adapters architecture |
| `architecture-paradigm-layered` | [archetypes](../plugins/archetypes.md) | Traditional N-tier architecture |
| `architecture-paradigm-microkernel` | [archetypes](../plugins/archetypes.md) | Plugin-based extensibility |
| `architecture-paradigm-microservices` | [archetypes](../plugins/archetypes.md) | Independent distributed services |
| `architecture-paradigm-modular-monolith` | [archetypes](../plugins/archetypes.md) | Single deployment with internal boundaries |
| `architecture-paradigm-pipeline` | [archetypes](../plugins/archetypes.md) | Pipes-and-filters model |
| `architecture-paradigm-serverless` | [archetypes](../plugins/archetypes.md) | Function-as-a-Service |
| `architecture-paradigm-service-based` | [archetypes](../plugins/archetypes.md) | Coarse-grained SOA |
| `architecture-paradigm-space-based` | [archetypes](../plugins/archetypes.md) | Data-grid architecture |
| `architecture-paradigms` | [archetypes](../plugins/archetypes.md) | Orchestrator for paradigm selection |
| `architecture-review` | [pensive](../plugins/pensive.md) | Architecture assessment |
| `authentication-patterns` | [leyline](../plugins/leyline.md) | Auth flow patterns |
| `bloat-detector` | [conserve](../plugins/conserve.md) | Detection algorithms for dead code, God classes, documentation duplication |
| `browser-recording` | [scry](../plugins/scry.md) | Playwright browser recordings |
| `bug-review` | [pensive](../plugins/pensive.md) | Bug hunting |
| `catchup` | [imbue](../plugins/imbue.md) | Context recovery |
| `clear-context` | [conserve](../plugins/conserve.md) | Auto-clear workflow with session state persistence |
| `code-quality-principles` | [conserve](../plugins/conserve.md) | Core principles for AI-assisted code quality |
| `code-refinement` | [pensive](../plugins/pensive.md) | Duplication, algorithms, and clean code analysis |
| `code-search` | [tome](../plugins/tome.md) | GitHub implementation search |
| `commit-messages` | [sanctum](../plugins/sanctum.md) | Conventional commits |
| `compression-strategy` | [conserve](../plugins/conserve.md) | Context compression analysis and recommendations |
| `computer-control` | [phantom](../plugins/phantom.md) | Desktop automation via Claude's vision and action API |
| `content-sanitization` | [leyline](../plugins/leyline.md) | External content sanitization |
| `context-optimization` | [conserve](../plugins/conserve.md) | MECW principles and 50% context rule |
| `cpu-gpu-performance` | [conserve](../plugins/conserve.md) | Resource monitoring and selective testing |
| `damage-control` | [leyline](../plugins/leyline.md) | Agent crash recovery and state reconciliation |
| `decisive-action` | [conserve](../plugins/conserve.md) | Decisive action patterns for efficient workflows |
| `deferred-capture` | [leyline](../plugins/leyline.md) | Contract for unified deferred-item capture across plugins |
| `delegation-core` | [conjure](../plugins/conjure.md) | Framework for delegation decisions |
| `diff-analysis` | [imbue](../plugins/imbue.md) | Semantic changeset analysis |
| `dig` | [tome](../plugins/tome.md) | Interactive research refinement |
| `digital-garden-cultivator` | [memory-palace](../plugins/memory-palace.md) | Digital garden maintenance |
| `discourse` | [tome](../plugins/tome.md) | Community discussion scanning |
| `doc-consolidation` | [sanctum](../plugins/sanctum.md) | Document merging |
| `doc-generator` | [scribe](../plugins/scribe.md) | Generate and remediate documentation |
| `doc-importer` | [scribe](../plugins/scribe.md) | Import external documents to markdown |
| `doc-updates` | [sanctum](../plugins/sanctum.md) | Documentation maintenance |
| `document-conversion` | [leyline](../plugins/leyline.md) | Universal document-to-markdown conversion |
| `do-issue` | [sanctum](../plugins/sanctum.md) | GitHub issue resolution workflow |
| `dorodango` | [attune](../plugins/attune.md) | Iterative code polishing workflow |
| `error-patterns` | [leyline](../plugins/leyline.md) | Standardized error handling |
| `escalation-governance` | [abstract](../plugins/abstract.md) | Model escalation decisions |
| `evaluation-framework` | [leyline](../plugins/leyline.md) | Decision thresholds |
| `feature-review` | [imbue](../plugins/imbue.md) | Feature prioritization with RICE/WSJF/Kano scoring |
| `file-analysis` | [sanctum](../plugins/sanctum.md) | File structure analysis |
| `gemini-delegation` | [conjure](../plugins/conjure.md) | Gemini CLI integration |
| `gif-generation` | [scry](../plugins/scry.md) | GIF processing and optimization |
| `git-platform` | [leyline](../plugins/leyline.md) | Cross-platform git forge detection and command mapping |
| `git-workspace-review` | [sanctum](../plugins/sanctum.md) | Repo state analysis |
| `github-initiative-pulse` | [minister](../plugins/minister.md) | Initiative progress tracking |
| `hook-authoring` | [abstract](../plugins/abstract.md) | Security-first hook development |
| `hooks-eval` | [abstract](../plugins/abstract.md) | Hook security scanning |
| `install-watchdog` | [egregore](../plugins/egregore.md) | Install crash-recovery watchdog |
| `knowledge-intake` | [memory-palace](../plugins/memory-palace.md) | Intake and curation |
| `knowledge-locator` | [memory-palace](../plugins/memory-palace.md) | Spatial search |
| `latent-space-engineering` | [imbue](../plugins/imbue.md) | Agent behavior shaping through instruction framing |
| `makefile-generation` | [attune](../plugins/attune.md) | Generate language-specific Makefiles |
| `makefile-review` | [pensive](../plugins/pensive.md) | Makefile best practices |
| `markdown-formatting` | [leyline](../plugins/leyline.md) | Line wrapping and style conventions |
| `math-review` | [pensive](../plugins/pensive.md) | Mathematical correctness |
| `mcp-code-execution` | [conserve](../plugins/conserve.md) | MCP patterns for data pipelines |
| `media-composition` | [scry](../plugins/scry.md) | Multi-source media stitching |
| `memory-palace-architect` | [memory-palace](../plugins/memory-palace.md) | Building virtual palaces |
| `metacognitive-self-mod` | [abstract](../plugins/abstract.md) | Hyperagents self-improvement analysis |
| `methodology-curator` | [abstract](../plugins/abstract.md) | Surface expert frameworks for skill development |
| `mission-orchestrator` | [attune](../plugins/attune.md) | Unified lifecycle orchestrator for project development |
| `modular-skills` | [abstract](../plugins/abstract.md) | Modular design patterns |
| `papers` | [tome](../plugins/tome.md) | Academic literature search |
| `plugin-review` | [abstract](../plugins/abstract.md) | Tiered plugin quality review with dependency-aware scoping |
| `pr-prep` | [sanctum](../plugins/sanctum.md) | PR preparation |
| `pr-review` | [sanctum](../plugins/sanctum.md) | PR review workflows |
| `precommit-setup` | [attune](../plugins/attune.md) | Set up pre-commit hooks |
| `progressive-loading` | [leyline](../plugins/leyline.md) | Dynamic content loading |
| `project-brainstorming` | [attune](../plugins/attune.md) | Socratic ideation workflow |
| `project-execution` | [attune](../plugins/attune.md) | Systematic implementation |
| `project-init` | [attune](../plugins/attune.md) | Interactive project initialization |
| `project-planning` | [attune](../plugins/attune.md) | Architecture and task breakdown |
| `project-specification` | [attune](../plugins/attune.md) | Spec creation from brainstorm |
| `proof-of-work` | [imbue](../plugins/imbue.md) | Evidence-based work validation |
| `python-async` | [parseltongue](../plugins/parseltongue.md) | Async patterns |
| `python-packaging` | [parseltongue](../plugins/parseltongue.md) | Packaging with uv |
| `python-performance` | [parseltongue](../plugins/parseltongue.md) | Profiling and optimization |
| `python-testing` | [parseltongue](../plugins/parseltongue.md) | Pytest/TDD workflows |
| `pytest-config` | [leyline](../plugins/leyline.md) | Pytest configuration patterns |
| `quality-gate` | [egregore](../plugins/egregore.md) | Pre-merge quality validation for autonomous sessions |
| `qwen-delegation` | [conjure](../plugins/conjure.md) | Qwen MCP integration |
| `quota-management` | [leyline](../plugins/leyline.md) | Rate limiting and quotas |
| `release-health-gates` | [minister](../plugins/minister.md) | Release readiness checks |
| `research` | [tome](../plugins/tome.md) | Multi-source research orchestration |
| `response-compression` | [conserve](../plugins/conserve.md) | Response compression patterns |
| `review-chamber` | [memory-palace](../plugins/memory-palace.md) | PR review knowledge capture and retrieval |
| `review-core` | [imbue](../plugins/imbue.md) | Scaffolding for detailed reviews |
| `rigorous-reasoning` | [imbue](../plugins/imbue.md) | Anti-sycophancy guardrails |
| `risk-classification` | [leyline](../plugins/leyline.md) | Inline 4-tier risk classification for agent tasks |
| `rule-catalog` | [hookify](../plugins/hookify.md) | Pre-built behavioral rule templates |
| `rules-eval` | [abstract](../plugins/abstract.md) | Evaluate and validate Claude Code rules in `.claude/rules/` directories |
| `rust-review` | [pensive](../plugins/pensive.md) | Rust-specific checking |
| `safety-critical-patterns` | [pensive](../plugins/pensive.md) | NASA Power of 10 rules for robust code |
| `scope-guard` | [imbue](../plugins/imbue.md) | Anti-overengineering |
| `service-registry` | [leyline](../plugins/leyline.md) | Service discovery patterns |
| `session-management` | [sanctum](../plugins/sanctum.md) | Session naming, checkpointing, and resume strategies |
| `session-palace-builder` | [memory-palace](../plugins/memory-palace.md) | Session-specific palaces |
| `session-replay` | [scribe](../plugins/scribe.md) | Convert session JSONL into GIF/MP4/WebM replays via VHS |
| `session-to-post` | [scribe](../plugins/scribe.md) | Convert sessions into shareable blog posts or case studies |
| `shared-patterns` | [abstract](../plugins/abstract.md) | Reusable plugin development patterns |
| `shell-review` | [pensive](../plugins/pensive.md) | Shell script auditing for safety and portability |
| `skill-authoring` | [abstract](../plugins/abstract.md) | TDD methodology for skill creation |
| `skills-eval` | [abstract](../plugins/abstract.md) | Skill quality assessment |
| `slop-detector` | [scribe](../plugins/scribe.md) | Detect AI-generated content markers |
| `smart-sourcing` | [conserve](../plugins/conserve.md) | Balance accuracy with token efficiency |
| `spec-writing` | [spec-kit](../plugins/spec-kit.md) | Specification authoring |
| `speckit-orchestrator` | [spec-kit](../plugins/spec-kit.md) | Workflow coordination |
| `stewardship` | [leyline](../plugins/leyline.md) | Cross-cutting stewardship principles with layer-specific guidance |
| `storage-templates` | [leyline](../plugins/leyline.md) | Storage abstraction patterns |
| `structured-output` | [imbue](../plugins/imbue.md) | Formatting patterns |
| `style-learner` | [scribe](../plugins/scribe.md) | Extract writing style from exemplar text |
| `subagent-testing` | [abstract](../plugins/abstract.md) | Testing patterns for subagent interactions |
| `summon` | [egregore](../plugins/egregore.md) | Spawn autonomous agent session with budget |
| `synthesize` | [tome](../plugins/tome.md) | Research findings synthesis |
| `task-planning` | [spec-kit](../plugins/spec-kit.md) | Task generation |
| `tech-tutorial` | [scribe](../plugins/scribe.md) | Plan, draft, and refine technical tutorials |
| `test-review` | [pensive](../plugins/pensive.md) | Test quality review |
| `test-updates` | [sanctum](../plugins/sanctum.md) | Test maintenance |
| `testing-quality-standards` | [leyline](../plugins/leyline.md) | Test quality guidelines |
| `tiered-audit` | [pensive](../plugins/pensive.md) | Three-tier escalation audit (git history, targeted, full) |
| `token-conservation` | [conserve](../plugins/conserve.md) | Token usage strategies |
| `triz` | [tome](../plugins/tome.md) | TRIZ cross-domain analogical reasoning |
| `tutorial-updates` | [sanctum](../plugins/sanctum.md) | Tutorial maintenance and updates |
| `unified-review` | [pensive](../plugins/pensive.md) | Review orchestration |
| `uninstall-watchdog` | [egregore](../plugins/egregore.md) | Remove crash-recovery watchdog |
| `update-readme` | [sanctum](../plugins/sanctum.md) | README maintenance and updates |
| `usage-logging` | [leyline](../plugins/leyline.md) | Telemetry tracking |
| `utility` | [leyline](../plugins/leyline.md) | Utility-guided action selection for orchestration |
| `version-updates` | [sanctum](../plugins/sanctum.md) | Version bumping |
| `vhs-recording` | [scry](../plugins/scry.md) | Terminal recordings with VHS |
| `war-room` | [attune](../plugins/attune.md) | Multi-LLM expert council with Type 1/2 reversibility routing |
| `war-room-checkpoint` | [attune](../plugins/attune.md) | Inline reversibility assessment for embedded escalation |
| `workflow-improvement` | [sanctum](../plugins/sanctum.md) | Workflow retrospectives |
| `workflow-monitor` | [imbue](../plugins/imbue.md) | Workflow execution monitoring and issue creation |
| `workflow-setup` | [attune](../plugins/attune.md) | Configure CI/CD pipelines |
| `writing-rules` | [hookify](../plugins/hookify.md) | Guide for authoring behavioral rules |

### All Commands (Alphabetical)

| Command | Plugin | Description |
|---------|--------|-------------|
| `/aggregate-logs` | abstract | Generate LEARNINGS.md from skill execution logs |
| `/ai-hygiene-audit` | conserve | Audit codebase for AI-generated code quality issues (vibe coding, Tab bloat, slop) |
| `/analyze-skill` | abstract | Skill complexity analysis |
| `/analyze-tests` | parseltongue | Test suite health report |
| `/api-review` | pensive | API surface review |
| `/architecture-review` | pensive | Architecture assessment |
| `/attune:arch-init` | attune | Initialize with architecture-aware templates |
| `/attune:blueprint` | attune | Plan architecture and break down tasks |
| `/attune:brainstorm` | attune | Brainstorm project ideas using Socratic questioning |
| `/attune:execute` | attune | Execute implementation tasks systematically |
| `/attune:mission` | attune | Run full project lifecycle as a single mission with state detection and recovery |
| `/attune:project-init` | attune | Initialize project with development infrastructure |
| `/attune:specify` | attune | Create detailed specifications from brainstorm |
| `/attune:upgrade-project` | attune | Add or update configurations in existing project |
| `/attune:validate` | attune | Validate project structure against best practices |
| `/attune:war-room` | attune | Multi-LLM expert deliberation with reversibility-based routing |
| `/bloat-scan` | conserve | Progressive bloat detection (3-tier scan) |
| `/bug-review` | pensive | Bug hunting review |
| `/bulletproof-skill` | abstract | Anti-rationalization workflow |
| `/catchup` | imbue | Quick context recovery |
| `/check-async` | parseltongue | Async pattern validation |
| `/close-issue` | minister | Analyze if GitHub issues can be closed based on commits |
| `/commit-msg` | sanctum | Generate commit message |
| `/context-report` | abstract | Context optimization report |
| `/control-desktop` | phantom | Run a computer use task on the desktop |
| `/create-command` | abstract | Scaffold new command |
| `/create-hook` | abstract | Scaffold new hook |
| `/create-issue` | minister | Create GitHub issue with labels and references |
| `/create-skill` | abstract | Scaffold new skill |
| `/create-tag` | sanctum | Create git tags for releases |
| `/dismiss` | egregore | Terminate autonomous agent session |
| `/do-issue` | sanctum | Fix GitHub issues |
| `/doc-generate` | scribe | Generate new documentation |
| `/doc-polish` | scribe | Clean up AI-generated content |
| `/evaluate-skill` | abstract | Evaluate skill execution quality |
| `/fix-pr` | sanctum | Address PR review comments |
| `/fix-workflow` | sanctum | Workflow retrospective with automatic improvement context gathering |
| `/full-review` | pensive | Unified code review |
| `/garden` | memory-palace | Manage digital gardens |
| `/git-catchup` | sanctum | Git repository catchup |
| `/hookify` | hookify | Create behavioral rules to prevent unwanted actions |
| `/hookify:configure` | hookify | Interactive rule enable/disable interface |
| `/hookify:from-hook` | hookify | Convert Python SDK hooks to declarative rules |
| `/hookify:help` | hookify | Display hookify help and documentation |
| `/hookify:install` | hookify | Install hookify rule from catalog |
| `/hookify:list` | hookify | List all hookify rules with status |
| `/hooks-eval` | abstract | Hook evaluation |
| `/improve-skills` | abstract | Auto-improve skills from observability data |
| `/install-watchdog` | egregore | Install crash-recovery watchdog |
| `/make-dogfood` | abstract | Makefile enhancement |
| `/makefile-review` | pensive | Makefile review |
| `/math-review` | pensive | Mathematical review |
| `/merge-docs` | sanctum | Consolidate ephemeral docs |
| `/navigate` | memory-palace | Search palaces |
| `/optimize-context` | conserve | Context optimization |
| `/palace` | memory-palace | Manage palaces |
| `/plugin-review` | abstract | Tiered plugin quality review (branch/pr/release) |
| `/prepare-pr` | sanctum | Complete PR preparation with updates and validation |
| `/pr-review` | sanctum | Enhanced PR review |
| `/promote-discussions` | abstract | Promote highly-voted community learnings from Discussions to Issues |
| `/record-browser` | scry | Record browser session |
| `/record-terminal` | scry | Create terminal recording |
| `/refine-code` | pensive | Analyze and improve living code quality |
| `/reinstall-all-plugins` | leyline | Refresh all plugins |
| `/resolve-threads` | sanctum | Resolve PR review threads |
| `/review-room` | memory-palace | Manage PR review knowledge in palaces |
| `/rules-eval` | abstract | Evaluate Claude Code rules for frontmatter, glob patterns, and content quality |
| `/run-profiler` | parseltongue | Profile code execution |
| `/rust-review` | pensive | Rust-specific review |
| `/session-replay` | scribe | Generate GIF/MP4/WebM replay from session JSONL |
| `/session-to-post` | scribe | Convert session into blog post or case study |
| `/shell-review` | pensive | Shell script safety and portability review |
| `/skill-history` | pensive | View recent skill executions with context |
| `/skill-logs` | memory-palace | View skill execution logs |
| `/skill-review` | pensive | Analyze skill metrics and stability gaps |
| `/skills-eval` | abstract | Skill quality assessment |
| `/speckit-analyze` | spec-kit | Check artifact consistency |
| `/speckit-checklist` | spec-kit | Generate checklist |
| `/speckit-clarify` | spec-kit | Clarifying questions |
| `/speckit-constitution` | spec-kit | Project constitution |
| `/speckit-implement` | spec-kit | Execute tasks |
| `/speckit-plan` | spec-kit | Generate plan |
| `/speckit-specify` | spec-kit | Create specification |
| `/speckit-startup` | spec-kit | Bootstrap workflow |
| `/speckit-tasks` | spec-kit | Generate tasks |
| `/speckit-taskstoissues` | spec-kit | Convert tasks.md entries to GitHub Issues |
| `/status` | egregore | Check autonomous session status |
| `/stewardship-health` | imbue | Display stewardship health dimensions for plugins |
| `/structured-review` | imbue | Structured review workflow |
| `/style-learn` | scribe | Create style profile from examples |
| `/summon` | egregore | Spawn autonomous agent session with budget |
| `/sync-capabilities` | sanctum | Detect and fix drift between plugin.json and docs |
| `/test-review` | pensive | Test quality review |
| `/test-skill` | abstract | Skill testing workflow |
| `/tome:cite` | tome | Generate formatted bibliography |
| `/tome:dig` | tome | Refine research results interactively |
| `/tome:export` | tome | Export research findings |
| `/tome:research` | tome | Run multi-source research session |
| `/unbloat` | conserve | Safe bloat remediation with interactive approval |
| `/uninstall-watchdog` | egregore | Remove crash-recovery watchdog |
| `/update-all-plugins` | leyline | Update all plugins |
| `/update-ci` | sanctum | Update pre-commit hooks and CI/CD workflows |
| `/update-dependencies` | sanctum | Update project dependencies |
| `/update-docs` | sanctum | Update documentation |
| `/update-labels` | minister | Reorganize GitHub issue labels with professional taxonomy |
| `/update-plugins` | sanctum | Audit plugin registrations + automatic performance analysis and improvement recommendations |
| `/update-tests` | sanctum | Maintain tests |
| `/update-tutorial` | sanctum | Update tutorial content |
| `/update-version` | sanctum | Bump versions |
| `/validate-hook` | abstract | Validate hook compliance |
| `/validate-plugin` | abstract | Check plugin structure |
| `/verify-plugin` | leyline | Verify plugin behavioral contract history via GitHub Attestations |

### All Agents (Alphabetical)

| Agent | Plugin | Description |
|-------|--------|-------------|
| `ai-hygiene-auditor` | conserve | Audit codebases for AI-generation warning signs |
| `architecture-reviewer` | pensive | Principal-level architecture review |
| `bloat-auditor` | conserve | Orchestrates bloat detection scans |
| `code-refiner` | pensive | Code quality refinement orchestrator |
| `code-reviewer` | pensive | Expert code review |
| `code-searcher` | tome | GitHub code search |
| `commit-agent` | sanctum | Commit message generator |
| `context-optimizer` | conserve | Context optimization |
| `continuation-agent` | conserve | Continue work from session state checkpoint |
| `dependency-updater` | sanctum | Dependency version management |
| `desktop-pilot` | phantom | Autonomous desktop control via Computer Use API |
| `discourse-scanner` | tome | Community discourse scanning |
| `doc-editor` | scribe | Interactive documentation editing |
| `doc-verifier` | scribe | QA validation using proof-of-work methodology |
| `garden-curator` | memory-palace | Digital garden maintenance |
| `git-workspace-agent` | sanctum | Repository state analyzer |
| `implementation-executor` | spec-kit | Task executor |
| `knowledge-librarian` | memory-palace | Knowledge routing |
| `knowledge-navigator` | memory-palace | Palace search |
| `literature-reviewer` | tome | Academic literature review |
| `media-recorder` | scry | Autonomous media generation for demos and GIFs |
| `meta-architect` | abstract | Plugin ecosystem design |
| `orchestrator` | egregore | Autonomous development lifecycle agent |
| `palace-architect` | memory-palace | Palace design |
| `plugin-validator` | abstract | Plugin validation |
| `pr-agent` | sanctum | PR preparation |
| `project-architect` | attune | Guides full-cycle workflow (brainstorm to plan) |
| `project-implementer` | attune | Executes implementation with TDD |
| `python-linter` | parseltongue | Strict ruff linting without bypasses |
| `python-optimizer` | parseltongue | Performance optimization |
| `python-pro` | parseltongue | Python 3.9+ expertise |
| `python-tester` | parseltongue | Testing expertise |
| `review-analyst` | imbue | Structured reviews |
| `rust-auditor` | pensive | Rust security audit |
| `sentinel` | egregore | Watchdog agent for crash recovery |
| `skill-auditor` | abstract | Skill quality audit |
| `skill-evaluator` | abstract | Skill execution evaluator |
| `skill-improver` | abstract | Implements skill improvements from observability |
| `slop-hunter` | scribe | Comprehensive AI slop detection |
| `spec-analyzer` | spec-kit | Spec consistency |
| `task-generator` | spec-kit | Task creation |
| `triz-analyst` | tome | TRIZ cross-domain analysis |
| `unbloat-remediator` | conserve | Executes safe bloat remediation |
| `workflow-improvement-analysis-agent` | sanctum | Workflow improvement analysis |
| `workflow-improvement-implementer-agent` | sanctum | Workflow improvement implementation |
| `workflow-improvement-planner-agent` | sanctum | Workflow improvement planning |
| `workflow-improvement-validator-agent` | sanctum | Workflow improvement validation |
| `workflow-recreate-agent` | sanctum | Workflow reconstruction |

### All Hooks (Alphabetical)

| Hook | Plugin | Type | Description |
|------|--------|------|-------------|
| `aggregate_learnings_daily.py` | abstract | UserPromptSubmit | Daily learning aggregation (24h cadence) with severity-based issue creation |
| `auto-star-repo.sh` | leyline | SessionStart | Auto-star the repo if not already starred |
| `config_change_audit.py` | sanctum | ConfigChange | Audit configuration changes |
| `context_warning.py` | conserve | PreToolUse | Context utilization monitoring |
| `deferred_item_sweep.py` | sanctum | Stop | Sweep session ledger and file deferred items as GitHub issues |
| `deferred_item_watcher.py` | sanctum | PostToolUse | Detect deferred items in Skill output and write to session ledger |
| `detect-git-platform.sh` | leyline | SessionStart | Detect git forge platform from remote URL |
| `fetch-recent-discussions.sh` | leyline | SessionStart | Fetch recent GitHub Discussions |
| `homeostatic_monitor.py` | abstract | PostToolUse | Stability gap monitoring, queues degrading skills for improvement |
| `local_doc_processor.py` | memory-palace | PostToolUse | Processes local docs |
| `noqa_guard.py` | leyline | PreToolUse | Block inline lint suppression directives |
| `permission_request.py` | conserve | PermissionRequest | Permission automation |
| `post-evaluation.json` | abstract | Config | Quality scoring config |
| `post_implementation_policy.py` | sanctum | SessionStart | Requires docs/tests updates |
| `pre-skill-load.json` | abstract | Config | Pre-load validation |
| `pre_compact.py` | tome | PreCompact | Checkpoint active research session |
| `pre_skill_execution.py` | abstract | PreToolUse | Skill execution tracking |
| `research_interceptor.py` | memory-palace | PreToolUse | Cache lookup before web |
| `sanitize_external_content.py` | leyline | PostToolUse | Sanitize external content for prompt injection |
| `security_pattern_check.py` | sanctum | PreToolUse | Security anti-pattern detection |
| `session_complete_notify.py` | sanctum | Stop, UserPromptSubmit | Cross-platform toast notifications and state management |
| `session_lifecycle.py` | memory-palace | Stop | Session lifecycle management |
| `session_start.py` | tome | SessionStart | Check for active research sessions |
| `session_start_hook.py` | egregore | SessionStart | Inject manifest context into new sessions |
| `session-start.sh` | conserve, imbue | SessionStart | Session initialization |
| `setup.sh` | conserve | Setup | Environment initialization |
| `setup.sh` | memory-palace | Setup | Palace directory initialization |
| `skill_execution_logger.py` | abstract | PostToolUse | Skill metrics logging |
| `stop_hook.py` | egregore | Stop | Prevent early exit while work items remain |
| `tdd_bdd_gate.py` | imbue | PreToolUse | Iron Law enforcement at write-time |
| `url_detector.py` | memory-palace | UserPromptSubmit | URL detection |
| `user-prompt-submit.sh` | imbue | UserPromptSubmit | Scope validation |
| `user_prompt_hook.py` | egregore | UserPromptSubmit | Resume orchestration after user interrupts |
| `verify_workflow_complete.py` | sanctum | Stop | End-of-session workflow verification |
| `web_research_handler.py` | memory-palace | PostToolUse | Web research processing and storage prompting |
