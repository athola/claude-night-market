# Skills Quality Scoring Rubric

Standard methodology for evaluating Claude Code skill quality across plugins.

## Scoring Dimensions

### Structure Compliance (0-100)

Evaluates YAML frontmatter completeness and consistency.

| Score | Criteria |
|-------|----------|
| 100 | Complete YAML with all relevant fields, no inconsistencies |
| 95 | All fields present, minor inconsistencies |
| 90 | Most fields present, some missing optional fields |
| 80 | Missing 1-2 key fields or inconsistencies |
| 70 | Multiple missing fields or structural issues |

### Content Quality (0-100)

Evaluates skill documentation completeness and clarity.

| Score | Criteria |
|-------|----------|
| 100 | Clear concept + workflow + examples + integration + outputs |
| 90 | Concept + workflow + most examples + some integration |
| 80 | Clear explanation + workflow + limited examples |
| 70 | Basic explanation + workflow but sparse details |
| 60 | Adequate but missing key sections |

### Token Efficiency (0-100)

Evaluates whether token allocation matches skill complexity.

| Score | Criteria |
|-------|----------|
| 100 | Optimal token use; well-balanced coverage |
| 90 | Good balance; some over/under-allocation |
| 75 | Noticeable inefficiency; could optimize |
| 60 | Significant mismatch between complexity and tokens |
| 40 | Severely under or over-allocated |

### Activation Reliability (0-100)

Evaluates metadata quality for skill discovery and selection.

| Score | Criteria |
|-------|----------|
| 100 | Clear naming + 5+ tags + explicit dependencies/tools |
| 90 | Clear naming + 4+ tags + most dependencies documented |
| 80 | Clear naming + 3+ tags + documented tools/deps |
| 70 | Naming clear but sparse metadata |
| 60 | Ambiguous or incomplete metadata |

## Overall Score Formula

```
Score = (Structure x 0.25) + (Content x 0.35) + (Tokens x 0.20) + (Activation x 0.20)
```

## Quality Thresholds

| Range | Rating | Action |
|-------|--------|--------|
| 85-100 | Excellent | No changes needed |
| 75-84 | Good | Minor improvements optional |
| 65-74 | Fair | Address medium-priority issues |
| 50-64 | Poor | Immediate fixes required |
| Below 50 | Critical | Skill may not function reliably |

## Usage

Run skill evaluations using the `abstract:skills-eval` skill or manually assess against this rubric during code review.
