# Capabilities Reference

Quick lookup table of all skills, commands, agents,
and hooks in the Claude Night Market.

**For full flag documentation and workflow examples**:
See [Capabilities Reference Details](capabilities-reference-details.md).

## Quick Reference Index

### All Workflows (Alphabetical)

Dynamic-workflow scripts under each plugin's `workflows/`. Discovery
is by convention, so none is declared in `plugin.json`. Invoke as
`/plugin-name:workflow-name`, where the name comes from the script's
`meta.name`.

A workflow only runs when it is asked for. None starts implicitly.

| Workflow | Plugin | Description |
|----------|--------|-------------|
| `atlas` | [cartograph](../plugins/cartograph.md) | Generate the architecture, dependency, data-flow and community diagrams of one codebase in parallel and report where they disagree |
| `bloat-sweep` | [conserve](../plugins/conserve.md) | Run the deep bloat scan across several code areas at once and consolidate the findings that span more than one |
| `capture-set` | [scry](../plugins/scry.md) | Capture several terminal or browser recordings in parallel and report which flows failed without stopping the rest |
| `doc-sweep` | [scribe](../plugins/scribe.md) | Review documents through four independent layers, from identity leaks and hallucinated paths down to sentence-level slop |
| `evidence-sweep` | [imbue](../plugins/imbue.md) | Check each completion claim in a change against the evidence offered for it, and report the ones running on assertion alone |
| `fix-workflow-analysis` | [sanctum](../plugins/sanctum.md) | Recreate a workflow slice, generate improvement options with trade-offs, and converge on one plan with acceptance criteria |
| `gate-audit` | [egregore](../plugins/egregore.md) | Check each pipeline gate for whether it can return a failing verdict, and prove each finding with an input that walks past it |
| `initiative-pulse` | [minister](../plugins/minister.md) | Gather delivery health for several GitHub milestones in parallel and roll them up into one programme view |
| `judge-panel` | [herald](../plugins/herald.md) | Judge one completion claim through three independent lenses and report the verdict with any dissent |
| `knowledge-extract` | [gauntlet](../plugins/gauntlet.md) | Extract and enrich the gauntlet knowledge base one subsystem per agent, then merge into a single corpus |
| `palace-sweep` | [memory-palace](../plugins/memory-palace.md) | Ask one question of every memory palace in parallel and rank the answers, including the ones filed under an unexpected domain |
| `paradigm-panel` | [archetypes](../plugins/archetypes.md) | Score candidate architecture paradigms independently against one requirement set and return a ranked comparison |
| `plugin-health` | [leyline](../plugins/leyline.md) | Check every plugin against the shared leyline contracts in parallel, then report contracts that no plugin satisfies |
| `provider-sweep` | [conjure](../plugins/conjure.md) | Ask every delegation provider in parallel whether this machine can call it, and separate a missing binary from a rejected credential |
| `python-sweep` | [parseltongue](../plugins/parseltongue.md) | Run the lint, type, performance and test specialists over the same Python in parallel and merge their findings |
| `quality-bench` | [oracle](../plugins/oracle.md) | Score a set of skills through the oracle in parallel and report each score against the distribution rather than alone |
| `research` | [tome](../plugins/tome.md) | Fan out one research question across tome channels and merge the findings into a ranked, per-channel report |
| `rule-sweep` | [hookify](../plugins/hookify.md) | Check each catalog rule against the codebase it governs and report the ones that no longer describe it |
| `skill-audit` | [abstract](../plugins/abstract.md) | Audit a set of skills across four independent quality dimensions, then verify each finding before reporting it |
| `skill-library` | [attune](../plugins/attune.md) | Discover what a project knows, author one skill per topic in parallel, and review each adversarially |
| `spec-review` | [spec-kit](../plugins/spec-kit.md) | Read one specification through four independent lenses and report what must be settled before planning starts |
| `surface-check` | [phantom](../plugins/phantom.md) | Verify each desktop control surface independently so one failing surface does not hide the state of the others |
| `unified-review` | [pensive](../plugins/pensive.md) | Review changed code across dimensions, adversarially verify each finding, and return one ranked list |

