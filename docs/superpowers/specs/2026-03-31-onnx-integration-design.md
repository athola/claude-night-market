# ONNX ML Inference Integration -- Design Spec

**Date:** 2026-03-31
**Status:** Draft
**Host plugin:** gauntlet (Phase 1), leyline extraction (Phase 2)

## Problem Statement

Gauntlet's open-ended challenge scoring uses word-overlap
(`|intersection| / |reference|`), which fails when a
correct answer uses different vocabulary than the reference.
A student who demonstrates genuine understanding but uses
synonyms or restructures the explanation scores poorly.

More broadly, the night-market plugin ecosystem has no ML
inference capability. Four plugins (gauntlet, conserve,
pensive, parseltongue) perform analytical work that would
benefit from lightweight classification and scoring models.

## Goals

1. Add ML-enhanced quality scoring to gauntlet's
   open-ended challenge evaluation
2. Establish an inference interface (`Scorer` protocol)
   that supports backend swapping (YAML to ONNX)
3. Maintain zero new runtime dependencies in Phase 1
4. Preserve backward compatibility: all existing tests
   must pass, grading thresholds stay the same
5. Design for Phase 2 extraction to leyline when a
   second plugin needs inference

## Success Criteria

- [ ] Open-ended scoring uses blended ML + word-overlap
- [ ] ML scoring degrades gracefully when model file is
      missing or corrupt (returns `None`, falls back to
      word-overlap)
- [ ] `Scorer` protocol is defined and `YamlScorer`
      implements it
- [ ] Feature extraction produces 7 features from
      challenge + answer pairs
- [ ] All existing `test_scoring.py` BDD tests pass
- [ ] 90% test coverage maintained
- [ ] Zero new dependencies in `pyproject.toml`

## Constraints

- **Python 3.9.6:** System Python. All code must use
  3.9-compatible syntax. `from __future__ import
  annotations` for union types.
- **No onnxruntime in Phase 1:** Current onnxruntime
  (1.24.x) requires Python >= 3.11. Phase 1 uses pure
  Python config-as-model pattern.
- **90% coverage gate:** Enforced in pyproject.toml.
- **pyyaml is the only dependency:** Already present.
  Model YAML files are loaded with it.

## Research Summary

Five research channels were consulted (full report in
`docs/research/onnx-research-2026-03-31.md`):

| Channel | Key Finding |
|---------|-------------|
| ONNX Python API | Core modules: helper, checker, shape_inference. Protobuf serialization. |
| GitHub (9 repos) | Optional-extras packaging is dominant. Sidecar process for inference isolation. |
| Community (15 findings) | Silent failures are #1 risk (33% of converter failures produce wrong outputs). |
| Academic (10 papers) | ONNX more secure than pickle. Performance not guaranteed without tuning. |
| TRIZ (5 fields) | Tiered architecture resolves the "ML capability vs deployment simplicity" contradiction. |

### Tiered Architecture (from TRIZ)

| Tier | What | Deps | Phase |
|------|------|------|-------|
| 0 | Config-as-model: YAML coefficients, dot-product inference | Zero | 1 |
| 1 | Rule-based heuristics: existing regex/AST hooks | Zero | Existing |
| 2 | Sidecar ONNX daemon: isolated venv (Python 3.11+) | onnxruntime | 2 |
| 3 | Claude API: reasoning-level analysis | Existing | Existing |

## Architecture

### Phase 1 File Layout

```
gauntlet/src/gauntlet/
  ml/
    __init__.py           # Public API: score_answer_quality()
    scorer.py             # Scorer protocol + YamlScorer
    features.py           # Feature extraction
    models/
      quality_v1.yaml     # Logistic regression coefficients
  scoring.py              # MODIFIED: ML-enhanced open-ended scoring
  models.py               # UNCHANGED
  __init__.py             # MODIFIED: export ml module
```

### Scorer Protocol

```python
class Scorer(Protocol):
    def score(self, features: dict[str, float]) -> float: ...
    def available(self) -> bool: ...
```

Phase 1: `YamlScorer` (pure Python dot product + sigmoid).
Phase 2: `OnnxSidecarScorer` (HTTP to localhost daemon).

Both implement `Scorer`. Consumer code never changes.

### Feature Schema

