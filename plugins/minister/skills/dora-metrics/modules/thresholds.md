# DORA Tier Thresholds

Source: DORA's State of DevOps research. The thresholds below match
the published bands; minor adjustments per release year are common
but the band shape is stable.

## Deployment Frequency (DF)

How often code is deployed to production. Higher is better.

| Tier | Threshold |
|------|-----------|
| Elite | At least once per day |
| High | Between once per week and once per day |
| Medium | Between once per month and once per week |
| Low | Less often than once per month |

## Lead Time for Changes (LT)

Median time from commit to production. Lower is better.

| Tier | Threshold |
|------|-----------|
| Elite | Less than one day |
| High | One day to one week |
| Medium | One week to one month |
| Low | More than one month |

## Change Failure Rate (CFR)

Percentage of deployments that cause a production failure. Lower is
better.

| Tier | Threshold |
|------|-----------|
| Elite | At most 15% |
| High | 16-30% |
| Medium | 31-45% |
| Low | More than 45% |

## Time to Restore Service (TRS)

Median time to recover from a production failure. Lower is better.

| Tier | Threshold |
|------|-----------|
| Elite | Less than one hour |
| High | Less than one day |
| Medium | Less than one week |
| Low | One week or more |

## Boundary Behavior

The implementation places the boundary value in the better tier:

- DF exactly 1.0/day classifies as Elite, not High.
- LT exactly 24 hours classifies as Elite, not High.
- CFR exactly 15% classifies as Elite, not High.
- TRS exactly 1 hour classifies as High, not Elite (TRS uses strict
  `<` for Elite to keep the "less than one hour" wording honest).

Boundary tests in
`plugins/minister/tests/unit/test_dora_metrics.py` pin these
choices.
