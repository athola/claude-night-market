# Capabilities Reference

Quick lookup table of all skills, commands, agents, and hooks in the Claude Night Market.

**For full flag documentation and workflow examples**: See [Capabilities Reference Details](capabilities-reference-details.md).

## Quick Reference Index

### All Skills (Alphabetical)

| Skill | Plugin | Description |
|-------|--------|-------------|
| `api-review` | [pensive](../plugins/pensive.md) | API surface evaluation |
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
| `agent-teams` | [conjure](../plugins/conjure.md) | Coordinate Claude Code Agent Teams through filesystem-based protocol |
| `architecture-aware-init` | [attune](../plugins/attune.md) | Architecture-aware project initialization with research |
| `architecture-review` | [pensive](../plugins/pensive.md) | Architecture assessment |
| `authentication-patterns` | [leyline](../plugins/leyline.md) | Auth flow patterns |
| `bloat-detector` | [conserve](../plugins/conserve.md) | Detection algorithms for dead code, God classes, documentation duplication |
| `browser-recording` | [scry](../plugins/scry.md) | Playwright browser recordings |
| `bug-review` | [pensive](../plugins/pensive.md) | Bug hunting |
| `catchup` | [imbue](../plugins/imbue.md) | Context recovery |
| `clear-context` | [conserve](../plugins/conserve.md) | Auto-clear workflow with session state persistence |
| `code-quality-principles` | [conserve](../plugins/conserve.md) | Core principles for AI-assisted code quality |
| `commit-messages` | [sanctum](../plugins/sanctum.md) | Conventional commits |
| `context-optimization` | [conserve](../plugins/conserve.md) | MECW principles and 50% context rule |
| `cpu-gpu-performance` | [conserve](../plugins/conserve.md) | Resource monitoring and selective testing |
| `decisive-action` | [conserve](../plugins/conserve.md) | Decisive action patterns for efficient workflows |
| `delegation-core` | [conjure](../plugins/conjure.md) | Framework for delegation decisions |
| `diff-analysis` | [imbue](../plugins/imbue.md) | Semantic changeset analysis |
| `digital-garden-cultivator` | [memory-palace](../plugins/memory-palace.md) | Digital garden maintenance |
| `doc-consolidation` | [sanctum](../plugins/sanctum.md) | Document merging |
| `doc-generator` | [scribe](../plugins/scribe.md) | Generate and remediate documentation |
| `doc-updates` | [sanctum](../plugins/sanctum.md) | Documentation maintenance |
| `error-patterns` | [leyline](../plugins/leyline.md) | Standardized error handling |
| `escalation-governance` | [abstract](../plugins/abstract.md) | Model escalation decisions |
| `evaluation-framework` | [leyline](../plugins/leyline.md) | Decision thresholds |
| `evidence-logging` | [imbue](../plugins/imbue.md) | Capture methodology |
| `feature-review` | [imbue](../plugins/imbue.md) | Feature prioritization and gap analysis |
| `file-analysis` | [sanctum](../plugins/sanctum.md) | File structure analysis |
| `do-issue` | [sanctum](../plugins/sanctum.md) | GitHub issue resolution workflow |
| `fpf-review` | [pensive](../plugins/pensive.md) | FPF architecture review (Functional/Practical/Foundation) |
| `gemini-delegation` | [conjure](../plugins/conjure.md) | Gemini CLI integration |
| `gif-generation` | [scry](../plugins/scry.md) | GIF processing and optimization |
| `git-platform` | [leyline](../plugins/leyline.md) | Cross-platform git forge detection and command mapping |
| `git-workspace-review` | [sanctum](../plugins/sanctum.md) | Repo state analysis |
| `github-initiative-pulse` | [minister](../plugins/minister.md) | Initiative progress tracking |
| `hook-authoring` | [abstract](../plugins/abstract.md) | Security-first hook development |
| `hooks-eval` | [abstract](../plugins/abstract.md) | Hook security scanning |
| `knowledge-intake` | [memory-palace](../plugins/memory-palace.md) | Intake and curation |
| `knowledge-locator` | [memory-palace](../plugins/memory-palace.md) | Spatial search |
| `makefile-dogfooder` | [abstract](../plugins/abstract.md) | Makefile analysis and enhancement |
| `makefile-generation` | [attune](../plugins/attune.md) | Generate language-specific Makefiles |
| `makefile-review` | [pensive](../plugins/pensive.md) | Makefile best practices |
| `math-review` | [pensive](../plugins/pensive.md) | Mathematical correctness |
| `mcp-code-execution` | [conserve](../plugins/conserve.md) | MCP patterns for data pipelines |
| `methodology-curator` | [abstract](../plugins/abstract.md) | Surface expert frameworks for skill development |
| `media-composition` | [scry](../plugins/scry.md) | Multi-source media stitching |
| `mission-orchestrator` | [attune](../plugins/attune.md) | Unified lifecycle orchestrator for project development |
| `mecw-patterns` | [leyline](../plugins/leyline.md) | MECW implementation |
| `memory-palace-architect` | [memory-palace](../plugins/memory-palace.md) | Building virtual palaces |
| `modular-skills` | [abstract](../plugins/abstract.md) | Modular design patterns |
| `optimizing-large-skills` | [conserve](../plugins/conserve.md) | Large skill optimization |
| `performance-optimization` | [abstract](../plugins/abstract.md) | Progressive loading, token budgeting, and context-aware content delivery |
| `code-refinement` | [pensive](../plugins/pensive.md) | Duplication, algorithms, and clean code analysis |
| `damage-control` | [leyline](../plugins/leyline.md) | Agent-level error recovery for multi-agent coordination |
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
| `qwen-delegation` | [conjure](../plugins/conjure.md) | Qwen MCP integration |
| `quota-management` | [leyline](../plugins/leyline.md) | Rate limiting and quotas |
| `release-health-gates` | [minister](../plugins/minister.md) | Release readiness checks |
| `review-chamber` | [memory-palace](../plugins/memory-palace.md) | PR review knowledge capture and retrieval |
| `response-compression` | [conserve](../plugins/conserve.md) | Response compression patterns |
| `review-core` | [imbue](../plugins/imbue.md) | Scaffolding for detailed reviews |
| `risk-classification` | [leyline](../plugins/leyline.md) | Inline 4-tier risk classification for agent tasks |
| `rigorous-reasoning` | [imbue](../plugins/imbue.md) | Anti-sycophancy guardrails |
| `rule-catalog` | [hookify](../plugins/hookify.md) | Pre-built behavioral rule templates |
| `rust-review` | [pensive](../plugins/pensive.md) | Rust-specific checking |
| `safety-critical-patterns` | [pensive](../plugins/pensive.md) | NASA Power of 10 rules for robust code |
| `scope-guard` | [imbue](../plugins/imbue.md) | Anti-overengineering |
| `service-registry` | [leyline](../plugins/leyline.md) | Service discovery patterns |
| `session-management` | [sanctum](../plugins/sanctum.md) | Session naming, checkpointing, and resume strategies |
| `session-palace-builder` | [memory-palace](../plugins/memory-palace.md) | Session-specific palaces |
| `shared-patterns` | [abstract](../plugins/abstract.md) | Reusable plugin development patterns |
| `shell-review` | [pensive](../plugins/pensive.md) | Shell script auditing for safety and portability |
| `slop-detector` | [scribe](../plugins/scribe.md) | Detect AI-generated content markers |
| `smart-sourcing` | [conserve](../plugins/conserve.md) | Balance accuracy with token efficiency |
| `skill-authoring` | [abstract](../plugins/abstract.md) | TDD methodology for skill creation |
| `skills-eval` | [abstract](../plugins/abstract.md) | Skill quality assessment |
| `spec-writing` | [spec-kit](../plugins/spec-kit.md) | Specification authoring |
| `speckit-orchestrator` | [spec-kit](../plugins/spec-kit.md) | Workflow coordination |
| `storage-templates` | [leyline](../plugins/leyline.md) | Storage abstraction patterns |
| `style-learner` | [scribe](../plugins/scribe.md) | Extract writing style from exemplar text |
| `structured-output` | [imbue](../plugins/imbue.md) | Formatting patterns |
| `task-planning` | [spec-kit](../plugins/spec-kit.md) | Task generation |
| `test-review` | [pensive](../plugins/pensive.md) | Test quality review |
| `subagent-testing` | [abstract](../plugins/abstract.md) | Testing patterns for subagent interactions |
| `test-updates` | [sanctum](../plugins/sanctum.md) | Test maintenance |
| `testing-quality-standards` | [leyline](../plugins/leyline.md) | Test quality guidelines |
| `token-conservation` | [conserve](../plugins/conserve.md) | Token usage strategies |
| `tutorial-updates` | [sanctum](../plugins/sanctum.md) | Tutorial maintenance and updates |
| `unified-review` | [pensive](../plugins/pensive.md) | Review orchestration |
| `update-readme` | [sanctum](../plugins/sanctum.md) | README modernization |
| `usage-logging` | [leyline](../plugins/leyline.md) | Telemetry tracking |
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
| `/ai-hygiene-audit` | conserve | Audit codebase for AI-generated code quality issues (vibe coding, Tab bloat, slop) |
| `/aggregate-logs` | abstract | Generate LEARNINGS.md from skill execution logs |
| `/analyze-growth` | conserve | Analyzes skill growth patterns |
| `/analyze-hook` | abstract | Analyzes hook for security/performance |
| `/bloat-scan` | conserve | Progressive bloat detection (3-tier scan) |
| `/analyze-skill` | abstract | Skill complexity analysis |
| `/analyze-tests` | parseltongue | Test suite health report |
| `/api-review` | pensive | API surface review |
| `/attune:brainstorm` | attune | Brainstorm project ideas using Socratic questioning |
| `/attune:execute` | attune | Execute implementation tasks systematically |
| `/attune:init` | attune | Initialize new project with development infrastructure |
| `/attune:mission` | attune | Run full project lifecycle as a single mission with state detection and recovery |
| `/attune:blueprint` | attune | Plan architecture and break down tasks |
| `/attune:specify` | attune | Create detailed specifications from brainstorm |
| `/attune:upgrade-project` | attune | Add or update configurations in existing project |
| `/attune:validate` | attune | Validate project structure against best practices |
| `/attune:war-room` | attune | Multi-LLM expert deliberation with reversibility-based routing |
| `/architecture-review` | pensive | Architecture assessment |
| `/bug-review` | pensive | Bug hunting review |
| `/bulletproof-skill` | abstract | Anti-rationalization workflow |
| `/catchup` | imbue | Quick context recovery |
| `/check-async` | parseltongue | Async pattern validation |
| `/close-issue` | minister | Analyze if GitHub issues can be closed based on commits |
| `/commit-msg` | sanctum | Generate commit message |
| `/context-report` | abstract | Context optimization report |
| `/create-tag` | sanctum | Create git tags for releases |
| `/create-command` | abstract | Scaffold new command |
| `/create-hook` | abstract | Scaffold new hook |
| `/create-issue` | minister | Create GitHub issue with labels and references |
| `/create-skill` | abstract | Scaffold new skill |
| `/doc-generate` | scribe | Generate new documentation |
| `/doc-polish` | scribe | Clean up AI-generated content |
| `/doc-verify` | scribe | Validate documentation claims with proof-of-work |
| `/estimate-tokens` | abstract | Token usage estimation |
| `/evaluate-skill` | abstract | Evaluate skill execution quality |
| `/feature-review` | imbue | Feature prioritization |
| `/do-issue` | sanctum | Fix GitHub issues |
| `/fix-pr` | sanctum | Address PR review comments |
| `/fix-workflow` | sanctum | Workflow retrospective with automatic improvement context gathering |
| `/full-review` | pensive | Unified code review |
| `/garden` | memory-palace | Manage digital gardens |
| `/git-catchup` | sanctum | Git repository catchup |
| `/hookify` | hookify | Create behavioral rules to prevent unwanted actions |
| `/hookify:configure` | hookify | Interactive rule enable/disable interface |
| `/hookify:help` | hookify | Display hookify help and documentation |
| `/hookify:install` | hookify | Install hookify rule from catalog |
| `/hookify:list` | hookify | List all hookify rules with status |
| `/hooks-eval` | abstract | Hook evaluation |
| `/improve-skills` | abstract | Auto-improve skills from observability data |
| `/make-dogfood` | abstract | Makefile enhancement |
| `/makefile-review` | pensive | Makefile review |
| `/math-review` | pensive | Mathematical review |
| `/merge-docs` | sanctum | Consolidate ephemeral docs |
| `/navigate` | memory-palace | Search palaces |
| `/optimize-context` | conserve | Context optimization |
| `/palace` | memory-palace | Manage palaces |
| `/plugin-review` | abstract | Comprehensive plugin architecture review |
| `/pr` | sanctum | Prepare pull request |
| `/prepare-pr` | sanctum | Complete PR preparation with updates and validation |
| `/promote-discussions` | abstract | Promote highly-voted community learnings from Discussions to Issues |
| `/pr-review` | sanctum | Enhanced PR review |
| `/record-browser` | scry | Record browser session |
| `/record-terminal` | scry | Create terminal recording |
| `/reinstall-all-plugins` | leyline | Refresh all plugins |
| `/resolve-threads` | sanctum | Resolve PR review threads |
| `/review-room` | memory-palace | Manage PR review knowledge in palaces |
| `/run-profiler` | parseltongue | Profile code execution |
| `/rust-review` | pensive | Rust-specific review |
| `/shell-review` | pensive | Shell script safety and portability review |
| `/skill-history` | pensive | View recent skill executions with context |
| `/skill-logs` | memory-palace | View and manage skill execution memories |
| `/skill-review` | pensive | Analyze skill metrics and stability gaps |
| `/slop-scan` | scribe | Scan files for AI slop markers |
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
| `/structured-review` | imbue | Structured review workflow |
| `/style-learn` | scribe | Create style profile from examples |
| `/test-review` | pensive | Test quality review |
| `/test-skill` | abstract | Skill testing workflow |
| `/unbloat` | conserve | Safe bloat remediation with interactive approval |
| `/update-all-plugins` | leyline | Update all plugins |
| `/update-dependencies` | sanctum | Update project dependencies |
| `/update-docs` | sanctum | Update documentation |
| `/update-labels` | minister | Reorganize GitHub issue labels with professional taxonomy |
| `/update-plugins` | sanctum | Audit plugin registrations + automatic performance analysis and improvement recommendations |
| `/update-readme` | sanctum | Modernize README |
| `/update-tests` | sanctum | Maintain tests |
| `/update-tutorial` | sanctum | Update tutorial content |
| `/update-version` | sanctum | Bump versions |
| `/validate-hook` | abstract | Validate hook compliance |
| `/validate-plugin` | abstract | Check plugin structure |

