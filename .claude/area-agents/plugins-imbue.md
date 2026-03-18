---
area_name: plugins/imbue
ownership_globs:
  - "plugins/imbue/**"
tags:
  - review-workflow
  - evidence-management
  - proof-of-work
  - quality-gates
---

# plugins/imbue Area Guide

Review workflow and evidence management -- ensures
all claims are backed by verifiable evidence.

## Patterns

- Proof-of-work requires [E1], [E2] evidence tags
  with actual command outputs
- Output contracts define required sections, minimum
  evidence count, and strictness levels
- Iron Law: no implementation without a failing test
- Structured output templates for consistent deliverables
- Scope guard evaluates worthiness before implementation
- Diff analysis for git-based change review

## Pitfalls

- Coverage threshold is strict (85% fail-under)
- Evidence count of 0 is unconditionally rejected
  regardless of strictness level
- Contract validator checks sections case-insensitively
  and treats underscores as spaces
- When adding to pyproject.toml lint config, test files
  already ignore D102, D103, D401

## Testing

```bash
cd plugins/imbue && uv run python -m pytest tests/ -v --tb=short
```

## Review Focus

- Evidence tag completeness and accuracy
- Output contract compliance
- Validator correctness (PASS/FAIL edge cases)
- Integration with other plugins' dispatch patterns
