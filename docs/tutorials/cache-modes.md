# Memory Palace Cache Modes

Transforming the Memory Palace into the research brain starts with choosing the
right interception mode for each session. This tutorial explains how the four
cache modes behave, when to use them, and how to debug unexpected decisions
from `hooks/research_interceptor.py`.

## Mode Overview

| Mode         | Behavior                                                                 | Typical Use Case                                     |
|--------------|--------------------------------------------------------------------------|------------------------------------------------------|
| `cache_only` | Deny outbound web tools when no confident corpus match is available.     | Offline work, air‑gapped reviews, policy audits.     |
| `cache_first`| Search corpus first; fall back to web when confidence < 40%.             | Default day‑to‑day research on evergreen topics.     |
| `augment`    | Always blend cached knowledge with live web results.                     | When freshness matters but local context is crucial. |
| `web_only`   | Bypass Memory Palace entirely (current Claude behavior).                 | Incident response, experimental debugging.           |

Modes can be set in `hooks/memory-palace-config.yaml` via `research_mode` or by
issuing a `config` update through the CLI.

## Decision Matrix

1. **Freshness detection** — queries containing `latest`, `2025`, `today`, etc.
   trigger augmentation even with strong cache hits.
2. **Match strength** — `match_score` > 0.8 is “strong”, 0.4–0.8 is “partial”.
3. **User mode** — `cache_only` denies low matches; `augment` injects context.
4. **Autonomy overrides** — when autonomy level ≥ 2 the hook may auto‑approve
   partial matches without re‑flagging the intake queue.

The hook emits structured telemetry (`data/telemetry/memory-palace.csv`) with
`decision`, `novelty_score`, and `intake_delta_reasoning` so you can audit how
each mode behaved.

## Troubleshooting

| Symptom                                   | Actions                                                                                                                   |
|-------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| Hook never fires                          | Confirm `feature_flags.cache_intercept` is `true` and `research_mode` ≠ `web_only`.                                       |
| Legitimate query blocked in `cache_only`  | Inspect `data/indexes/keyword-index.yaml` for missing entry; rerun `scripts/build_indexes.py`.                            |
| Too many augmentation messages            | Lower `intake_threshold` or raise autonomy level via `python -m memory_palace.cli autonomy set --level 2`.               |
| Intake spam after web search              | Review duplicates in `intakeFlagPayload.duplicate_entry_ids` and tidy corpus entries in `docs/knowledge-corpus`.         |

## Operational Checklist

1. Update `docs/curation-log.md` after each KonMari session to document why
   entries were promoted, merged, or archived.
2. Keep `data/indexes/vitality-scores.yaml` fresh so the hook knows which
   entries are evergreen vs. probationary (affects confidence bands).
3. When rolling out a new cache mode default, gate it with the
   `feature_flags.cache_intercept` toggle and dry-run `pytest
   tests/hooks/test_research_interceptor.py`.
