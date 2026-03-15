---
name: mecw-principles
description: |
  Maximum Effective Context Window (MECW) theory, the 50% context rule,
  and hallucination prevention fundamentals.
category: conservation
---

# MECW Principles Module

## Overview

This module covers the theoretical foundations of Maximum Effective Context Window (MECW) principles, including the critical 50% rule that prevents hallucinations.

## The 50% Context Rule

**Core Principle**: Never use more than 50% of the *effective* context window for input content.

> **Important (Claude Code 2.1.7+)**: The effective context window is smaller than the total context window because it reserves space for max output tokens. When monitoring context usage, the 50% rule applies to the effective context, not the total. The status line's `used_percentage` field reports usage against the effective context.

### Why 50%?

| Context Usage | Effect on Model |
|---------------|-----------------|
| < 30% | Optimal performance, high accuracy |
| 30-50% | Good performance, slight accuracy degradation |
| 50-70% | Degraded performance, increased hallucination risk |
| > 70% | Severe degradation, high hallucination probability |

### The Physics of Context Pressure

```python
def calculate_context_pressure(current_tokens, max_tokens):
    """
    Context pressure increases non-linearly as usage approaches limits.
    """
    usage_ratio = current_tokens / max_tokens

    if usage_ratio < 0.3:
        return "LOW"      # Plenty of headroom
    elif usage_ratio < 0.5:
        return "MODERATE" # Within MECW limits
    elif usage_ratio < 0.7:
        return "HIGH"     # Exceeding MECW, risk zone
    else:
        return "CRITICAL" # Severe hallucination risk
```

## Hallucination Prevention

### Root Cause
When context exceeds MECW limits:
1. Model attention becomes diffuse across too many tokens
2. Earlier context gets "forgotten" or compressed
3. Model compensates by generating plausible-sounding but incorrect content

### Prevention Strategies

1. **Early Detection**: Monitor context usage continuously
2. **Proactive Compression**: Summarize before hitting limits
3. **Strategic Delegation**: Use subagents for complex workflows
4. **Progressive Disclosure**: Load only needed information

## Practical Application

### Monitoring Context Usage

**Native Visibility (Claude Code 2.0.65+)**: The status line displays context window utilization in real-time, providing immediate visibility into your current usage.

**Improved Accuracy (2.0.70+)**: The `current_usage` field in the status line input enables precise context percentage calculations, eliminating estimation variance.

**Improved Visualization (2.0.74+)**: The `/context` command now groups skills and agents by source plugin, showing:
- Plugin organization and context contribution
- Slash commands in use
- Sorted token counts for optimization
- Better visibility into which plugins consume context

This complements our MECW thresholds:
- **Status line** shows accurate current usage %
- **/context command** shows detailed breakdown by plugin (2.0.74+)

### 1M Context Window (GA, March 2025)

1M tokens is now generally available for Opus 4.6 and
Sonnet 4.6 at standard pricing (no long-context premium).
MECW thresholds scale proportionally:

| Context Window | 30% (Optimal) | 50% (MECW Limit) | 80% (Emergency) |
|---------------|---------------|-------------------|------------------|
| **200K** | 60K tokens | 100K tokens | 160K tokens |
| **1M** | 300K tokens | 500K tokens | 800K tokens |

> **Note**: The statusline reads `context_window_size`
> dynamically from the Claude Code JSON input, so it
> adapts automatically to whatever window the model
> reports (200K for Sonnet/Haiku, 1M for Opus).

#### Why Conservation Still Matters at 1M

A 1M window full of repeated tool outputs and stale file
reads performs worse than 200K of relevant, structured
state. The performance dropoff at 800-900K tokens still
exists even if less dramatic. Additionally:

- **Quota burn**: Larger context = more input tokens per
  turn = faster quota consumption. Surgical reads and
  selective loading protect your budget.
- **Attention dilution**: Model attention spreads across
  more tokens. Earlier context gets progressively less
  weight. Conservation keeps signal-to-noise high.
- **Agentic compounding**: Parallel agents each accumulate
  tool outputs independently. 5 agents at 200K each can
  collectively burn 1M in tokens while the parent context
  stays lean. Use git worktrees to isolate agent state.

#### The Plan-Clear-Implement Pattern

The 1M window's greatest benefit is enabling large
implementation plans without compaction interruptions:

1. **Plan**: Construct the full implementation plan
   (built-in planning, spec-kit, or similar)