### All Agents (Alphabetical)

| Agent | Plugin | Description |
|-------|--------|-------------|
| `ai-hygiene-auditor` | conserve | Audit codebases for AI-generation warning signs |
| `architecture-reviewer` | pensive | Principal-level architecture review |
| `bloat-auditor` | conserve | Orchestrates bloat detection scans |
| `code-reviewer` | pensive | Expert code review |
| `commit-agent` | sanctum | Commit message generator |
| `context-optimizer` | conserve | Context optimization |
| `continuation-agent` | conserve | Continue work from session state checkpoint |
| `doc-editor` | scribe | Interactive documentation editing |
| `doc-verifier` | scribe | QA validation using proof-of-work methodology |
| `dependency-updater` | sanctum | Dependency version management |
| `garden-curator` | memory-palace | Digital garden maintenance |
| `git-workspace-agent` | sanctum | Repository state analyzer |
| `implementation-executor` | spec-kit | Task executor |
| `knowledge-librarian` | memory-palace | Knowledge routing |
| `knowledge-navigator` | memory-palace | Palace search |
| `media-recorder` | scry | Autonomous media generation for demos and GIFs |
| `meta-architect` | abstract | Plugin ecosystem design |
| `palace-architect` | memory-palace | Palace design |
| `plugin-validator` | abstract | Plugin validation |
| `pr-agent` | sanctum | PR preparation |
| `project-architect` | attune | Guides full-cycle workflow (brainstorm → plan) |
| `project-implementer` | attune | Executes implementation with TDD |
| `python-linter` | parseltongue | Strict ruff linting without bypasses |
| `python-optimizer` | parseltongue | Performance optimization |
| `python-pro` | parseltongue | Python 3.12+ expertise |
| `python-tester` | parseltongue | Testing expertise |
| `review-analyst` | imbue | Structured reviews |
| `rust-auditor` | pensive | Rust security audit |
| `skill-auditor` | abstract | Skill quality audit |
| `skill-evaluator` | abstract | Skill execution evaluator |
| `skill-improver` | abstract | Implements skill improvements from observability |
| `slop-hunter` | scribe | Comprehensive AI slop detection |
| `spec-analyzer` | spec-kit | Spec consistency |
| `task-generator` | spec-kit | Task creation |
| `unbloat-remediator` | conserve | Executes safe bloat remediation |
| `workflow-improvement-*` | sanctum | Workflow improvement pipeline |
| `workflow-recreate-agent` | sanctum | Workflow reconstruction |

