# Minister Integration Guide

Wire GitHub data into Minister's tracking workflows. See [README.md](../README.md) for capabilities and quick start.

## Input Sources

| Source | Setup | Tracker Hook |
|--------|-------|--------------|
| **Projects V2** | Export or sync nightly via cron. | Updates `data/project-data.json`, then `tracker.py status` ingests fields. |
| **Labels** | Apply `risk:red`, `risk:yellow` during triage. | Maps to `Task.priority` and `Task.status` in Initiative Pulse. |
| **Checks** | Configure required checks on release PRs. | Health gate workflows emit JSON for readiness scoring. |
| **Discussions** | Capture decisions, copy permalink to Project note. | Store in `status_comment_url` field for tracker context. |

## Permalink Loop

Minister maintains GitHub conversation threads by storing comment permalinks:

```bash
# Generate → Post → Store
uv run python plugins/minister/scripts/tracker.py status --github-comment > .claude/minister/latest.md
gh issue comment 456 --body-file .claude/minister/latest.md
# Copy resulting permalink into Projects custom field `status_comment_url`
```

Each subsequent digest links back to the same thread, preserving conversation history.

## Extending Minister

| Extension | Location | Reference |
|-----------|----------|-----------|
| Custom skill modules | `skills/*/modules/` | Describe bespoke workflows. |
| Python helpers | `src/minister/` | GitHub API clients, data transforms. |
| New rituals | `docs/playbooks/` | Add to README capabilities table. |
