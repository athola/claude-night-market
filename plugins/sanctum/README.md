# Sanctum

Git and workspace management for commits, pull requests, documentation, and versioning.

## Overview

Sanctum manages repository state and development workflows. It provides preflight checks for staged changes, drafts conventional commit messages, and prepares pull requests with quality gate verification. It also automates version management and merges ephemeral documentation into permanent files so project history and guides remain current.

## Features

### Skills

| Skill | Description |
|-------|-------------|
| **git-workspace-review** | Preflight checklist for repo state, staged changes, and diffs |
| **file-analysis** | Codebase structure mapping and file pattern detection |
| **commit-messages** | Conventional commit generation from staged changes |
| **pr-prep** | PR preparation with quality gates and template completion |
| **doc-consolidation** | Merge ephemeral LLM-generated docs into permanent documentation |
| **doc-updates** | Documentation updates with ADR support |
| **test-updates** | Test generation and enhancement with TDD/BDD patterns |
| **update-readme** | Update README with current best practices |
| **version-updates** | Version bumping across configs and changelogs |
| **workflow-improvement** | Improve skills, agents, commands, and hooks from the most recent session slice |
| **pr-review** | Scope-focused PR review with knowledge capture integration |
| **do-issue** | Fix GitHub issues using parallel execution via sub-agents |
| **tutorial-updates** | Generate tutorials with GIF recordings |
| **session-management** | Manage named sessions with `/rename`, `/resume`, and checkpoints |

### Commands

| Command | Description |
|---------|-------------|
| `/git-catchup` | Catch up on git repository changes using the imbue methodology |
| `/commit-msg` | Draft conventional commit message |
| `/do-issue` | Fix GitHub issues using parallel execution via sub-agents |
| `/fix-workflow` | Improve the most recent workflow slice through a retrospective |
| `/fix-pr` | Address PR review comments, implement fixes, resolve threads |
| `/pr` | Prepare PR description with quality gates |
| `/update-docs` | Update project documentation |
| `/update-readme` | Update README with recent changes |
| `/update-tests` | Update and maintain tests with TDD/BDD principles |
| `/update-version` | Bump project versions |
| `/update-dependencies` | Scan and update dependencies across all ecosystems |
| `/update-tutorial` | Generate or update tutorial documentation with VHS/Playwright recordings |
| `/pr-review` | Scope-focused PR review with knowledge capture |
| `/resolve-threads` | Batch-resolve unresolved PR review threads via GitHub GraphQL |
| `/create-tag` | Create git tags from merged PRs or version arguments |
| `/merge-docs` | Consolidate ephemeral LLM-generated docs into permanent files |
| `/prepare-pr` | Complete PR preparation with updates and code review |
| `/update-plugins` | Audit and sync plugin.json with disk contents |

### Agents

| Agent | Description |
|-------|-------------|
| **git-workspace-agent** | Repository state analysis and change tracking |
| **commit-agent** | Conventional commit message generation |
| **pr-agent** | Pull request preparation and documentation |
| **workflow-recreate-agent** | Recreates the most recent workflow slice and surfaces inefficiencies |
| **workflow-improvement-analysis-agent** | Generates improvement approaches with trade-offs and metrics |
| **workflow-improvement-planner-agent** | Converges on a bounded plan with acceptance criteria |
| **workflow-improvement-implementer-agent** | Implements the agreed workflow improvements |
| **workflow-improvement-validator-agent** | Validate improvements via tests and minimal reproduction replay |
| **dependency-updater** | Dependency scanning and updates across ecosystems |

### Hooks

| Hook | Event | Description |
|------|-------|-------------|
| **security_pattern_check.py** | PreToolUse (Write\|Edit\|MultiEdit) | Checks for security anti-patterns in code changes |
| **post_implementation_policy.py** | SessionStart | Injects governance protocol and proof-of-work reminders |
| **verify_workflow_complete.py** | Stop | Post-implementation checklist reminder |
| **session_complete_notify.py** | Stop | Cross-platform toast notification when command completes |

#### Stop Hooks

**verify_workflow_complete.py** - Shows post-implementation checklist when sessions end:
- Reminds to complete proof-of-work verification
- Lists documentation update commands
- Displays quality gate checklist

**session_complete_notify.py** - Desktop toast notification when commands complete:
- **Platforms**: Linux (notify-send), macOS (osascript), Windows (PowerShell), WSL
- **Context**: Shows terminal info (Zellij session, tmux window, project name)
- **Performance**: ~95ms total for both hooks (varies with system load)
- **Disable**: Set `CLAUDE_NO_NOTIFICATIONS=1` environment variable
- **Sound Control**: Set `CLAUDE_NOTIFICATION_SOUND=0` for silent notifications

#### Troubleshooting Notifications

**Linux notifications not working?**
```bash
# Install libnotify (provides notify-send)
sudo apt install libnotify-bin  # Debian/Ubuntu
sudo dnf install libnotify      # Fedora
sudo pacman -S libnotify        # Arch
```

**macOS notifications not working?**
- Check System Settings → Notifications → Script Editor (or your terminal)
- Verify "Allow Notifications" is enabled

**Windows/WSL notifications not working?**
- Ensure PowerShell execution policy allows scripts:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- WSL: Verify Windows PowerShell is accessible from WSL
- Check Windows Focus Assist settings (might suppress notifications)

**Still seeing notifications?**
```bash
# Permanently disable notifications
export CLAUDE_NO_NOTIFICATIONS=1

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export CLAUDE_NO_NOTIFICATIONS=1' >> ~/.bashrc
```

## Quick Start

### Git Workspace Review
```bash
# Understand current repository state before other operations
Skill(sanctum:git-workspace-review)
```

