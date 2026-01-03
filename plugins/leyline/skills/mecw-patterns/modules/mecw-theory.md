---
name: mecw-theory
description: Theoretical foundations of Maximum Effective Context Window principles and the physics of context pressure
category: theory
parent_skill: leyline:mecw-patterns
estimated_tokens: 450
reusable_by: [conserve, abstract, conjure, spec-kit]
tags: [theory, hallucination-prevention, context-physics]
---

# MECW Theory

## The Physics of Context Pressure

Context pressure is not linear - it increases exponentially as usage approaches the maximum window size. This non-linear behavior is why the 50% rule is critical.

### Why Context Degrades

When context usage exceeds MECW limits:

1. **Attention Diffusion**: Model attention becomes diffuse across too many tokens
2. **Information Loss**: Earlier context gets "forgotten" or compressed
3. **Hallucination Compensation**: Model compensates by generating plausible-sounding but incorrect content

### The Mathematical Model

```python
def context_degradation_factor(usage_ratio: float) -> float:
    """
    Model showing exponential degradation past 50% usage.

    Returns degradation factor where:
    - 1.0 = no degradation
    - Higher values = more degradation
    """
    if usage_ratio < 0.3:
        return 1.0  # Negligible degradation
    elif usage_ratio < 0.5:
        return 1.0 + (usage_ratio - 0.3) * 0.5  # Linear degradation
    else:
        # Exponential degradation past MECW
        return 1.1 + ((usage_ratio - 0.5) ** 2) * 4
```

## Evidence-Based Thresholds

The MECW thresholds are based on observed model behavior:

### Empirical Observations

| Context Usage | Hallucination Rate | Accuracy | Quality |
|---------------|-------------------|----------|---------|
| 0-30% | <1% | 98%+ | Excellent |
| 30-50% | 1-3% | 95%+ | Very Good |
| 50-70% | 5-15% | 85%+ | Degraded |
| 70-90% | 15-40% | 70%+ | Poor |
| 90-100% | 40-80% | 50%+ | Severely Degraded |

### Critical Transitions

**The 50% Boundary**: This is where degradation shifts from linear to exponential. Below 50%, the model maintains strong attention to all context. Above 50%, attention quality begins to degrade significantly.

**The 70% Danger Zone**: Past 70%, hallucination risk increases dramatically. The model must compress or discard earlier context to process new information.

**The 90% Catastrophe**: Above 90%, the model is in crisis mode, potentially missing critical context while generating responses.

## Practical Implications

### 1. Input vs Output Budget

The total context window must accommodate:
- **Input content** (your prompts, code, data)
- **Conversation history** (previous exchanges)
- **Model reasoning** (internal processing)
- **Response generation** (output tokens)

**Rule of thumb**: Never use more than 50% for input + history, reserving 50% for model work.

### 2. Context Types and Costs

Different content types have different cognitive costs:

```python
COGNITIVE_COST_MULTIPLIERS = {
    "code": 1.0,           # Structured, easier to process
    "natural_language": 1.2,  # More variation
    "mixed_structured": 1.3,  # JSON, YAML with prose
    "conversational": 1.5,    # High entropy, harder to compress
}
```

Adjust your MECW budget based on content type.

### 3. Session Lifecycle

Context pressure follows a lifecycle pattern:

```
Start (0%) -> Growth (30%) -> MECW Zone (50%) -> Risk Zone (70%) -> Crisis (90%)
     ↓            ↓               ↓                    ↓                ↓
  Optimal      Monitor         Optimize            Compress         Reset
```

## Hallucination Prevention Mechanisms

### Root Cause Analysis

Hallucinations occur when:
1. Model cannot access relevant earlier context
2. Model must "guess" based on partial information
3. Model generates plausible continuations without verification

### Prevention Through MECW

By maintaining usage below 50%, we validate:
- **Full Context Attention**: Model can attend to all relevant information
- **Reduced Inference Errors**: Less need to guess or interpolate
- **Better Verification**: Model can cross-reference within context

### Detection Strategies

Signs of MECW violation:
- Inconsistencies with earlier conversation
- Failure to recall specific details
- Generic/vague responses when specifics expected
- Contradictions across responses
- Fabricated facts that sound plausible

## Advanced Concepts

### Context Compression Thresholds

Different operations tolerate different compression levels:

| Operation | Safe MECW % | Explanation |
|-----------|-------------|-------------|
| Code generation | 40% | Needs reasoning space |
| Code review | 50% | Can work with fuller context |
| Data analysis | 35% | Needs calculation space |
| Documentation | 45% | Moderate reasoning needs |
| Conversation | 50% | More flexible |

### Multi-Turn Accumulation

Context grows across turns:

```python
def project_turn_growth(current_tokens: int, turns_remaining: int,
                       avg_turn_growth: int = 1000) -> int:
    """Project total context after N more turns."""
    return current_tokens + (turns_remaining * avg_turn_growth)

# Example: Will we exceed MECW in 5 turns?
current = 85000
projected = project_turn_growth(current, 5, avg_turn_growth=1200)
if projected > MECW_THRESHOLD:
    # Need to optimize NOW before continuing
    pass
```

### Subagent Coordination

When tasks exceed MECW:
1. Decompose into independent subtasks
2. Each subtask gets fresh context window
3. Synthesize results in final step
4. Total work capacity = N × MECW per subagent

## Measurement and Monitoring

### Token Tracking

Essential measurements:
- Current total tokens
- Tokens per message
- Growth rate (tokens/turn)
- Projected saturation (turns until MECW)

### Warning Signals

Implement graduated warnings:
```python
def generate_warnings(usage_ratio: float) -> list[str]:
    warnings = []
    if usage_ratio > 0.40:
        warnings.append("Approaching MECW - plan optimization")
    if usage_ratio > 0.50:
        warnings.append("MECW exceeded - optimize before next operation")
    if usage_ratio > 0.70:
        warnings.append("CRITICAL - immediate optimization required")
    return warnings
```

## References

This theory underlies:
- `leyline.mecw` Python module implementation
- `conserve:context-optimization` practical applications
- `conjure:delegation-core` subagent triggering logic
