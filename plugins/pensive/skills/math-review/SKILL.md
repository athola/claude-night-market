---
name: math-review
description: Verifies math-heavy code for algorithmic correctness and numerical stability. Use when reviewing scientific algorithms, ML models, or numerical code.
alwaysApply: false
category: specialized
tags:
- math
- algorithms
- numerical
- stability
- verification
- scientific
tools: []
usage_patterns:
- algorithm-review
- numerical-analysis
- derivation-verification
- stability-assessment
complexity: advanced
model_hint: deep
estimated_tokens: 200
progressive_loading: true
dependencies:
- imbue:proof-of-work
- imbue:review-core
- imbue:structured-output
---

# Mathematical Algorithm Review

Intensive analysis ensuring numerical stability and alignment with standards.

## Quick Start

```bash
/math-review
```
**Verification:** Run the command with `--help` flag to verify availability.

## When To Use

- Changes to mathematical models or algorithms
- Statistical routines or probabilistic logic
- Numerical integration or optimization
- Scientific computing code
- ML/AI model implementations
- Safety-critical calculations

## When NOT To Use

- General algorithm review -
  use architecture-review
- Performance optimization - use parseltongue:python-performance

## Required TodoWrite Items

1. `math-review:context-synced`
2. `math-review:requirements-mapped`
3. `math-review:derivations-verified`
4. `math-review:stability-assessed`
5. `math-review:evidence-logged`
6. `math-review:findings-verified`

## Core Workflow

### 1. Context Sync
```bash
pwd && git status -sb && git diff --stat origin/main..HEAD
```
**Verification:** Run `git status` to confirm working tree state.
Enumerate math-heavy files (source, tests, docs, notebooks). Classify risk: safety-critical, financial, ML fairness.

### 2. Requirements Mapping
Translate requirements → mathematical invariants. Document pre/post conditions, conservation laws, bounds. **Load**: `modules/requirements-mapping.md`

### 3. Derivation Verification
Re-derive formulas using CAS. Challenge approximations. Cite authoritative standards (NASA-STD-7009, ASME VVUQ). **Load**: `modules/derivation-verification.md`

### 4. Stability Assessment
Evaluate conditioning, precision, scaling, randomness. Compare complexity. Quantify uncertainty. **Load**: `modules/numerical-stability.md`

### 5. Proof of Work
```bash
pytest tests/math/ --benchmark
jupyter nbconvert --execute derivation.ipynb
```
**Verification:** Run `pytest -v tests/math/` to verify.
Log deviations, recommend: Approve / Approve with actions / Block. **Load**: `modules/testing-strategies.md`

### 6. Verify Findings Are Grounded (`math-review:findings-verified`)

Write issues to `.review/findings.json` and run the citation verifier
as `Skill(imbue:review-core)` Step 5 describes. Only issues the
verifier passes enter the report. Drop or label `UNVERIFIED` the rest.

## Progressive Loading

**Default (200 tokens)**: Core workflow, checklists
**+Requirements** (+300 tokens): Invariants, pre/post conditions, coverage analysis
**+Derivation** (+350 tokens): CAS verification, standards, citations
**+Stability** (+400 tokens): Numerical properties, precision, complexity
**+Testing** (+350 tokens): Edge cases, benchmarks, reproducibility

**Total with all modules**: ~1600 tokens

## Essential Checklist

**Correctness**: Formulas match spec | Edge cases handled | Units consistent | Domain enforced
**Stability**: Condition number OK | Precision sufficient | No cancellation | Overflow prevented
**Verification**: Derivations documented | References cited | Tests cover invariants | Benchmarks reproducible
**Documentation**: Assumptions stated | Limitations documented | Error bounds specified | References linked

## Output Format

```markdown
## Summary
[Brief findings]

## Context
Files | Risk classification | Standards

## Requirements Analysis
| Invariant | Verified | Evidence |

## Derivation Review
[Status and conflicts]

## Stability Analysis
Condition number | Precision | Risks

## Issues
[M1] [Title]
- Location: file.py:123
- Anchor: `verbatim source text at line 123`
- Issue: [what is wrong] | Fix: [remediation] | Evidence: [E1]

## Recommendation
Approve / Approve with actions / Block
```
Every issue's `Anchor` is the exact source text at `Location`; it is what
`citation_verifier.py` re-reads to prove the finding is real.
**Verification:** Run the command with `--help` flag to verify availability.

## Exit Criteria

- Context synced, requirements mapped, derivations verified, stability assessed, evidence logged with citations
- Every reported issue carries a `Location` + verbatim `Anchor`, and `citation_verifier.py` confirmed all citations (exit `0`) or unverified issues were dropped or labeled `UNVERIFIED`
