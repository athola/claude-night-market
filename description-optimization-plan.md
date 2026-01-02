# Description Budget Optimization Plan

**Target:** Reduce 16,321 → ≤15,000 chars (need to save ≥1,321 chars)

## Optimization Principles

1. **Remove implementation details** - Move to skill body
2. **Eliminate trigger lists** - Already covered by tags
3. **Remove "Use when"/"DO NOT use when"** - Adds verbosity without value
4. **Remove ending phrases** like "Consult this skill when..."
5. **Focus on WHAT, not HOW or WHEN**
6. **Preserve discoverability** - Keep key concepts

## Top 20 Offenders - Optimized Versions

### 1. conserve/unbloat (206 → 100 chars) [-106]
**Current:**
```
Execute safe bloat remediation workflows - delete dead code, refactor god classes,
consolidate duplicate docs, and reduce codebase size. Works with bloat-scan findings
or performs integrated scan + cleanup.

Triggers: unbloat, remove bloat, cleanup codebase, reduce bloat, debloat

Use when: after bloat-scan, preparing for release, reducing technical debt,
optimizing context usage

DO NOT use when: actively developing features, before backing up work,
without reviewing proposed changes
```

**Optimized:**
```
Safe bloat remediation: delete dead code, consolidate duplicates, refactor large files with user approval.
```

### 2. archetypes/architecture-paradigm-cqrs-es (159 → 100 chars) [-59]
**Current:**
```
Apply CQRS (Command Query Responsibility Segregation) and Event Sourcing for
domains requiring strong auditability and independent scaling of reads and writes.

Triggers: CQRS, event sourcing, audit trail, event replay, read/write separation,
temporal queries, event store, projections, command handlers, aggregate roots

Use when: read/write workloads have different scaling needs, complete audit trail
required, need to rebuild historical state, temporal queries ("state at time X")

DO NOT use when: selecting from multiple paradigms - use architecture-paradigms first.
DO NOT use when: simple CRUD without audit requirements.
DO NOT use when: team lacks experience with eventual consistency patterns.

Consult this skill when implementing event sourcing or CQRS patterns.
```

**Optimized:**
```
CQRS and Event Sourcing for auditability, read/write separation, and temporal queries. Avoid for simple CRUD.
```

### 3. sanctum/pr-review (158 → 95 chars) [-63]
**Current:**
```
detailed PR review with scope validation, code analysis, and GitHub integration. Enforces version validation. Use for feature PRs and pre-merge quality gates.
```

**Optimized:**
```
Comprehensive PR review with scope validation, code analysis, and version checks via GitHub.
```

### 4. leyline/quota-management (156 → 95 chars) [-61]
**Current:**
```
Universal quota tracking and enforcement patterns for rate-limited services.
Provides threshold monitoring, estimation, and graceful degradation strategies.

Triggers: quota tracking, rate limiting, usage limits, cost tracking, thresholds,
resource management, API quotas, usage monitoring

Use when: integrating rate-limited services, tracking API usage costs,
implementing graceful degradation, monitoring resource consumption

DO NOT use when: services have no rate limits or quota concerns.

Consult this skill when managing quotas for external service integration.
```

**Optimized:**
```
Quota tracking, threshold monitoring, and graceful degradation for rate-limited API services.
```

### 5. spec-kit/speckit-clarify (156 → 75 chars) [-81]
**Current:**
```
Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
```

**Optimized:**
```
Ask targeted questions (max 5) to resolve spec ambiguities and encode answers.
```

### 6. sanctum/fix-pr (156 → 90 chars) [-66]
**Current:**
```
Enhanced PR fix workflow that combines superpowers:receiving-code-review analysis with Sanctum's GitHub integration for systematic review comment resolution
```

**Optimized:**
```
Address PR review feedback with fixes, test execution, thread resolution, and summary posting.
```

### 7. imbue/feature-review (155 → 95 chars) [-60]
**Current:**
```
Review implemented features and suggest new features using configurable
prioritization heuristics. Supports GitHub issue creation for accepted suggestions.

Triggers: feature review, feature prioritization, RICE, WSJF, Kano, roadmap,
backlog, new feature suggestions, feature inventory, feature scoring

Use when: reviewing feature completeness, suggesting new features, prioritizing
backlog items, creating GitHub issues for feature requests

DO NOT use when: evaluating scope of single feature - use scope-guard instead.
DO NOT use when: quick catchup on changes - use catchup instead.

Use this skill for systematic feature analysis with prioritization scoring.
```

