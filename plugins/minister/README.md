# Minister

> *Project ministers keep initiatives aligned with GitHub truth. This plugin turns repositories, issues, and projects into living program dashboards.*

## Overview

Minister keeps programs honest by turning GitHub Projects, issues, and checks into the single source of status truth. It ships scripts, playbooks, and Claude skills so every status, gate, and roadmap call flows from repository data.

## Focus Areas

1. **Initiative Pulse** – Generates GitHub comment-ready snapshots from Projects data and issue labels.
2. **Release Health Gates** – Blocks releases until CI, docs, and risk labels meet the checklist.
3. **Reporting Kits** – Provides tracker scripts and templates that publish markdown directly into GitHub threads.

## Capabilities

| Area | Description | Assets |
|------|-------------|--------|
| Initiative Tracking | Structured data model plus CLI to record/inspect initiative metrics and surface GitHub comment digests. | `scripts/tracker.py`, `src/minister/project_tracker.py`, `skills/github-initiative-pulse` |
| Tracker → GitHub Loop | Use `uv run python plugins/minister/scripts/tracker.py status --github-comment` to emit markdown, then `gh issue comment <id> --body-file .claude/minister/latest.md`. | `scripts/tracker.py`, `.github/workflows/minister-comment.yml` |
| Release Governance | Health-check gates that merge CI signals, open issue risk, and documentation state. | `skills/release-health-gates` |
| Reporting | Curated templates and playbooks for weekly status, stakeholder packets, and burndown dashboards. | `docs/templates/status-report-template.md`, `docs/playbooks/*` |
| Data Backbone | JSON data store ready for syncing with GitHub Projects or REST data, with CSV export helpers. | `data/project-data.json` |

## Tracker-to-GitHub Workflow

1. `uv run python plugins/minister/scripts/tracker.py status --github-comment > .claude/minister/latest.md`
2. `gh issue comment 456 --body-file .claude/minister/latest.md`
3. Link the comment URL back into the Projects v2 view notes field so every lane shows the latest permalink.

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
| `github-initiative-pulse` | Generates digestible snapshots of initiative progress plus ready-to-post GitHub comments. | Weekly program reviews, issue/PR status updates. |
| `release-health-gates` | Defines quality gates that block releases until GitHub checks, documentation, and comms are satisfied. | Ship room reviews, release candidate approvals. |

Each skill includes a `SKILL.md` frontmatter block, scenario modules, and references back to shared scripts.

## Scripts

### `tracker.py`

```
uv run python plugins/minister/scripts/tracker.py status --github-comment
```

*Adds or updates tasks, exports CSV rollups, and prints GitHub-ready markdown.*

Key commands:
- `add` – capture a task tied to a GitHub issue/PR URL.
- `update` – refresh status, percent complete, or linked artifacts.
- `status --github-comment` – emit comment-ready markdown.
- `export --output report.csv` – share data with PM tools.

## Docs & Playbooks

- `docs/overview.md` – canonical guide on wiring GitHub inputs to Minister.
- [`docs/playbooks/github-program-rituals.md`](plugins/minister/docs/playbooks/github-program-rituals.md) – walks Monday/Wednesday rituals that paste Initiative Pulse output into Program Review issues via `gh issue comment`.
- [`docs/playbooks/release-train-health.md`](plugins/minister/docs/playbooks/release-train-health.md) – details the release manager checklist, including when to run `gh pr comment $PR --body-file .claude/minister/latest.md`.
- `docs/templates/status-report-template.md` – drop-in status template referencing GitHub signals.

## Integration Tips

1. Reference Minister skills from other plugins’ frontmatter to advertise dependencies.
2. Automate data ingest by pointing cron jobs at `src/minister/project_tracker.ProjectTracker`.
3. Store generated artifacts inside `.claude/minister/` for portability across repos.
4. Pair with Leyline for quota-aware GitHub API calls when syncing Projects data.

## Roadmap

- GitHub Projects v2 sync adapter.
- Issue Label heuristics for risk scoring.
- Release cut automation with CODEOWNERS-driven approvals.
