---
name: multi-metric-evaluation-methodology
description: Mathematically rigorous framework for multi-metric evaluation with proper normalization, weighting, and trade-off analysis
category: evaluation
tags: [mcda, metrics, methodology]
estimated_tokens: 800
---

# Multi-Metric Evaluation Methodology

Framework for evaluating artifacts across multiple dimensions using Multi-Criteria Decision Analysis (MCDA).

## Core Principles

### Core Principles

1. **Scale Invariance**: Rankings unchanged when units change (use vector normalization)
2. **Explicit Trade-offs**: Use Pareto analysis, context weighting, multi-dimensional reporting
3. **Validated Weights**: Derive through AHP, expert judgment, or empirical validation

## Normalization Techniques

### Vector Normalization (Recommended)
Scale-invariant normalization using Euclidean norm: `value / sqrt(sum_of_squares)`

### Logarithmic Normalization
For values spanning multiple orders of magnitude: `log(value + 1)`

### Min-Max Normalization (Caution)
NOT scale-invariant. Only use when absolute 0-100 bounds required.

## Weighting Methodologies

### Analytic Hierarchy Process (AHP)
Pairwise comparison with consistency checking. Consistency ratio must be < 0.1 to be acceptable.

### Expert Judgment Elicitation
Structured process using 5-15 calibrated experts with performance-based weighting.

## Handling Contradictory Metrics

### Pareto Frontier Analysis
Identify non-dominated solutions where no metric can improve without worsening another.

### Context-Aware Weighting
Adjust weights based on use case (e.g., safety-critical vs performance-critical).

### Multi-Dimensional Reporting
Report scores by dimension instead of collapsing to single score. Show trade-offs explicitly.

## Aggregation Methods

### Weighted Sum Model (WSM)

**Use when**: Metrics are independent and preferences are additive

```python
def weighted_sum_model(normalized_scores, weights):
    """
    Calculates composite score using weighted sum.

    Properties:
    - Simple and interpretable
    - Allows trade-offs between criteria
    - Assumes preferential independence
    """
    return sum(
        score * weight
        for score, weight in zip(normalized_scores, weights)
    )
```

**Limitation**: Doesn't handle preferential dependence

### TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)

**Use when**: You want to consider both ideal and worst-case scenarios

```python
def topsis(decision_matrix, weights):
    """
    Ranks alternatives by closeness to ideal solution.

    Steps:
    1. Normalize decision matrix (vector normalization)
    2. Apply weights
    3. Determine ideal and negative-ideal solutions
    4. Calculate separation measures
    5. Calculate relative closeness to ideal
    6. Rank by closeness

    Returns:
        List of (alternative, closeness_score) ranked by score
    """
    # Step 1: Vector normalization
    normalized = vector_normalize_columns(decision_matrix)

    # Step 2: Apply weights
    weighted = normalized * weights

    # Step 3: Determine ideal solutions
    ideal_best = weighted.max(axis=0)  # For benefit criteria
    ideal_worst = weighted.min(axis=0)  # For benefit criteria

    # Step 4: Calculate separation
    separation_best = sqrt(sum((weighted - ideal_best)**2, axis=1))
    separation_worst = sqrt(sum((weighted - ideal_worst)**2, axis=1))

    # Step 5: Relative closeness
    closeness = separation_worst / (separation_best + separation_worst)

    # Step 6: Rank
    return sorted(enumerate(closeness), key=lambda x: x[1], reverse=True)
```

**Advantages**:
- considers both best and worst cases
- Simple mathematical structure
- Widely used and validated

## Sensitivity Analysis

**Critical Step**: Always test how sensitive rankings are to weight changes

### One-at-a-Time (OAT) Sensitivity

```python
def sensitivity_analysis(base_weights, decision_matrix, variation=0.20):
    """
    Tests how rankings change when each weight varies by ±variation%.

    Returns:
        Dict mapping criterion to ranking stability
    """
    base_ranking = rank_alternatives(decision_matrix, base_weights)
    sensitivity = {}

    for i, criterion in enumerate(base_weights.keys()):
        # Test +20% change
        weights_plus = base_weights.copy()
        for key in weights_plus.keys():
            weights_plus[key] *= 0.80  # Reduce others
        weights_plus[criterion] *= 1.20  # Increase this one

        ranking_plus = rank_alternatives(decision_matrix, weights_plus)
        correlation_plus = rank_correlation(base_ranking, ranking_plus)

        # Test -20% change
        weights_minus = base_weights.copy()
        for key in weights_minus.keys():
            weights_minus[key] *= 1.20  # Increase others
        weights_minus[criterion] *= 0.80  # Reduce this one

        ranking_minus = rank_alternatives(decision_matrix, weights_minus)
        correlation_minus = rank_correlation(base_ranking, ranking_minus)

        sensitivity[criterion] = {
            "avg_correlation": (correlation_plus + correlation_minus) / 2,
            "sensitive": correlation_plus < 0.8 or correlation_minus < 0.8
        }

    return sensitivity
```

### Monte Carlo Sensitivity

