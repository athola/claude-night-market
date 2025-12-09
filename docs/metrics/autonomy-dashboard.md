# Autonomy Dashboard

Tracks guardrails for the autonomy control loop during rollout.

## KPIs

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Global regret rate | < 5% | Computed from `autonomy_regret_decision_total` / total decisions |
| Flagged domains | ≤ 1 | Count of domains exceeding threshold in past hour |
| Pending demotions | 0 | Derived from `autonomy_pending_demotions` gauge |

## Escalation Criteria

1. Global regret rate ≥ 5% for two consecutive buckets.
2. Any single domain regret rate ≥ 8% OR flagged twice within 30 minutes.
3. Pending demotions > 0 for more than 10 minutes.

## Recovery Actions

- Run `python -m memory_palace.cli autonomy status --json` and attach output to incident thread.
- Trigger `python plugins/memory-palace/scripts/update_autonomy_state.py --alerts-json telemetry/alerts/autonomy.json`.
- If a domain is locked, use `python -m memory_palace.cli garden demote --domain <domain> --level 0 --lock`.
- Document actions in `docs/runbooks/memory-palace-rollout-dry-run.md`.

## Data Sources

- `telemetry/autonomy_history.json`
- `plugins/memory-palace/telemetry/alerts/autonomy.json`
- Governance CLI transcripts captured during dry runs.
