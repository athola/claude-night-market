---
name: multi-metric-evaluation-methodology
description: Mathematically rigorous framework for evaluating skills, hooks, and commands across multiple dimensions with proper normalization, weighting, and trade-off analysis
category: evaluation
tags: [mcda, metrics, methodology, normalization, weighting, pareto, sensitivity-analysis]
estimated_tokens: 1200
---

# Multi-Metric Evaluation Methodology

Mathematically rigorous framework for evaluating artifacts across multiple, potentially contradictory dimensions using Multi-Criteria Decision Analysis (MCDA) best practices.

## Core Principles

### 1. Scale Invariance

**Critical Requirement**: Evaluation rankings must not change when units change (e.g., milliseconds → seconds, bytes → KB).

**Violation Example**:
```yaml
# BAD: Min-max normalization is NOT scale-invariant
score = (value - min) / (max - min)
# Changing units changes min/max, which changes rankings

# GOOD: Vector normalization is scale-invariant
score = value / sqrt(sum_of_squares)
# Multiplying all values by constant cancels out
```

### 2. Explicit Trade-offs

When metrics are contradictory (e.g., speed vs. safety), acknowledge rather than hide the trade-off.

**Approaches**:
- **Pareto Analysis**: Identify non-dominated solutions
- **Context-Aware Weighting**: Adjust weights based on use case
- **Multi-Dimensional Reporting**: Don't collapse to single score

### 3. Validated Weights

Weights must be derived through systematic processes, not arbitrary assignment.

**Validation Methods**:
- **Analytic Hierarchy Process (AHP)**: Pairwise comparison with consistency checks
- **Expert Judgment**: Structured elicitation with calibration
- **Empirical Validation**: Test weights against outcomes

## Normalization Techniques

### Vector Normalization (Recommended)

**Use when**: Scale invariance is required (most cases)

```python
def vector_normalize(values):
    """
    Normalizes values using Euclidean norm.
    Scale-invariant: multiplying all values by constant doesn't change results.

    Properties:
    - Preserves scale invariance
    - Handles outliers better than min-max
    - Works for both benefit and cost criteria
    """
    norm = sqrt(sum(v**2 for v in values))
    return [v / norm for v in values]
```

**Example**:
```yaml
execution_times_ms: [50, 100, 200, 500]
# Vector normalized: [0.093, 0.186, 0.371, 0.928]

# Convert to seconds: [0.050, 0.100, 0.200, 0.500]
# Vector normalized: [0.093, 0.186, 0.371, 0.928]
# Same rankings! Scale-invariant.
```

### Logarithmic Normalization

**Use when**: Values span multiple orders of magnitude

```python
def log_normalize(values):
    """
    Normalizes using log transformation.
    Useful for heavily skewed distributions.
    """
    log_values = [log(v + 1) for v in values]  # +1 to avoid log(0)
    norm = sum(log_values)
    return [v / norm for v in log_values]
```

**Example use case**: Token counts (range: 100 to 100,000+)

### Min-Max Normalization (Use with Caution)

**Use when**: Bounded scale needed, NOT scale-invariant

```python
def minmax_normalize(values):
    """
    Normalizes to [0, 1] range.
    WARNING: NOT scale-invariant. Use sparingly.
    """
    min_val, max_val = min(values), max(values)
    return [(v - min_val) / (max_val - min_val) for v in values]
```

**When to use**: Only when you need absolute 0-100 bounds and accept scale dependence

## Weighting Methodologies

### Analytic Hierarchy Process (AHP)

**Best for**: When you have multiple experts and need rigorous weight validation

**Process**:

1. **Structure Criteria Hierarchy**
```
Overall Quality
├── Functional (40%)
│   ├── Correctness (60%)
│   └── Completeness (40%)
├── Performance (30%)
│   ├── Speed (50%)
│   └── Efficiency (50%)
└── Quality (30%)
    ├── Reliability (40%)
    └── Safety (40%)
```

2. **Pairwise Comparison**

Compare criteria two at a time:

```yaml
comparison_scale:
  1: Equal importance
  3: Moderately more important
  5: Strongly more important
  7: Very strongly more important
  9: Extremely more important
  2,4,6,8: Intermediate values
```

3. **Calculate Weights**

