---
name: quality-metrics
description: Concrete quality thresholds for code, docs, and skills with sources, defaults, and how to measure
category: evaluation
tags: [coverage, complexity, slop, ratios, thresholds, metrics]
estimated_tokens: 900
---

# Quality Metrics

Concrete numeric thresholds for evaluating code, docs, and
skill artifacts. Each metric below has a name, a default
threshold, a measurement command, and a citation. Defaults
are starting points: tighten or loosen them per repository
based on historical data, then document the deviation in
your repo's evaluation config.

## Code Quality Metrics

### Test Coverage

Line and branch coverage from a coverage tool.

| Tier | Line | Branch | Posture |
|------|------|--------|---------|
| Critical (libs, billing) | >= 90% | >= 85% | Hard fail below |
| Standard (apps, services) | >= 80% | >= 70% | Warn below |
| Experimental (spikes) | >= 60% | tracked | Informational |

**Why these numbers**: Google's testing guide reports
diminishing returns above 90%; below 60% bug regression
risk doubles in tracked studies. See "How Google Tests
Software" (Whittaker, Arbon, Carollo).

**Measure**: `pytest --cov --cov-branch --cov-report=term`
(Python), `cargo tarpaulin` (Rust), `go test -cover` (Go).

### Cyclomatic Complexity (per function)

McCabe complexity counts independent paths through a
function.

| Score | Posture |
|-------|---------|
| 1-10 | Acceptable |
| 11-20 | Refactor candidate; add tests |
| 21-50 | Refactor required |
| > 50 | Block merge |

**Source**: McCabe 1976; SEI guidance. Functions above 10
have a measurably higher defect rate.

**Measure**: `radon cc -s -a src/` (Python),
`gocyclo -over 10 .` (Go), `clippy::cognitive_complexity`
(Rust).

### Function Length

| Lines | Posture |
|-------|---------|
| < 50 | Acceptable |
| 50-100 | Review for extraction |
| > 100 | Refactor required |

Long functions correlate with high cyclomatic complexity;
flag both, fix the one with worse trend.

### Cognitive Complexity (Sonar)

Variant of cyclomatic complexity that penalizes nesting.
More predictive of human readability.

| Score | Posture |
|-------|---------|
| 0-15 | Acceptable |
| 16-25 | Review |
| > 25 | Refactor required |

**Source**: SonarSource white paper "Cognitive Complexity"
(2017).

### Test-to-Code Ratio

Ratio of test code lines to non-test code lines.

| Ratio | Interpretation |
|-------|----------------|
| < 0.5 | Under-tested; add tests before extending |
| 0.5-1.5 | Healthy range for most apps |
| 1.5-3.0 | Test-heavy; expected for libraries / safety-critical |
| > 3.0 | Possible test bloat; check for redundant cases |

**Measure**:

```bash
test_lines=$(find tests/ -name "*.py" | xargs wc -l | tail -1 | awk '{print $1}')
code_lines=$(find src/  -name "*.py" | xargs wc -l | tail -1 | awk '{print $1}')
echo "ratio = $(bc -l <<< "$test_lines / $code_lines")"
```

### Mutation Score

Percent of injected mutations killed by the test suite.
Catches the case where coverage is high but assertions are
weak.

| Score | Posture |
|-------|---------|
| >= 80% | Strong tests |
| 60-80% | Acceptable |
| < 60% | Tests assert too little |

**Measure**: `mutmut run` (Python), `cargo mutants` (Rust),
`pitest` (Java).

### Duplication

Percent of lines duplicated across the repo (token-level,
not byte).

| Percent | Posture |
|---------|---------|
| < 3% | Healthy |
| 3-7% | Investigate top duplicates |
| > 7% | Refactor required |

**Measure**: `jscpd .` or `pmd cpd`.

## Documentation Quality Metrics

### Coverage of Public API

Fraction of public symbols with at least one docstring or
doc comment.

| Coverage | Posture |
|----------|---------|
| >= 95% | Acceptable |
| 80-95% | Warn |
| < 80% | Block release |

**Measure**: `interrogate -v src/` (Python), `cargo doc
--no-deps` checked for missing-docs lint.

### Doc-to-Code Ratio

Lines of prose docs per 100 lines of code.

| Ratio | Interpretation |
|-------|----------------|
| < 5 | Under-documented |
| 5-25 | Healthy for most apps |
| 25-50 | Doc-heavy; expected for libraries |
| > 50 | Possible doc bloat; consolidate |

### Slop Indicators

Concrete prose markers that flag low-quality docs. Each
indicator has a per-1000-words target.

