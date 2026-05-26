---
name: evaluation-rubric
description: Concrete rubric templates for skills, plugins, and features with dimensions, weights, scales, and aggregation rules
category: evaluation
tags: [rubric, scoring, templates, dimensions, weights]
estimated_tokens: 850
---

# Evaluation Rubric

Concrete rubric templates you can copy and adapt. A rubric
fixes four things before any artifact is scored: the
dimensions (what you measure), the scale (how you score
each dimension), the weights (how dimensions combine), and
the aggregation rule (how a final number is produced).

## Anatomy of a Rubric

Every reusable rubric has the same five parts. Skip any of
them and reviewers drift.

| Part | Purpose | Failure if missing |
|------|---------|--------------------|
| Dimensions | What is being measured | Reviewers invent their own |
| Anchored scale | What each score means | Score inflation, no calibration |
| Weights | Relative importance | Implicit politics determine outcome |
| Aggregation rule | How parts combine | Different reviewers compute differently |
| Decision mapping | What the score triggers | Score with no consequence is theatre |

The first four are below; decision mapping is in
`modules/decision-thresholds.md`.

## Picking a Scale

Three scales cover most cases. Pick one per rubric and do
not mix.

### 0-2 Ordinal (Pass / Partial / Fail)

Use when the dimension is binary in spirit but you want to
allow partial credit. Cheap to score, hard to game.

| Score | Meaning |
|-------|---------|
| 2 | Fully satisfied, no caveats |
| 1 | Partially satisfied, named caveat |
| 0 | Not satisfied or absent |

Best for: gates, checklists, presence-of-evidence
dimensions ("has tests", "has version pin").

### 1-5 Likert

Use when reviewers must distinguish "good" from "great".
Five points let raters separate adequate from excellent
without false precision. Anchor every odd score (1, 3, 5)
with a worked example.

| Score | Meaning |
|-------|---------|
| 5 | Exemplary; reference for others |
| 4 | Above bar; minor gaps |
| 3 | Meets bar |
| 2 | Below bar; named gaps |
| 1 | Does not meet bar |

Best for: skill quality, doc quality, code review.

### 0-100 Continuous

Use when you have measurable inputs (coverage percent,
benchmark numbers) or need fine differentiation across many
items. More expensive to calibrate; risks false precision
if anchors are vague.

Best for: large rankings, ML evals, automated scoring.

**Rule of thumb**: if you cannot tell the difference
between score N and N+1 without a reference example, your
scale is too granular.

## Template 1: Skill Quality Rubric

Drop-in rubric for evaluating Claude Code skills. Scale: 1-5.

```yaml
rubric: skill-quality
scale: 1-5
dimensions:
  activation_clarity:
    weight: 0.20
    question: "Does the skill activate at the right moment?"
    anchors:
      5: "Trigger conditions list 3+ phrases; tested in subagent"
      3: "Trigger described prose-only; activates most cases"
      1: "Activation unclear; depends on user remembering name"
  evidence_grounding:
    weight: 0.20
    question: "Are claims backed by tests, sources, or runs?"
    anchors:
      5: "Every recommendation cites a working example or test"
      3: "Claims are plausible; partial evidence"
      1: "Assertions with no proof; pattern-matched advice"
  scope_discipline:
    weight: 0.15
    question: "Does it stay in its lane?"
    anchors:
      5: "Explicit when-not-to-use; defers to siblings"
      3: "Stays in scope but no deferral guidance"
      1: "Overlaps with other skills; no boundaries"
  token_economy:
    weight: 0.15
    question: "Is the skill body small and modules paged?"
    anchors:
      5: "SKILL.md under 500 lines; modules loaded on demand"
      3: "Single file 500-1500 lines; no progressive loading"
      1: "Monolithic 2000+ lines; loaded eagerly"
  testability:
    weight: 0.15
    question: "Can the skill be exercised by a subagent test?"
    anchors:
      5: "RED/GREEN test exists; documented invocation"
      3: "Manual test plan exists; not automated"
      1: "No test path documented"
  composition:
    weight: 0.15
    question: "Does it play with sibling skills cleanly?"
    anchors:
      5: "Declares dependencies; cited by 2+ peer skills"
      3: "Standalone; no broken refs"
      1: "Dangling Skill() refs or duplicated logic"
aggregation: weighted_sum
range: [1.0, 5.0]
```

## Template 2: Plugin Quality Rubric

For plugin-level review. Mixes 0-2 gate dimensions with
1-5 quality dimensions. Plugins fail if any gate is 0.