2. **Clear**: `/compact` or `/clear` to start with a
   clean context (built-in planning does this
   automatically before implementation)
3. **Implement**: Execute the plan without compaction,
   maintaining full context of what was done and why
4. **Iterate**: Make follow-up changes while still on
   the same topic with the same context
5. **Repeat**: New plan, new clear, new implementation

This pattern avoids the old cycle of compact, lose
context, re-explore code, repeat instructions. With
discipline, automatic compaction becomes rare.

Server-side compaction (Opus 4.6) provides an additional
safety net: the API automatically summarizes earlier
conversation parts when approaching limits. This does not
replace MECW discipline but reduces catastrophic failure
risk.

### Tool Result Disk Persistence (2.1.51+)

Tool results larger than **50K characters** are now
persisted to disk instead of kept inline in the
conversation context. Previously the threshold was 100K.
This means large tool outputs (file reads, grep results,
web fetches) consume less context window space. Factor
this into MECW calculations: tool-heavy workflows now
have better context longevity than before.

### Compaction Image Preservation (2.1.70+)

Compaction now preserves images in the summarizer
request, allowing prompt cache reuse across compaction
boundaries. This makes compaction faster and cheaper,
especially for image-heavy sessions (screenshots,
diagrams). Previously, images were dropped during
compaction, busting the prompt cache.

### Read Tool Image Safety (2.1.71+)

The Read tool previously put oversized images into
context when image processing failed, breaking
subsequent turns in long image-heavy sessions. Fixed
in 2.1.71: failed image processing no longer injects
oversized data into context. This protects MECW
compliance in sessions that read many images.

### Resume Token Savings (2.1.70+)

Skill listings are no longer re-injected on every
`--resume` invocation, saving ~600 tokens per resume.
This improves context efficiency for workflows that
frequently resume sessions.

**"Summarize from here" (2.1.32+)**: Partial conversation summarization via the message selector provides a manual middle ground between `/compact` (full) and `/new` (clean slate). Use when only older context is stale.
- **Conservation plugin** provides proactive optimization recommendations when approaching thresholds

**Context Optimization with /context (2.0.74+)**:
```bash
# View detailed context breakdown
/context

# Identify high-consuming plugins:
# - Look for plugins with unexpectedly high token counts
# - Check if all loaded skills are actively needed
# - Consider unloading unused plugins to free context

# Example optimization strategy:
# 1. Run /context to see breakdown
# 2. Identify plugins using >10% context
# 3. Evaluate if each plugin's value justifies its context cost
# 4. Unload or defer plugins not needed for current task
```

```python
class MECWMonitor:
    """max_context defaults to 1M (Opus 4.6 GA default)."""
    def __init__(self, max_context=1_000_000):
        self.max_context = max_context
        self.mecw_threshold = max_context * 0.5

    def check_compliance(self, current_tokens):
        if current_tokens > self.mecw_threshold:
            return {
                'compliant': False,
                'overage': current_tokens - self.mecw_threshold,
                'action': 'immediate_optimization_required'
            }
        return {'compliant': True}
```

### Compression Techniques

1. **Code Summarization**: Replace full code with signatures + descriptions
2. **Content Chunking**: Process in MECW-compliant segments
3. **Result Synthesis**: Combine partial results efficiently
4. **Context Rotation**: Swap out completed context for new tasks
5. **LSP Optimization (2.0.74+)**: **Default approach** for token-efficient code navigation
   - **Old grep approach**: Load many files, search text (10,000+ tokens)
   - **LSP approach (PREFERRED)**: Query semantic index, read only target (500 tokens)
   - **Savings**: ~90% token reduction for reference finding
   - **Default strategy**: Always use LSP when available
   - **Enable permanently**: Add `export ENABLE_LSP_TOOL=1` to shell rc
   - **Fallback**: Only use grep when LSP unavailable for language

## Best Practices

1. **Plan for 40%**: Design workflows to use ~40% of context
2. **Buffer for Response**: Leave 50% for model reasoning + response
3. **Monitor Continuously**: Check context at each major step
4. **Fail Fast**: Abort and restructure when approaching limits
5. **Document Aggressively**: Keep summaries for context recovery

## Integration

- **Assessment**: Use with `mecw-assessment` module for analysis
- **Coordination**: Use with `subagent-coordination` for delegation
- **Conservation**: Aligns with `token-conservation` strategies
