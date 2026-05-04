# Advanced Pattern Composition

How to combine multiple shared patterns in a single skill or hook
without duplication, and how to choose between patterns when
several look applicable.

## Multi-Pattern Integration

Most non-trivial skills use two or more patterns from this skill
in combination. The composition order matters: validation runs
before workflow execution, error handling wraps both, and tests
exercise the composed surface.

### Standard Composition Order

```python
# 1. Validate input first (validation-patterns)
result = validate_required_fields(data, ["name", "description"])
if result:
    raise ValidationError(
        f"Missing fields: {result}", code="E001"
    )

# 2. Run workflow logic (workflow-patterns)
output = process_with_checklist(data)

# 3. Wrap the whole thing in fail-safe handling (error-handling)
try:
    write_output(output)
except StructureError as exc:
    logger.error("Write failed", extra={"code": "E003"})
    return fail_safe_result(data, exc)
```

### Cross-Module References

Each module can reference siblings by relative path:

| From | To | Relative Path |
|------|----|----|
| `creation.md` | `validation-patterns.md` | `./validation-patterns.md` |
| `editing.md` | `error-handling.md` | `./error-handling.md` |
| `troubleshooting.md` | `workflow-patterns.md` | `./workflow-patterns.md` |

Keep references one-directional where possible. Cycles between
modules make the skill harder to load progressively.

## Pattern Selection Heuristics

When two patterns overlap, pick the one whose primary axis matches
your failure mode.

| Failure Mode | Primary Axis | Pattern |
|--------------|--------------|---------|
| Bad input shape | data | validation-patterns |
| Operation fails partway | control flow | error-handling |
| Multi-step process needs ordering | workflow | workflow-patterns |
| Need to verify behavior | observation | testing-templates |

If two axes apply, compose them rather than picking one. A skill
that needs both validated input and a recovery path uses
`validate_required_fields()` (from validation-patterns) inside a
`try` block that catches `ValidationError` (from error-handling).

## When to Compose vs Inline

Compose a shared pattern when:

- The same logic appears in 2+ skills already
- The pattern has a stable public shape (function signature,
  exception class, frontmatter field set)
- A new caller can use it without editing the source

Inline a one-off variant when:

- The skill needs a tweak that no other caller needs
- Forcing the change upstream would break existing callers
- The variant is small enough that inlining is cheaper than
  documenting the divergence

## Anti-Patterns

- **Pattern stacking without need**: Pulling in all four pattern
  modules because "we might use them later". Each unused import
  is dead context.
- **Cyclic module references**: Module A points to B, B points
  back to A. Progressive loaders cannot order the load.
- **Silent overrides**: Redefining `ValidationError` locally to
  add a field instead of subclassing the one in
  `error-handling.md`. Callers downstream see two unrelated
  exception types with the same name.
- **Pattern as decoration**: Wrapping straight-line code in
  `try/except ValidationError` when the code never raises
  `ValidationError`. Adds noise without catching anything.

## Cross-Reference

See `creation.md` for extracting a new shared pattern from a
recurring need, and `editing.md` for changing one safely.
