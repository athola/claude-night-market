# Superpowers Integration

How Claude Night Market plugins integrate with the [superpowers](https://github.com/obra/superpowers) skills.

## Overview

Many Night Market capabilities achieve their full potential when used alongside superpowers. While all plugins work standalone, superpowers provides foundational methodology skills that enhance workflows.

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
| **sanctum** | `/pr` | Command | `receiving-code-review` | PR validation |
| **sanctum** | `/pr-review` | Command | `receiving-code-review` | PR analysis |
| **sanctum** | `/fix-pr` | Command | `receiving-code-review` | Comment resolution |
| **sanctum** | `/fix-issue` | Command | Multiple | Full workflow |
| **spec-kit** | `/speckit.clarify` | Command | `brainstorming` | Clarification |
| **spec-kit** | `/speckit.plan` | Command | `writing-plans` | Planning |
| **spec-kit** | `/speckit.tasks` | Command | `executing-plans`, `systematic-debugging` | Task breakdown |
| **spec-kit** | `/speckit.implement` | Command | `executing-plans`, `systematic-debugging` | Execution |
| **spec-kit** | `/speckit.analyze` | Command | `systematic-debugging`, `verification-before-completion` | Consistency |
| **spec-kit** | `/speckit.checklist` | Command | `verification-before-completion` | Validation |
| **pensive** | `/full-review` | Command | `systematic-debugging`, `verification-before-completion` | Debugging + evidence |
| **parseltongue** | `python-testing` | Skill | `test-driven-development`, `testing-anti-patterns` | TDD + anti-patterns |
| **imbue** | `scope-guard` | Skill | `brainstorming`, `writing-plans`, `execute-plan` | Anti-overengineering |
| **imbue** | `/feature-review` | Command | `brainstorming` | Feature prioritization |
| **conservation** | `/optimize-context` | Command | `condition-based-waiting` | Smart waiting |
| **minister** | `issue-management` | Skill | `systematic-debugging` | Bug investigation |

## Superpowers Skills Referenced

| Skill | Purpose | Used By |
|-------|---------|---------|
| `brainstorming` | Socratic questioning for idea refinement | abstract, spec-kit, imbue |
| `test-driven-development` | RED-GREEN-REFACTOR TDD cycle | abstract, sanctum, parseltongue |
| `receiving-code-review` | Technical rigor for evaluating suggestions | sanctum |
| `requesting-code-review` | Quality gates for code submission | sanctum |
| `writing-plans` | Structured implementation planning | spec-kit, imbue |
| `executing-plans` | Task execution with checkpoints | spec-kit |
| `systematic-debugging` | Four-phase debugging framework | spec-kit, pensive, minister |
| `verification-before-completion` | Evidence-based review standards | spec-kit, pensive, imbue |
| `testing-anti-patterns` | Common testing mistake prevention | parseltongue |
| `condition-based-waiting` | Smart polling/waiting strategies | conservation |
| `subagent-driven-development` | Autonomous subagent orchestration | sanctum |
| `finishing-a-development-branch` | Branch cleanup and finalization | sanctum |

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

## Example: /fix-issue Workflow

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
2. [subagent-driven-development] Plan subagent tasks
3. [writing-plans] Create structured plan
4. [test-driven-development] Write failing test
5. Implement fix
6. [requesting-code-review] Self-review
7. [finishing-a-development-branch] Cleanup
8. Create PR
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
