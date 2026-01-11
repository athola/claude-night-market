# sanctum

Git and workspace operations for active development workflows.

## Overview

Sanctum handles the practical side of development: commits, PRs, documentation updates, and version management. It's the plugin you'll use most during active coding.

## Installation

```bash
/plugin install sanctum@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `git-workspace-review` | Preflight repo state analysis | Before any git operation |
| `file-analysis` | Codebase structure mapping | Understanding project layout |
| `commit-messages` | Conventional commit generation | After staging changes |
| `pr-prep` | PR preparation with quality gates | Before creating PRs |
| `pr-review` | PR analysis and feedback | Reviewing others' PRs |
| `doc-consolidation` | Merge ephemeral docs | Consolidating LLM-generated docs |
| `doc-updates` | Documentation maintenance | Syncing docs with code |
| `test-updates` | Test generation and enhancement | Maintaining test suites |
| `update-readme` | README modernization | Refreshing project entry points |
| `version-updates` | Version bumping | Managing semantic versions |
| `workflow-improvement` | Workflow retrospectives | Improving development processes |
| `tutorial-updates` | Tutorial maintenance | Keeping tutorials current |

## Commands

| Command | Description |
|---------|-------------|
| `/git-catchup` | Git repository catchup |
| `/commit-msg` | Draft conventional commit message |
| `/pr` | Prepare PR with quality gates |
| `/pr-review` | Enhanced PR review |
| `/fix-pr` | Address PR review comments |
| `/fix-issue` | Fix GitHub issues systematically |
| `/fix-workflow` | Improve recent workflow |
| `/merge-docs` | Consolidate ephemeral docs |
| `/update-docs` | Update documentation |
| `/update-readme` | Modernize README |
| `/update-tests` | Maintain tests |
| `/update-tutorial` | Update tutorial content |
| `/update-version` | Bump versions |
| `/update-dependencies` | Update project dependencies |
| `/create-tag` | Create git tags for releases |
| `/resolve-threads` | Resolve PR review threads |

## Agents

| Agent | Description |
|-------|-------------|
| `git-workspace-agent` | Repository state analysis |
| `commit-agent` | Commit message generation |
| `pr-agent` | PR preparation specialist |
| `workflow-recreate-agent` | Workflow slice reconstruction |
| `workflow-improvement-*` | Workflow improvement pipeline |
| `dependency-updater` | Dependency version management |

## Hooks

| Hook | Type | Description |
|------|------|-------------|
| `post_implementation_policy.py` | SessionStart | Requires docs/tests/readme updates |
| `verify_workflow_complete.py` | Stop | Verifies workflow completion |
| `session_complete_notify.py` | Stop | Toast notification when awaiting input |

## Usage Examples

### Pre-Commit Workflow

```bash
# Stage changes
git add -p

# Review workspace
Skill(sanctum:git-workspace-review)

# Generate commit message
Skill(sanctum:commit-messages)

# Apply
git commit -m "<generated message>"
```

### PR Preparation

```bash
# Run quality checks first
make fmt && make lint && make test

# Prepare PR
/pr

# Creates:
# - Summary
# - Change list
# - Testing checklist
# - Quality gate results
```

### Fix PR Review Comments

```bash
/fix-pr

# Claude will:
# 1. Read PR comments
# 2. Triage by priority
# 3. Implement fixes
# 4. Resolve threads on GitHub
```

### Fix GitHub Issue

```bash
/fix-issue 42

# Uses subagent-driven-development:
# 1. Analyze issue
# 2. Create plan
# 3. Implement fix
# 4. Test
# 5. Prepare PR
```

## Skill Dependencies

Most sanctum skills depend on `git-workspace-review`:

```
git-workspace-review (foundation)
├── commit-messages
├── pr-prep
├── doc-updates
├── update-readme
└── version-updates

file-analysis (standalone)
```

Always run `git-workspace-review` first to establish context.

## TodoWrite Integration

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

## Workflow Patterns

### Pre-Commit
```bash
git add -p
Skill(sanctum:git-workspace-review)
Skill(sanctum:commit-messages)
```

### Pre-PR
```bash
make fmt && make lint && make test
Skill(sanctum:git-workspace-review)
Skill(sanctum:pr-prep)
```

### Post-Review
```bash
/fix-pr
# Implements fixes, resolves threads
```

### Release
```bash
Skill(sanctum:git-workspace-review)
Skill(sanctum:version-updates)
Skill(sanctum:doc-updates)
git commit && git tag
```

## Superpowers Integration

| Command | Enhancement |
|---------|-------------|
| `/pr` | Uses `receiving-code-review` for validation |
| `/pr-review` | Uses `receiving-code-review` for analysis |
| `/fix-pr` | Uses `receiving-code-review` for resolution |
| `/fix-issue` | Uses multiple superpowers for full workflow |

## Related Plugins

- **imbue**: Provides review scaffolding sanctum uses
- **pensive**: Code review complements sanctum's git operations