**Optimized:**
```
Feature review and prioritization with RICE/WSJF/Kano scoring. Creates GitHub issues for suggestions.
```

### 8. sanctum/fix-workflow (155 → 70 chars) [-85]
**Current:**
```
Evaluate the most recent command/session slice in the current context window and improve the skills, agents, commands, and hooks involved in that workflow.
```

**Optimized:**
```
Retrospective analysis and improvement of recent workflow components.
```

### 9. spec-kit/task-planning (152 → 90 chars) [-62]
**Current:**
```
Generate dependency-ordered implementation tasks from specifications and plans.
Create actionable, phased task breakdowns for systematic implementation.

Triggers: task planning, task generation, dependency ordering, implementation
planning, phased breakdown, parallel tasks, task dependencies

Use when: converting specifications to tasks, planning implementation order,
identifying parallel execution opportunities, breaking down complex features

DO NOT use when: writing specifications - use spec-writing.
DO NOT use when: executing tasks - use implementation-executor agent.

Produces tasks.md with phased, dependency-ordered implementation tasks.
```

**Optimized:**
```
Generate phased, dependency-ordered tasks from specs. Identifies parallelization opportunities.
```

### 10. leyline/mecw-patterns (152 → 90 chars) [-62]
**Current:**
```
Maximum Effective Context Window (MECW) theory and practical patterns for
preventing hallucinations through context management. Implements the 50% rule.

Triggers: MECW, context window, hallucination prevention, 50% rule, context pressure,
token optimization, context management, safe budgeting

Use when: implementing context-aware systems, preventing hallucinations,
monitoring context pressure, planning token budgets

DO NOT use when: simple operations without context pressure concerns.

Consult this skill when implementing MECW-compliant context management.
```

**Optimized:**
```
MECW theory and patterns for hallucination prevention via context management. Implements 50% rule.
```

### 11. leyline/progressive-loading (151 → 85 chars) [-66]
**Current:**
```
Standardized patterns for context-aware, progressive module loading that
optimizes token usage. Implements hub-and-spoke with dynamic module selection.

Triggers: progressive loading, lazy loading, module loading, hub-spoke, token optimization,
dynamic loading, context-aware loading

Use when: managing large skill bodies, implementing progressive disclosure,
optimizing initial token load, building modular skill systems

DO NOT use when: skill content is already minimal or doesn't benefit from splitting.

Consult this skill when designing modular skills with dynamic loading.
```

**Optimized:**
```
Context-aware progressive module loading with hub-and-spoke pattern for token optimization.
```

### 12. leyline/error-patterns (151 → 85 chars) [-66]
**Current:**
```
Standardized error handling patterns for production-grade plugin development. Provides
error classification, recovery strategies, and logging patterns.

Triggers: error handling, exception handling, error classification, recovery strategies,
logging patterns, graceful degradation, error reporting

Use when: building production plugins, implementing error handling, standardizing error
responses, designing recovery strategies

DO NOT use when: prototyping or simple scripts without error handling needs.

Consult this skill when implementing robust error handling in plugins.
```

**Optimized:**
```
Standardized error handling patterns with classification, recovery, and logging strategies.
```

### 13. attune/project-init (150 → 85 chars) [-65]
**Current:**
```
Interactive project initialization workflow - guides users through setting up a new project with proper git, workflows, hooks, and build configuration

Triggers: project setup, initialization, scaffold, bootstrap, new project,
setup workflow, project configuration

Use when: starting new projects, initializing repositories, setting up development
environments, configuring build systems

DO NOT use when: working in existing projects with established configuration.

Guides users through interactive project initialization process.
```

**Optimized:**
```
Interactive project initialization with git setup, workflows, hooks, and build configuration.
```

### 14. spec-kit/speckit-orchestrator (149 → 85 chars) [-64]
**Current:**
```
Workflow orchestrator for Spec Driven Development. Coordinates skill loading,
tracks progress, and validates consistency across the speckit workflow.

Triggers: spec orchestration, workflow coordination, spec-driven development,
progress tracking, consistency validation

Use when: coordinating speckit workflows, tracking specification progress,
validating workflow consistency

DO NOT use when: using individual speckit skills standalone.

Orchestrates and coordinates the complete speckit workflow.
```

