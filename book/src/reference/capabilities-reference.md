# Capabilities Reference

Complete listing of all skills, commands, agents, and hooks in the Claude Night Market.

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
| `architecture-review` | [pensive](../plugins/pensive.md) | Architecture assessment |
| `authentication-patterns` | [leyline](../plugins/leyline.md) | Auth flow patterns |
| `bug-review` | [pensive](../plugins/pensive.md) | Bug hunting |
| `catchup` | [imbue](../plugins/imbue.md) | Context recovery |
| `commit-messages` | [sanctum](../plugins/sanctum.md) | Conventional commits |
| `context-optimization` | [conservation](../plugins/conservation.md) | MECW principles and 50% context rule |
| `cpu-gpu-performance` | [conservation](../plugins/conservation.md) | Resource monitoring and selective testing |
| `delegation-core` | [conjure](../plugins/conjure.md) | Framework for delegation decisions |
| `diff-analysis` | [imbue](../plugins/imbue.md) | Semantic changeset analysis |
| `digital-garden-cultivator` | [memory-palace](../plugins/memory-palace.md) | Digital garden maintenance |
| `doc-consolidation` | [sanctum](../plugins/sanctum.md) | Document merging |
| `doc-updates` | [sanctum](../plugins/sanctum.md) | Documentation maintenance |
| `error-patterns` | [leyline](../plugins/leyline.md) | Standardized error handling |
| `escalation-governance` | [abstract](../plugins/abstract.md) | Model escalation decisions |
| `evaluation-framework` | [leyline](../plugins/leyline.md) | Decision thresholds |
| `evidence-logging` | [imbue](../plugins/imbue.md) | Capture methodology |
| `feature-review` | [imbue](../plugins/imbue.md) | Feature prioritization and gap analysis |
| `file-analysis` | [sanctum](../plugins/sanctum.md) | File structure analysis |
| `gemini-delegation` | [conjure](../plugins/conjure.md) | Gemini CLI integration |
| `git-workspace-review` | [sanctum](../plugins/sanctum.md) | Repo state analysis |
| `github-initiative-pulse` | [minister](../plugins/minister.md) | Initiative progress tracking |
| `hook-authoring` | [abstract](../plugins/abstract.md) | Security-first hook development |
| `hooks-eval` | [abstract](../plugins/abstract.md) | Hook security scanning |
| `knowledge-intake` | [memory-palace](../plugins/memory-palace.md) | Intake and curation |
| `knowledge-locator` | [memory-palace](../plugins/memory-palace.md) | Spatial search |
| `makefile-dogfooder` | [abstract](../plugins/abstract.md) | Makefile analysis and enhancement |
| `makefile-review` | [pensive](../plugins/pensive.md) | Makefile best practices |
| `math-review` | [pensive](../plugins/pensive.md) | Mathematical correctness |
| `mcp-code-execution` | [conservation](../plugins/conservation.md) | MCP patterns for data pipelines |
| `mecw-patterns` | [leyline](../plugins/leyline.md) | MECW implementation |
| `memory-palace-architect` | [memory-palace](../plugins/memory-palace.md) | Building virtual palaces |
| `modular-skills` | [abstract](../plugins/abstract.md) | Modular design patterns |
| `optimizing-large-skills` | [conservation](../plugins/conservation.md) | Large skill optimization |
| `pr-prep` | [sanctum](../plugins/sanctum.md) | PR preparation |
| `pr-review` | [sanctum](../plugins/sanctum.md) | PR review workflows |
| `progressive-loading` | [leyline](../plugins/leyline.md) | Dynamic content loading |
| `python-async` | [parseltongue](../plugins/parseltongue.md) | Async patterns |
| `python-packaging` | [parseltongue](../plugins/parseltongue.md) | Packaging with uv |
| `python-performance` | [parseltongue](../plugins/parseltongue.md) | Profiling and optimization |
| `python-testing` | [parseltongue](../plugins/parseltongue.md) | Pytest/TDD workflows |
| `pytest-config` | [leyline](../plugins/leyline.md) | Pytest configuration patterns |
| `qwen-delegation` | [conjure](../plugins/conjure.md) | Qwen MCP integration |
| `quota-management` | [leyline](../plugins/leyline.md) | Rate limiting and quotas |
| `release-health-gates` | [minister](../plugins/minister.md) | Release readiness checks |
| `review-core` | [imbue](../plugins/imbue.md) | Scaffolding for detailed reviews |
| `rust-review` | [pensive](../plugins/pensive.md) | Rust-specific checking |
| `scope-guard` | [imbue](../plugins/imbue.md) | Anti-overengineering |
| `service-registry` | [leyline](../plugins/leyline.md) | Service discovery patterns |
| `session-palace-builder` | [memory-palace](../plugins/memory-palace.md) | Session-specific palaces |
| `shared-patterns` | [abstract](../plugins/abstract.md) | Reusable plugin development patterns |
| `skill-authoring` | [abstract](../plugins/abstract.md) | TDD methodology for skill creation |
| `skills-eval` | [abstract](../plugins/abstract.md) | Skill quality assessment |
| `spec-writing` | [spec-kit](../plugins/spec-kit.md) | Specification authoring |
| `speckit-orchestrator` | [spec-kit](../plugins/spec-kit.md) | Workflow coordination |
| `storage-templates` | [leyline](../plugins/leyline.md) | Storage abstraction patterns |
| `structured-output` | [imbue](../plugins/imbue.md) | Formatting patterns |
| `task-planning` | [spec-kit](../plugins/spec-kit.md) | Task generation |
| `test-review` | [pensive](../plugins/pensive.md) | Test quality review |
| `test-updates` | [sanctum](../plugins/sanctum.md) | Test maintenance |
| `testing-quality-standards` | [leyline](../plugins/leyline.md) | Test quality guidelines |
| `token-conservation` | [conservation](../plugins/conservation.md) | Token usage strategies |
| `unified-review` | [pensive](../plugins/pensive.md) | Review orchestration |
| `update-readme` | [sanctum](../plugins/sanctum.md) | README modernization |
| `usage-logging` | [leyline](../plugins/leyline.md) | Telemetry tracking |
| `version-updates` | [sanctum](../plugins/sanctum.md) | Version bumping |
| `workflow-improvement` | [sanctum](../plugins/sanctum.md) | Workflow retrospectives |

