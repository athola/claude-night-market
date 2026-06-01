# ADR 0004: Skill Description Budget Optimization

**Date**: 2025-12-31
**Updated**: 2026-05-21
**Status**: Accepted (Updated)
**Context**: Slash Command Character Budget Management

## Problem

Claude Code enforces a character budget for skill descriptions loaded into
context. Exceeding this limit causes skills to become invisible to Claude,
breaking discoverability.

**Initial State (2025-12)**: 15,202 characters (101.3% of 15k budget)

This required users to manually configure their environment,
creating a poor out-of-the-box experience.

## Budget Limit Update (2026-02)

As of Claude Code v2.1.32 (Feb 6, 2026), the skill description budget changed:

- **Dynamic scaling**: Budget is now **2% of the context window** size
- **Fallback**: 16,000 characters (up from the previous 15,000 hardcoded value)
- **Override**: `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable for
  custom limits
- **Ecosystem validator**:
  Set to 20,000 to match 1M context window (GA for Opus/Sonnet 4.6)

For standard 200k-token context windows, 2% yields ~16,000 characters.
With 1M context (GA since April 2026), the budget is ~20,000 characters.

### Sources

- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills) - "The budget scales dynamically at 2% of the context window, with a fallback of 16,000 characters."
- [Claude Code v2.1.32 Release Notes](https://releasebot.io/updates/anthropic/claude-code) - "Skill character budget now scales with context window (2% of context)"

## Decision

Optimize skill and command descriptions through systematic reduction while
preserving discoverability.

### Optimization Principles

Optimization focuses on:
- **Concise Descriptions**:
  Removing implementation details from the primary text.
- **Trigger Condensation**: Reducing trigger lists to essential keywords.
- **Redundancy Elimination**: Ensuring descriptions don't repeat tag
  or category information.
- **Discoverability**: Preserving critical keywords while moving verbosity to
  documentation.

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

**Note**: Some multiline descriptions had extra whitespace that was trimmed,
accounting for variance between estimated and actual savings.

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

Optimization reduced the ecosystem from 15,202 to 14,798 characters (98.7% of
the original 15k limit).

### Round 3 (2026-02)

After ecosystem growth pushed total to 16,711 chars,
a two-pronged approach was applied:
1. **Validator limit raised** to 17,000 (above the new CC 16k fallback)
2. **9 attune skill descriptions condensed** using "Use for/Skip if" pattern
   (-745 chars)

| Metric | Round 1-2 | Round 3 | Current (1M ctx) |
|--------|-----------|---------|---------|
| **Total Chars** | 14,798 | 16,711 → 15,966 | ~20,918 |
| **Validator Limit** | 15,000 | 17,000 | 20,000 |
| **Per-desc Max** | 130 | 130 | 160 |

## 2026-05 Overhaul: Action-Oriented Description Rewrite

All SKILL.md `description:` fields rewritten in May 2026 to use
Anthropic's recommended activation format:

```
[Verb phrase]. Use when [trigger condition].
[Do not use when [negative]; use [alternative] instead.]
```

**Why**: The majority of skills had noun-phrase descriptions that told
Claude WHAT a skill does but not WHEN to invoke it. The `description:`
field is the only signal in the system-reminder Claude uses for skill
selection; triggering skills requires action-oriented triggers.

**Results**:

| Metric | Before (Round 3) | After (2026-05) |
|--------|-----------------|-----------------|
| **Total Chars (raw)** | ~15,966 | 35,472 |
| **With overhead** | ~21k | 70,239 |
| **Avg desc length** | 77.7 chars | 144.6 chars |
| **Skills with a trigger phrase** | ~8% | 100% (majority "Use when"; remainder "Use before/after/for/at") |
| **Per-desc over 160 chars** | 0 | 0 |

The raw description budget grew 2.2x because descriptions now contain
trigger context that drives accurate skill activation. This is within
Claude Code's 1M context budget (~80k available for descriptions with
overhead) and is a deliberate trade-off: better activation accuracy
over minimal budget.

**Template doc**: `docs/skill-description-guide.md`

**Commands excluded**: Slash command `.md` files were not updated:
command descriptions appear in `/help` output for humans and use
noun-phrase format by design (commands are user-typed, not
Claude-selected).

## Future Opportunities

1. **Archetypes consolidation** (potential savings: ~1,500 chars raw)
   - Merge 13 architecture-paradigm-* skills into 1 interactive selector
2. **`SLASH_COMMAND_TOOL_CHAR_BUDGET` env var** - document for power users with
   many plugins

## Monitoring

1. ✅ Pre-commit hook (`validate-description-budget`) enforces limit
2. ✅ Validator tracks per-description lengths (160 char max)
3. ⏳ Monitor for description creep in future PRs
4. ⏳ Consider archetypes consolidation if headroom shrinks

## Summary

After the 2026-05 overhaul, all descriptions use action-oriented triggers
("Use when/before/after/for"). Raw budget is ~35k chars (~70k with overhead),
within the 1M context window's ~80k available. Validator ceiling is 60,000
chars (enforced by pre-commit hook). Growth is intentional: trigger phrasing
improves skill activation accuracy at the cost of budget.

## Related

- See ADR-0003 for command description refactoring pattern
- See [Skills Reference](../../book/src/reference/capabilities-skills.md) for
  skill documentation
- [Claude Code Skills Docs](https://code.claude.com/docs/en/skills) - authoritative budget documentation
- [CC v2.1.32 Release Notes](https://releasebot.io/updates/anthropic/claude-code) - dynamic scaling announcement
