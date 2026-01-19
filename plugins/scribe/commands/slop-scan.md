# Slop Scan

Detect AI-generated content markers in documentation.

## Usage

```bash
/slop-scan [target] [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `target` | File or directory to scan (default: current directory) |

## Options

| Option | Description |
|--------|-------------|
| `--severity` | Minimum severity to report: low, medium, high (default: low) |
| `--format` | Output format: text, json, markdown (default: text) |
| `--fix` | Suggest fixes for each finding |
| `--type` | Content type: auto, technical, narrative, fiction (default: auto) |

## Examples

```bash
# Scan current directory
/slop-scan

# Scan specific file with fixes
/slop-scan README.md --fix

# Scan docs folder, high severity only
/slop-scan docs/ --severity high

# JSON output for CI
/slop-scan --format json
```

## Output

```
## Slop Scan: README.md

Score: 3.2/10 (Moderate)
Words: 1,245

### High Severity (3)
- Line 12: "delve into" -> "explore"
- Line 45: "comprehensive overview" -> "overview"
- Line 89: "In today's fast-paced world" -> [delete]

### Medium Severity (5)
- Line 23: "leverage" -> "use"
...

### Structural Issues
- Em dash density: 6/1000 (elevated)
- Bullet ratio: 48% (elevated)
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No issues or below threshold |
| 1 | Issues found above threshold |
| 2 | Error during scan |

## See Also

- `Skill(scribe:slop-detector)` - Full detection skill
- `/doc-polish` - Fix detected issues
