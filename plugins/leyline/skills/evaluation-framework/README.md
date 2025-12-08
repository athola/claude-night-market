# Evaluation Framework

A generic weighted scoring and threshold-based decision framework for evaluating artifacts against configurable criteria.

## Purpose

This skill provides reusable evaluation patterns that can be customized for different domains. It abstracts the common pattern of:

1. Define criteria with weights
2. Score against criteria
3. Calculate weighted total
4. Apply decision thresholds
5. Take appropriate actions

## Structure

```
evaluation-framework/
├── SKILL.md                          # Hub - core patterns (149 lines)
└── modules/
    ├── scoring-patterns.md           # Detailed scoring methodology
    └── decision-thresholds.md        # Threshold design patterns
```

## Usage

### As a Dependency

```yaml
# In your skill's frontmatter
dependencies: [leyline:evaluation-framework]
```

### Common Use Cases

- **Quality Gates**: Code review decisions, PR approval, release readiness
- **Content Evaluation**: Document quality, knowledge intake, skill assessment
- **Resource Allocation**: Backlog prioritization, investment decisions, triage

## Design Principles

- **Generic and Reusable**: Works across different evaluation domains
- **Configurable**: Users define their own criteria and weights
- **Consistent**: Same methodology applies everywhere
- **Actionable**: Clear mapping from scores to decisions

## Consumers

This framework is designed to be consumed by:

- `memory-palace/skills/knowledge-intake/modules/evaluation-rubric.md`
- `abstract/skills/skills-eval/modules/quality-metrics.md`
- Any plugin needing systematic evaluation with weighted criteria

## Token Budget

- SKILL.md: ~550 tokens (estimated)
- scoring-patterns.md: ~800 tokens (estimated)
- decision-thresholds.md: ~700 tokens (estimated)
- **Total**: ~2050 tokens (progressive loading)