```yaml
rubric: plugin-quality
gates:                       # 0-2 each; any 0 fails
  manifest_valid:
    description: "plugin.json parses and schema validates"
  no_dangling_refs:
    description: "Every Skill() and command ref resolves"
  declared_deps_match_imports:
    description: "Frontmatter dependencies match real imports"
quality:                     # 1-5 each; weighted
  skill_quality_avg:
    weight: 0.30
    source: "mean of skill-quality rubric scores"
  doc_quality:
    weight: 0.20
    anchors:
      5: "README has thesis, examples, anti-goals"
      3: "README describes purpose; no examples"
      1: "Stub README"
  test_coverage:
    weight: 0.20
    anchors:
      5: ">= 85% lines, branch coverage tracked"
      3: "60-85% lines"
      1: "< 60% or no test target"
  release_hygiene:
    weight: 0.15
    anchors:
      5: "CHANGELOG, semver, signed tags"
      3: "Versions bumped but no changelog entries"
      1: "No version bumps; tags missing"
  cross_plugin_fit:
    weight: 0.15
    anchors:
      5: "Used by 2+ peer plugins; clear API"
      3: "Self-contained; no peers consume it"
      1: "Duplicates work done by another plugin"
aggregation: |
  if any gate == 0: fail
  else: quality_score = sum(weight_i * score_i)
range: [1.0, 5.0]
```

## Template 3: Feature Backlog Rubric

For prioritizing backlog items. Compact wrapper around
RICE+WSJF; details are in the `scoring-framework` module of
the `feature-review` skill (under `plugins/imbue/`).

```yaml
rubric: feature-backlog
scale: fibonacci [1, 2, 3, 5, 8, 13]
value_dimensions:
  reach: {weight: 0.25}
  impact: {weight: 0.30}
  business_value: {weight: 0.25}
  time_criticality: {weight: 0.20}
cost_dimensions:
  effort: {weight: 0.40}
  risk: {weight: 0.30}
  complexity: {weight: 0.30}
aggregation: |
  value = sum(w_v * score_v)
  cost = sum(w_c * score_c)
  priority = (value / cost) * confidence
range: [0.0, 13.0]
```

## Aggregation Rules

Pick one explicitly. Each has trade-offs.

| Rule | Formula | Use when |
|------|---------|----------|
| Weighted sum | sum(w_i * s_i) | Dimensions are substitutable |
| Weighted product | product(s_i ** w_i) | One bad dim should drag total down |
| Min (worst-of) | min(s_i) | Any failing dim is a real failure |
| Lexicographic | sort by d1, ties by d2 | Strict priority order |
| Weighted sum and gates | gates pass AND weighted sum | Some dims are veto-class |

Weighted sum is the default. Pick anything else only if you
can name the dimension that should be allowed to veto.

## Worked Example: Scoring a Skill

A reviewer applies the skill-quality rubric to a fictional
`tome:research` skill.

```text
activation_clarity:  4   (3+ trigger phrases; no subagent test)
evidence_grounding:  5   (every claim has a worked search)
scope_discipline:    4   (defers to dig and synthesize)
token_economy:       3   (SKILL.md is 1100 lines, no paging)
testability:         3   (manual plan only)
composition:         5   (used by feature-review and minister)

weighted_sum =
   4 * 0.20 + 5 * 0.20 + 4 * 0.15 +
   3 * 0.15 + 3 * 0.15 + 5 * 0.15
 = 0.80 + 1.00 + 0.60 + 0.45 + 0.45 + 0.75
 = 4.05
```

Decision mapping (per `decision-thresholds.md`):

| Range | Action |
|-------|--------|
| 4.5-5.0 | Promote to exemplar set |
| 3.5-4.4 | Ship; track top gap |
| 2.5-3.4 | Iterate before next release |
| < 2.5 | Block release |

A 4.05 ships with the token-economy gap tracked.

## Pitfalls

**Inventing dimensions per artifact.** If reviewers add
their own dimensions, the rubric is dead. Lock the
dimension list and version the rubric.

**Anchors only at the extremes.** "5 = best, 1 = worst"
guarantees central tendency bias. Anchor odd scores at
minimum, with a real example.

**Weights summing to 1.0 by accident.** State the sum
and assert it in the file. A weight of 0.30 next to 0.40
next to 0.40 sums to 1.10 and silently overweights all
dimensions.

**Mixing scales within one rubric.** A 0-100 dimension
combined with a 1-5 dimension under weighted sum hands the
0-100 dimension 20x the influence. Normalize first or
keep scales matched.

**No decision mapping.** A score that triggers nothing
trains reviewers to score for vibes.

**Rubric never revisited.** If 90% of artifacts score
4-5, the rubric stopped discriminating. Recalibrate
anchors against the current population yearly.

## Cross-Reference

See `modules/scoring-patterns.md` for calibration and
`modules/decision-thresholds.md` for mapping scores to
actions.
