---
name: analyze-growth
description: Analyze skill growth patterns and predict context budget impact
usage: /analyze-growth [skill-path]
---

# Analyze Growth Patterns

Analyzes skill file growth patterns over time and predicts future context budget impact. Helps identify skills that need proactive optimization.

## Usage

```bash
# Analyze specific skill
/analyze-growth skills/context-optimization

# Analyze entire skills directory
/analyze-growth skills/

# Compare before/after optimization
/analyze-growth --compare skills/my-skill
```

## What It Analyzes

### Growth Metrics
- **Historical size changes**: Git-based growth tracking
- **Token velocity**: Rate of token accumulation
- **Complexity trajectory**: Section and depth growth
- **Dependency expansion**: Module reference growth

### Predictions
- **30-day forecast**: Estimated size in one month
- **Threshold crossing**: When skill will exceed limits
- **Optimization urgency**: Priority ranking

## Examples

```bash
/analyze-growth skills/context-optimization
# Output:
# Growth Analysis: context-optimization
# =====================================
# Current Size: 6,384 bytes (1,650 tokens)
# 30-day Growth Rate: +15%
# Predicted Size: 7,341 bytes (1,897 tokens)
#
# Status: WATCH
# Recommendation: Monitor for modularization opportunity

/analyze-growth skills/ --report
# Full report across all skills with rankings
```

## Growth Categories

| Category | Growth Rate | Action |
|----------|-------------|--------|
| Stable | < 5%/month | No action |
| Growing | 5-15%/month | Monitor |
| Fast | 15-30%/month | Plan optimization |
| Critical | > 30%/month | Immediate modularization |

## Integration

Pairs with:
- `/optimize-context` - Current state analysis
- `growth-controller.py` - Automated growth management
- `optimizing-large-skills` skill - Implementation patterns

## Implementation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/growth-analyzer.py --growth "${1:-.}"
```
