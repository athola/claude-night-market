---
name: fallback
description: Output normalization for git diff fallback path
parent_skill: leyline:sem-integration
estimated_tokens: 250
---

# Fallback Output Normalization

When sem is unavailable, produce entity-like output from
standard git commands.

## Entity Schema

Both sem and fallback paths produce entries with:

```json
{
  "name": "entity_or_filename",
  "kind": "function|class|file",
  "change_type": "added|modified|deleted|renamed",
  "file": "path/to/file.py"
}
```

sem populates `kind` with function/class/method.
Fallback uses `file` as the kind since git diff
operates at file level.

## Fallback Commands

```bash
# Collect changes by type
added=$(git diff --name-only --diff-filter=A <baseline>)
modified=$(git diff --name-only --diff-filter=M <baseline>)
deleted=$(git diff --name-only --diff-filter=D <baseline>)
renamed=$(git diff --name-only --diff-filter=R <baseline>)
```

## Entity Extraction from Diff Hunks

For richer fallback (optional), parse diff hunks for
function/class definitions:

```bash
# Extract added functions from diff
git diff <baseline> | grep '^+def \|^+class ' | \
  sed 's/^+//' | sed 's/(.*//'
```

This gives function-level granularity without sem,
though it misses renames and cross-file dependencies.

## Impact Fallback

When `sem impact` is unavailable, trace callers with rg:

```bash
# For each changed file, find importers
git diff --name-only HEAD | while read f; do
  module=$(basename "$f" .py)
  if command -v rg &>/dev/null; then
    rg -l "import.*$module|from.*$module" --type py .
  else
    grep -rl "import.*$module\|from.*$module" \
      --include="*.py" .
  fi
done | sort -u
```
