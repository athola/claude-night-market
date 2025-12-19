# Claude Night Market Capabilities Reference

A detailed guide to the skills, commands, agents, and hooks available across the Claude Night Market ecosystem.

## Table of Contents

- [Abstract](#abstract)
- [Archetypes](#archetypes)
- [Conjure](#conjure)
- [Conservation](#conservation)
- [Imbue](#imbue)
- [Leyline](#leyline)
- [Memory Palace](#memory-palace)
- [Minister](#minister)
- [Parseltongue](#parseltongue)
- [Pensive](#pensive)
- [Sanctum](#sanctum)
- [Spec Kit](#spec-kit)
- [Superpowers Dependencies](#superpowers-dependencies)

---

## Superpowers Dependencies

Many Claude Night Market capabilities achieve their full potential when used alongside the [**superpowers**](https://github.com/obra/superpowers) skills from the superpowers-marketplace. While all plugins work standalone, superpowers provides foundational methodology skills (TDD cycles, systematic debugging, code review patterns) that significantly enhance workflows.

### Installation

```bash
# Add the superpowers marketplace
/plugin marketplace add obra/superpowers

# Install the superpowers plugin
/plugin install superpowers@superpowers-marketplace
```

### Dependency Overview

The table below shows which Night Market components depend on superpowers skills for enhanced functionality.

| Plugin | Component | Type | Superpowers Dependency | Enhancement |
|--------|-----------|------|------------------------|-------------|
| **abstract** | `/create-skill` | Command | `superpowers:brainstorming` | Socratic questioning for skill idea refinement |
| **abstract** | `/create-command` | Command | `superpowers:brainstorming` | Guided command concept development |
| **abstract** | `/create-hook` | Command | `superpowers:brainstorming` | Security-first hook design brainstorming |
| **abstract** | `/test-skill` | Command | `superpowers:test-driven-development` | RED-GREEN-REFACTOR TDD methodology |
| **sanctum** | `/pr` | Command | `superpowers:receiving-code-review` | Automated PR validation before creation |
| **sanctum** | `/pr-review` | Command | `superpowers:receiving-code-review` | Comprehensive scope-focused PR analysis |
| **sanctum** | `/fix-pr` | Command | `superpowers:receiving-code-review` | Systematic review comment resolution |
| **sanctum** | `/fix-issue` | Command | `superpowers:subagent-driven-development`, `superpowers:writing-plans`, `superpowers:test-driven-development`, `superpowers:requesting-code-review`, `superpowers:finishing-a-development-branch` | Full issue-to-PR workflow automation |
| **spec-kit** | `/speckit.clarify` | Command | `superpowers:brainstorming` | Enhanced clarification questioning |
| **spec-kit** | `/speckit.plan` | Command | `superpowers:writing-plans` | Structured implementation planning |
| **spec-kit** | `/speckit.tasks` | Command | `superpowers:executing-plans`, `superpowers:systematic-debugging` | Task breakdown with debugging support |
| **spec-kit** | `/speckit.implement` | Command | `superpowers:executing-plans`, `superpowers:systematic-debugging` | Execution with error handling |
| **spec-kit** | `/speckit.analyze` | Command | `superpowers:systematic-debugging`, `superpowers:verification-before-completion` | Cross-artifact consistency checks |
| **spec-kit** | `/speckit.checklist` | Command | `superpowers:verification-before-completion` | Evidence-based checklist validation |
| **spec-kit** | `speckit-orchestrator` | Skill | Multiple superpowers | Full SDD workflow coordination |
| **spec-kit** | `task-planning` | Skill | `superpowers:writing-plans`, `superpowers:executing-plans` | Structured task generation |
| **pensive** | `/full-review` | Command | `superpowers:systematic-debugging`, `superpowers:verification-before-completion` | Four-phase debugging + evidence standards |
| **parseltongue** | `python-testing` | Skill | `superpowers:test-driven-development`, `superpowers:testing-anti-patterns` | TDD cycles + anti-pattern detection |
| **imbue** | `scope-guard` | Skill | `superpowers:brainstorming`, `superpowers:writing-plans`, `superpowers:execute-plan` | Anti-overengineering during workflows |
| **conservation** | `/optimize-context` | Command | `superpowers:condition-based-waiting` | Smart waiting strategies for optimization |
| **minister** | `issue-management` | Skill | `superpowers:systematic-debugging` | Methodical bug investigation |

### Superpowers Skills Referenced

The following superpowers skills are used across the Night Market ecosystem:

| Superpowers Skill | Purpose | Used By |
|-------------------|---------|---------|
| `brainstorming` | Socratic questioning for idea refinement | abstract, spec-kit, imbue |
| `test-driven-development` | RED-GREEN-REFACTOR TDD cycle | abstract, sanctum, parseltongue |
| `receiving-code-review` | Technical rigor for evaluating suggestions | sanctum |
| `requesting-code-review` | Quality gates for code submission | sanctum |
| `writing-plans` | Structured implementation planning | spec-kit, imbue |
| `executing-plans` | Task execution with checkpoints | spec-kit |
| `systematic-debugging` | Four-phase debugging framework | spec-kit, pensive, minister, conservation |
| `verification-before-completion` | Evidence-based review standards | spec-kit, pensive, imbue |
| `testing-anti-patterns` | Common testing mistake prevention | parseltongue |
| `condition-based-waiting` | Smart polling/waiting strategies | conservation |
| `subagent-driven-development` | Autonomous subagent orchestration | sanctum |
| `finishing-a-development-branch` | Branch cleanup and finalization | sanctum |

### Graceful Degradation

All Night Market plugins are designed to work without superpowers installed. When superpowers skills are not available:

- **Commands**: Execute core functionality but skip enhanced methodology phases
- **Skills**: Provide standalone guidance without methodology integration
- **Agents**: Function with reduced automation depth

### Recommended Installation

For the full Night Market experience:

```bash
# 1. Add marketplaces
/plugin marketplace add obra/superpowers
/plugin marketplace add athola/claude-night-market

# 2. Install superpowers (foundational)
/plugin install superpowers@superpowers-marketplace

# 3. Install desired Night Market plugins
/plugin install sanctum@claude-night-market
/plugin install spec-kit@claude-night-market
/plugin install pensive@claude-night-market
# ... additional plugins as needed
```

---

## Abstract

**Purpose**: Meta-skills infrastructure for the plugin ecosystem. Handles skill authoring, hook development, and quality evaluation.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `skill-authoring` | TDD methodology for skill creation. | Creating a new skill with high quality standards. | `Skill(abstract:skill-authoring)` |
| `hook-authoring` | Security-first hook development. | Creating safe and effective hooks. | `Skill(abstract:hook-authoring)` |
| `modular-skills` | Modular design patterns. | Breaking down large skills into manageable modules. | `Skill(abstract:modular-skills)` |
| `skills-eval` | Skill quality assessment. | Auditing existing skills for token efficiency and clarity. | `Skill(abstract:skills-eval)` |
| `hooks-eval` | Hook security scanning. | Verifying hooks don't leak secrets or run unsafe code. | `Skill(abstract:hooks-eval)` |
| `escalation-governance` | Model escalation decisions. | Deciding when to escalate from haiku to sonnet/opus. | `Skill(abstract:escalation-governance)` |
| `makefile-dogfooder` | Makefile analysis and enhancement. | Ensuring Makefiles cover all user functionality. | `Skill(abstract:makefile-dogfooder)` |
| `shared-patterns` | Reusable plugin development patterns. | Templates for validation, error handling, and testing. | `Skill(abstract:shared-patterns)` |
| `performance-optimization` | Skill loading optimization. | Conditional loading and quick-start patterns. | (Internal usage) |

### Commands

| Command | Description |
|---------|-------------|
| `/validate-plugin` | Checks a plugin's structure against requirements. |
| `/create-skill` | Scaffolds a new skill using best practices. |
| `/create-command` | Scaffolds a new command. |
| `/create-hook` | Scaffolds a new hook with security-first design. |
| `/analyze-hook` | Analyzes individual hook files for security and performance. |
| `/analyze-skill` | Analyzes skill complexity and gets modularization recommendations. |
| `/bulletproof-skill` | Anti-rationalization workflow for hardening skills. |
| `/context-report` | Generates context optimization report for skill directories. |
| `/estimate-tokens` | Estimates token usage for skill files and dependencies. |
| `/hooks-eval` | Comprehensive hook evaluation framework. |
| `/make-dogfood` | Analyzes and enhances Makefiles for functionality coverage. |
| `/skills-eval` | Runs skill quality assessment. |
| `/test-skill` | Skill testing workflow with TDD methodology. |
| `/validate-hook` | Validates hook security, performance, and compliance. |

### Agents

| Agent | Description |
|-------|-------------|
| `meta-architect` | Designs architectures for the plugin ecosystem. |
| `plugin-validator` | Validates plugin structure against official requirements. |
| `skill-auditor` | Audits skills for quality and compliance. |

### Hooks

| Hook | Type | Description |
|------|------|-------------|
| `post-evaluation.json` | After | Runs after skill evaluation completes. |
| `pre-skill-load.json` | Before | Validates skills before loading. |

---

## Archetypes

**Purpose**: Architecture paradigm selection and implementation planning.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `architecture-paradigms` | Orchestrator for paradigm selection. | Choosing the right architecture for a new system. | `Skill(archetypes:architecture-paradigms)` |
| `architecture-paradigm-layered` | Traditional N-tier architecture. | Simple web apps or internal tools. | `Skill(archetypes:architecture-paradigm-layered)` |
| `architecture-paradigm-hexagonal` | Ports & Adapters architecture. | Systems needing infrastructure independence. | `Skill(archetypes:architecture-paradigm-hexagonal)` |
| `architecture-paradigm-microservices` | Independent distributed services. | Large-scale enterprise applications. | `Skill(archetypes:architecture-paradigm-microservices)` |
| `architecture-paradigm-event-driven` | Asynchronous communication. | Real-time processing and decoupling. | `Skill(archetypes:architecture-paradigm-event-driven)` |
| `architecture-paradigm-serverless` | Function-as-a-Service. | Event-driven apps with minimal infrastructure. | `Skill(archetypes:architecture-paradigm-serverless)` |
| `architecture-paradigm-pipeline` | Pipes-and-filters model. | ETL, media processing, or compiler-like workloads. | `Skill(archetypes:architecture-paradigm-pipeline)` |
| `architecture-paradigm-cqrs-es` | CQRS and Event Sourcing. | Audit trails, event replay, separate read/write scaling. | `Skill(archetypes:architecture-paradigm-cqrs-es)` |
| `architecture-paradigm-microkernel` | Plugin-based extensibility. | Minimal core with feature plug-ins. | `Skill(archetypes:architecture-paradigm-microkernel)` |
| `architecture-paradigm-modular-monolith` | Single deployment with internal boundaries. | Module separation without distributed complexity. | `Skill(archetypes:architecture-paradigm-modular-monolith)` |
| `architecture-paradigm-space-based` | Data-grid architecture. | High-scale stateful workloads. | `Skill(archetypes:architecture-paradigm-space-based)` |
| `architecture-paradigm-service-based` | Coarse-grained SOA. | Modular deployment without microservices. | `Skill(archetypes:architecture-paradigm-service-based)` |
| `architecture-paradigm-functional-core` | Functional Core, Imperative Shell. | Superior testability with pure functions. | `Skill(archetypes:architecture-paradigm-functional-core)` |
| `architecture-paradigm-client-server` | Client-server communication. | Systems with clear client-server responsibilities. | `Skill(archetypes:architecture-paradigm-client-server)` |

---

## Conjure

**Purpose**: Delegation to external LLM services (Gemini, Qwen) for long-context or bulk tasks.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `delegation-core` | Framework for delegation decisions. | Assessing if a task should be offloaded. | `Skill(conjure:delegation-core)` |
| `gemini-delegation` | Gemini CLI integration. | Processing massive context windows. | `Skill(conjure:gemini-delegation)` |
| `qwen-delegation` | Qwen MCP integration. | Tasks requiring reasoning with specific privacy needs. | `Skill(conjure:qwen-delegation)` |

### Commands (Makefile)

| Command | Description | Example |
|---------|-------------|---------|
| `delegate-auto` | Auto-selects best service for a task. | `make delegate-auto PROMPT="Summarize" FILES="src/"` |
| `quota-status` | Shows current quota usage. | `make quota-status` |
| `usage-report` | Summarizes token usage and costs. | `make usage-report` |

### Hooks

| Hook | Type | Description |
|------|------|-------------|
| `bridge.on_tool_start` | Before | Suggests delegation when input files exceed context thresholds. |
| `bridge.after_tool_use` | After | Suggests delegation if tool output is truncated or massive. |

---

## Conservation

**Purpose**: Resource optimization, context window management, and performance monitoring. Automatically loads optimization guidance at session start.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `context-optimization` | MECW principles and 50% context rule. | Reducing context pressure when utilization > 30%. | `Skill(conservation:context-optimization)` |
| `token-conservation` | Token usage strategies and quota tracking. | Start of session, before heavy loads. | `Skill(conservation:token-conservation)` |
| `cpu-gpu-performance` | Resource monitoring and selective testing. | Before builds, tests, or training jobs. | `Skill(conservation:cpu-gpu-performance)` |
| `mcp-code-execution` | MCP patterns for data pipelines. | Processing data outside the context window. | `Skill(conservation:mcp-code-execution)` |
| `optimizing-large-skills` | Large skill optimization. | Breaking down or optimizing oversized skills. | `Skill(conservation:optimizing-large-skills)` |

### Commands

| Command | Description |
|---------|-------------|
| `/optimize-context` | Analyzes and optimizes context window usage using MECW principles. |
| `/analyze-growth` | Analyzes skill growth patterns and predicts context budget impact. |

### Agents

| Agent | Description |
|-------|-------------|
| `context-optimizer` | Autonomous agent for context window optimization and MECW compliance. |

### Hooks

| Hook | Type | Description |
|------|------|-------------|
| `session-start.sh` | Session | Loads conservation skills guidance at session start. Supports bypass modes via `CONSERVATION_MODE` env var. |

### Bypass Modes

The session-start hook supports three modes via the `CONSERVATION_MODE` environment variable:

| Mode | Usage | Behavior |
|------|-------|----------|
| `normal` (default) | `claude` | Full conservation guidance loaded |
| `quick` | `CONSERVATION_MODE=quick claude` | Skip guidance for fast processing |
| `deep` | `CONSERVATION_MODE=deep claude` | Full guidance with extended resource allowance |

### Key Thresholds

- **Context**: < 30% LOW | 30-50% MODERATE | > 50% CRITICAL (optimize immediately)
- **Token Quota**: 5-hour rolling cap + weekly cap (check with `/status`)
- **CPU/GPU**: Establish baseline before heavy tasks

---

## Imbue

**Purpose**: Methodologies for analysis, evidence gathering, and structured output.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `review-core` | Scaffolding for detailed reviews. | Starting an architecture or security review. | `Skill(imbue:review-core)` |
| `diff-analysis` | Semantic changeset analysis. | Understanding "what changed" in a PR or release. | `Skill(imbue:diff-analysis)` |
| `catchup` | Context recovery. | Getting up to speed on a repo after time away. | `Skill(imbue:catchup)` |
| `evidence-logging` | Capture methodology. | Creating a verifiable audit trail of findings. | `Skill(imbue:evidence-logging)` |
| `structured-output` | Formatting patterns. | Creating consistent reports. | `Skill(imbue:structured-output)` |
| `scope-guard` | Anti-overengineering. | Evaluating if a feature is worth the cost. | `Skill(imbue:scope-guard)` |

### Commands

| Command | Description |
|---------|-------------|
| `/catchup` | Quickly understand recent changes and extract actionable insights. |
| `/review` | Start a structured review workflow with evidence logging. |
| `/full-review` | Comprehensive review workflow with formatted output. |

### Agents

| Agent | Description |
|-------|-------------|
| `review-analyst` | Autonomous agent for structured reviews with evidence gathering. |

### Hooks

| Hook | Type | Description |
|------|------|-------------|
| `session-start.sh` | Session | Initializes session with scope-guard and learning mode. |
| `user-prompt-submit.sh` | Prompt | Validates prompts against scope thresholds. |
| `pre-pr-scope-check.sh` | Pre-PR | Checks scope before PR creation. |

---

## Leyline

**Purpose**: Infrastructure and pipeline building blocks.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `quota-management` | Rate limiting and quotas. | Building services that consume APIs. | `dependencies: [leyline:quota-management]` |
| `usage-logging` | Telemetry tracking. | Logging tool usage for analytics. | `dependencies: [leyline:usage-logging]` |
| `service-registry` | Service discovery patterns. | Managing multiple external tool connections. | `dependencies: [leyline:service-registry]` |
| `error-patterns` | Standardized error handling. | Implementing robust error recovery. | `dependencies: [leyline:error-patterns]` |
| `authentication-patterns` | Auth flow patterns. | Handling API keys and OAuth. | `dependencies: [leyline:authentication-patterns]` |
| `evaluation-framework` | Decision thresholds. | Building evaluation criteria for decisions. | `dependencies: [leyline:evaluation-framework]` |
| `mecw-patterns` | MECW implementation. | Minimal Effective Context Window patterns. | `dependencies: [leyline:mecw-patterns]` |
| `progressive-loading` | Dynamic content loading. | Loading patterns and selection strategies. | `dependencies: [leyline:progressive-loading]` |
| `pytest-config` | Pytest configuration patterns. | Standardized test configuration. | `dependencies: [leyline:pytest-config]` |
| `storage-templates` | Storage abstraction patterns. | File and database storage templates. | `dependencies: [leyline:storage-templates]` |
| `testing-quality-standards` | Test quality guidelines. | Ensuring high-quality test suites. | `dependencies: [leyline:testing-quality-standards]` |

### Commands

| Command | Description |
|---------|-------------|
| `/reinstall-all-plugins` | Uninstalls and reinstalls all plugins to refresh cache. |
| `/update-all-plugins` | Updates all installed plugins from marketplaces. |

---

## Memory Palace

**Purpose**: Spatial memory techniques for knowledge organization.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `memory-palace-architect` | Building virtual palaces. | Organizing complex concepts into spatial structures. | `Skill(memory-palace:memory-palace-architect)` |
| `knowledge-locator` | Spatial search. | Finding information stored in palaces. | `Skill(memory-palace:knowledge-locator)` |
| `knowledge-intake` | Intake and curation. | Processing new information into the system. | `Skill(memory-palace:knowledge-intake)` |
| `digital-garden-cultivator` | Digital garden maintenance. | Tending to long-term knowledge bases. | `Skill(memory-palace:digital-garden-cultivator)` |
| `session-palace-builder` | Session-specific palaces. | Building temporary palaces for current work. | `Skill(memory-palace:session-palace-builder)` |

### Commands

| Command | Description |
|---------|-------------|
| `/palace` | Manage memory palaces. |
| `/garden` | Manage digital gardens. |
| `/navigate` | Search and traverse palaces. |

### Agents

| Agent | Description |
|-------|-------------|
| `palace-architect` | Designs memory palace architectures. |
| `knowledge-navigator` | Searches and retrieves from palaces. |
| `knowledge-librarian` | Evaluates and routes knowledge for storage. |
| `garden-curator` | Maintains digital gardens. |

### Hooks

| Hook | Type | Description |
|------|------|-------------|
| `research_interceptor.py` | Before | Checks local knowledge before web searches. |
| `url_detector.py` | After | Suggests intake for URLs in output. |
| `local_doc_processor.py` | Process | Processes local documentation files. |
| `web_content_processor.py` | Process | Processes web content for storage. |

---

## Minister

**Purpose**: Project management and GitHub initiative tracking.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `github-initiative-pulse` | Initiative progress tracking. | Weekly status reports and stakeholder updates. | `Skill(minister:github-initiative-pulse)` |
| `release-health-gates` | Release readiness checks. | Verifying CI, docs, and risk before release. | `Skill(minister:release-health-gates)` |

### Scripts (CLI)

| Script | Description |
|--------|-------------|
| `tracker.py` | CLI for managing the initiative database and generating reports. |

---

## Parseltongue

**Purpose**: Modern Python development suite.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `python-testing` | Pytest/TDD workflows. | Writing and running robust tests. | `Skill(parseltongue:python-testing)` |
| `python-performance` | Profiling and optimization. | Debugging slow Python code. | `Skill(parseltongue:python-performance)` |
| `python-async` | Async patterns. | Implementing asyncio concurrency. | `Skill(parseltongue:python-async)` |
| `python-packaging` | Packaging with uv. | Managing pyproject.toml and dependencies. | `Skill(parseltongue:python-packaging)` |

### Commands

| Command | Description |
|---------|-------------|
| `/analyze-tests` | Reports on test suite health. |
| `/run-profiler` | Profiles code execution. |
| `/check-async` | Validates async patterns. |

### Agents

| Agent | Description |
|-------|-------------|
| `python-pro` | Master Python 3.12+ with modern features and best practices. |
| `python-tester` | Expert testing agent for pytest, TDD, and mocking strategies. |
| `python-optimizer` | Expert performance optimization and profiling agent. |

---

## Pensive

**Purpose**: Code review and analysis toolkit.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `unified-review` | Review orchestration. | Starting a review and letting Claude pick the right tools. | `Skill(pensive:unified-review)` |
| `api-review` | API surface evaluation. | Reviewing OpenAPI specs or library exports. | `Skill(pensive:api-review)` |
| `architecture-review` | Architecture assessment. | Checking alignment with ADRs and design principles. | `Skill(pensive:architecture-review)` |
| `bug-review` | Bug hunting. | Systematic search for logic errors. | `Skill(pensive:bug-review)` |
| `rust-review` | Rust-specific checking. | Auditing unsafe code and borrow checker patterns. | `Skill(pensive:rust-review)` |
| `test-review` | Test quality review. | Ensuring tests actually verify behavior. | `Skill(pensive:test-review)` |
| `makefile-review` | Makefile best practices. | Reviewing Makefiles for quality and patterns. | `Skill(pensive:makefile-review)` |
| `math-review` | Mathematical correctness. | Reviewing mathematical logic and proofs. | `Skill(pensive:math-review)` |

### Commands

| Command | Description |
|---------|-------------|
| `/full-review` | Runs unified review. |
| `/api-review` | Runs API review. |
| `/architecture-review` | Runs architecture review. |
| `/bug-review` | Runs bug review. |
| `/rust-review` | Runs Rust-specific review. |
| `/test-review` | Runs test quality review. |
| `/makefile-review` | Runs Makefile review. |
| `/math-review` | Runs mathematical review. |

### Agents

| Agent | Description |
|-------|-------------|
| `code-reviewer` | Expert code review for bugs, security, and quality. |
| `architecture-reviewer` | Principal-level architecture review specialist. |
| `rust-auditor` | Expert Rust security and safety auditor. |

---

## Sanctum

**Purpose**: Git and workspace operations.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `git-workspace-review` | Repo state analysis. | Checking status before starting work. | `Skill(sanctum:git-workspace-review)` |
| `commit-messages` | Conventional commits. | Generating standard commit messages. | `Skill(sanctum:commit-messages)` |
| `pr-prep` | PR preparation. | Drafting PR descriptions and checking quality. | `Skill(sanctum:pr-prep)` |
| `pr-review` | PR review workflows. | Comprehensive PR analysis and feedback. | `Skill(sanctum:pr-review)` |
| `doc-updates` | Documentation maintenance. | Keeping docs in sync with code. | `Skill(sanctum:doc-updates)` |
| `doc-consolidation` | Document merging. | Consolidating ephemeral LLM-generated docs. | `Skill(sanctum:doc-consolidation)` |
| `update-readme` | README modernization. | Refreshing project entry points. | `Skill(sanctum:update-readme)` |
| `version-updates` | Version bumping. | Managing semantic versioning. | `Skill(sanctum:version-updates)` |
| `test-updates` | Test maintenance. | Updating and maintaining tests with TDD/BDD. | `Skill(sanctum:test-updates)` |
| `file-analysis` | File structure analysis. | Understanding file organization and dependencies. | `Skill(sanctum:file-analysis)` |
| `workflow-improvement` | Workflow retrospectives. | Improving slow, confusing, or fragile workflows. | `Skill(sanctum:workflow-improvement)` |

### Commands

| Command | Description |
|---------|-------------|
| `/catchup` | Summarizes recent repo activity. |
| `/commit-msg` | Generates a commit message. |
| `/pr` | Prepares a Pull Request. |
| `/pr-review` | Enhanced PR review with quality checks. |
| `/fix-pr` | Addresses PR review comments with thread resolution and automatic issue linkage (closes/comments on related issues). |
| `/fix-issue` | Workflow for fixing GitHub issues systematically with parallel execution. |
| `/fix-workflow` | Runs workflow retrospective and improves components. |
| `/merge-docs` | Consolidates ephemeral docs into permanent documentation. |
| `/update-docs` | Updates documentation. |
| `/update-readme` | Updates README with language-aware exemplar mining. |
| `/update-tests` | Updates and maintains tests. |
| `/update-version` | Bumps project versions. |

### Agents

| Agent | Description |
|-------|-------------|
| `git-workspace-agent` | Repository state analyzer. |
| `commit-agent` | Conventional commit message generator. |
| `pr-agent` | Pull request preparation specialist. |
| `workflow-recreate-agent` | Reconstructs workflow slices and surfaces inefficiencies. |
| `workflow-improvement-analysis-agent` | Generates improvement approaches with trade-offs. |
| `workflow-improvement-planner-agent` | Selects approach and creates execution plan. |
| `workflow-improvement-implementer-agent` | Applies focused changes with tests. |
| `workflow-improvement-validator-agent` | Validates improvements via replay and metrics. |

### Hooks

| Hook | Type | Description |
|------|------|-------------|
| `post_implementation_policy.py` | Session | Injects post-implementation protocol requiring docs/tests/readme updates. |
| `verify_workflow_complete.py` | Stop | Verifies workflow completion. |
| `session_complete_notify.py` | Stop | Cross-platform toast notification (Linux/macOS/Windows) when Claude awaits input. |

---

## Spec Kit

**Purpose**: Specification-Driven Development (SDD).

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `speckit-orchestrator` | Workflow coordination. | Managing the entire spec-to-code lifecycle. | `Skill(spec-kit:speckit-orchestrator)` |
| `spec-writing` | Specification authoring. | Writing clear requirements from vague ideas. | `Skill(spec-kit:spec-writing)` |
| `task-planning` | Task generation. | Breaking specs into implementable tasks. | `Skill(spec-kit:task-planning)` |

### Commands

| Command | Description |
|---------|-------------|
| `/speckit.specify` | Create a new specification. |
| `/speckit.plan` | Generate an implementation plan. |
| `/speckit.tasks` | Generate tasks from the plan. |
| `/speckit.implement` | Execute the tasks. |
| `/speckit.analyze` | Check consistency across artifacts. |
| `/speckit.checklist` | Generate a custom checklist for the feature. |
| `/speckit.clarify` | Identify underspecified areas with targeted questions. |
| `/speckit.constitution` | Create or update project constitution. |
| `/speckit.startup` | Bootstrap speckit workflow at session start. |

### Agents

| Agent | Description |
|-------|-------------|
| `spec-analyzer` | Validates consistency across spec artifacts. |
| `task-generator` | Creates implementation tasks. |
| `implementation-executor` | Executes tasks and writes code. |
