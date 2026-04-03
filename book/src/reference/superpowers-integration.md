# Superpowers Integration

How Claude Night Market plugins integrate with the
[superpowers](https://github.com/obra/superpowers) skills.

**Last synced**: superpowers v5.0.7 (2026-03-31)

## Overview

Many Night Market capabilities achieve their full potential
when used alongside superpowers.
While all plugins work standalone, superpowers provides
foundational methodology skills that enhance workflows.

Since v4.0.0, superpowers enforces workflows via hard
gates, DOT flowcharts, and mandatory checklists rather
than simply describing them.
Since v5.0.6, inline self-review replaces subagent review
loops, cutting review overhead from ~25 minutes to ~30
seconds.

## Installation

```bash
# Add the superpowers marketplace
/plugin marketplace add obra/superpowers

# Install the superpowers plugin
/plugin install superpowers@superpowers-marketplace
```

## Dependency Matrix

| Plugin | Component | Type | Superpowers Dependency | Enhancement |
|--------|-----------|------|------------------------|-------------|
| **abstract** | `/create-skill` | Command | `brainstorming` | Socratic questioning |
| **abstract** | `/create-command` | Command | `brainstorming` | Concept development |
| **abstract** | `/create-hook` | Command | `brainstorming` | Security design |
| **abstract** | `/test-skill` | Command | `test-driven-development` | TDD methodology |
| **sanctum** | `/pr` | Command | `receiving-code-review`, `requesting-code-review` | PR validation |
| **sanctum** | `/pr-review` | Command | `receiving-code-review` | PR analysis |
| **sanctum** | `/fix-pr` | Command | `receiving-code-review` | Comment resolution |
| **sanctum** | `/do-issue` | Command | `subagent-driven-development`, `dispatching-parallel-agents`, `using-git-worktrees` | Full workflow |
| **spec-kit** | `/speckit-clarify` | Command | `brainstorming` | Clarification |
| **spec-kit** | `/speckit-plan` | Command | `writing-plans` | Planning |
| **spec-kit** | `/speckit-tasks` | Command | `executing-plans`, `systematic-debugging` | Task breakdown |
| **spec-kit** | `/speckit-implement` | Command | `executing-plans`, `systematic-debugging` | Execution |
| **spec-kit** | `/speckit-analyze` | Command | `systematic-debugging`, `verification-before-completion` | Consistency |
| **spec-kit** | `/speckit-checklist` | Command | `verification-before-completion` | Validation |
| **pensive** | `/full-review` | Command | `systematic-debugging`, `verification-before-completion` | Debugging + evidence |
| **parseltongue** | `python-testing` | Skill | `test-driven-development` (includes testing-anti-patterns) | TDD + anti-patterns |
| **imbue** | `scope-guard`, `proof-of-work` | Skill | `brainstorming`, `writing-plans`, `executing-plans`, `verification-before-completion` | Anti-overengineering, evidence-based completion |
| **conserve** | `/optimize-context` | Command | `systematic-debugging` (includes condition-based-waiting) | Smart waiting |
| **minister** | `issue-management` | Skill | `systematic-debugging` | Bug investigation |

## Superpowers Skills Referenced

| Skill | Purpose | Used By |
|-------|---------|---------|
| `brainstorming` | Socratic questioning with hard gates and visual companion | abstract, spec-kit, imbue |
| `test-driven-development` | RED-GREEN-REFACTOR TDD cycle (includes testing-anti-patterns) | abstract, sanctum, parseltongue |
| `receiving-code-review` | Technical rigor for evaluating suggestions | sanctum |
| `requesting-code-review` | Quality gates for code submission | sanctum |
| `writing-plans` | Structured planning with inline self-review | spec-kit, imbue |
| `executing-plans` | Continuous task execution (no longer batches) | spec-kit |
| `systematic-debugging` | Four-phase framework (includes root-cause-tracing, defense-in-depth, condition-based-waiting) | spec-kit, pensive, minister, conserve |
| `verification-before-completion` | Evidence-based review standards | spec-kit, pensive, imbue |
| `subagent-driven-development` | Autonomous subagent orchestration (mandatory on capable harnesses) | sanctum |
| `dispatching-parallel-agents` | Parallel task dispatch for 2+ independent tasks | sanctum |
| `using-git-worktrees` | Isolated implementation in feature branches | sanctum |
| `finishing-a-development-branch` | Branch cleanup, merge strategy, and finalization | sanctum |
| `writing-skills` | Skill authoring with description trap guidance | abstract |

## Graceful Degradation

All Night Market plugins work without superpowers:

### Without Superpowers

- **Commands**: Execute core functionality
- **Skills**: Provide standalone guidance
- **Agents**: Function with reduced automation

### With Superpowers

- **Commands**: Enhanced methodology phases
- **Skills**: Integrated methodology patterns
- **Agents**: Full automation depth

## Skill Consolidation Notes (v4.0.0+)

Several standalone skills were merged into parent skills:

| Former Standalone | Now Bundled In | Access |
|-------------------|----------------|--------|
| `testing-anti-patterns` | `test-driven-development` | Module file within TDD skill |
| `root-cause-tracing` | `systematic-debugging` | Module file within debugging skill |
| `defense-in-depth` | `systematic-debugging` | Module file within debugging skill |
| `condition-based-waiting` | `systematic-debugging` | Module file within debugging skill |

## Deprecated Commands

These superpowers slash commands show deprecation notices
since v5.0.0. Use the skill equivalents:

| Deprecated | Replacement |
|------------|-------------|
| `/brainstorm` | `Skill(superpowers:brainstorming)` |
| `/write-plan` | `Skill(superpowers:writing-plans)` |
| `/execute-plan` | `Skill(superpowers:executing-plans)` |

## Key Patterns

### Inline Self-Review (v5.0.6)

Superpowers replaced subagent review loops with inline
self-review checklists. This cut review time from ~25
minutes to ~30 seconds with comparable defect detection.
Night Market review workflows (pensive, sanctum, imbue)
should follow this pattern when delegating to superpowers.

### SUBAGENT-STOP Gate

Superpowers skills include `<SUBAGENT-STOP>` blocks that
prevent subagents from activating full skill workflows.
Night Market dispatch patterns (sanctum:do-issue,
conserve:clear-context) should be aware of this when
delegating work to subagents with superpowers installed.

### Instruction Priority Hierarchy

Superpowers enforces: User instructions > Superpowers
skills > Default system prompt. Night Market commands
respect this ordering when combining skill invocations.

### Context Isolation

All superpowers delegation skills now scope subagent
context explicitly. Night Market's parallel execution
patterns should follow the same principle.

## Example: /do-issue Workflow

### Without Superpowers

```
1. Parse issue
2. Analyze codebase
3. Implement fix
4. Create PR
```

### With Superpowers

```
1. Parse issue
2. [using-git-worktrees] Create isolated worktree
3. [subagent-driven-development] Plan subagent tasks
4. [dispatching-parallel-agents] Dispatch parallel work
5. [writing-plans] Create structured plan
6. [test-driven-development] Write failing test
7. Implement fix
8. [requesting-code-review] Inline self-review
9. [finishing-a-development-branch] Cleanup and merge
10. Create PR
```

## Recommended Setup

For the full Night Market experience:

```bash
# 1. Add marketplaces
/plugin marketplace add obra/superpowers
/plugin marketplace add athola/claude-night-market

# 2. Install superpowers (foundational)
/plugin install superpowers@superpowers-marketplace

# 3. Install Night Market plugins
/plugin install sanctum@claude-night-market
/plugin install spec-kit@claude-night-market
/plugin install pensive@claude-night-market
```

## Checking Integration

Verify superpowers is available:

```bash
/plugin list
# Should show superpowers@superpowers-marketplace
```

Commands will automatically detect and use superpowers when available.
