# Minister

Project management and initiative alignment using GitHub repository data.

## Overview

Minister synchronizes GitHub Projects, issues, and status checks to provide dashboards and roadmap tracking. It generates snapshots of initiative health from live GitHub data and governs releases through automated checks on CI status and documentation completeness.

## Capabilities

| Area | Description | Assets |
|------|-------------|--------|
| Issue Lifecycle | Manage GitHub issues with analysis and automation. | `commands/create-issue.md`, `commands/close-issue.md`, `commands/update-labels.md` |
| Initiative Tracking | Data model and CLI for initiative metrics. | `scripts/tracker.py`, `src/minister/project_tracker.py` |
| GitHub Integration | Emit markdown comments on issues. | `scripts/tracker.py`, `.github/workflows/minister-comment.yml` |
| Release Governance | Health-check gates for CI and documentation. | `skills/release-health-gates` |
| Reporting | Status report templates and playbooks. | `docs/templates/status-report-template.md`, `docs/playbooks/*` |
| Data store | JSON storage for GitHub Projects sync. | `data/project-data.json` |

## Workflow Integration

The `ProjectTracker` manages initiative data by linking tasks to GitHub issues or PRs. Use `tracker.py status --github-comment` to generate markdown reports that can be posted directly to GitHub issues using the `gh` CLI. This workflow allows for linking status comments back to Projects v2 view notes for centralized tracking.

Integrate Minister by referencing its skills in other plugins or automating data ingestion through cron jobs. Artifacts are stored in `.claude/minister/` for organization, and Leyline handles GitHub API calls to manage quota limits.

```
plugins/minister/
├── data/                    # Initiative state + cached GitHub metrics
├── docs/                    # Playbooks, templates, integrations
├── scripts/                 # CLI entry points
├── skills/                  # Loadable Claude Code skills
└── src/minister/            # Python package powering the skills/scripts
```

## Commands

| Command | Purpose | Usage |
|---------|---------|-------|
| `/create-issue` | Create GitHub issues with formatting and references. | Quick issue creation, bug reports, feature requests. |
| `/close-issue` | Analyze if issues can be closed based on commits/code. | Issue triage, completion verification. |
| `/update-labels` | Reorganize labels into professional taxonomy. | Label standardization, backlog cleanup. |

## Skills

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `github-initiative-pulse` | Generate snapshots of initiative progress. | Weekly program reviews, status updates. |
| `release-health-gates` | Define quality gates for releases. | Release candidate approvals. |

Each skill includes a `SKILL.md` frontmatter block, scenario modules, and references back to shared scripts.

## Scripts

### Tracker Capabilities

`tracker.py` manages initiative tracking. Use `add` to link tasks to GitHub issues or PRs, and `update` to refresh progress. The `status --github-comment` command generates markdown for GitHub, while `export` creates CSV rollups for external tools.

## Docs & Playbooks

| Document | Purpose |
|----------|---------|
| [Integration Guide](docs/overview.md) | Wire GitHub inputs to Minister tracking. |
| [Program Rituals](docs/playbooks/github-program-rituals.md) | Weekly cadences for Program Review issues. |
| [Release Health](docs/playbooks/release-train-health.md) | Gate checklist for release managers. |
| [Status Template](docs/templates/status-report-template.md) | Status report with GitHub signal references. |

## Integration Patterns

Integrate Minister by referencing its skills in other plugins. Automate data ingestion via cron jobs targeting the `ProjectTracker` class. Store artifacts in `.claude/minister/` for organization. Use Leyline for GitHub API calls to respect quota limits.

## Roadmap

- GitHub Projects v2 sync adapter.
- Issue Label heuristics for risk scoring.
- Release cut automation with CODEOWNERS-driven approvals.
