# Unified Review Command

Run a comprehensive review using intelligent skill selection based on codebase analysis.

## Usage

```bash
# Auto-detect and run appropriate reviews
/full-review

# Focus on specific domains
/full-review api          # API surface review
/full-review architecture # Architecture review
/full-review bugs         # Bug hunting
/full-review tests        # Test suite review
/full-review rust         # Rust-specific review
/full-review math         # Mathematical review
/full-review makefile     # Makefile review
/full-review all          # Run all applicable
```

## Skill Detection

Automatically selects review skills based on:

1. **Language Detection**: File extensions and manifests
2. **File Patterns**: Makefiles, API definitions, test files
3. **Git Context**: Status and diffs
4. **Project Structure**: Architecture patterns and build systems

## Detection Matrix

| Pattern | Skills Triggered |
|---------|-----------------|
| `*.rs`, `Cargo.toml` | rust-review, bug-review, api-review |
| `openapi.yaml`, `routes/` | api-review, architecture-review |
| `test_*.py`, `*_test.go` | test-review, bug-review |
| `Makefile`, `*.mk` | makefile-review |
| Math algorithms | math-review, bug-review |
| ADRs, architecture docs | architecture-review |

## Execution Flow

1. **Context Analysis**: Analyze repository structure
2. **Skill Selection**: Choose based on detected patterns
3. **Parallel Execution**: Run selected skills concurrently
4. **Integrated Report**: Consolidate findings

## Output

- **Summary**: Overall assessment
- **Domain Findings**: Per-skill analysis
- **Integrated Issues**: Cross-domain patterns
- **Action Items**: Prioritized with owners
