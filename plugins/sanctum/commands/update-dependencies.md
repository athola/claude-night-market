---
name: update-dependencies
description: Scan and update dependencies across all ecosystems with conflict detection
usage: /update-dependencies [--dry-run] [--ecosystem python|rust|javascript|go]

# Claude Code 2.1.0+ lifecycle hooks
hooks:
  PreToolUse:
    - matcher: "Task"
      command: |
        # Log command invocation with user context
        echo "[cmd:update-dependencies] ⚠️  SECURITY-CRITICAL: Dependency update initiated at $(date) | User: ${USER:-unknown}" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/command-audit.log
        if echo "$CLAUDE_TOOL_INPUT" | grep -q "dependency-updater"; then
          echo "[cmd:update-dependencies] Spawning dependency-updater agent" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/command-audit.log
        fi
        # Track dry-run vs actual execution
        if echo "$CLAUDE_TOOL_INPUT" | grep -q "dry-run"; then
          echo "[cmd:update-dependencies] Mode: DRY-RUN (safe)" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/command-audit.log
        else
          echo "[cmd:update-dependencies] Mode: LIVE EXECUTION (modifying dependencies)" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/command-audit.log
        fi
      once: true
  Stop:
    - command: |
        echo "[cmd:update-dependencies] === Command completed at $(date) ===" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/command-audit.log
        # Export to security audit dashboard
---

# Update Dependencies

Scan the repository for outdated dependencies across Python, Rust, JavaScript, and Go ecosystems. Detect conflicts, find compatible versions, and apply updates with code migration support.

> **Note**: This command handles UPDATING existing dependencies. Before ADDING new dependencies, use the dependency-updater agent's verification checklist to validate version, security, and compatibility.

## Usage

```bash
# Check all ecosystems
/update-dependencies

# Preview without making changes
/update-dependencies --dry-run

# Limit to specific ecosystem
/update-dependencies --ecosystem python
```

## Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Show available updates without applying changes |
| `--ecosystem <name>` | Limit to: python, rust, javascript, or go |

## What This Command Does

Spawns a `dependency-updater` agent that:

1. **Discovers** all dependency files in the monorepo
   - pyproject.toml (Python)
   - Cargo.toml (Rust)
   - package.json (JavaScript)
   - go.mod (Go)

2. **Checks** each ecosystem for available updates using native tooling

3. **Analyzes** version conflicts and breaking changes
   - Identifies incompatible version combinations
   - Attempts to find compatible version sets
   - Flags major version bumps requiring review

4. **Presents** summary table for approval
   - Package name, current version, latest version
   - Status: safe, major bump, needs code changes, conflict

5. **Applies** approved updates
   - Updates dependency files
   - Regenerates lock files
   - Runs builds/tests to verify

6. **Migrates** code for breaking changes
   - Identifies deprecated API usage
   - Shows proposed fixes as diff
   - Applies after approval

7. **Reviews** final diff before committing

## Example Output

```
Scanning for dependency files...
Found 12 pyproject.toml, 0 Cargo.toml, 1 package.json, 0 go.mod

Python Updates Available:
| Package   | Current | Latest | Status    |
|-----------|---------|--------|-----------|
| requests  | 2.28.0  | 2.31.0 | [OK] safe    |
| django    | 4.1     | 5.0    | [WARN] major   |
| pydantic  | 1.10    | 2.5    | [FIX] code   |

JavaScript Updates Available:
| Package   | Current | Latest | Status    |
|-----------|---------|--------|-----------|
| typescript| 5.2.0   | 5.3.0  | [OK] safe    |

Apply updates? [y/N]
```

## Requirements

For full functionality, these tools should be installed:

- **Python**: `uv` or `pip`
- **Rust**: `cargo-outdated` (`cargo install cargo-outdated`)
- **JavaScript**: `npm` or `pnpm`
- **Go**: `go` toolchain

Missing tools are detected and skipped with a warning.

## See Also

- Agent: `sanctum:dependency-updater`
