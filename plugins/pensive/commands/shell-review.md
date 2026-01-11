# Shell Script Review Command

Audit shell scripts for correctness, safety, and portability.

## Usage

```bash
/shell-review [path/to/script.sh]
```

Without arguments, reviews all `.sh` files in `scripts/` and `.git/hooks/`.

## What It Does

1. **Context Mapping**: Find shell scripts and integration points
2. **Exit Code Audit**: Check pipeline exit code propagation
3. **Portability Check**: POSIX vs Bash compatibility
4. **Safety Patterns**: Quoting, set flags, temp files
5. **Evidence Logging**: Document findings

## Scope

- Exit code propagation in pipelines
- set -euo pipefail usage
- Variable quoting
- POSIX vs Bash compatibility
- Temporary file handling
- Directory change safety

## Key Anti-Patterns Detected

- `cmd | grep` in if conditions (exit code masked)
- Unquoted variables
- Missing set flags
- Bash-isms in `/bin/sh` scripts
- Unsafe temp file creation

## Output

- Exit code issues with fix patterns
- Portability warnings
- Safety recommendations
- Overall assessment
