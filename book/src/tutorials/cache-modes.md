# Memory Palace Cache Modes

Learn how to configure Memory Palace's research interceptor for different use cases.

## Prerequisites

- Memory Palace plugin installed
- Familiarity with Memory Palace concepts

## Objectives

By the end of this tutorial, you'll:

- Understand the four cache modes
- Configure modes for different scenarios
- Debug interceptor decisions
- Monitor cache performance

## Mode Overview

The research interceptor supports four modes:

| Mode | Behavior | Use Case |
|------|----------|----------|
| `cache_only` | Block web when no confident match | Offline work, policy audits |
| `cache_first` | Check cache, fall back to web | Default research (recommended) |
| `augment` | Blend cache with live results | When freshness matters |
| `web_only` | Bypass Memory Palace entirely | Incident response, debugging |

## Step 1: Check Current Mode

View your current configuration:

```bash
cat plugins/memory-palace/hooks/memory-palace-config.yaml
```

Look for the `research_mode` setting:

```yaml
research_mode: cache_first
```

## Step 2: Understanding the Decision Matrix

The interceptor evaluates queries using:

### Freshness Detection

Queries containing temporal keywords trigger augmentation:
- `latest`, `2025`, `today`, `this week`
- Even with strong cache hits

### Match Strength

| Score | Classification | Action |
|-------|----------------|--------|
| > 0.8 | Strong match | Use cache |
| 0.4-0.8 | Partial match | Mode-dependent |
| < 0.4 | Weak/no match | Fall back to web |

### Autonomy Overrides

When autonomy level >= 2, partial matches auto-approve without flagging the intake queue.

## Step 3: Changing Modes

Edit the configuration file:

```yaml
# hooks/memory-palace-config.yaml

# For offline work
research_mode: cache_only

# For normal research (default)
research_mode: cache_first

# For real-time topics
research_mode: augment

# To bypass completely
research_mode: web_only
```

Restart Claude Code for changes to take effect.

## Step 4: Monitoring Decisions

The interceptor logs decisions to telemetry:

```bash
cat plugins/memory-palace/data/telemetry/memory-palace.csv
```

Fields include:
- `decision`: cache_hit, cache_miss, augmented, blocked
- `novelty_score`: 0-1 score for new information
- `intake_delta_reasoning`: Why intake was triggered/skipped

## Troubleshooting

### Hook never fires

**Check**: Is `cache_intercept` enabled?

```yaml
feature_flags:
  cache_intercept: true
```

**Check**: Is mode not `web_only`?

### Legitimate query blocked in cache_only

**Solution**: Add missing entry to corpus

```bash
# Inspect keyword index
cat plugins/memory-palace/data/indexes/keyword-index.yaml

# Rebuild indexes
uv run python plugins/memory-palace/scripts/build_indexes.py
```

### Too many augmentation messages

**Solution**: Adjust thresholds

```yaml
# Raise intake threshold
intake_threshold: 0.6

# Or increase autonomy
autonomy_level: 2
```

### Intake queue spam

**Solution**: Review duplicates

Check `intakeFlagPayload.duplicate_entry_ids` in telemetry and tidy corpus entries.

## Operational Checklist

After configuring modes:

1. Update `docs/curation-log.md` documenting mode choice
2. Keep `data/indexes/vitality-scores.yaml` fresh
3. When changing defaults, gate with feature flag
4. Run interceptor tests:
   ```bash
   pytest tests/hooks/test_research_interceptor.py
   ```

## Verification

Confirm your configuration works:

```bash
# Make a test query
# In Claude, ask about a topic in your corpus

# Check telemetry for decision
tail -1 plugins/memory-palace/data/telemetry/memory-palace.csv
```

Expected output shows `cache_hit` for known topics.

## Next Steps

- [Embedding Upgrade](embedding-upgrade.md) for semantic search
- [Memory Palace Curation](memory-palace-curation.md) for intake workflow

<div class="achievement-unlock" data-achievement="cache-modes-complete">
Achievement Unlocked: Cache Commander
</div>