### All Skills (Alphabetical)

| Skill | Plugin | Description |
|-------|--------|-------------|
| `action-first-output` | [conserve](../plugins/conserve.md) | Action-first output shaping |
| `additive-bias-defense` | [leyline](../plugins/leyline.md) | Scrutiny questions to challenge unnecessary additions |
| `agent-expenditure` | [conserve](../plugins/conserve.md) | Per-agent token usage tracking |
| `agent-teams` | [conjure](../plugins/conjure.md) | Coordinate Claude Code Agent Teams through filesystem-based protocol |
| `api-review` | [pensive](../plugins/pensive.md) | API surface evaluation |
| `architecture-aware-init` | [attune](../plugins/attune.md) | Architecture-aware project initialization with research |
| `architecture-diagram` | [cartograph](../plugins/cartograph.md) | Component relationship diagrams |
| `architecture-paradigm-client-server` | [archetypes](../plugins/archetypes.md) | Client-server communication |
| `architecture-paradigm-cqrs-es` | [archetypes](../plugins/archetypes.md) | CQRS and Event Sourcing |
| `architecture-paradigm-domain-driven` | [archetypes](../plugins/archetypes.md) | Modeling a business in its own language |
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
| `assisted-mastery` | [imbue](../plugins/imbue.md) | Assistance-dilemma resolution: visible reasoning, tradeoff surfacing, and fading help to build judgment |
| `authentication-patterns` | [leyline](../plugins/leyline.md) | Auth flow patterns |
| `blast-radius` | [pensive](../plugins/pensive.md) | Code change blast radius analysis with risk scoring |
| `bloat-detector` | [conserve](../plugins/conserve.md) | Detection algorithms for dead code, God classes, documentation duplication |
| `browser-recording` | [scry](../plugins/scry.md) | Playwright browser recordings |
| `bug-review` | [pensive](../plugins/pensive.md) | Bug hunting |
| `call-chain` | [cartograph](../plugins/cartograph.md) | Trace execution paths through code knowledge graph |
| `catchup` | [imbue](../plugins/imbue.md) | Context recovery |
| `challenge` | [gauntlet](../plugins/gauntlet.md) | Adaptive difficulty challenge session for codebase knowledge testing |
| `class-diagram` | [cartograph](../plugins/cartograph.md) | Class and interface diagrams |
| `clear-context` | [conserve](../plugins/conserve.md) | Auto-clear workflow with session state persistence |
| `code-communities` | [cartograph](../plugins/cartograph.md) | Detect architectural clusters via community detection |
| `code-quality-principles` | [conserve](../plugins/conserve.md) | Core principles for AI-assisted code quality |
| `code-refinement` | [pensive](../plugins/pensive.md) | Duplication, algorithms, and clean code analysis |
| `code-search` | [tome](../plugins/tome.md) | GitHub implementation search |
| `codex-delegation` | [conjure](../plugins/conjure.md) | OpenAI Codex CLI (codex exec) integration |
| `commit-messages` | [sanctum](../plugins/sanctum.md) | Conventional commits |
| `compression-strategy` | [conserve](../plugins/conserve.md) | Context compression analysis and recommendations |
| `computer-control` | [phantom](../plugins/phantom.md) | Desktop automation via Claude's vision and action API |
| `content-sanitization` | [leyline](../plugins/leyline.md) | External content sanitization |
| `context-optimization` | [conserve](../plugins/conserve.md) | MECW principles and 50% context rule |
| `cpu-gpu-performance` | [conserve](../plugins/conserve.md) | Resource monitoring and selective testing |
| `curate` | [gauntlet](../plugins/gauntlet.md) | Add or edit knowledge annotations with tribal context |
| `damage-control` | [leyline](../plugins/leyline.md) | Agent crash recovery and state reconciliation |
| `data-flow` | [cartograph](../plugins/cartograph.md) | Data movement diagrams |
| `decision-journal` | [leyline](../plugins/leyline.md) | Contract for the project decision journal (tradeoffs and lessons-learned logs) |
| `decisive-action` | [conserve](../plugins/conserve.md) | Decisive action patterns for efficient workflows |
| `deferred-capture` | [leyline](../plugins/leyline.md) | Contract for unified deferred-item capture across plugins |
| `delegation-core` | [conjure](../plugins/conjure.md) | Framework for delegation decisions |
| `dependency-graph` | [cartograph](../plugins/cartograph.md) | Import and dependency diagrams |
| `dependency-verification` | [imbue](../plugins/imbue.md) | Package-hallucination and slopsquat defense: verifies a package exists before install |
| `diff-analysis` | [imbue](../plugins/imbue.md) | Semantic changeset analysis |
| `dig` | [tome](../plugins/tome.md) | Interactive research refinement |
| `digital-garden-cultivator` | [memory-palace](../plugins/memory-palace.md) | Digital garden maintenance |
| `discourse` | [tome](../plugins/tome.md) | Community discussion scanning |
| `do-issue` | [sanctum](../plugins/sanctum.md) | GitHub issue resolution workflow |
| `doc-consolidation` | [sanctum](../plugins/sanctum.md) | Document merging |
| `doc-generator` | [scribe](../plugins/scribe.md) | Generate and remediate documentation |
| `doc-importer` | [scribe](../plugins/scribe.md) | Import external documents to markdown |
| `doc-updates` | [sanctum](../plugins/sanctum.md) | Documentation maintenance |
| `document-conversion` | [leyline](../plugins/leyline.md) | Universal document-to-markdown conversion |
| `dora-metrics` | [minister](../plugins/minister.md) | Compute DORA delivery-performance metrics with tier classification |
| `dorodango` | [attune](../plugins/attune.md) | Iterative code polishing workflow |
| `elegant-code` | [conserve](../plugins/conserve.md) | Minimal-code decision ladder with full safety, edge, and negative-case coverage |
| `error-patterns` | [leyline](../plugins/leyline.md) | Standardized error handling |
| `escalation-governance` | [abstract](../plugins/abstract.md) | Model escalation decisions |
| `evaluation-framework` | [leyline](../plugins/leyline.md) | Decision thresholds |
| `export` | [tome](../plugins/tome.md) | Export research findings for knowledge-intake |
| `extract` | [gauntlet](../plugins/gauntlet.md) | Analyze codebase and build a knowledge base |
| `feature-review` | [imbue](../plugins/imbue.md) | Feature prioritization with RICE/WSJF/Kano scoring and optional research enrichment via tome (`--research`) |
| `file-analysis` | [sanctum](../plugins/sanctum.md) | File structure analysis |
| `friction-detector` | [abstract](../plugins/abstract.md) | Detect friction signals and graduate recurring patterns into rules |
| `gauntlet-curate` | [gauntlet](../plugins/gauntlet.md) | Research and refresh the problem bank; surveys coverage gaps and proposes YAML-valid entries |
| `gemini-delegation` | [conjure](../plugins/conjure.md) | Gemini CLI integration |
| `gif-generation` | [scry](../plugins/scry.md) | GIF processing and optimization |
| `git-platform` | [leyline](../plugins/leyline.md) | Cross-platform git forge detection and command mapping |
| `git-workspace-review` | [sanctum](../plugins/sanctum.md) | Repo state analysis |
| `github-initiative-pulse` | [minister](../plugins/minister.md) | Initiative progress tracking |
| `glimmer-delegation` | [conjure](../plugins/conjure.md) | Muse Glimmer served locally through ollama, no quota |
| `glm-delegation` | [conjure](../plugins/conjure.md) | Z.ai GLM-5.x via Anthropic-compatible endpoint swap |
| `graduated-implementation` | [imbue](../plugins/imbue.md) | Bounded start then ramp the next increment's ambition only on demonstrated competence of the prior one |
| `graph-build` | [gauntlet](../plugins/gauntlet.md) | Build or update the code knowledge graph |
| `graph-search` | [gauntlet](../plugins/gauntlet.md) | FTS5 search of the code knowledge graph |
| `harden` | [pensive](../plugins/pensive.md) | Active codebase hardening with NIST/CWE-cited findings and concrete remediation proposals |
| `hook-authoring` | [abstract](../plugins/abstract.md) | Security-first hook development |
| `hook-scope-guide` | [abstract](../plugins/abstract.md) | Decide where to place hooks (plugin/project/global) |
| `hooks-eval` | [abstract](../plugins/abstract.md) | Hook security scanning |
| `ideate` | [tome](../plugins/tome.md) | Diverse ideation methods with category-spanning selection and rotation |
| `install-watchdog` | [egregore](../plugins/egregore.md) | Install crash-recovery watchdog |
| `justify` | [imbue](../plugins/imbue.md) | Anti-additive-bias change audit |
| `karpathy-principles` | [imbue](../plugins/imbue.md) | Compact four-principle synthesis for LLM coding pitfalls |
| `knowledge-intake` | [memory-palace](../plugins/memory-palace.md) | Intake and curation |
| `knowledge-locator` | [memory-palace](../plugins/memory-palace.md) | Spatial search |
| `latent-space-engineering` | [imbue](../plugins/imbue.md) | Agent behavior shaping through instruction framing |
| `loop-optimization` | [leyline](../plugins/leyline.md) | Hand-vs-compiler decision rule for loop transforms |
| `makefile-generation` | [attune](../plugins/attune.md) | Generate language-specific Makefiles |
| `makefile-review` | [pensive](../plugins/pensive.md) | Makefile best practices |
| `markdown-formatting` | [leyline](../plugins/leyline.md) | Line wrapping and style conventions |
| `math-review` | [pensive](../plugins/pensive.md) | Mathematical correctness |
| `mcp-code-execution` | [conserve](../plugins/conserve.md) | MCP patterns for data pipelines |
| `media-composition` | [scry](../plugins/scry.md) | Multi-source media stitching |
| `memory-clarity-probe` | [memory-palace](../plugins/memory-palace.md) | Memory clarity assessment via anchor questions |
| `memory-palace-architect` | [memory-palace](../plugins/memory-palace.md) | Building virtual palaces |
| `metacognitive-self-mod` | [abstract](../plugins/abstract.md) | Hyperagents self-improvement analysis |
| `methodology-curator` | [abstract](../plugins/abstract.md) | Surface expert frameworks for skill development |
| `minimax-delegation` | [conjure](../plugins/conjure.md) | MiniMax CLI (mmx) integration |
| `mission-orchestrator` | [attune](../plugins/attune.md) | Unified lifecycle orchestrator for project development |
| `modular-skills` | [abstract](../plugins/abstract.md) | Modular design patterns |
| `muse-delegation` | [conjure](../plugins/conjure.md) | Meta Muse Code CLI (muse exec) integration |
| `onboard` | [gauntlet](../plugins/gauntlet.md) | Guided five-stage onboarding path through a codebase |
| `opencode-delegation` | [conjure](../plugins/conjure.md) | OpenCode CLI (opencode run) integration |
| `palace-diagram` | [memory-palace](../plugins/memory-palace.md) | Visual palace structure diagrams |
| `palace-index-curator` | [memory-palace](../plugins/memory-palace.md) | Web-capture index curation |
| `papers` | [tome](../plugins/tome.md) | Academic literature search |
| `performance-review` | [pensive](../plugins/pensive.md) | Time and space complexity hotspot detection |
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
| `provider-setup` | [conjure](../plugins/conjure.md) | Reports, installs and records which delegation CLIs this machine can call |
| `pytest-config` | [leyline](../plugins/leyline.md) | Pytest configuration patterns |
| `python-async` | [parseltongue](../plugins/parseltongue.md) | Async patterns |
| `python-packaging` | [parseltongue](../plugins/parseltongue.md) | Packaging with uv |
| `python-performance` | [parseltongue](../plugins/parseltongue.md) | Profiling and optimization |
| `python-testing` | [parseltongue](../plugins/parseltongue.md) | Pytest/TDD workflows |
| `quality-gate` | [egregore](../plugins/egregore.md) | Pre-merge quality validation for autonomous sessions |
| `quota-management` | [leyline](../plugins/leyline.md) | Rate limiting and quotas |
| `qwen-delegation` | [conjure](../plugins/conjure.md) | Qwen MCP integration |
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
| `sem-integration` | [leyline](../plugins/leyline.md) | Semantic diff CLI detection and fallback |
| `service-registry` | [leyline](../plugins/leyline.md) | Service discovery patterns |
| `session-handoff` | [memory-palace](../plugins/memory-palace.md) | Typed session handoff units and on-demand recall |
| `session-management` | [sanctum](../plugins/sanctum.md) | Session naming, checkpointing, and resume strategies |
| `session-palace-builder` | [memory-palace](../plugins/memory-palace.md) | Session-specific palaces |
| `session-replay` | [scribe](../plugins/scribe.md) | Convert session JSONL into GIF/MP4/WebM replays via VHS |
| `session-to-post` | [scribe](../plugins/scribe.md) | Convert sessions into shareable blog posts or case studies |
| `setup` | [oracle](../plugins/oracle.md) | Install and configure the oracle ONNX inference daemon |
| `shared-patterns` | [abstract](../plugins/abstract.md) | Reusable plugin development patterns |
| `shell-review` | [pensive](../plugins/pensive.md) | Shell script auditing for safety and portability |
| `simplified-technical-english` | [scribe](../plugins/scribe.md) | Apply an ASD-STE100-derived register to operator and procedural text |
| `skill-authoring` | [abstract](../plugins/abstract.md) | TDD methodology for skill creation |
| `skill-graph-audit` | [abstract](../plugins/abstract.md) | Map Skill() refs across plugins; detect hubs, isolates, dangling targets |
| `skill-library-mission` | [attune](../plugins/attune.md) | Build a project skill library via discovery, parallel authoring, and review |
| `skills-eval` | [abstract](../plugins/abstract.md) | Skill quality assessment |
| `slop-detector` | [scribe](../plugins/scribe.md) | Detect AI-generated content markers |
| `smart-sourcing` | [conserve](../plugins/conserve.md) | Balance accuracy with token efficiency |
| `spec-writing` | [spec-kit](../plugins/spec-kit.md) | Specification authoring |
| `speckit-orchestrator` | [spec-kit](../plugins/spec-kit.md) | Workflow coordination |
| `stack-create` | [sanctum](../plugins/sanctum.md) | Initialize a branch stack from a multi-step plan |
| `stack-mode` | [sanctum](../plugins/sanctum.md) | Shared stack detection and multi-PR iteration contract for `/pr-review --stack` and `/fix-pr --stack` |
| `stack-push` | [sanctum](../plugins/sanctum.md) | Push stack branches and open or update dependent PRs |
| `stack-rebase` | [sanctum](../plugins/sanctum.md) | Cascading rebase after a base PR merges |
| `stewardship` | [leyline](../plugins/leyline.md) | Cross-cutting stewardship principles with layer-specific guidance |
| `storage-templates` | [leyline](../plugins/leyline.md) | Storage abstraction patterns |
| `structured-output` | [imbue](../plugins/imbue.md) | Formatting patterns |
| `style-learner` | [scribe](../plugins/scribe.md) | Extract writing style from exemplar text |
| `subagent-testing` | [abstract](../plugins/abstract.md) | Testing patterns for subagent interactions |
| `summon` | [egregore](../plugins/egregore.md) | Spawn autonomous agent session with budget |
| `supply-chain-advisory` | [leyline](../plugins/leyline.md) | Known-bad version detection, lockfile auditing, incident response |
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
| `validate-pr` | [sanctum](../plugins/sanctum.md) | Diff-derived PR test plan with revert-test quality checks |
| `version-updates` | [sanctum](../plugins/sanctum.md) | Version bumping |
| `vhs-recording` | [scry](../plugins/scry.md) | Terminal recordings with VHS |
| `voice-extract` | [scribe](../plugins/scribe.md) | SICO comparative extraction from writing samples |
| `voice-generate` | [scribe](../plugins/scribe.md) | Generate text in learned writing voice |
| `voice-learn` | [scribe](../plugins/scribe.md) | Learning loop from manual edits |
| `voice-review` | [scribe](../plugins/scribe.md) | Dual-gate review against voice profile |
| `vow-enforcement` | [imbue](../plugins/imbue.md) | Three-layer constraint enforcement with soft vows, hard vows, and external validators |
| `war-room` | [attune](../plugins/attune.md) | Multi-LLM expert council with Type 1/2 reversibility routing |
| `war-room-checkpoint` | [attune](../plugins/attune.md) | Inline reversibility assessment for embedded escalation |
| `workflow-diagram` | [cartograph](../plugins/cartograph.md) | Process and state transition diagrams |
| `workflow-improvement` | [sanctum](../plugins/sanctum.md) | Workflow retrospectives |
| `workflow-monitor` | [imbue](../plugins/imbue.md) | Workflow execution monitoring and issue creation |
| `workflow-setup` | [attune](../plugins/attune.md) | Configure CI/CD pipelines |
| `writing-rules` | [hookify](../plugins/hookify.md) | Guide for authoring behavioral rules |

