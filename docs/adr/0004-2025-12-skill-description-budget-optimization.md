# ADR 0004: Skill Description Budget Optimization

**Date**: 2025-12-31
**Status**: Accepted
**Context**: Slash Command Character Budget Management

## Problem

Claude Code enforces a 15,000 character budget for slash command descriptions (`SLASH_COMMAND_TOOL_CHAR_BUDGET`). Exceeding this limit causes skills to become invisible to Claude, breaking the ecosystem's discoverability.

**Initial State**: 15,202 characters (101.3% of budget) 🔴

This required users to manually configure their environment, creating a poor out-of-the-box experience.

## Decision

Optimize skill and command descriptions through systematic reduction while preserving discoverability.

### Optimization Principles

Optimization focuses on:
- **Concise Descriptions**: Removing implementation details from the primary text.
- **Trigger Condensation**: Reducing trigger lists to essential keywords.
- **Redundancy Elimination**: Ensuring descriptions don't repeat tag or category information.
- **Discoverability**: Preserving critical keywords while moving verbosity to documentation.

## Implementation

### Round 1: Top 5 Verbose Descriptions

1. ✅ abstract/validate-plugin: 264 → 95 chars (-169 chars)
2. ✅ sanctum/pr-review: 247 → 163 chars (-84 chars)
3. ✅ sanctum/tutorial-updates: 194 → 106 chars (-88 chars)
4. ✅ sanctum/doc-updates: 187 → 110 chars (-77 chars)
5. ✅ leyline/usage-logging: 160 → 95 chars (-65 chars)

**Round 1 Savings**: 483 chars

### Round 2: Conservation Plugin Bloat

6. ✅ conservation/bloat-detector: 248 → 110 chars (-138 chars)
7. ✅ conservation/mcp-code-execution: 143 → 105 chars (-38 chars)

**Round 2 Savings**: 176 chars

**Note**: Some multiline descriptions had extra whitespace that was trimmed, accounting for variance between estimated and actual savings.

## Results

### Final Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Total Characters** | 15,202 | 14,798 | -404 chars (-2.7%) |
| **Budget Usage** | 101.3% 🔴 | 98.7% ✅ | **Under by 202 chars** |
| **Headroom** | -202 chars | +202 chars | **1.3% buffer** |

### Budget Distribution After Optimization

| Plugin | Components | Total Chars | Avg/Component | Status |
|--------|-----------|-------------|---------------|--------|
| sanctum | 30 | 3,159 (-248) | 105 | Optimized |
| archetypes | 14 | 1,823 | 130 | Consolidation candidate |
| abstract | 23 | 1,759 (-165) | 76 | Excellent |
| leyline | 14 | 1,704 (-67) | 122 | Improved |
| imbue | 12 | 1,137 | 95 | Good |
| pensive | 17 | 820 | 48 | Most efficient |
| conservation | 8 | 729 (-176) | 91 | Debloated |
| memory-palace | 10 | 610 | 61 | Efficient |
| scry | 6 | 596 | 99 | Good |
| minister | 3 | 352 | 117 | Good |
| parseltongue | 7 | 343 | 49 | Most efficient |
| conjure | 3 | 310 | 103 | Good |

## Consequences

Optimization reduced the ecosystem description budget to 14,798 characters (98.7% of the 15k limit). A 202-character buffer ensures skill visibility without manual configuration.

## User Experience Impact

The 15k budget now works without environment adjustments, ensuring reliable skill triggering and providing a 1.3% growth buffer. Additionally, the reduced system prompt size may contribute to faster skill loading.

### Neutral

- 12 descriptions still >140 chars (but within budget)
- Potential for further optimization if needed

## Future Opportunities

### Low Priority (Not Blocking)

1. **Archetypes consolidation** (potential savings: ~1,500 chars)
   - Merge 13 architecture-paradigm-* skills into 1 interactive selector
   - Impact: 130 → 100 avg chars per component

2. **Further description refinement** (potential savings: ~300 chars)
   - 12 descriptions still >140 chars
   - Target: All descriptions <130 chars

3. **Total potential headroom with all optimizations**: ~2,000 chars (13% buffer)

## Monitoring

### Next Steps

1. ✅ Update README with optimization results
2. ✅ Update action plan to reflect success
3. ⏳ Monitor for description creep in future PRs
4. ⏳ Add pre-commit hook to validate budget
5. ⏳ Consider archetypes consolidation in v1.2.0

### Pre-commit Hook (Proposed)

```bash
#!/bin/bash
# Check slash command character budget
total=$(python scripts/count_descriptions.py)
if [ "$total" -gt 15000 ]; then
    echo "ERROR: Slash command descriptions exceed 15K budget ($total chars)"
    exit 1
fi
```

## Summary

The ecosystem now works with default settings, establishing reliable discoverability for all skills and commands.

## Related

- See ADR-0003 for command description refactoring pattern
- See [Skill Discovery Documentation](../guides/skill-discovery.md)
- Tracking issue: #budget-optimization (closed)