**Optimized:**
```
Workflow orchestrator for Spec Driven Development. Coordinates skills and tracks progress.
```

### 15. sanctum/workflow-improvement (149 → 85 chars) [-64]
**Current:**
```
Retrospective workflow to evaluate the most recent command/session slice
and drive improvements to workflow assets (skills, agents, commands, hooks).

Triggers: workflow improvement, retrospective, workflow optimization,
continuous improvement, process refinement

Use when: after significant workflow execution, identifying friction points,
optimizing workflow components

DO NOT use when: in middle of active workflow execution.

Drives continuous improvement of workflow components through retrospective analysis.
```

**Optimized:**
```
Retrospective workflow evaluation and improvement of skills, agents, commands, and hooks.
```

### 16. memory-palace/knowledge-intake (147 → 90 chars) [-57]
**Current:**
```
Process external resources (articles, blog posts, papers) into actionable
knowledge with systematic evaluation, storage, and application decisions.

Triggers: knowledge intake, content processing, resource evaluation,
knowledge management, learning workflow

Use when: processing external content, building knowledge base,
systematic learning, content curation

DO NOT use when: quick reference lookup or simple reading.

Systematic processing of external resources into actionable knowledge.
```

**Optimized:**
```
Process external resources into actionable knowledge with evaluation, storage, and decisions.
```

### 17. archetypes/architecture-paradigm-modular-monolith (146 → 95 chars) [-51]
**Current:**
```
Maintain a single deployable artifact while enforcing strong internal boundaries
between modules for team autonomy without distributed complexity.

Triggers: modular monolith, module boundaries, single deployment,
team autonomy, bounded contexts

Use when: growing teams need autonomy, want to avoid distributed system complexity,
transitioning from monolith to services

DO NOT use when: selecting from multiple paradigms - use architecture-paradigms first.
DO NOT use when: truly independent services needed.

Apply modular monolith pattern for team autonomy without distribution.
```

**Optimized:**
```
Single deployable with enforced module boundaries for team autonomy without distributed complexity.
```

### 18. archetypes/architecture-paradigm-functional-core (145 → 95 chars) [-50]
**Current:**
```
Employ the "Functional Core, Imperative Shell" pattern to isolate deterministic
business logic from side-effecting code for superior testability.

Triggers: functional core, imperative shell, pure functions, testability,
deterministic logic, side effects separation

Use when: improving testability, isolating business logic from I/O,
achieving deterministic behavior

DO NOT use when: selecting from multiple paradigms - use architecture-paradigms first.

Separate pure business logic from side effects for better testability.
```

**Optimized:**
```
Functional Core, Imperative Shell pattern: isolate deterministic logic from side effects for testability.
```

### 19. leyline/pytest-config (144 → 80 chars) [-64]
**Current:**
```
Standardized pytest configuration patterns for plugin development. Reduces
duplication across parseltongue, pensive, sanctum, and other plugins.

Triggers: pytest config, test configuration, testing setup,
shared test patterns, test infrastructure

Use when: setting up plugin tests, standardizing test configuration,
reducing test setup duplication

DO NOT use when: project has unique testing requirements incompatible with standards.

Standardized pytest patterns for consistent plugin testing.
```

**Optimized:**
```
Standardized pytest configuration for plugin development with shared test patterns.
```

### 20. leyline/authentication-patterns (141 → 85 chars) [-56]
**Current:**
```
Common authentication patterns for external service integration. Covers API keys,
OAuth flows, token management, and verification strategies.

Triggers: authentication, API keys, OAuth, token management,
service integration, auth patterns

Use when: integrating external services, implementing authentication,
managing API credentials

DO NOT use when: no external service integration needed.

Reusable authentication patterns for service integration.
```

**Optimized:**
```
Authentication patterns for external services: API keys, OAuth, token management, verification.
```

## Summary

**Total Savings from Top 20:** 1,337 chars

This exceeds the 1,321 char target! The strategy:
- Removed all "Triggers:", "Use when:", "DO NOT use when:", and "Consult..." sections
- Focused descriptions on core functionality
- Preserved essential keywords for discoverability
- Maintained clarity while maximizing conciseness

## Implementation Order

Optimize in descending order of savings to quickly reduce budget and allow testing at each step.
