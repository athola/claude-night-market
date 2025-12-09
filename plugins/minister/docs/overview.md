# Minister Documentation Overview

Minister turns GitHub Projects, issues, and pull requests into actionable status loops. Use this guide to pick the workflow asset that matches the GitHub surface you need to update.

## Input Sources

| Source | GitHub Action | Tracker Hook |
|--------|---------------|--------------|
| GitHub Projects V2 | Maintain initiative lanes, owner swimlanes, and status notes in a shared view. Export or sync that view nightly. | Cron job updates `plugins/minister/data/project-data.json`, then `tracker.py status` ingests the refreshed fields. |
| Issues & PR Labels | Apply readiness, risk, and severity labels during triage so blockers stand out in search (`label:risk:red is:open`). | Labels map directly into `Task.priority` and `Task.status` when `tracker.py status` builds the Initiative Pulse. |
| Checks & Deployments | Promote release PRs through required checks and deployments so approvals live on GitHub. | Health gate workflows emit JSON that tracker loads for release readiness scoring. |
| Discussions & Decision Logs | Capture decisions in GitHub Discussions or issue threads and copy the permalink into your Project note. | Store the permalink in Projects custom field `status_comment_url` so tracker echoes the latest decision context. |

## Output Loop

1. `uv run python plugins/minister/scripts/tracker.py status --github-comment > .claude/minister/latest.md` – render the Initiative Pulse markdown with the exact metrics backing your program.
2. `gh issue comment <issue-id> --body-file .claude/minister/latest.md` or `gh pr comment <pr-number> --body-file .claude/minister/latest.md` – post the digest directly where sponsors read updates.
3. Add the resulting comment URL to the Projects custom field `status_comment_url` (or the note body) so the next sync can link back to the same GitHub artifact.

> Tracker Output → `gh issue/gh pr comment` → Link back into Projects custom field `status_comment_url`. Save the permalink so every subsequent digest keeps the conversation in a single GitHub thread.

## Usage Patterns

- **Program Review Mondays**: Run the tracker command above, paste the digest into the Program Review issue via `gh issue comment`, and store the permalink in the Projects view.
- **Midweek Risk Sync**: Filter `tracker.py status` output for `priority="High"`, then drop only the blockers into the risk issue using `gh issue comment`.
- **Release Cut Fridays**: Use `gh pr comment $DEPLOY_PR --body-file .claude/minister/latest.md`, follow the release-health gates checklist, and ensure the Projects item links to the deployment thread.

## Extending Minister

1. Write new modules inside `skills/*/modules` describing bespoke workflows.
2. Add python helpers under `src/minister/` (e.g., GitHub API clients) and import them in scripts.
3. Document new rituals under `docs/playbooks/` and reference them from README tables.
