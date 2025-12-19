# Scoring Framework

Hybrid prioritization combining RICE (Intercom), WSJF (SAFe), and Kano classification.

## The Formula

```
Feature Score = (Value Score / Cost Score) * Confidence

Where:
  Value Score = weighted_avg(Reach, Impact, Business Value, Time Criticality)
  Cost Score = weighted_avg(Effort, Risk, Complexity)
  Confidence = 0.0 to 1.0 (how certain are we about estimates?)
```

## Value Factors

### Reach (R)

**Question:** How many users/use-cases does this affect?

| Score | Meaning | Example |
|-------|---------|---------|
| 1 | Very few (<5%) | Niche admin feature |
| 2 | Some (5-15%) | Power user feature |
| 3 | Moderate (15-35%) | Common workflow |
| 5 | Many (35-60%) | Core user journey |
| 8 | Most (60-85%) | Essential feature |
| 13 | Nearly all (>85%) | Universal need |

### Impact (I)

**Question:** How much does this improve the user experience?

| Score | Meaning | Kano Category |
|-------|---------|---------------|
| 1 | Minimal improvement | Basic (expected) |
| 2 | Slight improvement | Basic |
| 3 | Noticeable improvement | Performance |
| 5 | Significant improvement | Performance |
| 8 | Major improvement | Performance |
| 13 | Transformative | Delighter |

### Business Value (BV)

**Question:** How does this contribute to business goals/OKRs?

| Score | Meaning | OKR Alignment |
|-------|---------|---------------|
| 1 | Tangential | No direct OKR connection |
| 2 | Supporting | Supports an initiative |
| 3 | Contributing | Contributes to Key Result |
| 5 | Advancing | Directly advances Key Result |
| 8 | Critical | Required for Key Result |
| 13 | Strategic | Core to company Objective |

### Time Criticality (TC)

**Question:** What's the cost of delay?

| Score | Meaning | Urgency |
|-------|---------|---------|
| 1 | Can wait indefinitely | Nice to have |
| 2 | Can wait 6+ months | Low urgency |
| 3 | Should do this quarter | Moderate urgency |
| 5 | Should do this month | High urgency |
| 8 | Should do this sprint | Very high urgency |
| 13 | Must do immediately | Blocking/critical |

## Cost Factors

### Effort (E)

**Question:** How much work is this?

| Score | Meaning | Time Estimate |
|-------|---------|---------------|
| 1 | Trivial | < 1 day |
| 2 | Small | 1-3 days |
| 3 | Moderate | 3-5 days |
| 5 | Large | 1-2 weeks |
| 8 | Very large | 2-4 weeks |
| 13 | Huge | > 1 month |

### Risk (Rk)

**Question:** What could go wrong?

| Score | Meaning | Risk Level |
|-------|---------|------------|
| 1 | Very low risk | Well-understood, no dependencies |
| 2 | Low risk | Minor unknowns |
| 3 | Moderate risk | Some unknowns or dependencies |
| 5 | High risk | Significant unknowns |
| 8 | Very high risk | Many unknowns, critical dependencies |
| 13 | Extreme risk | Uncharted territory |

### Complexity (Cx)

**Question:** How hard is this to build correctly?

| Score | Meaning | Complexity Level |
|-------|---------|------------------|
| 1 | Simple | Single component, clear requirements |
| 2 | Straightforward | Few components, clear interfaces |
| 3 | Moderate | Multiple components, some edge cases |
| 5 | Complex | Cross-cutting concerns, many edge cases |
| 8 | Very complex | Architectural changes, distributed state |
| 13 | Extremely complex | Novel algorithms, fundamental changes |

## Confidence Scoring

Rate your confidence in the estimates:

| Confidence | Meaning | When to Use |
|------------|---------|-------------|
| 0.9-1.0 | High | Clear requirements, similar past work |
| 0.7-0.9 | Moderate | Some unknowns, reasonable estimates |
| 0.5-0.7 | Low | Many unknowns, rough estimates |
| 0.3-0.5 | Very low | Mostly guessing |
| < 0.3 | Speculative | Requires spike/research first |

**Guardrail:** Features with confidence < 0.5 should be flagged for research before commitment.

## Kano Classification

After scoring, classify the feature:

### Basic (Must-Have)

- Users expect this; absence causes dissatisfaction
- Doesn't increase satisfaction when present
- **Action:** Ensure these exist before anything else

### Performance (Linear)

- More is better; satisfaction scales with quality
- Competitive differentiator
- **Action:** Optimize based on ROI

### Delighters (Wow Factors)

- Unexpected features that create joy
- Absence doesn't hurt; presence delights
- **Action:** Build after basics and key performers

### Indifferent

- Users don't care either way
- **Action:** Deprioritize or cut

### Reverse

- Feature that some users actively dislike
- **Action:** Make optional or remove

## Calculation Example

```yaml
Feature: Auto-save drafts

# Value Factors
Reach: 8          # Most users write drafts
Impact: 5         # Significant UX improvement
Business Value: 3 # Supports retention KR
Time Criticality: 3 # Should do this quarter

Value Score = (8 + 5 + 3 + 3) / 4 = 4.75

# Cost Factors
Effort: 3         # 3-5 days
Risk: 2           # Low risk, understood problem
Complexity: 3     # Moderate, needs state management

Cost Score = (3 + 2 + 3) / 3 = 2.67

# Confidence
Confidence: 0.8   # Similar features built before

# Final Score
Feature Score = (4.75 / 2.67) * 0.8 = 1.42

# Classification
Kano: Performance (more saving = better UX)
Priority: Medium (1.42 is between 1.5-2.5 threshold)
```

## Interpreting Scores

| Score Range | Priority | Recommendation |
|-------------|----------|----------------|
| > 2.5 | High | Schedule for next sprint |
| 1.5 - 2.5 | Medium | Add to roadmap, plan timing |
| 1.0 - 1.5 | Low | Backlog, revisit quarterly |
| < 1.0 | Very Low | Defer indefinitely or reject |

## Custom Weights

Default weights can be customized in `.feature-review.yaml`:

```yaml
weights:
  value:
    reach: 0.25           # Equal weighting
    impact: 0.30          # Slightly favor user impact
    business_value: 0.25  # Equal to reach
    time_criticality: 0.20 # Slightly less weight
  cost:
    effort: 0.40          # Effort matters most
    risk: 0.30            # Risk is significant
    complexity: 0.30      # Complexity matters
```

**Guardrail:** Weights within each category must sum to 1.0.

## Comparison with Pure RICE

| Aspect | RICE | Feature Review |
|--------|------|----------------|
| Value factors | Reach, Impact | Reach, Impact, BV, TC |
| Cost factors | Effort only | Effort, Risk, Complexity |
| Time sensitivity | Not explicit | Time Criticality factor |
| Business alignment | Not explicit | Business Value factor |
| Uncertainty | Confidence | Confidence |
| Classification | None | Kano model |

Feature Review extends RICE with WSJF's time criticality and business value, plus Kano classification for strategic context.