```python
def ahp_weights(comparison_matrix):
    """
    Calculates weights from pairwise comparison matrix.
    Returns weights and consistency_ratio.
    """
    # Calculate eigenvector
    eigenvalues, eigenvectors = np.linalg.eig(comparison_matrix)
    principal_eigenvalue = max(eigenvalues.real)
    weights = eigenvectors[:, eigenvalues.argmax()].real
    weights = weights / weights.sum()  # Normalize

    # Check consistency
    n = len(weights)
    consistency_index = (principal_eigenvalue - n) / (n - 1)
    random_index = [0, 0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49][n]
    consistency_ratio = consistency_index / random_index

    if consistency_ratio > 0.1:
        warning(f"Inconsistent judgments (CR={consistency_ratio:.2f})")

    return weights, consistency_ratio
```

4. **Validate Consistency**

- **Consistency Ratio < 0.1**: Acceptable
- **Consistency Ratio > 0.1**: Reconsider judgments

### Expert Judgment Elicitation

**Best for**: When you have domain experts but limited time

**Structured Process**:

1. **Calibration Questions**: Include questions with known answers to assess expert accuracy
2. **Multiple Experts**: Use 5-15 experts to reduce individual bias
3. **Performance-Based Weighting**: Weight contributions by calibration performance
4. **Feedback**: Provide experts with feedback on their performance

**Example**:

```yaml
expert_elicitation:
  experts:
    - name: "Expert A"
      calibration_score: 0.85
      weight: 0.35
    - name: "Expert B"
      calibration_score: 0.72
      weight: 0.30
    - name: "Expert C"
      calibration_score: 0.91
      weight: 0.35

  criteria_weights:
    correctness: {A: 0.35, B: 0.30, C: 0.35}
    performance: {A: 0.28, B: 0.36, C: 0.36}
    safety: {A: 0.40, B: 0.25, C: 0.35}
```

## Handling Contradictory Metrics

### Pareto Frontier Analysis

**Use when**: Metrics genuinely conflict and no single optimal solution exists

**Definition**: A solution is Pareto-optimal if you cannot improve one metric without worsening another.

**Algorithm**:

```python
def find_pareto_front(solutions):
    """
    Identifies Pareto-optimal solutions from multi-metric evaluations.

    Args:
        solutions: List of dicts with metric scores

    Returns:
        List of Pareto-optimal solutions
    """
    pareto_front = []

    for candidate in solutions:
        is_dominated = False

        for other in solutions:
            if other is candidate:
                continue

            # Check if 'other' dominates 'candidate'
            # Other dominates if it's >= on all metrics and > on at least one
            better_or_equal = all(
                other[metric] >= candidate[metric]
                for metric in candidate.keys()
            )
            strictly_better = any(
                other[metric] > candidate[metric]
                for metric in candidate.keys()
            )

            if better_or_equal and strictly_better:
                is_dominated = True
                break

        if not is_dominated:
            pareto_front.append(candidate)

    return pareto_front
```

**Example Application**:

```python
skills = [
    {"name": "skill-a", "speed": 95, "safety": 60},
    {"name": "skill-b", "speed": 70, "safety": 85},
    {"name": "skill-c", "speed": 80, "safety": 75},
    {"name": "skill-d", "speed": 65, "safety": 80},
]

pareto_optimal = find_pareto_front(skills)
# Returns: skill-a, skill-b (skill-c and d are dominated)
```

**Visualization**: Always plot Pareto front to make trade-offs visible

### Context-Aware Weighting

**Use when**: Optimal trade-off depends on context

```yaml
contexts:
  safety_critical:
    weights:
      speed: 0.20
      safety: 0.80
    rationale: "Safety failures are unacceptable"

  performance_critical:
    weights:
      speed: 0.70
      safety: 0.30
    rationale: "Performance is primary, safety checks are sufficient"

  balanced:
    weights:
      speed: 0.50
      safety: 0.50
    rationale: "Equal priority on both dimensions"
```

### Multi-Dimensional Reporting

**Instead of single score**: Report scores by dimension

```yaml
evaluation_report:
  skill_name: "async-executor"

  dimension_scores:
    correctness: 92/100
    performance: 78/100
    reliability: 88/100
    safety: 85/100
    usability: 90/100

  trade_offs:
    - "High performance (78) comes from minimal error handling"
    - "Consider adding error checks for safety-critical contexts"

  recommendations:
    - "Use in performance-critical contexts"
    - "Avoid in safety-critical systems without enhancements"
```

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
