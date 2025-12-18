# Decision Framework

Core worthiness formula and scoring system for evaluating features.

## Worthiness Formula

```
Worthiness = (Business Value + Time Criticality + Risk Reduction) / (Complexity + Token Cost + Scope Drift)
```

Score each factor on Fibonacci scale (1, 2, 3, 5, 8, 13).

## Value Factors (Numerator)

| Factor | 1 | 5 | 13 |
|--------|---|---|---|
| **Business Value** | Nice-to-have, no stated requirement | Addresses indirect need | Directly required by spec/customer |
| **Time Criticality** | No deadline | Soft deadline this quarter | Hard deadline, blocking release |
| **Risk Reduction** | Hypothetical future risk | Documented risk, low impact | Active production risk |

## Cost Factors (Denominator)

| Factor | 1 | 5 | 13 |
|--------|---|---|---|
| **Complexity** | < 100 lines, single file | 300-500 lines, 3-5 files | 1000+ lines, architectural change |
| **Token Cost** | Quick implementation, minimal iteration | Moderate exploration needed | Research-heavy, multiple attempts |
| **Scope Drift** | Core to branch purpose | Related but adjacent | Different epic entirely |

## Example Calculation

```
Feature: Add retry logic to API client

Business Value: 8 (addresses known flakiness complaints)
Time Criticality: 3 (no hard deadline)
Risk Reduction: 5 (reduces documented intermittent failures)

Complexity: 3 (< 200 lines, 2 files)
Token Cost: 2 (straightforward pattern)
Scope Drift: 2 (related to current API work)

Worthiness = (8 + 3 + 5) / (3 + 2 + 2) = 16 / 7 = 2.3

Decision: > 2.0 → Implement now
```

## Decision Thresholds

| Score | Decision | Action |
|-------|----------|--------|
| > 2.0 | **Implement now** | Proceed with work |
| 1.0 - 2.0 | **Discuss** | Justify before proceeding, consider alternatives |
| < 1.0 | **Defer to backlog** | Add to queue.md with full context |

## Comparison Against Backlog

When evaluating a new feature:

1. Check `docs/backlog/queue.md` for existing items
2. If relevant items exist:
   - Compare Worthiness Scores
   - New item must beat top queued item OR fit within branch budget
3. If no relevant items in queue:
   - Generate 2 reasonable alternatives
   - Score alternatives
   - Compare and pick highest

**Comparison Prompt:**
```
Proposed: [Feature X] - Worthiness: 1.8

Top backlog items for comparison:
1. [Feature A] - Worthiness: 2.1 - Added: 2025-12-01
2. [Feature B] - Worthiness: 1.6 - Added: 2025-12-05

Does Feature X (1.8) justify:
- Displacing Feature A (2.1)?
- OR consuming branch budget?
```
