# ADR 0004: Skill Description Budget Optimization

**Date**: 2025-12-31
**Updated**: 2026-02-07
**Status**: Accepted (Updated)
**Context**: Slash Command Character Budget Management

## Problem

Claude Code enforces a character budget for skill descriptions loaded into context. Exceeding this limit causes skills to become invisible to Claude, breaking discoverability.

**Initial State (2025-12)**: 15,202 characters (101.3% of 15k budget)

This required users to manually configure their environment, creating a poor out-of-the-box experience.

## Budget Limit Update (2026-02)

As of Claude Code v2.1.32 (Feb 6, 2026), the skill description budget changed:

- **Dynamic scaling**: Budget is now **2% of the context window** size
- **Fallback**: 16,000 characters (up from the previous 15,000 hardcoded value)
- **Override**: `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable for custom limits
- **Ecosystem validator**: Set to 17,000 to provide growth headroom for future plugins

For standard 200k-token context windows, 2% yields ~16,000 characters. Users with larger context windows get proportionally more budget automatically.

### Sources

- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills) - "The budget scales dynamically at 2% of the context window, with a fallback of 16,000 characters."
- [Claude Code v2.1.32 Release Notes](https://releasebot.io/updates/anthropic/claude-code) - "Skill character budget now scales with context window (2% of context)"

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

### Round 1-2 (2025-12)

Optimization reduced the ecosystem from 15,202 to 14,798 characters (98.7% of the original 15k limit).

### Round 3 (2026-02)

After ecosystem growth pushed total to 16,711 chars, a two-pronged approach was applied:
1. **Validator limit raised** to 17,000 (above the new CC 16k fallback)
2. **9 attune skill descriptions condensed** using "Use for/Skip if" pattern (-745 chars)

| Metric | Round 1-2 | Round 3 | Current |
|--------|-----------|---------|---------|
| **Total Chars** | 14,798 | 16,711 → 15,966 | 15,966 |
| **Validator Limit** | 15,000 | 17,000 | 17,000 |
| **Headroom** | 202 chars | 1,034 chars | **6.1% buffer** |

## Future Opportunities

1. **Archetypes consolidation** (potential savings: ~1,500 chars)
   - Merge 13 architecture-paradigm-* skills into 1 interactive selector
2. **`SLASH_COMMAND_TOOL_CHAR_BUDGET` env var** - document for power users with many plugins

## Monitoring

1. ✅ Pre-commit hook (`validate-description-budget`) enforces limit
2. ✅ Validator tracks per-description lengths (150 char recommendation)
3. ⏳ Monitor for description creep in future PRs
4. ⏳ Consider archetypes consolidation if headroom shrinks

## Summary

The ecosystem works with default CC settings (16k fallback). The validator uses a 17k limit to provide growth headroom. Description condensation preserved all functional keywords while standardizing on a shorter "Use for/Skip if" pattern.

## Related

- See ADR-0003 for command description refactoring pattern
- See [Skills Reference](../../book/src/reference/capabilities-skills.md) for skill documentation
- [Claude Code Skills Docs](https://code.claude.com/docs/en/skills) - authoritative budget documentation
- [CC v2.1.32 Release Notes](https://releasebot.io/updates/anthropic/claude-code) - dynamic scaling announcement
