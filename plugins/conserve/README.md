# Conservation Plugin

Resource optimization and performance monitoring for Claude Code. Uses MCP patterns and the Maximum Effective Context Window (MECW) principle to reduce token usage.

## Quick Start

```bash
# Install as plugin
claude plugin install conserve

# Development setup
git clone https://github.com/athola/conservation
cd conservation
make deps
```

## Session Start Integration

Conservation skills load at session start via hooks. This optimizes performance, token usage, and context management for each session.

### Modes

Set the `CONSERVATION_MODE` environment variable:

| Mode | Command | Behavior |
|------|---------|----------|
| `normal` | `claude` | Standard conservation guidance. |
| `quick` | `CONSERVATION_MODE=quick claude` | Skip guidance for speed. |
| `deep` | `CONSERVATION_MODE=deep claude` | Use additional resources for analysis. |

## Core Principles

- **MECW (Maximum Effective Context Window)**: Maintain context pressure under 50% of the total window to prevent response quality degradation.
- **MCP Patterns**: Process data at the source using MCP tools instead of passing large datasets through conversation context.
- **Progressive Loading**: Load modules on demand to reduce initial context footprint.

## Commands

### `/bloat-scan` - Detect Codebase Bloat

Identify dead code, duplication, and documentation bloat.

```bash
/bloat-scan                              # Quick scan (Tier 1)
/bloat-scan --level 2                    # Targeted analysis
/bloat-scan --level 2 --focus code       # Focus on code bloat
/bloat-scan --level 3 --report audit.md  # Detailed audit
```

**Detection Targets:**
- Large files.
- Stale code (unchanged for 6+ months).
- Dead code (zero references).
- Duplicate documentation.
- Unused dependencies.

**Output:** Prioritized report with token savings and remediation steps.

### `/unbloat` - Safe Bloat Remediation

Execute deletions, refactorings, and consolidations with user approval and automatic backups.

```bash
/unbloat                                 # Scan and remediate
/unbloat --from-scan bloat-report.md     # Use existing scan results
/unbloat --auto-approve low              # Auto-approve low risk changes
/unbloat --dry-run                       # Preview changes
/unbloat --focus code                    # Focus on code cleanup
```

**Operational Safeguards:**
- **Backup branches**: Automatic timestamped backups before changes.
- **Interactive approval**: Review each change before execution.
- **Test verification**: Run tests after changes; rollback on failure.
- **Reversible operations**: Use `git rm` or `git mv` for easy recovery.

**Remediation Types:**
- **DELETE**: Remove dead code with high confidence.
- **REFACTOR**: Split large classes into focused modules.
- **CONSOLIDATE**: Merge duplicate documentation.
- **ARCHIVE**: Move stale files to an archive directory.

**Workflow Example:**
```bash
# 1. Scan for bloat
/bloat-scan --level 2 --report findings.md

# 2. Review findings.md to plan the approach.

# 3. Execute remediation
/unbloat --from-scan findings.md

# 4. Verify and commit
make test
git add -A
git commit -m "Unbloat: reduce codebase size"
```

## Agents

| Agent | Purpose | Tools | Model |
|-------|---------|-------|-------|
| `bloat-auditor` | Orchestrate bloat detection scans. | Bash, Grep, Glob, Read, Write | Sonnet |
| `unbloat-remediator` | Execute bloat remediation workflows. | Bash, Grep, Glob, Read, Write, Edit | Sonnet/Opus |
| `context-optimizer` | Assess and optimize MECW. | Read, Grep | Sonnet |

## Skills

| Skill | Purpose |
|-------|---------|
| `context-optimization` | MECW assessment and subagent coordination. |
| `token-conservation` | Token budget enforcement and quota tracking. |
| `cpu-gpu-performance` | Hardware resource tracking and selective testing. |
| `bloat-detector` | Progressive bloat detection. |
| `mcp-code-execution` | MCP patterns for data pipelines. |
| `optimizing-large-skills` | Modularization of oversized skills. |

### Bloat Detection

The `bloat-detector` skill supports `/bloat-scan` and `/unbloat`.

**Detection Tiers:**
- **Tier 1**: Heuristic-based analysis.
- **Tier 2**: Static analysis integration (Vulture/Knip).
- **Tier 3**: Deep audit with full tooling.

**Benefits:**
- Reduces context usage by 10-20% on average.
- Identifies technical debt.
- Improves codebase navigability.

## Thresholds

- **Context**: < 30% LOW | 30-50% MODERATE | > 50% CRITICAL.
- **Token Quota**: 5-hour rolling cap and weekly cap.
- **CPU/GPU**: Establish baseline before executing heavy tasks.

## Requirements

Python 3.10+, Claude Code.

## Development

```bash
make deps           # Install dependencies
make format         # Format code
make lint           # Run linting
make test           # Run validation
```

See `docs/` for MCP optimization patterns and architecture decisions.

## License

MIT
