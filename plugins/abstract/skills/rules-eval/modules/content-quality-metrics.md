# Content Quality Metrics

## Quality Criteria

### Actionability
Rules should provide clear, actionable guidance. Descriptions alone are insufficient.

```markdown
<!-- BAD: Just a description -->
This project uses TypeScript.

<!-- GOOD: Actionable guidance -->
Use strict TypeScript. Enable `noImplicitAny` and `strictNullChecks`.
Prefer interfaces over type aliases for object shapes.
```

### Conciseness
Each rule file should be focused and concise (< 500 tokens typical).

### Non-Conflicting
Rules across files should not contradict each other.

### Single Topic
Each rule file should address one focused topic.

## Scoring (25 points)

| Check | Points | Criteria |
|-------|--------|----------|
| Actionable content | 8 | Contains imperative guidance |
| Conciseness | 7 | Not overly verbose (< 500 tokens) |
| Focused topic | 5 | One topic per file |
| No conflicts | 5 | No contradictions with other rules |