### All Commands (Alphabetical)

| Command | Plugin | Description |
|---------|--------|-------------|
| `/analyze-growth` | conservation | Analyzes skill growth patterns |
| `/analyze-hook` | abstract | Analyzes hook for security/performance |
| `/analyze-skill` | abstract | Skill complexity analysis |
| `/analyze-tests` | parseltongue | Test suite health report |
| `/api-review` | pensive | API surface review |
| `/architecture-review` | pensive | Architecture assessment |
| `/bug-review` | pensive | Bug hunting review |
| `/bulletproof-skill` | abstract | Anti-rationalization workflow |
| `/catchup` | imbue | Quick context recovery |
| `/check-async` | parseltongue | Async pattern validation |
| `/commit-msg` | sanctum | Generate commit message |
| `/context-report` | abstract | Context optimization report |
| `/create-command` | abstract | Scaffold new command |
| `/create-hook` | abstract | Scaffold new hook |
| `/create-skill` | abstract | Scaffold new skill |
| `/estimate-tokens` | abstract | Token usage estimation |
| `/feature-review` | imbue | Feature prioritization |
| `/fix-issue` | sanctum | Fix GitHub issues |
| `/fix-pr` | sanctum | Address PR review comments |
| `/fix-workflow` | sanctum | Workflow retrospective |
| `/full-review` | pensive | Unified code review |
| `/garden` | memory-palace | Manage digital gardens |
| `/git-catchup` | sanctum | Git repository catchup |
| `/hooks-eval` | abstract | Hook evaluation |
| `/make-dogfood` | abstract | Makefile enhancement |
| `/makefile-review` | pensive | Makefile review |
| `/math-review` | pensive | Mathematical review |
| `/merge-docs` | sanctum | Consolidate ephemeral docs |
| `/navigate` | memory-palace | Search palaces |
| `/optimize-context` | conservation | Context optimization |
| `/palace` | memory-palace | Manage palaces |
| `/pr` | sanctum | Prepare pull request |
| `/pr-review` | sanctum | Enhanced PR review |
| `/reinstall-all-plugins` | leyline | Refresh all plugins |
| `/review` | imbue | Structured review |
| `/run-profiler` | parseltongue | Profile code execution |
| `/rust-review` | pensive | Rust-specific review |
| `/skills-eval` | abstract | Skill quality assessment |
| `/speckit.analyze` | spec-kit | Check artifact consistency |
| `/speckit.checklist` | spec-kit | Generate checklist |
| `/speckit.clarify` | spec-kit | Clarifying questions |
| `/speckit.constitution` | spec-kit | Project constitution |
| `/speckit.implement` | spec-kit | Execute tasks |
| `/speckit.plan` | spec-kit | Generate plan |
| `/speckit.specify` | spec-kit | Create specification |
| `/speckit.startup` | spec-kit | Bootstrap workflow |
| `/speckit.tasks` | spec-kit | Generate tasks |
| `/structured-review` | imbue | Structured review workflow |
| `/test-review` | pensive | Test quality review |
| `/test-skill` | abstract | Skill testing workflow |
| `/update-all-plugins` | leyline | Update all plugins |
| `/update-docs` | sanctum | Update documentation |
| `/update-readme` | sanctum | Modernize README |
| `/update-tests` | sanctum | Maintain tests |
| `/update-version` | sanctum | Bump versions |
| `/validate-hook` | abstract | Validate hook compliance |
| `/validate-plugin` | abstract | Check plugin structure |

