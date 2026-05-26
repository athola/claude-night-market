# Editing an Existing Shared Pattern

How to change a shared pattern without breaking the skills that
depend on it. Covers versioning, backward compatibility, and
caller migration.

## Before You Edit

Find every caller first. A shared pattern in this skill is
referenced by relative path, by `Skill()` call, or by Python
import. Each surface needs its own search.

```bash
# Markdown references (relative path)
rg "shared-patterns/modules/<pattern-name>" plugins/

# Skill activation references
rg "Skill\(abstract:shared-patterns\)" plugins/

# Python imports (if the pattern ships code)
rg "from abstract.shared_patterns" plugins/
```

If the pattern has more than five callers, treat the edit as a
release: write down the contract change, the migration path,
and the deprecation timeline before touching code.

## Change Classes

| Class | Example | Backward Compat | Caller Action |
|-------|---------|-----------------|---------------|
| Additive | New optional parameter, new error subclass | Yes | None |
| Renaming | Rename function or field | No | Update call site |
| Semantic | Same signature, different behavior | No | Re-test |
| Removal | Delete function, drop field | No | Replace or pin |

Additive changes can ship without coordination. The other three
need a migration plan.

## Versioning

This skill follows the parent plugin's version. Bump the parent
`SKILL.md` `version:` field when a non-additive change ships.

```yaml
# plugins/abstract/skills/shared-patterns/SKILL.md
---
name: shared-patterns
version: 1.9.4   # bump on non-additive edits
---
```

For Python-shipped patterns, mirror the bump in
`plugins/abstract/pyproject.toml` and add a changelog entry.

## Backward Compatibility Tactics

### Deprecation Window

Keep the old surface working for one release while pointing
callers at the new one.

```python
import warnings

def validate_required_fields(data, required, fields=None):
    """Validate required fields in a dict.

    .. deprecated:: 1.9.4
        ``fields`` was renamed to ``required``. Pass ``required=``.
    """
    if fields is not None:
        warnings.warn(
            "validate_required_fields(fields=) is deprecated; "
            "use required= instead",
            DeprecationWarning,
            stacklevel=2,
        )
        required = fields
    return [f for f in required if f not in data or not data[f]]
```

### Subclass for New Behavior

Add a new class instead of mutating the existing one when the
contract changes.

```python
class ValidationError(AbstractError):
    """Original. Keep as-is."""

class StrictValidationError(ValidationError):
    """New variant that includes a field path."""
    def __init__(self, message, field_path):
        super().__init__(message)
        self.field_path = field_path
```

Existing `except ValidationError` blocks still catch the new
class. Callers who want the new field can match the subclass.

## Migration of Callers

For breaking changes, walk each caller in order:

1. Identify all callers (see "Before You Edit").
2. Update them in a single PR or a stack, smallest first.
3. Run the caller's test suite at each step.
4. Land the new pattern and the caller updates together so no
   intermediate commit references a missing surface.

If callers are in multiple plugins, coordinate via the parent
plugin's release notes rather than landing partial migrations.

## Anti-Patterns

- **Silent semantic change**: Same function name, same
  signature, different behavior. No warning, no version bump.
  Callers break in production.
- **Soft delete**: Removing a function but leaving the docs
  pointing at it. New callers waste time before discovering it
  is gone.
- **Forever deprecation**: Marking a function deprecated and
  never removing it. The deprecation loses meaning and callers
  ignore the warning.
- **Local fork to avoid the migration**: A caller copy-pastes
  the old version into its own module to dodge the rename. The
  drift compounds at the next change.

## Cross-Reference

See `creation.md` for adding a new pattern, and
`troubleshooting.md` for diagnosing failures after a change.