`extract_answer_features(challenge, answer)` returns:

| Feature | Description |
|---------|-------------|
| `word_overlap_ratio` | Existing metric reused from scoring.py |
| `length_ratio` | answer length / reference length |
| `keyword_coverage` | words from challenge.context present in answer / total context words |
| `structural_depth` | count of code blocks, bullets, examples |
| `unique_word_ratio` | unique words / total words |
| `negation_density` | negation terms / total words |
| `numeric_match` | matching numerics / reference numerics |

### Scoring Integration

`evaluate_answer()` modified for open-ended types only:

```python
ratio = _word_overlap_ratio(challenge.answer, stripped)
ml_score = score_answer_quality(challenge, stripped)
if ml_score is not None:
    combined = 0.4 * ratio + 0.6 * ml_score
else:
    combined = ratio
```

- Blend weights configurable in model YAML
- Thresholds unchanged: >= 0.5 pass, >= 0.2 partial
- `multiple_choice` and `dependency_map` unchanged

### Model YAML Format

```yaml
schema_version: 1
model_type: logistic_regression
features:
  - word_overlap_ratio
  - length_ratio
  - keyword_coverage
  - structural_depth
  - unique_word_ratio
  - negation_density
  - numeric_match
weights:
  word_overlap_ratio: 1.82
  length_ratio: 0.45
  keyword_coverage: 2.14
  structural_depth: 0.73
  unique_word_ratio: 0.38
  negation_density: -1.21
  numeric_match: 1.05
intercept: -2.31
sigmoid: true
blend:
  word_overlap_weight: 0.4
  ml_weight: 0.6
metadata:
  trained_on: "gauntlet answer corpus v1"
  accuracy: 0.87
  f1: 0.84
```

## Phase 2 Upgrade Path

When a second plugin needs inference:

1. Add `OnnxSidecarScorer` to gauntlet
2. Extract `Scorer` protocol, `YamlScorer`, and sidecar
   client to `leyline/src/leyline/ml/`
3. Gauntlet and other plugins import from leyline
4. Sidecar daemon: separate Python 3.11+ venv,
   `onnxruntime`, localhost HTTP, SessionStart hook
   spawns it, SessionEnd hook stops it

No changes to `scoring.py`, `features.py`, or model YAML.
The `score_answer_quality()` function swaps the backend
internally based on `OnnxSidecarScorer.available()`.

## Testing Strategy

### Unit Tests

- **features.py:** Given Challenge + answer, assert feature
  dict keys and value ranges
- **scorer.py:** Load test YAML, verify dot-product math,
  verify sigmoid transform, verify `available()` returns
  False for missing/corrupt files
- **ml/__init__.py:** Verify `score_answer_quality()` returns
  `None` when model unavailable, returns 0.0-1.0 when
  available

### Integration Tests

- **scoring.py:** All existing BDD tests pass with ML active
- **Backward compatibility:** Run existing test suite with
  and without model file present

### Coverage

90% minimum enforced. No new dependencies to mock.

## Out of Scope (Phase 1)

- Sidecar daemon infrastructure
- Semantic similarity and embeddings
- Model training pipeline (coefficients hand-tuned or
  trained offline, shipped as YAML)
- Other plugin integrations (conserve, pensive,
  parseltongue)
- ONNX Runtime dependency
- GPU support

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| ML score worse than word-overlap for some cases | Medium | Blend weights keep word-overlap influence at 40%; easy to adjust |
| Model YAML tampered with | Low | Gauntlet is a dev tool, not security-critical; model is version-controlled |
| Feature extraction too slow | Very low | 7 features from string ops; sub-millisecond |
| Phase 2 extraction breaks gauntlet | Low | Scorer protocol makes extraction a refactor, not a rewrite |

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Host in gauntlet, not new plugin | Avoids plugin sprawl; first consumer is the host |
| Config-as-model over ONNX Runtime | Python 3.9 constraint; zero-dependency Phase 1 |
| Extract to leyline in Phase 2 | Leyline already has Python runtime code; most plugins depend on it |
| Keep word-overlap as fallback | ISSTA 2024: 33% of ML failures are silent; belt-and-suspenders |
| YAML over JSON for model | Supports comments for human auditability |
| Blend not replace | Backward compatible; thresholds unchanged |
