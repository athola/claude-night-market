# Claude Night Market Capabilities Reference

A detailed guide to the skills, commands, agents, and hooks available across the Claude Night Market ecosystem.

---

## Quick Reference Index

### All Skills (Alphabetical)

| Skill | Plugin | Description |
|-------|--------|-------------|
| `api-review` | [pensive](#pensive) | API surface evaluation |
| `browser-recording` | [scry](#scry) | Playwright browser recording |
| `architecture-paradigm-client-server` | [archetypes](#archetypes) | Client-server communication |
| `architecture-paradigm-cqrs-es` | [archetypes](#archetypes) | CQRS and Event Sourcing |
| `architecture-paradigm-event-driven` | [archetypes](#archetypes) | Asynchronous communication |
| `architecture-paradigm-functional-core` | [archetypes](#archetypes) | Functional Core, Imperative Shell |
| `architecture-paradigm-hexagonal` | [archetypes](#archetypes) | Ports & Adapters architecture |
| `architecture-paradigm-layered` | [archetypes](#archetypes) | Traditional N-tier architecture |
| `architecture-paradigm-microkernel` | [archetypes](#archetypes) | Plugin-based extensibility |
| `architecture-paradigm-microservices` | [archetypes](#archetypes) | Independent distributed services |
| `architecture-paradigm-modular-monolith` | [archetypes](#archetypes) | Single deployment with internal boundaries |
| `architecture-paradigm-pipeline` | [archetypes](#archetypes) | Pipes-and-filters model |
| `architecture-paradigm-serverless` | [archetypes](#archetypes) | Function-as-a-Service |
| `architecture-paradigm-service-based` | [archetypes](#archetypes) | Coarse-grained SOA |
| `architecture-paradigm-space-based` | [archetypes](#archetypes) | Data-grid architecture |
| `architecture-paradigms` | [archetypes](#archetypes) | Orchestrator for paradigm selection |
| `architecture-review` | [pensive](#pensive) | Architecture assessment |
| `authentication-patterns` | [leyline](#leyline) | Auth flow patterns |
| `bug-review` | [pensive](#pensive) | Bug hunting |
| `catchup` | [imbue](#imbue) | Context recovery |
| `commit-messages` | [sanctum](#sanctum) | Conventional commits |
| `context-optimization` | [conservation](#conservation) | MECW principles and 50% context rule |
| `cpu-gpu-performance` | [conservation](#conservation) | Resource monitoring and selective testing |
| `delegation-core` | [conjure](#conjure) | Framework for delegation decisions |
| `diff-analysis` | [imbue](#imbue) | Semantic changeset analysis |
| `digital-garden-cultivator` | [memory-palace](#memory-palace) | Digital garden maintenance |
| `doc-consolidation` | [sanctum](#sanctum) | Document merging |
| `doc-updates` | [sanctum](#sanctum) | Documentation maintenance |
| `error-patterns` | [leyline](#leyline) | Standardized error handling |
| `escalation-governance` | [abstract](#abstract) | Model escalation decisions |
| `evaluation-framework` | [leyline](#leyline) | Decision thresholds |
| `evidence-logging` | [imbue](#imbue) | Capture methodology |
| `feature-review` | [imbue](#imbue) | Feature prioritization and gap analysis |
| `file-analysis` | [sanctum](#sanctum) | File structure analysis |
| `gemini-delegation` | [conjure](#conjure) | Gemini CLI integration |
| `gif-generation` | [scry](#scry) | Video to GIF conversion |
| `git-workspace-review` | [sanctum](#sanctum) | Repo state analysis |
| `github-initiative-pulse` | [minister](#minister) | Initiative progress tracking |
| `hook-authoring` | [abstract](#abstract) | Security-first hook development |
| `hooks-eval` | [abstract](#abstract) | Hook security scanning |
| `knowledge-intake` | [memory-palace](#memory-palace) | Intake and curation |
| `knowledge-locator` | [memory-palace](#memory-palace) | Spatial search |
| `makefile-dogfooder` | [abstract](#abstract) | Makefile analysis and enhancement |
| `makefile-review` | [pensive](#pensive) | Makefile best practices |
| `math-review` | [pensive](#pensive) | Mathematical correctness |
| `mcp-code-execution` | [conservation](#conservation) | MCP patterns for data pipelines |
| `media-composition` | [scry](#scry) | Multi-source GIF stitching |
| `mecw-patterns` | [leyline](#leyline) | MECW implementation |
| `memory-palace-architect` | [memory-palace](#memory-palace) | Building virtual palaces |
| `modular-skills` | [abstract](#abstract) | Modular design patterns |
| `optimizing-large-skills` | [conservation](#conservation) | Large skill optimization |
| `performance-optimization` | [abstract](#abstract) | Skill loading optimization |
| `pr-prep` | [sanctum](#sanctum) | PR preparation |
| `pr-review` | [sanctum](#sanctum) | PR review workflows |
| `progressive-loading` | [leyline](#leyline) | Dynamic content loading |
| `python-async` | [parseltongue](#parseltongue) | Async patterns |
| `python-packaging` | [parseltongue](#parseltongue) | Packaging with uv |
| `python-performance` | [parseltongue](#parseltongue) | Profiling and optimization |
| `python-testing` | [parseltongue](#parseltongue) | Pytest/TDD workflows |
| `pytest-config` | [leyline](#leyline) | Pytest configuration patterns |
| `qwen-delegation` | [conjure](#conjure) | Qwen MCP integration |
| `quota-management` | [leyline](#leyline) | Rate limiting and quotas |
| `release-health-gates` | [minister](#minister) | Release readiness checks |
| `review-core` | [imbue](#imbue) | Scaffolding for detailed reviews |
| `rust-review` | [pensive](#pensive) | Rust-specific checking |
| `scope-guard` | [imbue](#imbue) | Anti-overengineering |
| `service-registry` | [leyline](#leyline) | Service discovery patterns |
| `session-palace-builder` | [memory-palace](#memory-palace) | Session-specific palaces |
| `shared-patterns` | [abstract](#abstract) | Reusable plugin development patterns |
| `skill-authoring` | [abstract](#abstract) | TDD methodology for skill creation |
| `skills-eval` | [abstract](#abstract) | Skill quality assessment |
| `spec-writing` | [spec-kit](#spec-kit) | Specification authoring |
| `speckit-orchestrator` | [spec-kit](#spec-kit) | Workflow coordination |
| `storage-templates` | [leyline](#leyline) | Storage abstraction patterns |
| `structured-output` | [imbue](#imbue) | Formatting patterns |
| `task-planning` | [spec-kit](#spec-kit) | Task generation |
| `test-review` | [pensive](#pensive) | Test quality review |
| `test-updates` | [sanctum](#sanctum) | Test maintenance |
| `testing-quality-standards` | [leyline](#leyline) | Test quality guidelines |
| `token-conservation` | [conservation](#conservation) | Token usage strategies and quota tracking |
| `tutorial-updates` | [sanctum](#sanctum) | Tutorial GIF generation orchestration |
| `unified-review` | [pensive](#pensive) | Review orchestration |
| `update-readme` | [sanctum](#sanctum) | README modernization |
| `usage-logging` | [leyline](#leyline) | Telemetry tracking |
| `version-updates` | [sanctum](#sanctum) | Version bumping |
| `vhs-recording` | [scry](#scry) | Terminal recordings via VHS |
| `workflow-improvement` | [sanctum](#sanctum) | Workflow retrospectives |

### All Commands (Alphabetical)

| Command | Plugin | Description |
|---------|--------|-------------|
| `/analyze-growth` | [conservation](#conservation) | Analyzes skill growth patterns and predicts context budget impact |
| `/analyze-hook` | [abstract](#abstract) | Analyzes individual hook files for security and performance |
| `/analyze-skill` | [abstract](#abstract) | Analyzes skill complexity and gets modularization recommendations |
| `/analyze-tests` | [parseltongue](#parseltongue) | Reports on test suite health |
| `/api-review` | [pensive](#pensive) | Runs API review |
| `/architecture-review` | [pensive](#pensive) | Runs architecture review |
| `/bug-review` | [pensive](#pensive) | Runs bug review |
| `/bulletproof-skill` | [abstract](#abstract) | Anti-rationalization workflow for hardening skills |
| `/catchup` | [imbue](#imbue) | Quickly understand recent changes and extract actionable insights |
| `/check-async` | [parseltongue](#parseltongue) | Validates async patterns |
| `/commit-msg` | [sanctum](#sanctum) | Generates a commit message |
| `/context-report` | [abstract](#abstract) | Generates context optimization report for skill directories |
| `/create-command` | [abstract](#abstract) | Scaffolds a new command |
| `/create-hook` | [abstract](#abstract) | Scaffolds a new hook with security-first design |
| `/create-skill` | [abstract](#abstract) | Scaffolds a new skill using best practices |
| `/estimate-tokens` | [abstract](#abstract) | Estimates token usage for skill files and dependencies |
| `/feature-review` | [imbue](#imbue) | Review implemented features using RICE+WSJF scoring |
| `/fix-issue` | [sanctum](#sanctum) | Workflow for fixing GitHub issues systematically |
| `/fix-pr` | [sanctum](#sanctum) | Addresses PR review comments with thread resolution |
| `/fix-workflow` | [sanctum](#sanctum) | Runs workflow retrospective and improves components |
| `/full-review` | [pensive](#pensive) | Unified code review with intelligent skill selection |
| `/garden` | [memory-palace](#memory-palace) | Manage digital gardens |
| `/git-catchup` | [sanctum](#sanctum) | Git repository catchup using imbue methodology |
| `/hooks-eval` | [abstract](#abstract) | Comprehensive hook evaluation framework |
| `/make-dogfood` | [abstract](#abstract) | Analyzes and enhances Makefiles for functionality coverage |
| `/makefile-review` | [pensive](#pensive) | Runs Makefile review |
| `/math-review` | [pensive](#pensive) | Runs mathematical review |
| `/merge-docs` | [sanctum](#sanctum) | Consolidates ephemeral docs into permanent documentation |
| `/navigate` | [memory-palace](#memory-palace) | Search and traverse palaces |
| `/optimize-context` | [conservation](#conservation) | Analyzes and optimizes context window usage using MECW principles |
| `/palace` | [memory-palace](#memory-palace) | Manage memory palaces |
| `/pr` | [sanctum](#sanctum) | Prepares a Pull Request |
| `/pr-review` | [sanctum](#sanctum) | Enhanced PR review with quality checks |
| `/record-browser` | [scry](#scry) | Record browser sessions using Playwright |
| `/record-terminal` | [scry](#scry) | Record terminal sessions using VHS |
| `/reinstall-all-plugins` | [leyline](#leyline) | Uninstalls and reinstalls all plugins to refresh cache |
| `/resolve-threads` | [sanctum](#sanctum) | Batch-resolve unresolved PR review threads |
| `/review` | [imbue](#imbue) | Start a structured review workflow with evidence logging |
| `/run-profiler` | [parseltongue](#parseltongue) | Profiles code execution |
| `/rust-review` | [pensive](#pensive) | Runs Rust-specific review |
| `/skills-eval` | [abstract](#abstract) | Runs skill quality assessment |
| `/speckit-analyze` | [spec-kit](#spec-kit) | Check consistency across artifacts |
| `/speckit-checklist` | [spec-kit](#spec-kit) | Generate a custom checklist for the feature |
| `/speckit-clarify` | [spec-kit](#spec-kit) | Identify underspecified areas with targeted questions |
| `/speckit-constitution` | [spec-kit](#spec-kit) | Create or update project constitution |
| `/speckit-implement` | [spec-kit](#spec-kit) | Execute the tasks |
| `/speckit-plan` | [spec-kit](#spec-kit) | Generate an implementation plan |
| `/speckit-specify` | [spec-kit](#spec-kit) | Create a new specification |
| `/speckit-startup` | [spec-kit](#spec-kit) | Bootstrap speckit workflow at session start |
| `/speckit-tasks` | [spec-kit](#spec-kit) | Generate tasks from the plan |
| `/structured-review` | [imbue](#imbue) | Start structured review workflow with evidence logging |
| `/test-review` | [pensive](#pensive) | Runs test quality review |
| `/test-skill` | [abstract](#abstract) | Skill testing workflow with TDD methodology |
| `/update-all-plugins` | [leyline](#leyline) | Updates all installed plugins from marketplaces |
| `/update-dependencies` | [sanctum](#sanctum) | Scan and update dependencies across all ecosystems |
| `/update-docs` | [sanctum](#sanctum) | Updates documentation |
| `/update-readme` | [sanctum](#sanctum) | Updates README with language-aware exemplar mining |
| `/update-tests` | [sanctum](#sanctum) | Updates and maintains tests |
| `/update-tutorial` | [sanctum](#sanctum) | Generate tutorials with GIF recordings |
| `/update-version` | [sanctum](#sanctum) | Bumps project versions |
| `/validate-hook` | [abstract](#abstract) | Validates hook security, performance, and compliance |
| `/validate-plugin` | [abstract](#abstract) | Checks a plugin's structure against requirements |
| `make delegate-auto` | [conjure](#conjure) | Auto-selects best service for a task |
| `make quota-status` | [conjure](#conjure) | Shows current quota usage |
| `make usage-report` | [conjure](#conjure) | Summarizes token usage and costs |

### All Agents (Alphabetical)

| Agent | Plugin | Description |
|-------|--------|-------------|
| `architecture-reviewer` | [pensive](#pensive) | Principal-level architecture review specialist |
| `code-reviewer` | [pensive](#pensive) | Expert code review for bugs, security, and quality |
| `commit-agent` | [sanctum](#sanctum) | Conventional commit message generator |
| `context-optimizer` | [conservation](#conservation) | Autonomous agent for context window optimization and MECW compliance |
| `dependency-updater` | [sanctum](#sanctum) | Multi-ecosystem dependency analysis and updates |
| `garden-curator` | [memory-palace](#memory-palace) | Maintains digital gardens |
| `git-workspace-agent` | [sanctum](#sanctum) | Repository state analyzer |
| `implementation-executor` | [spec-kit](#spec-kit) | Executes tasks and writes code |
| `knowledge-librarian` | [memory-palace](#memory-palace) | Evaluates and routes knowledge for storage |
| `knowledge-navigator` | [memory-palace](#memory-palace) | Searches and retrieves from palaces |
| `meta-architect` | [abstract](#abstract) | Designs architectures for the plugin ecosystem |
| `palace-architect` | [memory-palace](#memory-palace) | Designs memory palace architectures |
| `plugin-validator` | [abstract](#abstract) | Validates plugin structure against official requirements |
| `pr-agent` | [sanctum](#sanctum) | Pull request preparation specialist |
| `python-optimizer` | [parseltongue](#parseltongue) | Expert performance optimization and profiling agent |
| `python-pro` | [parseltongue](#parseltongue) | Master Python 3.12+ with modern features and best practices |
| `python-tester` | [parseltongue](#parseltongue) | Expert testing agent for pytest, TDD, and mocking strategies |
| `review-analyst` | [imbue](#imbue) | Autonomous agent for structured reviews with evidence gathering |
| `rust-auditor` | [pensive](#pensive) | Expert Rust security and safety auditor |
| `skill-auditor` | [abstract](#abstract) | Audits skills for quality and compliance |
| `spec-analyzer` | [spec-kit](#spec-kit) | Validates consistency across spec artifacts |
| `task-generator` | [spec-kit](#spec-kit) | Creates implementation tasks |
| `workflow-improvement-analysis-agent` | [sanctum](#sanctum) | Generates improvement approaches with trade-offs |
| `workflow-improvement-implementer-agent` | [sanctum](#sanctum) | Applies focused changes with tests |
| `workflow-improvement-planner-agent` | [sanctum](#sanctum) | Selects approach and creates execution plan |
| `workflow-improvement-validator-agent` | [sanctum](#sanctum) | Validates improvements via replay and metrics |
| `workflow-recreate-agent` | [sanctum](#sanctum) | Reconstructs workflow slices and surfaces inefficiencies |

### All Hooks (Alphabetical)

| Hook | Plugin | Type | Description |
|------|--------|------|-------------|
| `bridge.after_tool_use` | [conjure](#conjure) | PostToolUse | Suggests delegation if tool output is truncated or massive |
| `bridge.on_tool_start` | [conjure](#conjure) | PreToolUse | Suggests delegation when input files exceed context thresholds |
| `local_doc_processor.py` | [memory-palace](#memory-palace) | PostToolUse | Processes local documentation files after Read operations |
| `post-evaluation.json` | [abstract](#abstract) | Config | Configuration for post-evaluation actions (quality scoring, improvement tracking) |
| `post_implementation_policy.py` | [sanctum](#sanctum) | SessionStart | Injects post-implementation protocol requiring docs/tests/readme updates |
| `pre-pr-scope-check.sh` | [imbue](#imbue) | Manual | Checks scope before PR creation (available for manual configuration) |
| `pre-skill-load.json` | [abstract](#abstract) | Config | Configuration for pre-load validation (YAML frontmatter, dependencies) |
| `research_interceptor.py` | [memory-palace](#memory-palace) | PreToolUse | Checks local knowledge before web searches (WebFetch/WebSearch) |
| `session-start.sh` | [conservation](#conservation), [imbue](#imbue) | SessionStart | Loads conservation/scope-guard guidance at session start |
| `session_complete_notify.py` | [sanctum](#sanctum) | Stop | Cross-platform toast notification when Claude awaits input |
| `url_detector.py` | [memory-palace](#memory-palace) | UserPromptSubmit | Detects URLs in user prompts and suggests knowledge intake |
| `user-prompt-submit.sh` | [imbue](#imbue) | UserPromptSubmit | Validates prompts against scope thresholds |
| `verify_workflow_complete.py` | [sanctum](#sanctum) | Stop | Verifies workflow completion |
| `web_content_processor.py` | [memory-palace](#memory-palace) | PostToolUse | Processes web content for storage after WebFetch/WebSearch |

---

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
- [Scry](#scry)
- [Spec Kit](#spec-kit)
- [Superpowers Dependencies](#superpowers-dependencies)
- [Project-Level Agents](#project-level-agents)

---

## Project-Level Agents

The claude-night-market repository includes three main-thread agent configurations in `.claude/agents/` for consistent multi-session workflows. These are **not plugin agents** (which run in subagent mode), but rather main-thread configurations that shape your entire session.

### Available Agents

| Agent | File | Purpose |
|-------|------|---------|
| `plugin-developer` | `.claude/agents/plugin-developer.md` | **Default agent** for night-market plugin development (set in `.claude/settings.json`) |
| `code-review-mode` | `.claude/agents/code-review-mode.md` | Evidence-based code review sessions with imbue/pensive integration |
| `documentation-mode` | `.claude/agents/documentation-mode.md` | Documentation-focused workflows with sanctum integration |

### Usage

**Automatic (Project Default)**:
```bash
# When you start claude in the project directory, plugin-developer loads automatically
cd claude-night-market
claude
```

**Explicit Agent Selection**:
```bash
# Start with a specific agent
claude --agent code-review-mode
claude --agent documentation-mode
```

**Configuration**:
The project default is set in `.claude/settings.json`:
```json
{
  "agent": "plugin-developer",
  "description": "claude-night-market project settings"
}
```

### Agent Capabilities

**plugin-developer**:
- Tools: Read, Write, Edit, Bash, Glob, Grep, Task, WebFetch, WebSearch
- Model: Sonnet
- Skills: `abstract:validate-plugin`, `abstract:skill-authoring`, `plugin-dev:plugin-structure`
- Focus: Validation-first development, skill quality, agent design

**code-review-mode**:
- Tools: Read, Grep, Glob, WebFetch, WebSearch (read-only analysis)
- Model: Sonnet
- Skills: `pensive:code-reviewer`, `imbue:evidence-logging`, `imbue:diff-analysis`
- Focus: Evidence-based code review, security analysis, quality assessment

**documentation-mode**:
- Tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch
- Model: Sonnet
- Skills: `sanctum:doc-updates`, `sanctum:git-workspace-review`, `conservation:context-optimization`
- Focus: Documentation maintenance, writing guidelines, accuracy verification

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
| **spec-kit** | `/speckit-clarify` | Command | `superpowers:brainstorming` | Enhanced clarification questioning |
| **spec-kit** | `/speckit-plan` | Command | `superpowers:writing-plans` | Structured implementation planning |
| **spec-kit** | `/speckit-tasks` | Command | `superpowers:executing-plans`, `superpowers:systematic-debugging` | Task breakdown with debugging support |
| **spec-kit** | `/speckit-implement` | Command | `superpowers:executing-plans`, `superpowers:systematic-debugging` | Execution with error handling |
| **spec-kit** | `/speckit-analyze` | Command | `superpowers:systematic-debugging`, `superpowers:verification-before-completion` | Cross-artifact consistency checks |
| **spec-kit** | `/speckit-checklist` | Command | `superpowers:verification-before-completion` | Evidence-based checklist validation |
| **spec-kit** | `speckit-orchestrator` | Skill | Multiple superpowers | Full SDD workflow coordination |
| **spec-kit** | `task-planning` | Skill | `superpowers:writing-plans`, `superpowers:executing-plans` | Structured task generation |
| **pensive** | `/full-review` | Command | `superpowers:systematic-debugging`, `superpowers:verification-before-completion` | Four-phase debugging + evidence standards |
| **parseltongue** | `python-testing` | Skill | `superpowers:test-driven-development`, `superpowers:testing-anti-patterns` | TDD cycles + anti-pattern detection |
| **imbue** | `scope-guard` | Skill | `superpowers:brainstorming`, `superpowers:writing-plans`, `superpowers:execute-plan` | Anti-overengineering during workflows |
| **imbue** | `/feature-review` | Command | `superpowers:brainstorming` | Evidence-based feature prioritization |
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
| `post-evaluation.json` | Config | Configuration for post-evaluation actions (quality scoring, improvement tracking). |
| `pre-skill-load.json` | Config | Configuration for pre-load validation (YAML frontmatter, dependencies). |

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
| `bridge.on_tool_start` | PreToolUse | Suggests delegation when input files exceed context thresholds. |
| `bridge.after_tool_use` | PostToolUse | Suggests delegation if tool output is truncated or massive. |

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
| `session-start.sh` | SessionStart | Loads conservation skills guidance at session start. Supports bypass modes via `CONSERVATION_MODE` env var. |

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
| `feature-review` | Feature prioritization and gap analysis. | Sprint planning, roadmap reviews, deciding what to build next. | `Skill(imbue:feature-review)` |

### Commands

| Command | Description |
|---------|-------------|
| `/catchup` | Quickly understand recent changes and extract actionable insights. |
| `/review` | Start a structured review workflow with evidence logging. |
| `/structured-review` | Structured review workflow with evidence logging and formatted output. |
| `/feature-review` | Review implemented features using RICE+WSJF scoring and suggest new features with GitHub integration. |

### Agents

| Agent | Description |
|-------|-------------|
| `review-analyst` | Autonomous agent for structured reviews with evidence gathering. |

### Hooks

| Hook | Type | Description |
|------|------|-------------|
| `session-start.sh` | SessionStart | Initializes session with scope-guard and learning mode. |
| `user-prompt-submit.sh` | UserPromptSubmit | Validates prompts against scope thresholds. |
| `pre-pr-scope-check.sh` | Manual | Checks scope before PR creation (available for manual configuration). |

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
| `research_interceptor.py` | PreToolUse | Checks local knowledge before web searches (WebFetch/WebSearch). |
| `url_detector.py` | UserPromptSubmit | Detects URLs in user prompts and suggests knowledge intake. |
| `local_doc_processor.py` | PostToolUse | Processes local documentation files after Read operations. |
| `web_content_processor.py` | PostToolUse | Processes web content for storage after WebFetch/WebSearch. |

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
| `tutorial-updates` | Tutorial GIF generation orchestration. | Regenerating tutorial GIFs, updating documentation demos. | `Skill(sanctum:tutorial-updates)` |
| `file-analysis` | File structure analysis. | Understanding file organization and dependencies. | `Skill(sanctum:file-analysis)` |
| `workflow-improvement` | Workflow retrospectives. | Improving slow, confusing, or fragile workflows. | `Skill(sanctum:workflow-improvement)` |

### Commands

| Command | Description |
|---------|-------------|
| `/git-catchup` | Git repository catchup using imbue methodology. |
| `/commit-msg` | Generates a commit message. |
| `/pr` | Prepares a Pull Request. |
| `/pr-review` | Enhanced PR review with quality checks. |
| `/fix-pr` | Addresses PR review comments with thread resolution and automatic issue linkage (closes/comments on related issues). |
| `/fix-issue` | Workflow for fixing GitHub issues systematically with parallel execution. |
| `/resolve-threads` | Batch-resolve all unresolved PR review threads via GraphQL. |
| `/fix-workflow` | Runs workflow retrospective and improves components. |
| `/merge-docs` | Consolidates ephemeral docs into permanent documentation. |
| `/update-docs` | Updates documentation. |
| `/update-readme` | Updates README with language-aware exemplar mining. |
| `/update-tests` | Updates and maintains tests. |
| `/update-tutorial` | Generate tutorials with accompanying GIF recordings. |
| `/update-dependencies` | Scan and update dependencies across all ecosystems. |
| `/update-version` | Bumps project versions. |

### Agents

| Agent | Description |
|-------|-------------|
| `git-workspace-agent` | Repository state analyzer. |
| `commit-agent` | Conventional commit message generator. |
| `pr-agent` | Pull request preparation specialist. |
| `dependency-updater` | Multi-ecosystem dependency analysis and updates. |
| `workflow-recreate-agent` | Reconstructs workflow slices and surfaces inefficiencies. |
| `workflow-improvement-analysis-agent` | Generates improvement approaches with trade-offs. |
| `workflow-improvement-planner-agent` | Selects approach and creates execution plan. |
| `workflow-improvement-implementer-agent` | Applies focused changes with tests. |
| `workflow-improvement-validator-agent` | Validates improvements via replay and metrics. |

### Hooks

| Hook | Type | Description |
|------|------|-------------|
| `post_implementation_policy.py` | SessionStart | Injects post-implementation protocol requiring docs/tests/readme updates. |
| `verify_workflow_complete.py` | Stop | Verifies workflow completion. |
| `session_complete_notify.py` | Stop | Cross-platform toast notification (Linux/macOS/Windows) when Claude awaits input. |

---

## Scry

**Purpose**: Media generation capabilities for terminal recordings (VHS), browser recordings (Playwright), GIF processing, and media composition.

### Skills

| Skill | Description | Use Case | Example |
|-------|-------------|----------|---------|
| `vhs-recording` | Terminal recordings via VHS. | Creating terminal demos for tutorials. | `Skill(scry:vhs-recording)` |
| `browser-recording` | Playwright browser recording. | Recording web UI interactions for documentation. | `Skill(scry:browser-recording)` |
| `gif-generation` | Video to GIF conversion. | Converting WebM/MP4 to optimized GIFs. | `Skill(scry:gif-generation)` |
| `media-composition` | Multi-source GIF stitching. | Combining terminal and browser recordings. | `Skill(scry:media-composition)` |

### Commands

| Command | Description |
|---------|-------------|
| `/record-terminal` | Record terminal sessions using VHS tape files. |
| `/record-browser` | Record browser sessions using Playwright specs. |

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
| `/speckit-specify` | Create a new specification. |
| `/speckit-plan` | Generate an implementation plan. |
| `/speckit-tasks` | Generate tasks from the plan. |
| `/speckit-implement` | Execute the tasks. |
| `/speckit-analyze` | Check consistency across artifacts. |
| `/speckit-checklist` | Generate a custom checklist for the feature. |
| `/speckit-clarify` | Identify underspecified areas with targeted questions. |
| `/speckit-constitution` | Create or update project constitution. |
| `/speckit-startup` | Bootstrap speckit workflow at session start. |

### Agents

| Agent | Description |
|-------|-------------|
| `spec-analyzer` | Validates consistency across spec artifacts. |
| `task-generator` | Creates implementation tasks. |
| `implementation-executor` | Executes tasks and writes code. |
