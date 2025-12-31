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
| **pr-review** | Scope-focused PR review with knowledge capture integration |
| **fix-issue** | Fix GitHub issues using subagent-driven-development |
| **tutorial-updates** | Orchestrate tutorial generation with GIF recordings |

### Commands

| Command | Description |
|---------|-------------|
| `/git-catchup` | Git repository catchup with imbue methodology |
| `/commit-msg` | Draft conventional commit message |
| `/fix-issue` | Fix GitHub issues using subagent-driven-development with parallel execution |
| `/fix-workflow` | Retrospective to improve the most recent workflow slice |
| `/fix-pr` | Address PR review comments, implement fixes, resolve threads |
| `/pr` | Prepare PR description with quality gates |
| `/update-docs` | Update project documentation |
| `/update-readme` | Modernize README with exemplar research |
| `/update-tests` | Update and maintain tests with TDD/BDD principles |
| `/update-version` | Bump project versions |
| `/update-dependencies` | Scan and update dependencies across all ecosystems |
| `/update-tutorial` | Generate or update tutorial documentation with VHS/Playwright recordings |
| `/pr-review` | Scope-focused PR review with knowledge capture |
| `/resolve-threads` | Batch-resolve unresolved PR review threads via GitHub GraphQL |
| `/create-tag` | Create git tags from merged PRs or version arguments |

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
| **dependency-updater** | Dependency scanning and updates across ecosystems |

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
│   ├── workflow-improvement-validator-agent.md
│   └── dependency-updater.md
├── commands/
│   ├── commit-msg.md
│   ├── create-tag.md
│   ├── fix-issue.md
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
│   ├── fix-issue/
│   └── tutorial-updates/
└── README.md
```

## Workflow Patterns

**Pre-Commit**: Stage changes with `git add -p`, run `Skill(sanctum:git-workspace-review)` for preflight, then `Skill(sanctum:commit-messages)` to generate the commit message.

**Pre-PR**: Run preflight, execute quality gates (`make fmt && make lint && make test`), then `Skill(sanctum:pr-prep)` to generate the PR description.

**Post-Review**: After receiving PR feedback, run `/fix-pr` to triage comments, implement fixes, and resolve threads on GitHub.

**Release**: Run preflight, bump version with `Skill(sanctum:version-updates)`, update docs with `Skill(sanctum:doc-updates)`, then commit and tag.

## Session Forking Workflows (Claude Code 2.0.73+)

Session forking enables "git branching for conversations" - explore alternative approaches without affecting your main workflow session.

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

- **Use descriptive session IDs**: `"pr-123-security-focused"` not `"fork1"`
- **Stay focused**: Each fork should explore one specific approach
- **Extract insights**: Save findings to files before closing forks
- **Document decisions**: Record why you chose one approach over others

See `plugins/abstract/docs/claude-code-compatibility.md` for comprehensive session forking patterns.

## License

MIT
