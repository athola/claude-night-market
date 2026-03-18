---
area_name: plugins/abstract
ownership_globs:
  - "plugins/abstract/**"
tags:
  - meta-plugin
  - plugin-validation
  - skill-auditing
---

# plugins/abstract Area Guide

The meta plugin -- tools for developing and validating
the plugin ecosystem itself.

## Patterns

- Plugin validator checks structure against the
  openpackage.yml schema
- Skill auditor measures token efficiency and quality
- Hook authoring guides use a scope-limited pattern
- Tests use `uv run python -m pytest tests/ -v --tb=short`

## Pitfalls

- Skill files MUST have YAML frontmatter with name,
  description, and category
- Hook files need kebab-case naming
- Changes here affect all other plugins -- test broadly

## Testing

```bash
cd plugins/abstract && uv run python -m pytest tests/ -v --tb=short
uv run ruff check --fix src/ tests/ hooks/
```

## Review Focus

- Schema validation correctness
- Token budget compliance for skills
- Cross-plugin compatibility
