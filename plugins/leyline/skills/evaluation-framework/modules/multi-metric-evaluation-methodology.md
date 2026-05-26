---
name: multi-metric-evaluation-methodology
description: Methods for combining multiple metrics into a decision: weighted sums, Pareto fronts, lexicographic ordering, TOPSIS, and when each fits
category: evaluation
tags: [mcda, weighted-sum, pareto, lexicographic, topsis, methodology]
estimated_tokens: 950
---

# Multi-Metric Evaluation Methodology

When a decision depends on more than one metric, you need a
rule for combining them. The rule you pick determines which
trade-offs are visible and which are silently smoothed
away. This module catalogs five families of combination
rules from Multi-Criteria Decision Analysis (MCDA), shows
the math, and gives a decision tree for picking one.

## The Combination Problem

Given n metrics m_1...m_n, a candidate scores a vector
s = (s_1, ..., s_n). To rank candidates you need a rule
f(s) -> R or a partial-order operator. The rules differ in
what they assume about substitutability between metrics and
about the decision-maker's preferences.

| Assumption | Rule family |
|------------|-------------|
| Metrics fully substitutable | Weighted sum / arithmetic mean |
| One bad metric should drag total | Weighted product / geometric mean |
| Any single metric can veto | Min / worst-of |
| Strict priority ordering | Lexicographic |
| No substitutability claim | Pareto front |
| Distance to ideal matters | TOPSIS |

## Normalization First

Every method below assumes metrics are on comparable scales.
Skip normalization and units silently dominate weights.

| Method | Formula | When |
|--------|---------|------|
| Min-max | (x - min) / (max - min) | Bounded scale, no outliers |
| Z-score | (x - mean) / stdev | Unbounded, normal-ish |
| Vector | x / sqrt(sum(x^2)) | Scale-invariant rankings |
| Logarithmic | log(x + 1) / log(max + 1) | Heavy-tailed, diminishing returns |

Document which method was used and why. The choice affects
final ranks more than reviewers usually expect.

## Method 1: Weighted Sum (SAW)

Simple Additive Weighting. The default. Every other method
should justify why weighted sum was rejected.

```
score(s) = sum_i (w_i * s_i)
subject to: sum_i (w_i) = 1.0,  w_i >= 0
```

**Assumes**: metrics are mutually preferentially independent
and freely substitutable. Trading one unit of m_1 for w_1/w_2
units of m_2 is acceptable everywhere on the scale.

**Use when**: dimensions are independent, similarly scaled,
and a rich basket of moderate scores is preferable to a
spiky basket with one zero.

**Avoid when**: any metric can be a deal-breaker (security,
correctness). A high score on six dimensions cannot
compensate for a zero on the seventh.

**Worked example**:

```
weights = {quality: 0.4, latency: 0.3, cost: 0.3}
scores  = {quality: 4,   latency: 5,   cost: 2}
total   = 0.4*4 + 0.3*5 + 0.3*2 = 1.6 + 1.5 + 0.6 = 3.7
```

## Method 2: Weighted Product / Geometric Mean

Compensatory but punishes low scores more than weighted sum.

```
score(s) = product_i (s_i ** w_i)
```

**Assumes**: a one-step drop in a low score hurts more than
a one-step drop in a high score. Multiplicative rather than
additive.

**Use when**: you want imbalance to be visible but not
absolute. A score of (5, 5, 1) should rank below (3, 3, 3)
even though their sums are equal.

**Worked example** (same inputs as above):

```
score = 4^0.4 * 5^0.3 * 2^0.3
      = 1.741 * 1.621 * 1.231
      = 3.475
```

A single low score costs more than under SAW.

## Method 3: Lexicographic Ordering

Strict priority: rank by m_1, break ties by m_2, then m_3.

```
sort candidates by m_1 desc;
  within ties, sort by m_2 desc;
    within ties, sort by m_3 desc;
      ...
```

**Assumes**: there is a true priority order, and no amount
of m_2 can compensate for any deficit in m_1.

**Use when**: regulatory or safety dimensions exist with
hard primacy. Example: "Pick the safest option; among
equally safe, pick the cheapest."

**Avoid when**: top-priority metric has fine-grained
differences. Lexicographic ignores all secondary data once
m_1 differs by any amount.

**Worked example**:

```
candidates: [(safety=5, cost=2), (safety=4, cost=5)]
m_1 = safety: 5 > 4, so (5,2) wins, full stop.
The cost gap of 3 is invisible.
```

## Method 4: Pareto Front (No Aggregation)

Refuse to aggregate. Report the non-dominated set.

```
A dominates B iff:
  for all i: s_i(A) >= s_i(B)  AND
  exists j:  s_j(A) >  s_j(B)

Pareto front = { x : no y dominates x }
```

**Assumes**: nothing about substitutability. Hands the
trade-off back to the decision-maker.

**Use when**: weights are contested or unknown, or you want
to surface the trade-off space rather than collapse it.