### All Hooks (Alphabetical)

| Hook | Plugin | Type | Description |
|------|--------|------|-------------|
| `bridge.after_tool_use` | conjure | PostToolUse | Suggests delegation for large output |
| `bridge.on_tool_start` | conjure | PreToolUse | Suggests delegation for large input |
| `context_warning.py` | conserve | PreToolUse | Context utilization monitoring |
| `detect-git-platform.sh` | leyline | SessionStart | Detect git forge platform from remote URL |
| `local_doc_processor.py` | memory-palace | PostToolUse | Processes local docs |
| `permission_request.py` | conserve | PermissionRequest | Permission automation |
| `post-evaluation.json` | abstract | Config | Quality scoring config |
| `post_implementation_policy.py` | sanctum | SessionStart | Requires docs/tests updates |
| `pre-skill-load.json` | abstract | Config | Pre-load validation |
| `homeostatic_monitor.py` | abstract | PostToolUse | Stability gap monitoring, queues degrading skills for improvement |
| `pre_skill_execution.py` | abstract | PreToolUse | Skill execution tracking |
| `research_interceptor.py` | memory-palace | PreToolUse | Cache lookup before web |
| `security_pattern_check.py` | sanctum | PreToolUse | Security anti-pattern detection |
| `session_complete_notify.py` | sanctum | Stop | Cross-platform toast notifications |
| `session-start.sh` | conserve/imbue | SessionStart | Session initialization |
| `skill_execution_logger.py` | abstract | PostToolUse | Skill metrics logging |
| `skill_tracker_pre.py` | memory-palace | PreToolUse | Skill execution start tracking |
| `skill_tracker_post.py` | memory-palace | PostToolUse | Skill execution completion |
| `tdd_bdd_gate.py` | imbue | PreToolUse | Iron Law enforcement at write-time |
| `url_detector.py` | memory-palace | UserPromptSubmit | URL detection |
| `user-prompt-submit.sh` | imbue | UserPromptSubmit | Scope validation |
| `verify_workflow_complete.py` | sanctum | Stop | End-of-session workflow verification |
| `web_content_processor.py` | memory-palace | PostToolUse | Web content processing |
