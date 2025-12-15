# Autonomy Alerting & Dashboards

The autonomy control loop must surface drift before cached knowledge degrades.

## Signals

| Metric | Source | Threshold | Action |
|--------|--------|-----------|--------|
| Regret rate (global) | `telemetry/autonomy_history.json` | >5% WoW | Auto-demote level, trigger review |
| Domain-specific regret | `update_autonomy_state.py --history domains/<name>.json` | >5% | Lock domain at Level 0 |
| Promotion readiness | Accuracy ≥ 90% for 20 decisions with regret ≤2% | Promote one level |
| Regret alerts JSON | `telemetry/alerts/autonomy.json` | Any entry present | Run recommended garden/autonomy command |

## Dashboards

1. `scripts/update_autonomy_state.py --history telemetry/autonomy_history.json`
   outputs JSON summary that feeds `docs/metrics/autonomy-dashboard.md`.
2. `scripts/metrics/regret_rate.py` (see below) charts regret trends with flag state overlays and now emits Markdown for dashboards.
3. Grafana panel (manual) references `telemetry/memory-palace.csv` filtered by `decision`.

## Regret Alerts JSON

1. Run `uv run python plugins/memory-palace/scripts/update_autonomy_state.py --alerts-json`.
2. Inspect `plugins/memory-palace/telemetry/alerts/autonomy.json`.
3. Each alert entry includes `recommended_command` (either `python -m memory_palace.cli autonomy demote` or `python -m memory_palace.cli garden demote --domain <domain>`).
4. Copy the `Garden command transcript` block from the CLI output into the incident log before executing mitigation.

## Alert Playbook

1. Run `python -m memory_palace.cli garden demote --domain <domain> --reason "regret spike"` to lock domain. Capture the emitted `Garden command transcript` (includes level, lock/unlock, reason, and state path) for the audit trail.
2. Append context to `docs/curation-log.md` alongside the transcript summary.
3. Open incident ticket with summary of affected entries.
4. After mitigation, run `python scripts/update_autonomy_state.py --history telemetry/autonomy_history.json` to recalc baseline.

## Supporting Scripts

- `plugins/memory-palace/scripts/update_autonomy_state.py`
- `plugins/memory-palace/scripts/metrics/regret_rate.py` (generates Markdown/CSV for dashboards)

## On-call Checklist

1. Tail telemetry for `autonomy` events.
2. Confirm curation backlog state.
3. Notify stakeholders via `#memory-palace`.
4. Document actions in this runbook footer.