| Indicator | Target | How to count |
|-----------|--------|--------------|
| Em dash as connector | <= 2 / 1k words | `grep -o '\\-' file.md \| wc -l` |
| Banned words from project list | 0 hits | rg with banned-word list |
| Model identity leaks | 0 hits | rg for known leak patterns |
| Heading-restating sentences | < 5% of paras | manual sample |
| Participial tail-loading | < 10% of sentences | manual sample |

The full slop checklist is in
`Skill(scribe:slop-detector)`. Apply to any markdown longer
than 100 words before merge.

### Reading Level

Flesch reading ease for non-reference docs.

| Score | Audience |
|-------|----------|
| 60-70 | General developers |
| 50-60 | Senior engineers |
| 40-50 | Specialists |
| < 40 | Reference docs only |

**Measure**: `pip install textstat; python -c "import
textstat,sys; print(textstat.flesch_reading_ease(open(sys.argv[1]).read()))"
file.md`.

### Link Health

| Metric | Threshold |
|--------|-----------|
| Broken internal links | 0 |
| Broken external links | < 1% |
| Dangling Skill() refs | 0 |

**Measure**: `lychee --no-progress docs/`.

## Skill Quality Metrics

For Claude Code skill files specifically.

### SKILL.md Length

| Lines | Posture |
|-------|---------|
| < 500 | Acceptable |
| 500-1500 | Add modules with progressive loading |
| > 1500 | Modularize; keep hub under 500 |

**Source**: token economy guidance in
`Skill(abstract:modular-skills)`.

### Module Count and Depth

| Modules | Posture |
|---------|---------|
| 0 | Single-file skill; check length |
| 1-7 | Healthy hub-and-spoke |
| 8-15 | Acceptable for hub skills |
| > 15 | Consider splitting into multiple skills |

### Trigger Phrase Count

Number of activation phrases in the skill description.

| Count | Posture |
|-------|---------|
| >= 3 | Acceptable |
| 1-2 | Add more |
| 0 | Skill will not activate reliably |

### Frontmatter Fields Required

| Field | Required |
|-------|----------|
| name | yes |
| description | yes |
| tags | yes (>= 2) |
| version | yes (semver) |
| dependencies | yes (may be empty list) |
| estimated_tokens | yes |

Missing fields fail validation in
`Skill(abstract:skills-eval)`.

## Worked Example: Scoring a Skill File

A reviewer measures a fictional `tome:research` skill
against the metrics above.

```text
Code-side metrics (its scripts/ directory):
  line coverage:        82%   -> meets standard tier
  branch coverage:      71%   -> meets standard tier
  cyclomatic max:       14    -> review candidate (one func)
  test/code ratio:      0.7   -> healthy
  mutation score:       63%   -> acceptable, weak edge
  duplication:          2.1%  -> healthy

Doc-side metrics (its SKILL.md and modules):
  SKILL.md lines:       420   -> acceptable
  module count:         6     -> hub-and-spoke ok
  trigger phrases:      4     -> ok
  em dashes / 1k words: 1.2   -> within target
  banned words:         0     -> clean
  Flesch:               55    -> senior engineer
  broken links:         0     -> clean

Aggregate verdict (using weighted_sum from
multi-metric-evaluation-methodology.md):
  weights: {coverage: 0.3, complexity: 0.2, doc: 0.3,
            slop: 0.2}
  score (1-5): (4 * 0.3) + (3 * 0.2) + (4 * 0.3) +
               (5 * 0.2) = 4.0
  Action: ship; track the one high-complexity function
  and the mutation gap.
```

## Calibration

Metrics drift. Re-measure quarterly.

1. Compute the distribution of each metric across the
   current population.
2. Set thresholds at the 25th / 50th / 75th percentile of
   the current healthy-set, not at vendor defaults.
3. Track the trend: if median complexity rose by 20% in a
   quarter, the threshold may already be too lenient.

## Pitfalls

**Coverage as a single number.** 90% line coverage with 0%
branch coverage hides every conditional. Track both.

**Complexity averaged over a file.** A file with one
80-cyclo function and ten 2-cyclo functions has an average
of 9 and looks fine. Track the maximum, not the mean.

**Ratios without absolute floors.** A 1.5 test-to-code
ratio on a 200-line codebase says nothing. Pair every ratio
with an absolute minimum (for example: at least 50 test
cases for any ratio claim to count).

**Doc-coverage gaming.** Single-line docstrings on every
public symbol pass the gate and teach nothing. Spot-check
samples for content, not just presence.

**Slop indicators applied to generated content.** Stack
traces and machine-generated tables will trip prose
metrics. Exclude generated paths from the slop scan.

**Thresholds copied without context.** A safety-critical
control system needs 100% MC/DC coverage; a marketing site
does not. Tier your thresholds by criticality before
applying.

## Cross-Reference

See `modules/scoring-patterns.md` for combining these
metrics into a calibrated rubric and
`modules/multi-metric-evaluation-methodology.md` for
aggregation rules.
