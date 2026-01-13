# Minister

Project management plugin that aligns initiatives with GitHub data. Converts repositories, issues, and projects into status dashboards.

## Overview

Minister syncs GitHub Projects, issues, and checks for status reporting and roadmap tracking.

## Focus Areas

1. **Initiative Pulse**: GitHub snapshots from Projects data.
2. **Release Health**: CI, docs, and risk label checks.
3. **Reporting**: Scripts and templates for status updates.

## Capabilities

| Area | Description | Assets |
|------|-------------|--------|
| Issue Lifecycle | Manage GitHub issues with analysis and automation. | `commands/create-issue.md`, `commands/close-issue.md`, `commands/update-labels.md` |
| Initiative Tracking | Data model and CLI for initiative metrics. | `scripts/tracker.py`, `src/minister/project_tracker.py` |
| GitHub Integration | Emit markdown comments on issues. | `scripts/tracker.py`, `.github/workflows/minister-comment.yml` |
| Release Governance | Health-check gates for CI and documentation. | `skills/release-health-gates` |
| Reporting | Status report templates and playbooks. | `docs/templates/status-report-template.md`, `docs/playbooks/*` |
| Data store | JSON storage for GitHub Projects sync. | `data/project-data.json` |

## Tracker-to-GitHub Workflow

1. `uv run python plugins/minister/scripts/tracker.py status --github-comment > .claude/minister/latest.md`
2. `gh issue comment 456 --body-file .claude/minister/latest.md`
3. Link the comment URL back into the Projects v2 view notes field.

## Directory Layout

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

### `tracker.py`

```
uv run python plugins/minister/scripts/tracker.py status --github-comment
```

*Adds or updates tasks, exports CSV rollups, and prints GitHub-ready markdown.*

Key commands:
- `add`: Capture a task tied to a GitHub issue/PR URL.
- `update`: Refresh status, percent complete, or linked artifacts.
- `status --github-comment`: Emit comment-ready markdown.
- `export --output report.csv`: Share data with PM tools.

## Docs & Playbooks

- `docs/overview.md`: Guide on wiring GitHub inputs to Minister.
- `docs/playbooks/github-program-rituals.md`: Workflows for Program Review issues.
- `docs/playbooks/release-train-health.md`: Release manager checklist.
- `docs/templates/status-report-template.md`: Status template referencing GitHub signals.

## Integration Tips

1. Reference Minister skills from other plugins’ frontmatter.
2. Automate data ingest by pointing cron jobs at `src/minister/project_tracker.ProjectTracker`.
3. Store generated artifacts inside `.claude/minister/`.
4. Use Leyline for quota-aware GitHub API calls.

## Roadmap

- GitHub Projects v2 sync adapter.
- Issue Label heuristics for risk scoring.
- Release cut automation with CODEOWNERS-driven approvals.
