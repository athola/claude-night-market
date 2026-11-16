# Superpowers Integration

How Claude Night Market plugins integrate with the
[superpowers](https://github.com/obra/superpowers) skills.

**Last synced**: superpowers v7.0.2 (2026-11-03)

## Overview

Many Night Market capabilities achieve their full potential
when used alongside superpowers.
While all plugins work standalone, superpowers provides
foundational methodology skills that enhance workflows.

Superpowers enforces its workflows with hard gates and
checklists. Since v6.0.0 its skills name actions ("dispatch a
subagent", "your instructions file") rather than Claude Code
tools, and a per-harness reference maps each action to a tool.

## Installation

```bash
/plugin install superpowers@claude-plugins-official
```

Superpowers is in Anthropic's official marketplace, which
needs no `marketplace add` step. The
`obra/superpowers-marketplace` marketplace also carries it as
`superpowers@superpowers-marketplace`.

## Dependency Matrix

| Plugin | Component | Type | Superpowers Dependency | Enhancement |
|--------|-----------|------|------------------------|-------------|
| **abstract** | `/create-skill` | Command | `brainstorming` | Intent-first design |
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
| **parseltongue** | `python-testing` | Skill | `test-driven-development` (includes `writing-good-tests.md`) | TDD + test quality |
| **imbue** | `scope-guard`, `proof-of-work` | Skill | `brainstorming`, `writing-plans`, `executing-plans`, `verification-before-completion` | Anti-overengineering, evidence-based completion |
| **conserve** | `/optimize-context` | Command | `systematic-debugging` (includes condition-based-waiting) | Smart waiting |
| **minister** | `issue-management` | Skill | `systematic-debugging` | Bug investigation |

## Superpowers Skills Referenced

| Skill | Purpose | Used By |
|-------|---------|---------|
| `brainstorming` | Asks why first, sizes the work, writes a design, runs a builder check | abstract, spec-kit, imbue |
| `test-driven-development` | RED-GREEN-REFACTOR, with the project's whole suite defining green | abstract, sanctum, parseltongue |
| `receiving-code-review` | Technical rigor for evaluating suggestions | sanctum |
| `requesting-code-review` | Dispatches a general-purpose reviewer from a prompt template | sanctum |
| `writing-plans` | Plans that record decisions, not code, with inline self-review | spec-kit, imbue |
| `executing-plans` | Native execution: the session implements every task, then one whole-branch review | spec-kit |
| `systematic-debugging` | Four-phase framework (includes root-cause-tracing, defense-in-depth, condition-based-waiting) | spec-kit, pensive, minister, conserve |
| `verification-before-completion` | Evidence-based review standards | spec-kit, pensive, imbue |
| `subagent-driven-development` | One implementer and one task reviewer per task, plan-scoped ledger | sanctum |
| `dispatching-parallel-agents` | Parallel task dispatch for 2+ independent tasks | sanctum |
| `using-git-worktrees` | Asks before creating a worktree, prefers the harness's native tool | sanctum |
| `finishing-a-development-branch` | Merge or PR, worktree cleanup that keeps untracked files | sanctum |
| `writing-skills` | Skill authoring, with support docs split into `references/` | abstract |

`diagnosing-superpowers` (v6.4.1) reads session transcripts to
explain why a superpowers session went wrong. No Night Market
plugin calls it. Ask for it by name after a bad session.

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

## Bundled Reference Files

Several former standalone skills are files inside a parent skill:

| Former Standalone | Now Bundled In | File |
|-------------------|----------------|------|
| `testing-anti-patterns` | `test-driven-development` | `writing-good-tests.md` (renamed in v6.2.0) |
| `root-cause-tracing` | `systematic-debugging` | `root-cause-tracing.md` |
| `defense-in-depth` | `systematic-debugging` | `defense-in-depth.md` |
| `condition-based-waiting` | `systematic-debugging` | `condition-based-waiting.md` |

The `/brainstorm`, `/write-plan` and `/execute-plan` commands
and the `superpowers:code-reviewer` agent were removed in v5.1.0.
Invoke the skills directly.

## Key Patterns

### Review Model (v6.0.0 to v7.0.0)

Review depends on the stage. A written plan gets an inline
self-review, which checks that the plan is proportionate to the
spec and that its Review Focus is covered. A brainstorm design
gets a builder check: a fresh subagent reads it as the person
who will build it and lists what it would still need to ask.
Subagent-driven development runs one reviewer per task, which
returns a spec verdict and a quality verdict together. Both
execution modes end with one whole-branch review on the most
capable model.

### Plan Shape (v6.0.0 to v6.4.2)

A superpowers plan carries a Global Constraints block copied
verbatim into every task, a per-task Interfaces block naming
what each task consumes and produces, and a Review Focus section
listing up to five inputs or failure modes the spec implies but
no task tests. A step records a signature, a test's assertions
or a command with its passing output. Code bodies appear only
where those do not determine the code. The person reviews the
saved plan before anything runs.

### Two Execution Modes (v6.4.1)

The plan handoff offers Subagent-driven and Native execution and
recommends one. Native runs every task in the session and is the
cheaper mode. Neither mode stops every few tasks to check in.

### Skill Size and Compaction (v7.0.1)

After compaction Claude Code re-attaches each invoked skill but
keeps only its first 5,000 tokens. Superpowers moved long
guidance into `references/` files that a skill reads at the step
that needs them. Night Market enforces the same bound on its own
skills in `tests/test_skill_survives_compaction.py`.

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

All superpowers delegation skills scope subagent context
explicitly. Since v6.0.0 task text and diffs move between
agents as files rather than pasted text. Night Market's
parallel execution patterns follow the same principle.

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
2. [using-git-worktrees] Create isolated worktree (asks first)
3. [writing-plans] Create plan, reviewed before it runs
4. [subagent-driven-development] Implement and review each task
5. [dispatching-parallel-agents] Dispatch independent tasks in parallel
6. [test-driven-development] Write failing test first
7. [requesting-code-review] Whole-branch review
8. [finishing-a-development-branch] Cleanup and merge
9. Create PR
```

## Recommended Setup

For the full Night Market experience:

```bash
# 1. Install superpowers (foundational)
/plugin install superpowers@claude-plugins-official

# 2. Add the Night Market marketplace
/plugin marketplace add athola/claude-night-market

# 3. Install Night Market plugins
/plugin install sanctum@claude-night-market
/plugin install spec-kit@claude-night-market
/plugin install pensive@claude-night-market
```

## Checking Integration

Verify superpowers is available:

```bash
/plugin list
# Should show superpowers@claude-plugins-official
```

Commands will automatically detect and use superpowers when available.
