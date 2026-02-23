# Frontmatter Validation

## Valid Frontmatter Fields

Claude Code rules support these frontmatter fields:

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `paths` | `list[string]` | No | Glob patterns for conditional loading |
| `description` | `string` | No | Brief description of rule purpose |

Rules without `paths` are unconditional (apply to all files).

## Common Errors

### YAML Syntax Errors
```yaml
# INVALID - unquoted glob starting with *
---
paths:
  - **/*.ts        # YAML parse error
---

# VALID - quoted glob
---
paths:
  - "**/*.ts"
---
```

### Wrong Field Names
```yaml
# INVALID - Cursor-specific fields
---
globs:             # Wrong! Use 'paths'
  - "*.ts"
alwaysApply: true  # Wrong! Cursor-only, not Claude Code
---
```

### Invalid Structure
```yaml
# INVALID - paths must be a list
---
paths: "**/*.ts"   # Should be a list
---

# VALID
---
paths:
  - "**/*.ts"
---
```

## Scoring (25 points)

| Check | Points | Criteria |
|-------|--------|----------|
| Valid YAML syntax | 10 | Parses without errors |
| Correct field names | 5 | No `globs`, `alwaysApply`, etc. |
| Proper quoting | 5 | Special chars quoted in globs |
| Valid structure | 5 | `paths` is list, types correct |
