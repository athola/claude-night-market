# Doc Verify

Validate documentation claims by testing commands and verifying paths.

## Usage

```bash
/doc-verify [target] [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `target` | File or directory to verify (default: README.md) |

## Options

| Option | Description |
|--------|-------------|
| `--category` | Verify only: commands, paths, examples, claims (default: all) |
| `--strict` | Fail on any BLOCKED items |
| `--timeout` | Max seconds per test (default: 30) |
| `--report` | Output report file path |

## Examples

```bash
# Verify README
/doc-verify README.md

# Verify all docs, commands only
/doc-verify docs/ --category commands

# Strict mode with report
/doc-verify --strict --report qa-report.md
```

## Verification Categories

### Commands

Tests every code block with executable commands:
- Installation commands
- CLI usage examples
- Script invocations

### Paths

Verifies every file/directory path mentioned:
- Config files
- Source directories
- Output locations

### Examples

Runs code examples to verify they work:
- Python snippets
- Shell scripts
- Configuration examples

### Claims

Validates factual statements:
- Counts (files, endpoints, patterns)
- Performance claims (when testable)
- Feature availability

## Output

```
## Doc Verify: README.md

Total: 15 items | Pass: 12 | Fail: 2 | Blocked: 1

### Failed
[E3] Command `npm install scribe` - Package not found
  Fix: Update to local installation

[E7] Path `.scribe/config.yaml` - Does not exist
  Fix: Add setup instructions

### Blocked
[E12] Claim "under 5ms" - Needs benchmark setup
```

## Evidence Format

Each check produces evidence:

```
[E1] Command: npm install scribe
Status: FAIL
Output: npm ERR! 404 Not Found
Recommendation: Update installation docs
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All items PASS |
| 1 | Some items FAIL |
| 2 | Error during verification |

## See Also

- `Agent(scribe:doc-verifier)` - Full verification agent
- `Skill(imbue:proof-of-work)` - Evidence methodology
- `/doc-polish` - Fix verified issues
