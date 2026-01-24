# Minister

Project management and initiative alignment using GitHub repository data.

## Overview

Minister synchronizes GitHub Projects, issues, and status checks for roadmap tracking. It generates snapshots of initiative status from live GitHub data and executes release governance through automated checks on CI status and documentation completeness.

## Capabilities

| Area | Description | Assets |
|------|-------------|--------|
| Issue Lifecycle | Manage GitHub issues with analysis and automated triage. | `commands/create-issue.md`, `commands/close-issue.md`, `commands/update-labels.md` |
| Initiative Tracking | Data model and CLI for tracking initiative metrics. | `scripts/tracker.py`, `src/minister/project_tracker.py` |
| GitHub Integration | Generate markdown comments for issues and pull requests. | `scripts/tracker.py`, `.github/workflows/minister-comment.yml` |
| Release Governance | Quality gates for CI status and documentation. | `skills/release-health-gates` |
| Reporting | Status report templates and project playbooks. | `docs/templates/status-report-template.md`, `docs/playbooks/*` |
| Data Store | JSON storage for synchronized GitHub Projects data. | `data/project-data.json` |

## Workflow Integration

The `ProjectTracker` links tasks to GitHub issues or PRs. Execute `tracker.py status --github-comment` to generate markdown reports for the `gh` CLI. This allows for linking status updates back to Projects v2 view notes.

Reference Minister's skills in other plugins or automate data ingestion through cron jobs. Artifacts are stored in `.claude/minister/` to maintain organization. Leyline manages GitHub API calls to stay within quota limits.

## Commands

- **/create-issue**: Create GitHub issues with specific formatting and references.
- **/close-issue**: Analyze commits and code to determine if an issue can be closed.
- **/update-labels**: Reorganize repository labels into a standardized taxonomy.

## Skills

- **github-initiative-pulse**: Generate snapshots of initiative progress for status updates.
- **release-health-gates**: Define and execute quality gates for release candidate approvals.

Each skill includes a `SKILL.md` file with scenario modules and references to the underlying Python scripts.

## Scripts

`tracker.py` provides the CLI for initiative management. Use `add` to link tasks to GitHub entities and `update` to refresh their progress. The `status --github-comment` command produces markdown for GitHub, while `export` creates CSV files for external analysis.

## Integration Patterns

Integrate Minister by calling its skills from other plugins. Use the `ProjectTracker` class for automated data ingestion via cron jobs. Manage GitHub API interactions through Leyline to respect rate limits and quotas.
