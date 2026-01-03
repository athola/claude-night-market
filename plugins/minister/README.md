# Minister

Project management plugin that aligns initiatives with GitHub data. Converts repositories, issues, and projects into status dashboards.

## Overview

Minister syncs GitHub Projects, issues, and checks to provide a single source of status. It includes scripts, playbooks, and Claude skills for status reporting and roadmap tracking.

## Focus Areas

1. **Initiative Pulse**: Generate GitHub comment-ready snapshots from Projects data.
2. **Release Health Gates**: Check CI, docs, and risk labels against release checklists.
3. **Reporting Kits**: Scripts and templates for publishing markdown status to GitHub threads.

## Capabilities

| Area | Description | Assets |
|------|-------------|--------|
| Initiative Tracking | Data model and CLI for initiative metrics and GitHub comments. | `scripts/tracker.py`, `src/minister/project_tracker.py`, `skills/github-initiative-pulse` |
| Tracker → GitHub | Workflow to emit markdown and comment on issues. | `scripts/tracker.py`, `.github/workflows/minister-comment.yml` |
| Release Governance | Health-check gates merging CI signals and documentation state. | `skills/release-health-gates` |
| Reporting | Templates and playbooks for status reporting. | `docs/templates/status-report-template.md`, `docs/playbooks/*` |
| Data Backbone | JSON data store for syncing with GitHub Projects. | `data/project-data.json` |

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
