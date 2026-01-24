# Sanctum

Git and workspace management for commits, pull requests, documentation, and versioning.

## Overview

Sanctum manages repository state and development workflows. It provides preflight checks for staged changes, drafts conventional commit messages, and prepares pull requests with quality gate verification. It automates version management and merges ephemeral documentation into permanent files to maintain project history and guides.

## Features

### Skills

| Skill | Description |
|-------|-------------|
| **git-workspace-review** | Preflight checklist for repo state, staged changes, and diffs. |
| **file-analysis** | Codebase structure mapping and file pattern detection. |
| **commit-messages** | Conventional commit generation from staged changes. |
| **pr-prep** | PR preparation with quality gates and template completion. |
| **doc-consolidation** | Merge ephemeral LLM-generated docs into permanent files. |
| **doc-updates** | Documentation updates with ADR support. |
| **test-updates** | Test generation and enhancement with TDD/BDD patterns. |
| **update-readme** | Update README with current project status. |
| **version-updates** | Version bumping across configs and changelogs. |
| **workflow-improvement** | Improve skills, agents, commands, and hooks based on the most recent session. |
| **pr-review** | Scope-focused PR review with knowledge capture integration. |
| **do-issue** | Fix GitHub issues using parallel execution via sub-agents. |
| **tutorial-updates** | Generate tutorials with GIF recordings. |
| **session-management** | Manage named sessions with `/rename`, `/resume`, and checkpoints. |

### Commands

| Command | Description |
|---------|-------------|
| `/git-catchup` | Catch up on git repository changes using the imbue methodology. |
| `/commit-msg` | Draft conventional commit message. |
| `/do-issue` | Fix GitHub issues using parallel execution via sub-agents. |
| `/fix-workflow` | Improve the most recent workflow slice through a retrospective. |
| `/fix-pr` | Address PR review comments, implement fixes, and resolve threads. |
| `/pr` | Prepare PR description with quality gates. |
| `/update-docs` | Update project documentation. |
| `/update-readme` | Update README with recent changes. |
| `/update-tests` | Update and maintain tests with TDD/BDD principles. |
| `/update-version` | Bump project versions. |
| `/update-dependencies` | Scan and update dependencies across ecosystems. |
| `/update-tutorial` | Generate or update tutorial documentation with recordings. |
| `/pr-review` | Scope-focused PR review with knowledge capture. |
| `/resolve-threads` | Batch-resolve unresolved PR review threads via GitHub GraphQL. |
| `/create-tag` | Create git tags from merged PRs or version arguments. |
| `/merge-docs` | Consolidate ephemeral LLM-generated docs into permanent files. |
| `/prepare-pr` | Complete PR preparation with updates and code review. |
| `/update-plugins` | Audit and sync plugin.json with disk contents. |

### Agents

| Agent | Description |
|-------|-------------|
| **git-workspace-agent** | Repository state analysis and change tracking. |
| **commit-agent** | Conventional commit message generation. |
| **pr-agent** | Pull request preparation and documentation. |
| **workflow-recreate-agent** | Recreates the most recent workflow and identifies inefficiencies. |
| **workflow-improvement-analysis-agent** | Generates improvement approaches with trade-offs and metrics. |
| **workflow-improvement-planner-agent** | Defines a bounded plan with acceptance criteria. |
| **workflow-improvement-implementer-agent** | Implements the agreed workflow improvements. |
| **workflow-improvement-validator-agent** | Validates improvements via tests and replay. |
| **dependency-updater** | Dependency scanning and updates across ecosystems. |

### Hooks

| Hook | Event | Description |
|------|-------|-------------|
| **security_pattern_check.py** | PreToolUse (Write\|Edit\|MultiEdit) | Checks for security anti-patterns in code changes. |
| **post_implementation_policy.py** | SessionStart | Injects governance protocol and proof-of-work reminders. |
| **verify_workflow_complete.py** | Stop | Post-implementation checklist reminder. |
| **session_complete_notify.py** | Stop | Cross-platform toast notification on command completion. |

#### Stop Hooks

**verify_workflow_complete.py** displays a checklist when a session ends. It reminds the developer to complete proof-of-work verification, lists documentation update commands, and displays a quality gate checklist.

**session_complete_notify.py** provides a desktop toast notification when commands complete. It supports Linux (notify-send), macOS (osascript), Windows (PowerShell), and WSL. It displays terminal info such as Zellij session, tmux window, and project name. Execution takes approximately 95ms. Notifications can be disabled by setting `CLAUDE_NO_NOTIFICATIONS=1` or muted with `CLAUDE_NOTIFICATION_SOUND=0`.

## Quick Start

### Git Workspace Review
```bash
# Understand repository state before other operations
Skill(sanctum:git-workspace-review)
```

### Commit Message Generation
```bash
# Generate conventional commit from staged changes
/commit-msg
```

### PR Preparation
```bash
# Full PR prep with quality gates
/pr
```

### Documentation Updates
```bash
# Update docs based on changes
/update-docs

# Modernize README
/update-readme

# Bump version numbers
/update-version
```

## Skill Dependencies

Most sanctum skills require `git-workspace-review` as a foundation. Skills like `commit-messages`, `pr-prep`, `doc-updates`, `update-readme`, and `version-updates` depend on its output. `file-analysis` operates independently.

## Workflow Patterns

**Pre-Commit**: Stage changes using `git add -p`, execute `git-workspace-review` for a preflight check, and run `commit-messages` to generate the message.

**Pre-PR**: Execute a preflight check, run quality gates such as `make fmt && make lint && make test`, and use `pr-prep` to generate the description.

**Post-Review**: Use `/fix-pr` to triage comments, implement fixes, and resolve threads.

**Release**: Run a preflight check, bump the version with `version-updates`, update documentation with `doc-updates`, then commit and tag the release.

## Session Forking (Claude Code 2.0.73+)

Session forking allows for exploring alternative implementations or commit strategies without affecting the main session history.

### Use Cases

For **Alternative Implementations**, fork a session to try different approaches, such as comparing an OAuth 2.0 implementation with a JWT-based one. For **Commit Strategies**, use forks to test atomic commits per file versus grouping by feature area. **PR Descriptions** can be forked to generate technical-focused versions and business-value versions, which can then be combined for the final draft. **Refactoring Explorations** allow for trying functional, OOP, or composition-based styles in parallel to evaluate trade-offs before implementation.

### Standards

Use descriptive session IDs like `pr-123-security-focused` instead of generic names. Keep each fork focused on a single approach. Extract insights to files before closing and document the reasoning for the final choice.
