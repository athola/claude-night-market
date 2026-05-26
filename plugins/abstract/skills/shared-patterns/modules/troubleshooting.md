# Troubleshooting Shared-Pattern Integration

Diagnostic steps for the failures that show up when a skill or
hook tries to use a pattern from this skill. Covers import
paths, version mismatch, and missing exports.

## First Triage

Before debugging, capture three facts:

1. The exact error message and stack trace
2. The caller's plugin and version (`plugin.json` or
   `SKILL.md` frontmatter)
3. The shared-patterns version in use (`SKILL.md` `version:`)

If the caller and the shared-patterns skill disagree on the
plugin version, that is the bug. Skip the rest of this guide
and reinstall the plugin.

```bash
# Verify versions match
rg "^version:" plugins/abstract/skills/shared-patterns/SKILL.md
rg "^version:" plugins/abstract/openpackage.yml
```

## Symptom Index

| Symptom | Likely Cause | Section |
|---------|--------------|---------|
| `ModuleNotFoundError` | Import path wrong | Import paths |
| `AttributeError: module has no attribute X` | Renamed export | Missing exports |
| `ValidationError` raised but not caught | Two `ValidationError` classes | Version mismatch |
| Markdown link 404 | Module path moved | Reference paths |
| Function returns unexpected shape | Semantic change | Version mismatch |

## Import Paths

Patterns shipped as Python live under the parent plugin's
package. The canonical import is:

```python
from abstract.shared_patterns.validation import validate_required_fields
from abstract.shared_patterns.errors import ValidationError
```

Common mistakes:

- `from shared_patterns import ...` (missing plugin prefix)
- `from abstract.skills.shared_patterns import ...` (using the
  skill directory layout instead of the package layout)
- `import shared-patterns` (hyphens in Python identifiers)

If the import works locally but fails in CI, check that the
plugin is installed in editable mode (`uv pip install -e .`)
in the CI environment.

## Reference Paths

Markdown references use the skill module layout, not the Python
package layout. From a sibling skill in the same plugin:

```markdown
See ../shared-patterns/modules/error-handling.md for the
exception hierarchy.
```

From a different plugin:

```markdown
See plugins/abstract/skills/shared-patterns/modules/error-handling.md
```

A 404 after a recent edit usually means the file was renamed.
Check `git log --diff-filter=R --follow modules/<old-name>.md`
to find the rename.

## Version Mismatch

Two copies of the same exception class break `except` blocks:

```python
# In caller, imported at module load
from abstract.shared_patterns.errors import ValidationError

# Somewhere else (different version cached, vendored copy, etc)
class ValidationError(Exception): ...   # different class!

try:
    do_thing()
except ValidationError:                  # only catches one
    handle()
```

Check for duplicate definitions:

```bash
rg "class ValidationError" plugins/
```

A single canonical definition is in
`plugins/abstract/skills/shared-patterns/modules/error-handling.md`
(reference) and the corresponding Python module. Anything else
is a fork to remove.

## Missing Exports

If `AttributeError` appears after upgrading the plugin, the
export was renamed or removed. Cross-check against
`editing.md`'s "Change Classes" table:

1. Look up the symbol in the current `error-handling.md`,
   `validation-patterns.md`, etc.
2. If absent, search recent commits to the modules directory:
   `git log -p plugins/abstract/skills/shared-patterns/modules/`
3. Find the deprecation note or migration instruction in the
   commit message.
4. Update the caller per the documented migration.

If no migration note exists, the change was undocumented; file
an issue against the skill before working around it.

## Diagnostic Snippet

Drop this into a caller to print which version of a shared
symbol is in use:

```python
import inspect
from abstract.shared_patterns.errors import ValidationError

print("ValidationError defined at:",
      inspect.getfile(ValidationError))
print("ValidationError MRO:",
      [c.__name__ for c in ValidationError.__mro__])
```

If the file path is unexpected (e.g. a `.venv` cache, a
vendored copy), that is the source of the mismatch.

## Anti-Patterns

- **Catch-all suppression**: Wrapping the integration in
  `except Exception: pass` to silence the error. The bug
  reappears later in a worse place.
- **Pinning forever**: Pinning the plugin to an old version to
  avoid the migration. Locks the caller out of unrelated fixes.
- **Patching the shared pattern in place**: Editing
  `error-handling.md` in `plugins/abstract/...` from a caller
  plugin to make a test pass. Other callers see the change
  next time they update.

## Cross-Reference

See `editing.md` for the migration patterns referenced above
and `creation.md` for when a new pattern (rather than a fix)
is the right answer.