**Worked example**:

```
candidates = [
  A: (quality=5, cost=4),
  B: (quality=4, cost=2),
  C: (quality=3, cost=3),
  D: (quality=2, cost=5),
]
A dominates D (5>=2, 4<=5? cost lower is better, so flip)
After flipping cost: minimize cost, maximize quality.
Front: A (best quality), B (best balance), D (cheapest).
C is dominated by B (B beats C on both axes).
```

The front size grows roughly with the square root of n
candidates; useful as a shortlist filter, not a final pick.

## Method 5: TOPSIS

Technique for Order Preference by Similarity to Ideal
Solution. Rank by distance to a synthetic best and worst.

```
for each metric i, compute:
  ideal_i      = max(s_i across candidates)  if benefit
                 min(s_i across candidates)  if cost
  anti_ideal_i = the opposite

distance_to_ideal(x)      = sqrt(sum_i (w_i * (x_i - ideal_i))^2)
distance_to_anti_ideal(x) = sqrt(sum_i (w_i * (x_i - anti_ideal_i))^2)

closeness(x) = d_anti(x) / (d_ideal(x) + d_anti(x))
rank by closeness desc.
```

**Assumes**: the best candidate minimizes Euclidean
distance to the ideal in normalized space.

**Use when**: candidates differ along many axes and you
want a single defensible ranking that respects both
positive and negative reference points.

**Avoid when**: dimensions are not commensurable even after
normalization, or when reviewers will not accept a
geometric distance interpretation.

## Picking a Method

Decision tree:

```
1. Is any metric veto-class (security, correctness)?
   -> Yes: weighted sum + gate, or lexicographic
   -> No: continue
2. Are weights contested or unknown?
   -> Yes: Pareto front (no aggregation)
   -> No: continue
3. Should imbalance be punished superlinearly?
   -> Yes: weighted product
   -> No: continue
4. Do you need defensible single ranking with reference points?
   -> Yes: TOPSIS
   -> No: weighted sum (default)
```

| Need | First choice | Second |
|------|--------------|--------|
| Fast and explainable | Weighted sum | Weighted product |
| Hard priority | Lexicographic | Weighted sum and veto |
| Surface trade-offs | Pareto front | TOPSIS |
| Defensible against critique | TOPSIS | Weighted sum and sensitivity |

## Sensitivity Analysis (Required)

No matter the method, vary weights by +/- 20% and check
whether top-3 ranks change. If they do, the result is
weight-driven and needs more evidence before action.

```python
def rank_stability(scores, weights, variation=0.20, top_k=3):
    base = rank(scores, weights)[:top_k]
    flips = 0
    for w_name in weights:
        for delta in (+variation, -variation):
            perturbed = adjust(weights, w_name, delta)
            new = rank(scores, perturbed)[:top_k]
            if set(new) != set(base):
                flips += 1
    return flips / (2 * len(weights))    # 0.0 = stable, 1.0 = chaos
```

A flip rate above 0.3 means the ranking is fragile. Either
gather more data per metric or switch to Pareto front.

## Worked Example: Combining Methods

A team scores three skill candidates on (quality, cost,
adoption) for inclusion in a release.

```text
Candidates:
  alpha: q=5, c=2, a=3
  beta:  q=4, c=4, a=5
  gamma: q=3, c=5, a=2

Step 1 (gate): require q >= 3. All pass.

Step 2 (weighted sum), weights {q: 0.5, c: 0.2, a: 0.3}:
  alpha: 2.5 + 0.4 + 0.9 = 3.8
  beta:  2.0 + 0.8 + 1.5 = 4.3
  gamma: 1.5 + 1.0 + 0.6 = 3.1

Step 3 (sensitivity): vary q weight by +/- 0.1
  q=0.6: alpha=4.0, beta=4.2, gamma=3.4 -> beta still wins
  q=0.4: alpha=3.6, beta=4.4, gamma=2.8 -> beta still wins

Decision: ship beta. Rank stable; gates clear.
```

## Pitfalls

**Combining unnormalized metrics.** A latency in
milliseconds and a cost in dollars cannot share weights
until both are scaled to the same range. Normalize first.

**Equal weights as a default.** Equal weights are a strong
prior, not a neutral one. State the choice and justify it
or derive weights from AHP / expert elicitation.

**Aggregating away the trade-off.** A single number hides
the shape of the candidate. Always report the per-metric
vector alongside the aggregate.

**Skipping sensitivity.** A ranking that flips when one
weight moves 10% is not a finding; it is a coin flip
dressed up in arithmetic.

**Lexicographic on noisy metrics.** If m_1 is measured with
+/- 5% noise, lexicographic will treat noise as a tiebreaker.
Bucket m_1 into bands first.

## Cross-Reference

See `modules/scoring-patterns.md` for calibration of inputs,
`modules/quality-metrics.md` for concrete metric thresholds,
and `modules/decision-thresholds.md` for mapping aggregate
scores to actions.
