# doc-sync Configuration Specification

Config file: `.claude/doc-sync.yaml`

## Purpose

Keep generated reference documentation in sync with plugin source-of-truth
files (`plugin.json`). The parser reads mappings, resolves source globs,
extracts registered items, compares them against target markdown sections,
and reports (or fixes) discrepancies.

## Schema

```yaml
version: 1

mappings:
  - name: <string>            # unique mapping identifier
    source: <glob>            # glob pattern relative to repo root
    extract:
      - path: <string>        # JSON key to extract from each source
        strip_prefix: <str>   # prefix to remove from each value (optional)
        strip_suffix: <str>   # suffix to remove from each value (optional)
    targets:
      - path: <string>        # markdown file relative to repo root
        section: <string>     # heading text to locate the table in
        format: <string>      # row template with {name}, {plugin}, {type}

defaults:
  on_missing: warn | error | ignore   # item in source but not in target
  on_extra: warn | error | ignore     # item in target but not in source
  auto_fix: true | false              # whether --fix is allowed
```

## Field Reference

### Top-level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | int | yes | Schema version, currently `1` |
| `mappings` | list | yes | One or more sync mappings |
| `defaults` | object | no | Fallback behavior settings |

### mappings[]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Human-readable mapping ID |
| `source` | string | yes | Glob for source files (e.g. `plugins/*/.claude-plugin/plugin.json`) |
| `extract` | list | yes | Fields to pull from each matched source |
| `targets` | list | yes | Markdown files to validate against |

### extract[]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | yes | JSON key name in source file (e.g. `skills`, `commands`, `agents`) |
| `strip_prefix` | string | no | Prefix stripped from each value before comparison |
| `strip_suffix` | string | no | Suffix stripped from each value before comparison |

### targets[]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | yes | Path to the markdown target file |
| `section` | string | yes | Heading that contains the table. Use `{type}` as placeholder for the extract path name |
| `format` | string | yes | Table row template. Placeholders: `{name}`, `{plugin}`, `{type}`, `{description}` |

### defaults

| Field | Default | Description |
|-------|---------|-------------|
| `on_missing` | `warn` | Action when source item is absent from target |
| `on_extra` | `warn` | Action when target item is absent from source |
| `auto_fix` | `false` | Allow `--fix` flag to write missing entries |

## Example

```yaml
version: 1

mappings:
  - name: plugin-capabilities
    source: "plugins/*/.claude-plugin/plugin.json"
    extract:
      - path: "skills"
        strip_prefix: "./skills/"
      - path: "commands"
        strip_prefix: "./commands/"
        strip_suffix: ".md"
      - path: "agents"
        strip_prefix: "./agents/"
        strip_suffix: ".md"
    targets:
      - path: "book/src/reference/capabilities-reference.md"
        section: "### All {type}s"
        format: "| `{name}` | [{plugin}](../plugins/{plugin}.md) | {description} |"

defaults:
  on_missing: warn
  on_extra: warn
  auto_fix: false
```

## CLI Usage

```bash
# Check for discrepancies (default config path)
python scripts/parse-doc-sync.py

# Custom config path
python scripts/parse-doc-sync.py --config path/to/doc-sync.yaml

# Auto-fix missing entries
python scripts/parse-doc-sync.py --fix

# Strict mode (exit 1 on any discrepancy)
python scripts/parse-doc-sync.py --strict
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All targets in sync |
| 1 | Discrepancies found (or errors in strict mode) |
| 2 | Config parse error or missing source files |