### All Commands (Alphabetical)

| Command | Plugin | Description |
|---------|--------|-------------|
| `/acp` | sanctum | Add, commit, push to current branch |
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
| `/elegant-code-review` | conserve | Review the working diff against the elegant-code decision ladder |
| `/evaluate-skill` | abstract | Evaluate skill execution quality |
| `/filter-log` | conserve | Suggest tier-1 filter commands for a log file before any compression or paste |
| `/fix-pr` | sanctum | Address PR review comments |
| `/fix-workflow` | sanctum | Workflow retrospective with automatic improvement context gathering |
| `/fixit` | sanctum | Fix broken functionality from pasted output using research, TDD, and proof-of-work |
| `/full-review` | pensive | Unified code review |
| `/garden` | memory-palace | Manage digital gardens |
| `/gauntlet` | gauntlet | Run an ad-hoc challenge session (5 questions, random scope) |
| `/gauntlet-curate` | gauntlet | Add or edit a knowledge annotation |
| `/gauntlet-extract` | gauntlet | Rebuild the knowledge base from the current codebase |
| `/gauntlet-graph` | gauntlet | Build, search, and query the code knowledge graph |
| `/gauntlet-onboard` | gauntlet | Start or resume a guided onboarding path |
| `/gauntlet-progress` | gauntlet | Show challenge accuracy stats, weak areas, and streak |
| `/git-catchup` | sanctum | Git repository catchup |
| `/harden` | pensive | Active codebase hardening with NIST/CWE-cited findings and concrete remediation proposals |
| `/hookify` | hookify | Create behavioral rules to prevent unwanted actions |
| `/hookify:configure` | hookify | Interactive rule enable/disable interface |
| `/hookify:from-hook` | hookify | Convert Python SDK hooks to declarative rules |
| `/hookify:help` | hookify | Display hookify help and documentation |
| `/hookify:install` | hookify | Install hookify rule from catalog |
| `/hookify:list` | hookify | List all hookify rules with status |
| `/hooks-eval` | abstract | Hook evaluation |
| `/improve-skills` | abstract | Auto-improve skills from observability data |
| `/install-watchdog` | egregore | Install crash-recovery watchdog |
| `/justify` | imbue | Audit changes for additive bias |
| `/karpathy-check` | imbue | Pre-flight gate for the four Karpathy principles |
| `/make-dogfood` | abstract | Makefile enhancement |
| `/makefile-review` | pensive | Makefile review |
| `/math-review` | pensive | Mathematical review |
| `/merge-docs` | sanctum | Consolidate ephemeral docs |
| `/navigate` | memory-palace | Search palaces |
| `/optimize-context` | conserve | Context optimization |
| `/oracle-setup` | oracle | Install and configure the oracle ONNX inference daemon |
| `/palace` | memory-palace | Manage palaces |
| `/performance-review` | pensive | Time and space complexity hotspot review |
| `/plugin-review` | abstract | Tiered plugin quality review (branch/pr/release) |
| `/pr-review` | sanctum | Enhanced PR review |
| `/prepare-pr` | sanctum | Complete PR preparation with updates and validation |
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
| `/skill-library` | attune | Build a project skill library as a resumable mission |
| `/skill-logs` | memory-palace | View skill execution logs |
| `/skill-review` | pensive | Analyze skill metrics and stability gaps |
| `/skills-eval` | abstract | Skill quality assessment |
| `/speckit-analyze` | spec-kit | Check artifact consistency |
| `/speckit-checklist` | spec-kit | Generate checklist |
| `/speckit-clarify` | spec-kit | Clarifying questions |
| `/speckit-constitution` | spec-kit | Project constitution |
| `/speckit-converge` | spec-kit | Append unbuilt work as tasks |
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
| `/validate-pr` | sanctum | Diff-derived PR test plan with area-targeted checks and revert-test quality proof |
| `/verify-plugin` | leyline | Verify plugin behavioral contract history via GitHub Attestations |
| `/visualize` | cartograph | Generate codebase diagrams via Mermaid Chart MCP |
| `/voice-extract` | scribe | Extract writing voice from samples |
| `/voice-generate` | scribe | Generate text in trained voice |
| `/voice-learn` | scribe | Learn from manual edits |
| `/voice-review` | scribe | Review text against voice profile |

