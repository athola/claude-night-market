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
| `escalation-governance` | Model escalation decisions. | Deciding when to interrupt the user vs. proceed automatically. | (Internal usage) |

### Commands

| Command | Description |
|---------|-------------|
| `/validate-plugin` | Checks a plugin's structure against requirements. |
| `/create-skill` | Scaffolds a new skill using best practices. |
| `/create-command` | Scaffolds a new command. |
| `/create-hook` | Scaffolds a new hook. |

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
| *(And 9 others covering Serverless, Pipeline, CQRS/ES, etc.)* | | | |

---

## Conjure

**Purpose**: Delegation to external LLM services (Gemini, Qwen) for long-context or bulk tasks.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `delegation-core` | Framework for delegation decisions. | Assessing if a task should be offloaded. | `Skill(conjure:delegation-core)` |
| `gemini-delegation` | Gemini CLI integration. | Processing massive context windows. | `Skill(conjure:gemini-delegation)` |
| `qwen-delegation` | Qwen MCP integration. | Tasks requiring reasoning with specific privacy needs. | `Skill(conjure:qwen-delegation)` |

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `delegate-auto` | Auto-selects best service for a task. | `make delegate-auto PROMPT="Summarize" FILES="src/"` |
| `quota-status` | Shows current quota usage. | `make quota-status` |
| `usage-report` | Summarizes token usage and costs. | `make usage-report` |

### Hooks

*   **`bridge.on_tool_start`**: Suggests delegation when input files exceed context thresholds.
*   **`bridge.after_tool_use`**: Suggests delegation if tool output is truncated or massive.

---

## Conservation

**Purpose**: Resource optimization and context window management.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `context-optimization` | MECW assessment. | Reducing context pressure when the window fills up. | `Skill(conservation:context-optimization)` |
| `mcp-code-execution` | MCP patterns for data pipelines. | Processing data outside the context window. | `Skill(conservation:mcp-code-execution)` |
| `cpu-gpu-performance` | Hardware resource tracking. | Monitoring system load during heavy tasks. | (Internal usage) |
| `token-conservation` | Token budget enforcement. | Keeping interactions within cost/token limits. | (Internal usage) |

---

## Imbue

**Purpose**: Methodologies for analysis, evidence gathering, and structured output.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `review-core` | Scaffolding for detailed reviews. | Starting an architecture or security review. | `Skill(imbue:review-core)` |
| `diff-analysis` | Semantic changeset analysis. | Understanding "what changed" in a PR or release. | `Skill(imbue:diff-analysis)` |
| `catchup` | Context recovery. | Getting up to speed on a repo after time away. | `Skill(imbue:catchup)` |
| `evidence-logging` | Capture methodology. | creating a verifiable audit trail of findings. | `Skill(imbue:evidence-logging)` |
| `structured-output` | Formatting patterns. | Creating consistent reports. | `Skill(imbue:structured-output)` |
| `scope-guard` | Anti-overengineering. | Evaluating if a feature is worth the cost. | `Skill(imbue:scope-guard)` |

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

---

## Memory Palace

**Purpose**: Spatial memory techniques for knowledge organization.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `palace-architect` | Building virtual palaces. | Organizing complex concepts into spatial structures. | `Skill(memory-palace:palace-architect)` |
| `knowledge-navigator` | Spatial search. | Finding information stored in palaces. | `Skill(memory-palace:knowledge-navigator)` |
| `knowledge-librarian` | Intake and curation. | Processing new information into the system. | `Skill(memory-palace:knowledge-librarian)` |
| `garden-curator` | Digital garden maintenance. | Tending to long-term knowledge bases. | `Skill(memory-palace:garden-curator)` |

### Commands

| Command | Description |
|---------|-------------|
| `/palace` | Manage memory palaces. |
| `/garden` | Manage digital gardens. |
| `/navigate` | Search and traverse palaces. |

### Agents

*   **`palace-architect`**: Designs architectures.
*   **`knowledge-navigator`**: Searches and retrieves.
*   **`garden-curator`**: Maintains gardens.

### Hooks

*   **`research_interceptor`**: Checks local knowledge before web searches.
*   **`url_detector`**: Suggests intake for URLs in output.

---

## Minister

**Purpose**: Project management and GitHub initiative tracking.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `github-initiative-pulse` | Initiative progress tracking. | Weekly status reports and stakeholder updates. | `Skill(minister:github-initiative-pulse)` |
| `release-health-gates` | Release readiness checks. | Verifying CI, docs, and risk before release. | `Skill(minister:release-health-gates)` |

