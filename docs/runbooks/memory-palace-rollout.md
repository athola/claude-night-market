# Memory Palace Rollout Playbook

This playbook governs the phased rollout of cache interception, autonomy gating, and lifecycle automation.

## Collateral

- Dry run transcript & validation log: [`docs/runbooks/memory-palace-rollout-dry-run.md`](memory-palace-rollout-dry-run.md)
- Cache intercept dashboard: [`../metrics/cache-hit-dashboard.md`](../metrics/cache-hit-dashboard.md)
- Autonomy guardrails dashboard: [`../metrics/autonomy-dashboard.md`](../metrics/autonomy-dashboard.md)
- Telemetry evidence: `plugins/memory-palace/telemetry/dry_runs/cache-intercept-staging.md`

## Change Management Checklist

1. Review the latest dry run transcript and confirm validation checklist is complete.
2. validate dashboard snapshots are refreshed (`cache-hit` + `autonomy` docs).
3. Verify rollback procedure owners are on-call and commands are rehearsed.
4. Update TodoWrite item `memory-palace-rollout:collateral` with links posted to `#memory-palace`.
5. Capture every flag change + CLI transcript into telemetry.

## Feature Flags

| Flag | Owner | Default | Description |
|------|-------|---------|-------------|
| `memory_palace.cache_intercept` | Research Team | false | Enables PreToolUse hook |
| `memory_palace.autonomy` | Governance Team | false | Turns on autonomy scoring + CLI |
| `memory_palace.lifecycle` | Knowledge Garden | false | Enables vitality decay + tending queues |

## Stages

1. **Dev Dry Run**
   - Run `uv run python scripts/seed_corpus.py` (no diff expected).
   - Enable flag via `python -m memory_palace.cli garden trust --domain dev --level 1`.
   - Capture telemetry snapshot (`telemetry/dry_runs/cache-intercept-staging.md`) and update the dry-run transcript doc.
2. **Staging**
   - Flip `memory_palace.cache_intercept=true` only.
   - Monitor `scripts/metrics/cache_hit_dashboard.py --preview` and attach the markdown export to `docs/metrics/cache-hit-dashboard.md`.
   - Validate `pytest tests/hooks/test_research_interceptor.py`.
3. **Production**
   - Enable `autonomy` and `lifecycle`.
   - Run `python scripts/update_autonomy_state.py --history telemetry/autonomy_history.json` and publish the resulting stats to `docs/metrics/autonomy-dashboard.md`.
   - Schedule `scripts/update_vitality_scores.py` via cron.

## Rollback

1. Disable offending flag in config + CLI.
2. Run `python -m memory_palace.cli autonomy status` to confirm revert and log the JSON in the dry-run transcript doc.
3. Rebuild indexes `uv run python scripts/build_indexes.py`.
4. Post-mortem entry in `docs/curation-log.md` referencing the dry-run + dashboard artifacts.

## Communication

- Announce via `#memory-palace` channel before each stage referencing the dry-run transcript and current dashboard snapshots.
- Update dashboard links in `docs/metrics/cache-hit-dashboard.md` and `docs/metrics/autonomy-dashboard.md`.
- Log every flag change in `telemetry/flag_changes.csv` and attach CLI transcripts.