### Commit Message Generation
```bash
# Generate conventional commit from staged changes
/commit-msg

# Or use skills directly
Skill(sanctum:git-workspace-review)
Skill(sanctum:commit-messages)
```

### PR Preparation
```bash
# Full PR prep with quality gates
/pr

# Or step by step
Skill(sanctum:git-workspace-review)
Skill(sanctum:pr-prep)
```

### Documentation Updates
```bash
# Update docs based on changes
/update-docs

# Modernize README with research
/update-readme

# Bump version numbers
/update-version
```

## Skill Dependencies

Most sanctum skills depend on `git-workspace-review` running first:

```
git-workspace-review (foundation)
├── commit-messages
├── pr-prep
├── doc-updates
├── update-readme
└── version-updates

file-analysis (standalone)
```

## TodoWrite Integration

Skills use TodoWrite for progress tracking:

```
git-review:repo-confirmed
git-review:status-overview
git-review:diff-stat
git-review:diff-details

pr-prep:workspace-reviewed
pr-prep:quality-gates
pr-prep:changes-summarized
pr-prep:testing-documented
pr-prep:pr-drafted
```

## Plugin Structure

```
sanctum/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── hooks/
│   ├── hooks.json                      # Hook registrations
│   ├── security_pattern_check.py       # PreToolUse security checks
│   ├── post_implementation_policy.py   # SessionStart governance reminders
│   ├── verify_workflow_complete.py     # Stop workflow checklist
│   ├── session_complete_notify.py      # Stop toast notifications
│   └── PERFORMANCE.md                   # Hook performance optimization notes
├── agents/
│   ├── git-workspace-agent.md
│   ├── commit-agent.md
│   ├── pr-agent.md
│   ├── workflow-recreate-agent.md
│   ├── workflow-improvement-analysis-agent.md
│   ├── workflow-improvement-planner-agent.md
│   ├── workflow-improvement-implementer-agent.md
│   ├── workflow-improvement-validator-agent.md
│   └── dependency-updater.md
├── commands/
│   ├── commit-msg.md
│   ├── create-tag.md
│   ├── do-issue.md
│   ├── fix-pr.md
│   ├── fix-workflow.md
│   ├── git-catchup.md
│   ├── merge-docs.md
│   ├── pr.md
│   ├── pr-review.md
│   ├── resolve-threads.md
│   ├── update-dependencies.md
│   ├── update-docs.md
│   ├── update-readme.md
│   ├── update-tests.md
│   ├── update-tutorial.md
│   └── update-version.md
├── skills/
│   ├── shared/
│   ├── git-workspace-review/
│   ├── file-analysis/
│   ├── commit-messages/
│   ├── doc-consolidation/
│   ├── test-updates/
│   ├── pr-prep/
│   ├── doc-updates/
│   ├── update-readme/
│   ├── workflow-improvement/
│   ├── version-updates/
│   ├── pr-review/
│   ├── do-issue/
│   ├── tutorial-updates/
│   └── session-management/
└── README.md
```

## Workflow Patterns

**Pre-Commit**: Stage changes (`git add -p`), run `git-workspace-review` for preflight, then `commit-messages` to generate the message.

**Pre-PR**: Run preflight, execute quality gates (`make fmt && make lint && make test`), then `pr-prep` to generate the description.

**Post-Review**: After receiving feedback, run `/fix-pr` to triage comments, implement fixes, and resolve threads.

**Release**: Run preflight, bump version with `version-updates`, update docs with `doc-updates`, then commit and tag.

## Session Forking Workflows (Claude Code 2.0.73+)

Session forking mimics git branching for conversations, letting you explore alternative approaches without affecting the main session.

### Use Cases

**Explore Alternative Implementations**
```bash
# Working on a feature in main session
claude "Implement user authentication"

# Fork to try OAuth approach
claude --fork-session --session-id "auth-oauth" --resume
> "Implement this using OAuth 2.0"

# Fork to try JWT approach
claude --fork-session --session-id "auth-jwt" --resume
> "Implement this using JWT"

# Compare results and choose best approach
```

**Test Different Commit Strategies**
```bash
# Have changes ready
claude "Generate commit messages for these changes"

# Fork to try atomic commits
claude --fork-session --session-id "atomic-commits" --resume
> "/commit-msg with atomic commits per file"

# Fork to try feature commits
claude --fork-session --session-id "feature-commits" --resume
> "/commit-msg grouping by feature area"

# Choose the commit organization that makes most sense
```

**Generate Alternative PR Descriptions**
```bash
# PR is ready
claude "/pr"

# Fork to generate technical-focused description
claude --fork-session --session-id "pr-technical" --resume
> "Generate PR description focused on technical implementation"

# Fork to generate business-focused description
claude --fork-session --session-id "pr-business" --resume
> "Generate PR description focused on business value"

# Mix the best parts from both approaches
```

**Parallel Refactoring Explorations**
```bash
# Main session: Need to refactor module
claude "Review this module for refactoring opportunities"

# Fork A: Try functional approach
claude --fork-session --session-id "refactor-functional" --resume
> "Refactor to functional style with pure functions"

# Fork B: Try OOP approach
claude --fork-session --session-id "refactor-oop" --resume
> "Refactor to object-oriented with dependency injection"

# Fork C: Try composition approach
claude --fork-session --session-id "refactor-composition" --resume
> "Refactor using composition over inheritance"

# Evaluate trade-offs and implement best approach in main session
```

### Best Practices

Use descriptive session IDs like `pr-123-security-focused` instead of generic names. Keep each fork focused on one approach. Extract insights to files before closing, and document the reasoning for the final choice.

See `plugins/abstract/docs/claude-code-compatibility.md` for detailed session forking patterns.

## License

MIT