### All Agents (Alphabetical)

| Agent | Plugin | Description |
|-------|--------|-------------|
| `ai-hygiene-auditor` | conserve | Audit codebases for AI-generation warning signs |
| `architecture-reviewer` | pensive | Principal-level architecture review |
| `blast-radius-reviewer` | pensive | Graph-aware code review using blast radius analysis |
| `bloat-auditor` | conserve | Orchestrates bloat detection scans |
| `code-refiner` | pensive | Code quality refinement orchestrator |
| `code-reviewer` | pensive | Expert code review |
| `code-searcher` | tome | GitHub code search |
| `codebase-explorer` | cartograph | Codebase structure analysis for diagrams |
| `commit-agent` | sanctum | Commit message generator |
| `context-optimizer` | conserve | Context optimization |
| `continuation-agent` | conserve | Continue work from session state checkpoint |
| `craft-reviewer` | scribe | Writing craft evaluation (naming, structure, anchoring) |
| `dependency-updater` | sanctum | Dependency version management |
| `desktop-pilot` | phantom | Autonomous desktop control via Computer Use API |
| `discourse-scanner` | tome | Community discourse scanning |
| `doc-editor` | scribe | Interactive documentation editing |
| `doc-verifier` | scribe | QA validation using proof-of-work methodology |
| `extractor` | gauntlet | Autonomous knowledge extraction agent for gauntlet knowledge base |
| `garden-curator` | memory-palace | Digital garden maintenance |
| `git-workspace-agent` | sanctum | Repository state analyzer |
| `harden-orchestrator` | pensive | Active hardening orchestrator (composes rust-review, supply-chain-advisory, bug-review) |
| `implementation-executor` | spec-kit | Task executor |
| `insight-engine` | abstract | Deep analysis for bugs, optimizations, and improvements |
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
| `prose-reviewer` | scribe | AI patterns, banned phrases, voice drift detection |
| `python-linter` | parseltongue | Strict ruff linting without bypasses |
| `python-optimizer` | parseltongue | Performance optimization |
| `python-pro` | parseltongue | Python 3.9+ expertise |
| `python-tester` | parseltongue | Testing expertise |
| `research` | tome | Multi-source research orchestrator (delegates to `Skill(tome:research)`) |
| `review-analyst` | imbue | Structured reviews |
| `rust-auditor` | pensive | Rust security audit |
| `sentinel` | egregore | Watchdog agent for crash recovery |
| `skill-auditor` | abstract | Skill quality audit |
| `skill-evaluator` | abstract | Skill execution evaluator |
| `skill-improver` | abstract | Implements skill improvements from observability |
| `slop-hunter` | scribe | Full-document AI slop detection |
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
| `daemon_lifecycle.py` | oracle | SessionStart, Stop | Oracle daemon lifecycle management |
| `deferred_item_sweep.py` | sanctum | Stop | Sweep session ledger and file deferred items as GitHub issues |
| `deferred_item_watcher.py` | sanctum | PostToolUse | Detect deferred items in Skill output and write to session ledger |
| `detect-git-platform.sh` | leyline | SessionStart | Detect git forge platform from remote URL |
| `fetch-recent-discussions.sh` | leyline | SessionStart | Fetch recent GitHub Discussions |
| `graph_auto_update.py` | gauntlet | PostToolUse | Auto-update code graph after git commits |
| `graph_community_refresh.py` | cartograph | PostToolUse | Refresh community detection after graph builds |
| `homeostatic_monitor.py` | abstract | PostToolUse | Stability gap monitoring, queues degrading skills for improvement |
| `local_doc_processor.py` | memory-palace | PostToolUse | Processes local docs |
| `noqa_guard.py` | leyline | PreToolUse | Block inline lint suppression directives |
| `permission_denied_logger.py` | conserve | PermissionDenied | Log auto-mode permission denials for observability |
| `permission_request.py` | conserve | PermissionRequest | Permission automation |
| `post-evaluation.json` | abstract | Config | Quality scoring config |
| `post_implementation_policy.py` | sanctum | SessionStart | Requires docs/tests updates |
| `post_learnings_stop.py` | abstract | Stop | Post learnings to GitHub Discussions on session stop |
| `pr_blast_radius.py` | pensive | PreToolUse | Surface blast radius context on PR creation |
| `pre-skill-load.json` | abstract | Config | Pre-load validation |
| `pre_compact.py` | tome | PreCompact | Checkpoint active research session |
| `pre_compact_preserve.py` | conserve | PreCompact | Preserve critical context before compression |
| `pre_skill_execution.py` | abstract | PreToolUse | Skill execution tracking |
| `precommit_gate.py` | gauntlet | PreToolUse | Pre-commit quality gate for gauntlet |
| `research_interceptor.py` | memory-palace | PreToolUse | Cache lookup before web |
| `sanitize_external_content.py` | leyline | PostToolUse | Sanitize external content for prompt injection |
| `security_pattern_check.py` | sanctum | PreToolUse | Security anti-pattern detection |
| `session-start.sh` | conserve, imbue | SessionStart | Session initialization |
| `session_complete_notify.py` | sanctum | Stop, UserPromptSubmit | Cross-platform toast notifications and state management |
| `session_lifecycle.py` | memory-palace | Stop | Session lifecycle management |
| `session_start.py` | tome | SessionStart | Check for active research sessions |
| `session_start_hook.py` | egregore | SessionStart | Inject manifest context into new sessions |
| `setup.sh` | conserve | Setup | Environment initialization |
| `setup.sh` | memory-palace | Setup | Palace directory initialization |
| `skill_execution_logger.py` | abstract | PostToolUse | Skill metrics logging |
| `stop_hook.py` | egregore | Stop | Prevent early exit while work items remain |
| `supply_chain_check.py` | leyline | SessionStart | Warn about known-compromised package versions in lockfiles |
| `task_created_tracker.py` | sanctum | TaskCreated | Track task creation for workflow completeness monitoring |
| `tdd_bdd_gate.py` | imbue | PreToolUse | Iron Law enforcement at write-time |
| `tool_output_summarizer.py` | conserve | PostToolUse | Monitor and warn about tool output bloat |
| `url_detector.py` | memory-palace | UserPromptSubmit | URL detection |
| `user-prompt-submit.sh` | imbue | UserPromptSubmit | Scope validation |
| `user_prompt_hook.py` | egregore | UserPromptSubmit | Resume orchestration after user interrupts |
| `verify_workflow_complete.py` | sanctum | Stop | End-of-session workflow verification |
| `vow_bounded_reads.py` | imbue | PreToolUse | Warns when discovery read budget (15 reads) is exceeded per session |
| `vow_no_ai_attribution.py` | imbue | PreToolUse | Blocks AI attribution strings (Co-authored-by: Claude, etc.) in commits |
| `vow_no_emoji_commits.py` | imbue | PreToolUse | Blocks emoji characters in git commit messages |
| `web_research_handler.py` | memory-palace | PostToolUse | Web research processing and storage prompting; skips non-2xx error pages (#547) |
