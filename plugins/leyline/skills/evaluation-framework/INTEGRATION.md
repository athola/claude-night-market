# Integration Guide

How to integrate the evaluation-framework skill into your plugin.

## For memory-palace (Knowledge Intake)

The memory-palace evaluation rubric can now depend on this shared framework:

```yaml
# In knowledge-intake/modules/evaluation-rubric.md
---
name: evaluation-rubric
dependencies: [leyline:evaluation-framework]
---

# Knowledge Evaluation Rubric

Based on the [evaluation-framework](leyline:evaluation-framework) with domain-specific criteria for knowledge intake.

## Criteria (following evaluation-framework pattern)

### 1. Novelty (25%)
See [scoring-patterns](leyline:evaluation-framework/modules/scoring-patterns.md) for methodology.

[Rest of domain-specific details...]
```

## For abstract (Quality Metrics)

The abstract quality-metrics module can reference this framework:

```yaml
# In skills-eval/modules/quality-metrics.md
---
name: quality-metrics
dependencies: [leyline:evaluation-framework]
---

# Quality Metrics Framework

Based on [evaluation-framework](leyline:evaluation-framework) for skill quality assessment.

## Scoring Categories (following evaluation-framework pattern)

### Structure Compliance (0-100)
Uses weighted scoring from [evaluation-framework](leyline:evaluation-framework).

[Rest of domain-specific details...]
```

## Benefits of Integration

### Reduced Duplication
- Common scoring methodology in one place
- Shared threshold patterns
- Single source of truth for evaluation concepts

### Consistency
- Same terminology across plugins
- Consistent scoring scales
- Unified decision-making patterns

### Maintainability
- Update evaluation patterns once
- All consumers benefit from improvements
- Clear dependency chain

## Migration Path

1. **Add Dependency**: Update frontmatter to include `leyline:evaluation-framework`
2. **Reference Core Patterns**: Link to framework for common concepts
3. **Focus on Domain**: Keep only domain-specific details in your skill
4. **Remove Duplication**: Delete explanations now in framework

## Example: Before and After

### Before (Duplicated)

```markdown
# My Evaluation

## Weighted Scoring

We use a weighted scoring system where each criterion has a weight...
[300 lines of generic explanation]

## Domain-Specific Criteria
[50 lines of actual domain logic]
```

### After (DRY with Framework)

```markdown
# My Evaluation

Uses [evaluation-framework](leyline:evaluation-framework) for weighted scoring.

## Domain-Specific Criteria
[50 lines of actual domain logic with references to framework patterns]
```

**Result**: 350 lines → 60 lines, clearer focus on domain logic.
