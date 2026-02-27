# Cache Hit Dashboard

The cache intercept rollout depends on demonstrating stable hit ratios and reversible behavior.

## KPIs

| Metric | Target | Notes |
|--------|--------|-------|
| Cache hit ratio (5 min) | ≥ 0.42 | Derived from `cache_intercept_decision_total{decision="cache_hit"}` / all decisions |
| Web bypass ratio | ≤ 0.25 | Indicates freshness pressure; track for staged rollout |
| Trust overrides | 0 per hour | Any non-zero indicates manual intervention

## Queries

```promql
# Hit ratio
sum(rate(cache_intercept_decision_total{decision="cache_hit"}[5m])) /
  sum(rate(cache_intercept_decision_total[5m]))

# Web bypass ratio
sum(rate(cache_intercept_decision_total{decision="web_bypass"}[5m])) /
  sum(rate(cache_intercept_decision_total[5m]))

# Trust overrides
sum(increase(cache_intercept_trust_override_total[1h]))
```

Store the rendered panel markdown + SVG in `plugins/memory-palace/telemetry/dashboards/cache-hit/` during each preview run.

## Alert Routes

- **Warning:** hit ratio drops below 0.35 for 15 minutes → notify `#memory-palace`.
- **Critical:** trust overrides > 0 for two consecutive hours → page governance engineer.
- **Info:** new corpus seed completes (`seed_corpus.py` success) → annotate dashboard timeline.

## Rollback Guide

1. Disable `memory_palace.cache_intercept` via `python -m memory_palace.cli garden demote --domain cache`.
2. Redeploy hooks without cache intercept overlay.
3. Confirm hit ratio metric flatlines at 0 and trust overrides reset to 0.
4. Link rollback evidence into the relevant rollout tracking issue.