```python
def monte_carlo_sensitivity(base_weights, decision_matrix, n_simulations=1000):
    """
    Tests ranking stability under random weight variations.

    Samples weights from Dirichlet distribution (ensures sum to 1.0)
    and calculates how often rankings change.
    """
    ranking_counts = defaultdict(Counter)

    for _ in range(n_simulations):
        # Sample random weights from Dirichlet distribution
        random_weights = np.random.dirichlet(list(base_weights.values()))
        ranking = rank_alternatives(decision_matrix, random_weights)

        for alt, rank in ranking:
            ranking_counts[alt][rank] += 1

    # Calculate stability metrics
    stability = {}
    for alt in ranking_counts.keys():
        most_common_rank = ranking_counts[alt].most_common(1)[0]
        stability[alt] = {
            "most_common_rank": most_common_rank[0],
            "frequency": most_common_rank[1] / n_simulations,
            "stable": most_common_rank[1] / n_simulations > 0.8
        }

    return stability
```

## Validation Framework

### Internal Validation

**Before using evaluation framework**:

```yaml
validation_checklist:
  normalization:
    - [ ] Technique documented (vector/log/minmax)
    - [ ] Scale invariance verified
    - [ ] Outlier handling tested

  weighting:
    - [ ] Weights sum to 1.0
    - [ ] Weight derivation method documented
    - [ ] AHP consistency ratio < 0.1 (if using AHP)
    - [ ] Expert calibration scores recorded

  aggregation:
    - [ ] Independence assumptions stated
    - [ ] Trade-off behavior tested
    - [ ] Edge cases examined

  sensitivity:
    - [ ] OAT sensitivity analysis completed
    - [ ] Critical weights identified (correlation < 0.8)
    - [ ] Monte Carlo stability tested (if high-stakes)
```

### External Validation

**Compare against ground truth**:

```python
def external_validation(evaluation_scores, ground_truth_outcomes):
    """
    Validates evaluation scores against actual outcomes.

    Metrics:
    - Rank correlation (Spearman's rho)
    - Classification accuracy (if quality gates exist)
    - Predictive value (if time-series data)
    """
    from scipy.stats import spearmanr

    correlation, p_value = spearmanr(evaluation_scores, ground_truth_outcomes)

    validation_report = {
        "spearman_correlation": correlation,
        "p_value": p_value,
        "validated": correlation > 0.7 and p_value < 0.05,
        "interpretation": interpret_correlation(correlation)
    }

    return validation_report
```

## Anti-Patterns

### ❌ Don't: Arbitrary Weights

```yaml
# BAD: Where did these numbers come from?
weights:
  structure: 0.20
  content: 0.25
  performance: 0.20
  activation: 0.20
  tools: 0.10
  docs: 0.05
```

### ✅ Do: Validated Weights

```yaml
# GOOD: Weights derived from AHP with expert panel
weights:
  structure: 0.20
  content: 0.25
  performance: 0.20
  activation: 0.20
  tools: 0.10
  docs: 0.05

derivation:
  method: "AHP"
  experts: 5
  consistency_ratio: 0.04
  date: "2025-01-07"
```

### ❌ Don't: Ignore Scale Invariance

```python
# BAD: Min-max normalization breaks with unit changes
def normalize_minmax(values):
    return [(v - min(values)) / (max(values) - min(values)) for v in values]

# If you change ms to seconds, rankings change!
```

### ✅ Do: Use Scale-Invariant Normalization

```python
# GOOD: Vector normalization preserves rankings
def normalize_vector(values):
    norm = sqrt(sum(v**2 for v in values))
    return [v / norm for v in values]

# Unit changes don't affect rankings
```

### ❌ Don't: Collapse Contradictory Metrics

```yaml
# BAD: Speed and safety trade-off hidden in single score
overall_score = 0.5 * speed + 0.5 * safety

# Speed=95, Safety=60 → 77.5
# Speed=70, Safety=85 → 77.5
# Same score, very different profiles!
```

### ✅ Do: Report Multi-Dimensionally

```yaml
# GOOD: Explicit trade-off reporting
dimension_scores:
  speed: 95/100
  safety: 60/100

trade_offs:
  - "High speed comes from minimal validation"
  - "Not suitable for safety-critical contexts"

classification: "performance_optimized"
alternative: "secure-variant" if safety required
```

### ❌ Don't: Skip Sensitivity Analysis

```yaml
# BAD: No understanding of robustness
final_score: 82.3/100
```

### ✅ Do: Include Sensitivity

```yaml
# GOOD: Robustness quantified
final_score: 82.3/100

sensitivity_analysis:
  critical_weights: ["content_quality"]  # Ranking changes if this varies >15%
  stable_weights: ["documentation", "tools"]  # Ranking stable even with ±30% variation
  monte_carlo_stability: 0.92  # 92% of simulations give same ranking

interpretation: "Score is robust to small weight variations, but sensitive to content quality weight"
```

## Implementation Checklist

When implementing evaluation frameworks:

- [ ] **Normalization**: Use vector normalization for scale invariance
- [ ] **Weighting**: Document weight derivation method (AHP, experts, empirical)
- [ ] **Contradictions**: Use Pareto analysis when metrics conflict
- [ ] **Sensitivity**: Run OAT sensitivity on all weights
- [ ] **Validation**: Test against known-good/bad examples
- [ ] **Documentation**: Explain all mathematical choices
- [ ] **Reproducibility**: Same inputs → same outputs

## References

- OECD Handbook on Constructing Composite Indicators (4,461 citations)
- "Normalization Techniques for MCDA" - Vafaei et al. (339 citations)
- "Scale dependence in MCDA methods" - Abbas (2023)
- "Multi-Objective Bayesian Optimization using Pareto-frontier Entropy" - Suzuki et al. (119 citations)
- "A Comprehensive Guide to TOPSIS" - SSRN (159 citations)
