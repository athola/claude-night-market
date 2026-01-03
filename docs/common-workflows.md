# Common Workflows Guide

This guide shows when and how to use commands, skills, and subagents for typical development tasks.

## Quick Reference

| Task | Primary Tool | Plugin |
|------|--------------|--------|
| [Initialize a project](#initializing-a-new-project) | `/attune:arch-init` | attune |
| [Review a PR](#reviewing-a-pull-request) | `/full-review` | pensive |
| [Fix PR feedback](#fixing-pr-feedback) | `/fix-pr` | sanctum |
| [Prepare a PR](#preparing-a-pull-request) | `/pr` | sanctum |
| [Catch up on changes](#catching-up-on-changes) | `/catchup` | imbue |
| [Write specifications](#writing-specifications) | `/speckit-specify` | spec-kit |
| [Debug an issue](#debugging-issues) | `Skill(superpowers:debugging)` | superpowers |
| [Manage knowledge](#managing-knowledge) | `/palace` | memory-palace |

---

## Initializing a New Project

**When**: Starting a new project from scratch or setting up a new codebase.

### Step 1: Architecture-Aware Initialization (Recommended)

```bash
# Interactive architecture selection with research
/attune:arch-init --name my-project
```

This guides you through:
- Project type selection (web-api, cli-tool, library, etc.)
- Team size and domain complexity assessment
- Online research into best practices
- Architecture paradigm recommendation
- Template customization

**Output**: Complete project structure with ARCHITECTURE.md, ADR, and paradigm-specific directories.

### Step 2: Standard Initialization (Architecture Decided)

```bash
# Quick initialization when you know the architecture
/attune:init --lang python --name my-project
```

**Output**: Language-specific project with Makefile, CI/CD, pre-commit hooks.

### Alternative: Full Brainstorming Workflow

For complex projects requiring exploration:

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
# Comprehensive review with skill selection
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
# Comprehensive PR preparation
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

# Implement with TDD (if superpowers installed)
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

---

## See Also

- [Quick Start Guide](../book/src/getting-started/quick-start.md) - Condensed recipes
- [Capabilities Reference](../book/src/reference/capabilities-reference.md) - All commands and skills
- [Plugin Catalog](../book/src/plugins/README.md) - Detailed plugin documentation
