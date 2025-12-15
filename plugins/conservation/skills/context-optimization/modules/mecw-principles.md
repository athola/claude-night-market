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

**Core Principle**: Never use more than 50% of the total context window for input content.

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

```python
class MECWMonitor:
    def __init__(self, max_context=200000):
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
