# Common Workflows Guide

When and how to use commands, skills, and subagents for typical development tasks.

## Quick Reference

| Task | Primary Tool | Plugin |
|------|--------------|--------|
| [Initialize a project](#initializing-a-new-project) | `/attune:arch-init` | attune |
| [Review a PR](#reviewing-a-pull-request) | `/full-review` | pensive |
| [Fix PR feedback](#fixing-pr-feedback) | `/fix-pr` | sanctum |
| [Prepare a PR](#preparing-a-pull-request) | `/pr` | sanctum |
| [Catch up on changes](#catching-up-on-changes) | `/catchup` | imbue |
| [Write specifications](#writing-specifications) | `/speckit-specify` | spec-kit |
| [Improve system](#meta-development-improving-the-system) | `/speckit-analyze` | spec-kit |
| [Debug an issue](#debugging-issues) | `Skill(superpowers:debugging)` | superpowers |
| [Manage knowledge](#managing-knowledge) | `/palace` | memory-palace |

---

## Initializing a New Project

**When**: Starting a new project from scratch or setting up a new codebase.

### Step 1: Architecture-Aware Initialization

Start with an architecture-aware initialization to select the right project structure based on team size and domain complexity. This process guides you through project type selection, online research into best practices, and template customization.

```bash
# Interactive architecture selection with research
/attune:arch-init --name my-project
```

**Output**: Complete project structure with ARCHITECTURE.md, ADR, and paradigm-specific directories.

### Step 2: Standard Initialization

If the architecture is decided, use standard initialization to generate language-specific boilerplate including Makefiles, CI/CD pipelines, and pre-commit hooks.

```bash
# Quick initialization when you know the architecture
/attune:init --lang python --name my-project
```

### Step 3: Establish Persistent State

Establish a persistent state to manage artifacts and constraints across sessions. This maintains non-negotiable principles and supports consistent progress tracking.

```bash
# (Once) Define non-negotiable principles for the project
/speckit-constitution

# (Each Claude session) Load speckit context + progress tracking
/speckit-startup
```

Optional enhancements:
- Install spec-kit for spec-driven artifacts: `/plugin install spec-kit@claude-night-market`
- Install superpowers for rigorous methodology loops:

```bash
/plugin marketplace add obra/superpowers
/plugin install superpowers@superpowers-marketplace
```

### Alternative: Brainstorming Workflow

For complex projects requiring exploration, begin by brainstorming the problem space and creating a detailed specification before planning the architecture and tasks.

```bash
# 1. Brainstorm the problem space
/attune:brainstorm --domain "my problem area"

# 2. Create detailed specification
/attune:specify

# 3. Plan architecture and tasks
/attune:plan

# 4. Initialize with chosen architecture
/attune:arch-init --name my-project

# 5. Execute implementation
/attune:execute
```

### What You Get

| Artifact | Description |
|----------|-------------|
| `pyproject.toml` / `Cargo.toml` / `package.json` | Build configuration |
| `Makefile` | Development targets (test, lint, format) |
| `.pre-commit-config.yaml` | Code quality hooks |
| `.github/workflows/` | CI/CD pipelines |
| `ARCHITECTURE.md` | Architecture overview |
| `docs/adr/` | Architecture decision records |

---

## Reviewing a Pull Request

**When**: Reviewing code changes in a PR or before merging.

### Full Multi-Discipline Review

```bash
# Full review with skill selection
/full-review
```

This orchestrates multiple specialized reviews:
- Architecture assessment
- API surface evaluation
- Bug hunting
- Test quality analysis

### Specific Review Types

```bash
# Architecture-focused review
/architecture-review

# API surface evaluation
/api-review

# Bug hunting
/bug-review

# Test quality assessment
/test-review

# Rust-specific review (for Rust projects)
/rust-review
```

### Using Skills Directly

For more control, invoke skills:

```bash
# First: understand the workspace state
Skill(sanctum:git-workspace-review)

# Then: run specific review
Skill(pensive:architecture-review)
Skill(pensive:api-review)
Skill(pensive:bug-review)
```

### External PR Review

```bash
# Review a GitHub PR by URL
/pr-review https://github.com/org/repo/pull/123

# Or just the PR number in current repo
/pr-review 123
```

---

## Fixing PR Feedback

**When**: Addressing review comments on your PR.

### Quick Fix

```bash
# Address PR review comments
/fix-pr

# Or with specific PR reference
/fix-pr 123
```

This:
1. Reads PR review comments
2. Identifies actionable feedback
3. Applies fixes systematically
4. Prepares follow-up commit

### Manual Workflow

```bash
# 1. Review the feedback
Skill(sanctum:git-workspace-review)

# 2. Apply fixes
# (make your changes)

# 3. Prepare commit message
/commit-msg

# 4. Update PR
git push
```

---

## Preparing a Pull Request

**When**: Code is complete and ready for review.

### Pre-PR Checklist

Run these commands before creating a PR:

```bash
# 1. Update documentation
/sanctum:update-docs

# 2. Update README if needed
/sanctum:update-readme

# 3. Review and update tests
/sanctum:update-tests

# 4. Update Makefile demo targets (for plugins)
/abstract:make-dogfood

# 5. Final quality check
make lint && make test
```

### Create the PR

```bash
# Full PR preparation
/pr

# This handles:
# - Branch status check
# - Commit message quality
# - Documentation updates
# - PR description generation
```

### Using Skills for PR Prep

```bash
# Review workspace before PR
Skill(sanctum:git-workspace-review)

# Generate quality commit message
Skill(sanctum:commit-messages)

# Check PR readiness
Skill(sanctum:pr-preparation)
```

---

## Catching Up on Changes

**When**: Returning to a project after time away, or joining an ongoing project.

### Quick Catchup

```bash
# Standard catchup on recent changes
/catchup

# Git-specific catchup
/git-catchup
```

### Detailed Understanding

```bash
# 1. Review workspace state
Skill(sanctum:git-workspace-review)

# 2. Analyze recent diffs
Skill(imbue:diff-analysis)

# 3. Understand branch context
Skill(sanctum:branch-comparison)
```

### Session Recovery

```bash
# Resume a previous Claude session
claude --resume

# Or continue with context
claude --continue
```

---

## Writing Specifications

**When**: Planning a feature before implementation.

### Spec-Driven Development Workflow

```bash
# 1. Create specification from idea
/speckit-specify Add user authentication with OAuth2

# 2. Generate implementation plan
/speckit-plan

# 3. Create ordered tasks
/speckit-tasks

# 4. Execute tasks with tracking
/speckit-implement
```

### Persistent Presence Loop (World Model + Agent Model)

Treat SDD artifacts as a self-modeling architecture where the repo state serves as the world model and the loaded skills as the agent model. Experiments are run with small diffs and verified through rigorous loops (tests, linters, repro scripts), while model updates refine both the code artifacts and the orchestration methodology to optimize future loops.

Curriculum generation via `/speckit-tasks` keeps actions grounded and dependency-ordered, while the skill library and iterative refinement ensure the plan adapts to reality. The cycle moves from planning to action to reflection via `/speckit-plan`, `/speckit-implement`, and `/speckit-analyze`.

Background reading:
- MineDojo: https://minedojo.org/ (internet-scale knowledge + benchmarks)
- Voyager: https://voyager.minedojo.org/ (arXiv: https://arxiv.org/abs/2305.16291) (automatic curriculum + skill library)
- GTNH_Agent: https://github.com/sefiratech/GTNH_Agent (persistent, modular Minecraft automation)

### Clarification and Analysis

```bash
# Ask clarifying questions about requirements
/speckit-clarify

# Analyze specification consistency
/speckit-analyze
```

### Using Skills

```bash
# Invoke spec writing skill directly
Skill(spec-kit:spec-writing)

# Task planning skill
Skill(spec-kit:task-planning)
```

---

## Meta-Development

**When**: Improving claude-night-market itself (skills, commands, templates, orchestration).

When improving the system itself, treat the repo as the world model and available tools as the agent model. Run experiments with minimal diffs behind verification, evaluate them with evidence-first methods like `/speckit-analyze` and `Skill(superpowers:verification-before-completion)`, and update both the artifacts and the methodology so the next loop is cheaper.

Optional pattern: split roles (planner/critic/executor) for long-horizon work, similar to multi-role agent stacks used in open-ended Minecraft agents.

Useful tools:

```bash
# Use speckit to keep artifacts + principles explicit
/speckit-constitution
/speckit-analyze

# Use superpowers to enforce evidence
Skill(superpowers:systematic-debugging)
Skill(superpowers:verification-before-completion)
```

---

## Debugging Issues

**When**: Investigating bugs or unexpected behavior.

### With Superpowers Integration

```bash
# Systematic debugging methodology
Skill(superpowers:debugging)

# This provides:
# - Hypothesis formation
# - Evidence gathering
# - Root cause analysis
# - Fix validation
```

### GitHub Issue Resolution

```bash
# Fix a GitHub issue
/fix-issue 42

# Or with URL
/fix-issue https://github.com/org/repo/issues/42
```

### Analysis Tools

```bash
# Test analysis (parseltongue)
/analyze-tests

# Performance profiling
/run-profiler

# Context optimization
/optimize-context
```

---

## Managing Knowledge

**When**: Capturing insights, decisions, or learnings.

### Memory Palace

```bash
# Open knowledge management
/palace

# Access digital garden
/garden
```

### Knowledge Capture

```bash
# Capture insight during work
Skill(memory-palace:knowledge-capture)

# Link related concepts
Skill(memory-palace:concept-linking)
```

---

## Plugin Development

**When**: Creating or maintaining Night Market plugins.

### Create a New Plugin

```bash
# Scaffold new plugin
make create-plugin NAME=my-plugin

# Or using attune for plugins
/attune:init --type plugin --name my-plugin
```

### Validate Plugin Structure

```bash
# Check plugin structure
/abstract:validate-plugin

# Audit skill quality
/abstract:skill-audit
```

### Update Plugin Documentation

```bash
# Update all documentation
/sanctum:update-docs

# Update Makefile demo targets
/abstract:make-dogfood

# Sync templates with reference projects
/attune:sync-templates
```

### Testing

```bash
# Run plugin tests
make test

# Validate structure
make validate

# Full quality check
make lint && make test && make build
```

---

## Context Management

**When**: Managing token usage or context window.

### Monitor Usage

```bash
# Check context window usage
/context

# Analyze context optimization
/optimize-context
```

### Reduce Context

```bash
# Clear context for fresh start
/clear

# Then catch up
/catchup

# Or scan for bloat
/bloat-scan
```

### Optimization Skills

```bash
# Context optimization skill
Skill(conserve:context-optimization)

# Growth analysis
/analyze-growth
```

---

## Subagent Delegation

**When**: Delegating specialized work to focused agents.

### Available Subagents

| Subagent | Purpose | When to Use |
|----------|---------|-------------|
| `abstract:plugin-validator` | Validate plugin structure | Before publishing plugins |
| `abstract:skill-auditor` | Audit skill quality | During skill development |
| `pensive:code-reviewer` | Focused code review | Reviewing specific files |
| `attune:project-architect` | Architecture design | Planning new features |
| `attune:project-implementer` | Task execution | Systematic implementation |

### Example: Code Review Delegation

```bash
# Delegate to specialized reviewer
Agent(pensive:code-reviewer) Review src/auth/ for security issues
```

### Example: Plugin Validation

```bash
# Delegate validation to subagent
Agent(abstract:plugin-validator) Check plugins/my-plugin
```

---

## End-to-End Example: New Feature

Here's a complete workflow for adding a new feature:

```bash
# 1. PLANNING PHASE
/speckit-specify Add caching layer for API responses
/speckit-plan
/speckit-tasks

# 2. IMPLEMENTATION PHASE
# Create branch
git checkout -b feature/add-caching

# Implement with Iron Law TDD
Skill(imbue:proof-of-work)  # Enforces: NO IMPLEMENTATION WITHOUT FAILING TEST FIRST

# Or with superpowers TDD
Skill(superpowers:tdd)

# Execute planned tasks
/speckit-implement

# 3. QUALITY PHASE
# Run reviews
/architecture-review
/test-review

# Fix any issues
# (make changes)

# 4. PR PREPARATION PHASE
/sanctum:update-docs
/sanctum:update-tests
make lint && make test

# 5. CREATE PR
/pr
```

---

## Command vs Skill vs Agent

| Type | Syntax | When to Use |
|------|--------|-------------|
| **Command** | `/command-name` | Quick actions, one-off tasks |
| **Skill** | `Skill(plugin:skill-name)` | Methodologies, detailed workflows |
| **Agent** | `Agent(plugin:agent-name)` | Delegated work, specialized focus |

### Examples

```bash
# Command: Quick action
/pr

# Skill: Detailed methodology
Skill(sanctum:pr-preparation)

# Agent: Delegated specialized work
Agent(pensive:code-reviewer) Review authentication module
```

### Skill Invocation: Secondary Strategy

The `Skill` tool is a Claude Code feature that may not be available in all environments. When the `Skill` tool is unavailable:

**Secondary Pattern:**
```bash
# 1. If Skill tool fails or is unavailable, read the skill file directly:
Read plugins/{plugin}/skills/{skill-name}/SKILL.md

# 2. Follow the skill content as instructions
# The skill file contains the complete methodology to execute
```

**Example:**
```bash
# Instead of: Skill(sanctum:commit-messages)
# Secondary:  Read plugins/sanctum/skills/commit-messages/SKILL.md
#             Then follow the instructions in that file
```

**Skill file locations:**
- Plugin skills: `plugins/{plugin}/skills/{skill-name}/SKILL.md`
- User skills: `~/.claude/skills/{skill-name}/SKILL.md`

This allows workflows to function across different environments.

---

## Claude Code 2.1.0 Features

### New Capabilities

| Feature | Description | Usage |
|---------|-------------|-------|
| **Skill Hot-Reload** | Skills auto-reload without restart | Edit SKILL.md, immediately available |
| **Plan Mode Shortcut** | Enter plan mode directly | `/plan` |
| **Forked Context** | Run skills in isolated context | `context: fork` in frontmatter |
| **Agent Field** | Specify agent for skill execution | `agent: agent-name` in frontmatter |
| **Frontmatter Hooks** | Lifecycle hooks in skills/agents | `hooks:` section in frontmatter |
| **Wildcard Permissions** | Flexible Bash patterns | `Bash(npm *)`, `Bash(* install)` |
| **Skill Visibility** | Control slash menu visibility | `user-invocable: false` |

### Skill Development Workflow (Hot-Reload)

With Claude Code 2.1.0, skill development is faster:

```bash
# 1. Create/edit skill
vim ~/.claude/skills/my-skill/SKILL.md

# 2. Save changes (no restart needed!)

# 3. Skill is immediately available
Skill(my-skill)

# 4. Iterate rapidly
```

### Using Forked Context

For isolated operations that shouldn't pollute main context:

```yaml
# In skill frontmatter
---
name: isolated-analysis
context: fork  # Runs in separate context
---
```

**Use cases:**
- Heavy file analysis that would bloat context
- Experimental operations that might fail
- Parallel workflows

### Frontmatter Hooks

Define hooks scoped to skill/agent/command lifecycle:

```yaml
---
name: validated-workflow
hooks:
  PreToolUse:
    - matcher: "Bash"
      command: "./validate.sh"
      once: true  # Run only once per session
  PostToolUse:
    - matcher: "Write|Edit"
      command: "./format.sh"
  Stop:
    - command: "./cleanup.sh"
---
```

### Permission Wildcards

New wildcard patterns for flexible permissions:

```yaml
allowed-tools:
  - Bash(npm *)      # All npm commands
  - Bash(* install)  # Any install command
  - Bash(git * main) # Git with main branch
```

### Disabling Specific Agents

Control which agents can be invoked:

```bash
# Via CLI
claude --disallowedTools "Task(expensive-agent)"

# Via settings.json
{
  "permissions": {
    "deny": ["Task(expensive-agent)"]
  }
}
```

### Subagent Resilience

Subagents are designed to continue operations after a permission denial by attempting alternative approaches instead of failing immediately. this behavior results in more reliable agent workflows when interacting with restrictive environments.

### Agent-Aware Hooks (2.1.2+)

SessionStart hooks receive `agent_type` field when launched with `--agent`:

```python
import json, sys
input_data = json.loads(sys.stdin.read())
agent_type = input_data.get("agent_type", "")

if agent_type in ["code-reviewer", "quick-query"]:
    context = "Minimal context"  # Skip heavy context
else:
    context = full_context

print(json.dumps({"hookSpecificOutput": {"additionalContext": context}}))
```

This reduces context overhead by 200-800 tokens for lightweight agents.

---

## See Also

- [Quick Start Guide](../book/src/getting-started/quick-start.md) - Condensed recipes
- [Capabilities Reference](../book/src/reference/capabilities-reference.md) - All commands and skills
- [Plugin Catalog](../book/src/plugins/README.md) - Detailed plugin documentation
