# Sanctum

Git and workspace operations for active development workflows - commit messages, PR prep, documentation updates, and version management.

## Installation

Add to your Claude Code plugins:
```bash
claude plugins install sanctum
```

Or reference directly from the marketplace:
```json
{
  "plugins": ["sanctum@claude-night-market"]
}
```

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
| **update-readme** | README modernization with exemplar research |
| **version-updates** | Version bumping across configs and changelogs |
| **workflow-improvement** | Retrospective workflow to improve skills, agents, commands, and hooks from the most recent session slice |

### Commands

| Command | Description |
|---------|-------------|
| `/catchup` | Git repository catchup with imbue methodology |
| `/commit-msg` | Draft conventional commit message |
| `/fix-workflow` | Retrospective to improve the most recent workflow slice |
| `/fix-pr` | Address PR review comments, implement fixes, resolve threads |
| `/pr` | Prepare PR description with quality gates |
| `/update-docs` | Update project documentation |
| `/update-readme` | Modernize README with exemplar research |
| `/update-tests` | Update and maintain tests with TDD/BDD principles |
| `/update-version` | Bump project versions |

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
| **workflow-improvement-validator-agent** | Validates improvements via tests and minimal reproduction replay |

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

All skills use TodoWrite for progress tracking:

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
├── agents/
│   ├── git-workspace-agent.md
│   ├── commit-agent.md
│   ├── pr-agent.md
│   ├── workflow-recreate-agent.md
│   ├── workflow-improvement-analysis-agent.md
│   ├── workflow-improvement-planner-agent.md
│   ├── workflow-improvement-implementer-agent.md
│   └── workflow-improvement-validator-agent.md
├── commands/
│   ├── catchup.md
│   ├── commit-msg.md
│   ├── fix-workflow.md
│   ├── fix-pr.md
│   ├── merge-docs.md
│   ├── pr.md
│   ├── update-docs.md
│   ├── update-readme.md
│   ├── update-tests.md
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
│   └── version-updates/
└── README.md
```

## Workflow Patterns

**Pre-Commit**: Stage changes with `git add -p`, run `Skill(sanctum:git-workspace-review)` for preflight, then `Skill(sanctum:commit-messages)` to generate the commit message.

**Pre-PR**: Run preflight, execute quality gates (`make fmt && make lint && make test`), then `Skill(sanctum:pr-prep)` to generate the PR description.

**Post-Review**: After receiving PR feedback, run `/fix-pr` to triage comments, implement fixes, and resolve threads on GitHub.

**Release**: Run preflight, bump version with `Skill(sanctum:version-updates)`, update docs with `Skill(sanctum:doc-updates)`, then commit and tag.

## License

MIT