### All Agents (Alphabetical)

| Agent | Plugin | Description |
|-------|--------|-------------|
| `architecture-reviewer` | pensive | Principal-level architecture review |
| `code-reviewer` | pensive | Expert code review |
| `commit-agent` | sanctum | Commit message generator |
| `context-optimizer` | conservation | Context optimization |
| `garden-curator` | memory-palace | Digital garden maintenance |
| `git-workspace-agent` | sanctum | Repository state analyzer |
| `implementation-executor` | spec-kit | Task executor |
| `knowledge-librarian` | memory-palace | Knowledge routing |
| `knowledge-navigator` | memory-palace | Palace search |
| `meta-architect` | abstract | Plugin ecosystem design |
| `palace-architect` | memory-palace | Palace design |
| `plugin-validator` | abstract | Plugin validation |
| `pr-agent` | sanctum | PR preparation |
| `python-optimizer` | parseltongue | Performance optimization |
| `python-pro` | parseltongue | Python 3.12+ expertise |
| `python-tester` | parseltongue | Testing expertise |
| `review-analyst` | imbue | Structured reviews |
| `rust-auditor` | pensive | Rust security audit |
| `skill-auditor` | abstract | Skill quality audit |
| `spec-analyzer` | spec-kit | Spec consistency |
| `task-generator` | spec-kit | Task creation |
| `workflow-improvement-*` | sanctum | Workflow improvement pipeline |
| `workflow-recreate-agent` | sanctum | Workflow reconstruction |

### All Hooks (Alphabetical)

| Hook | Plugin | Type | Description |
|------|--------|------|-------------|
| `bridge.after_tool_use` | conjure | PostToolUse | Suggests delegation for large output |
| `bridge.on_tool_start` | conjure | PreToolUse | Suggests delegation for large input |
| `local_doc_processor.py` | memory-palace | PostToolUse | Processes local docs |
| `post-evaluation.json` | abstract | Config | Quality scoring config |
| `post_implementation_policy.py` | sanctum | SessionStart | Requires docs/tests updates |
| `pre-pr-scope-check.sh` | imbue | Manual | Scope check before PR |
| `pre-skill-load.json` | abstract | Config | Pre-load validation |
| `research_interceptor.py` | memory-palace | PreToolUse | Cache lookup before web |
| `session-start.sh` | conservation/imbue | SessionStart | Session initialization |
| `session_complete_notify.py` | sanctum | Stop | Completion notification |
| `url_detector.py` | memory-palace | UserPromptSubmit | URL detection |
| `user-prompt-submit.sh` | imbue | UserPromptSubmit | Scope validation |
| `verify_workflow_complete.py` | sanctum | Stop | Workflow verification |
| `web_content_processor.py` | memory-palace | PostToolUse | Web content processing |
