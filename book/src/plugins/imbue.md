# imbue

Workflow methodologies for analysis, evidence gathering, and structured output.

## Overview

Imbue provides reusable patterns for approaching analysis tasks. It's a methodology plugin - the patterns apply to various inputs (git diffs, specs, logs) and chain together for complex workflows.

**Core Philosophy**: "NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST" - The Iron Law enforced through proof-of-work validation.

## Installation

```bash
/plugin install imbue@claude-night-market
```

## Principles

- **Generalizable**: Patterns work across different input types
- **Composable**: Skills chain together naturally
- **Evidence-based**: Emphasizes capturing proof for reproducibility
- **TDD-First**: Iron Law enforcement prevents cargo cult testing

## Skills

### Review Patterns

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `review-core` | Scaffolding for detailed reviews | Starting architecture, security, or code quality reviews |
| `evidence-logging` | Evidence capture methodology | Creating audit trails during analysis |
| `structured-output` | Output formatting patterns | Preparing final reports |

### Analysis Methods

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `diff-analysis` | Semantic changeset analysis | Understanding impact of changes |
| `catchup` | Context recovery | Getting up to speed after time away |

### Workflow Guards

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `scope-guard` | Anti-overengineering | Evaluating if features should be built now |
| `proof-of-work` | Evidence-based validation | Enforcing Iron Law TDD discipline |
| `rigorous-reasoning` | Anti-sycophancy guardrails | Analyzing conflicts, evaluating contested claims |

### Feature Planning

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `feature-review` | Feature prioritization | Sprint planning, roadmap reviews |

### Workflow Automation

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `workflow-monitor` | Execution monitoring and issue creation | After workflow failures or inefficiencies |

## Commands

| Command | Description |
|---------|-------------|
| `/catchup` | Quick context recovery from recent changes |
| `/structured-review` | Start structured review workflow with evidence logging |
| `/feature-review` | Feature prioritization with RICE+WSJF scoring |

## Agents

| Agent | Description |
|-------|-------------|
| `review-analyst` | Autonomous structured reviews with evidence gathering |

## Hooks

| Hook | Type | Description |
|------|------|-------------|
| `session-start.sh` | SessionStart | Initializes scope-guard, Iron Law, and learning mode |
| `user-prompt-submit.sh` | UserPromptSubmit | Validates prompts against scope thresholds |
| `tdd_bdd_gate.py` | PreToolUse | Enforces Iron Law at write-time |
| `pre-pr-scope-check.sh` | Manual | Checks scope before PR creation |
| `proof-enforcement.md` | Design | Iron Law TDD compliance enforcement |

## Usage Examples

### Structured Review

```bash
Skill(imbue:review-core)

# Required TodoWrite items:
# 1. review-core:context-established
# 2. review-core:scope-inventoried
# 3. review-core:evidence-captured
# 4. review-core:deliverables-structured
# 5. review-core:contingencies-documented
```

### Diff Analysis

```bash
Skill(imbue:diff-analysis)

# Answers: "What changed and why does it matter?"
# - Categorizes changes by function
# - Assesses risks
# - Summarizes implications
```

### Quick Catchup

```bash
/catchup

# Summarizes:
# - Recent commits
# - Changed files
# - Key decisions
# - Action items
```

### Feature Prioritization

```bash
/feature-review

# Uses hybrid RICE+WSJF scoring:
# - Reach, Impact, Confidence, Effort
# - Weighted Shortest Job First
# - ISO 25010 quality dimensions
```

## Scope Guard

The scope-guard skill prevents overengineering via four components:

| Component | Purpose |
|-----------|---------|
| `decision-framework` | Worthiness formula and scoring |
| `anti-overengineering` | Rules to prevent scope creep |
| `branch-management` | Threshold monitoring (lines, commits, days) |
| `baseline-scenarios` | Validated test scenarios |

## Iron Law TDD Enforcement

The proof-of-work skill enforces the **Iron Law**:

```
NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST
```

This prevents "Cargo Cult TDD" where tests validate pre-conceived implementations.

### Self-Check Protocol

| Thought Pattern | Violation | Action |
|-----------------|-----------|--------|
| "Let me plan the implementation first" | Skipping RED | Write failing test FIRST |
| "I know what tests we need" | Pre-conceived impl | Document failure, THEN design |
| "The design is straightforward" | Skipping uncertainty | Let design EMERGE from tests |

### TodoWrite Items

```
proof:iron-law-red     - Failing test documented
proof:iron-law-green   - Minimal code to pass
proof:iron-law-refactor - Code improved, tests green
proof:iron-law-coverage - Coverage gates verified
```

See `iron-law-enforcement.md` module for full enforcement patterns.

## Rigorous Reasoning

The rigorous-reasoning skill prevents sycophantic patterns through structured analysis:

| Component | Purpose |
|-----------|---------|
| `priority-signals` | Override principles (no courtesy agreement, checklist over intuition) |
| `conflict-analysis` | Harm/rights checklist for interpersonal conflicts |
| `debate-methodology` | Truth claims and contested territory handling |
| `red-flag monitoring` | Detect sycophantic thought patterns |

### Red Flag Self-Check

| Thought Pattern | Reality Check | Action |
|-----------------|---------------|--------|
| "I agree that..." | Did you validate? | Apply harm/rights checklist |
| "You're right that..." | Is this proven? | Check for evidence |
| "That's a fair point" | Fair by what standard? | Specify the standard |

## TodoWrite Integration

All skills output TodoWrite items for progress tracking:

```
review-core:context-established
review-core:scope-inventoried
diff-analysis:baseline-established
diff-analysis:changes-categorized
catchup:context-confirmed
catchup:delta-captured
```

## Integration Pattern

Imbue is foundational - other plugins build on it:

```bash
# Sanctum uses imbue for review patterns
Skill(imbue:review-core)
Skill(sanctum:git-workspace-review)

# Pensive uses imbue for evidence gathering
Skill(imbue:evidence-logging)
Skill(pensive:architecture-review)
```

## Superpowers Integration

| Skill | Enhancement |
|-------|-------------|
| `scope-guard` | Uses `brainstorming`, `writing-plans`, `execute-plan` |
| `/feature-review` | Uses `brainstorming` for feature suggestions |

## Related Plugins

- **sanctum**: Uses imbue for review scaffolding
- **pensive**: Uses imbue for evidence gathering
- **spec-kit**: Uses imbue for analysis patterns