### Scripts (CLI)

*   `tracker.py`: CLI for managing the initiative database and generating reports.

---

## Parseltongue

**Purpose**: Modern Python development suite.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `python-testing` | Pytest/TDD workflows. | Writing and running robust tests. | `Skill(parseltongue:python-testing)` |
| `python-performance` | Profiling and optimization. | debugging slow Python code. | `Skill(parseltongue:python-performance)` |
| `python-async` | Async patterns. | Implementing asyncio concurrency. | `Skill(parseltongue:python-async)` |
| `python-packaging` | Packaging with uv. | Managing pyproject.toml and dependencies. | `Skill(parseltongue:python-packaging)` |

### Commands

| Command | Description |
|---------|-------------|
| `/analyze-tests` | Reports on test suite health. |
| `/run-profiler` | Profiles code execution. |
| `/check-async` | Validates async patterns. |

### Agents

*   **`python-pro`**: General modern Python assistant.
*   **`python-tester`**: Testing specialist.
*   **`python-optimizer`**: Performance specialist.

---

## Pensive

**Purpose**: Code review and analysis toolkit.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `unified-review` | Review orchestration. | Starting a review and letting Claude pick the right tools. | `Skill(pensive:unified-review)` |
| `api-review` | API surface evaluation. | Reviewing OpenAPI specs or library exports. | `Skill(pensive:api-review)` |
| `architecture-review` | Architecture assessment. | Checking alignment with ADRs. | `Skill(pensive:architecture-review)` |
| `bug-review` | Bug hunting. | Systematic search for logic errors. | `Skill(pensive:bug-review)` |
| `rust-review` | Rust-specific checking. | Auditing unsafe code and borrow checker patterns. | `Skill(pensive:rust-review)` |
| `test-review` | Test quality review. | Ensuring tests actually verify behavior. | `Skill(pensive:test-review)` |

### Commands

| Command | Description |
|---------|-------------|
| `/full-review` | Runs unified review. |
| `/api-review` | Runs API review. |
| `/architecture-review` | Runs architecture review. |
| `/bug-review` | Runs bug review. |

### Agents

*   **`code-reviewer`**: General reviewer.
*   **`architecture-reviewer`**: Principal-level assessor.
*   **`rust-auditor`**: Rust specialist.

---

## Sanctum

**Purpose**: Git and workspace operations.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `git-workspace-review` | Repo state analysis. | Checking status before starting work. | `Skill(sanctum:git-workspace-review)` |
| `commit-messages` | Conventional commits. | Generating standard commit messages. | `Skill(sanctum:commit-messages)` |
| `pr-prep` | PR preparation. | Drafting PR descriptions and checking quality. | `Skill(sanctum:pr-prep)` |
| `doc-updates` | Documentation maintenance. | Keeping docs in sync with code. | `Skill(sanctum:doc-updates)` |
| `update-readme` | README modernization. | Refreshing project entry points. | `Skill(sanctum:update-readme)` |
| `version-updates` | Version bumping. | Managing semantic versioning. | `Skill(sanctum:version-updates)` |
| `workflow-improvement` | Workflow retrospectives. | Improving slow, confusing, or fragile workflows. | `Skill(sanctum:workflow-improvement)` |

### Commands

| Command | Description |
|---------|-------------|
| `/catchup` | Summarizes recent repo activity. |
| `/commit-msg` | Generates a commit message. |
| `/pr` | Prepares a Pull Request. |
| `/fix-pr` | Helps address PR review comments. |
| `/fix-workflow` | Runs workflow retrospective and improves skill/agent/command/hook components. |
| `/update-docs` | Updates documentation. |

### Agents

*   **`git-workspace-agent`**: Analyzer.
*   **`commit-agent`**: Message generator.
*   **`pr-agent`**: PR author.
*   **`workflow-recreate-agent`**: Reconstructs workflow slices and surfaces inefficiencies.
*   **`workflow-improvement-analysis-agent`**: Generates improvement approaches with trade-offs.
*   **`workflow-improvement-planner-agent`**: Selects approach and creates execution plan.
*   **`workflow-improvement-implementer-agent`**: Applies focused changes with tests.
*   **`workflow-improvement-validator-agent`**: Validates improvements via replay and metrics.

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

### Agents

*   **`spec-analyzer`**: Validates consistency.
*   **`task-generator`**: Creates tasks.
*   **`implementation-executor`**: Writes code.
