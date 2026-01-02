# Conservation Plugin

Resource optimization and performance monitoring for Claude Code. Uses MCP patterns and the Maximum Effective Context Window (MECW) principle to reduce token usage and keep context pressure low.

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

Conservation skills are automatically loaded at session start via hooks. This optimizes performance, token usage, and context management from the beginning of every Claude Code session.

### Bypass Modes

Set the `CONSERVATION_MODE` environment variable to control behavior:

| Mode | Command | Behavior |
|------|---------|----------|
| `normal` | `claude` | Full conservation guidance (default) |
| `quick` | `CONSERVATION_MODE=quick claude` | Skip guidance for fast processing |
| `deep` | `CONSERVATION_MODE=deep claude` | Extended resources for thorough analysis |

## Key Concepts

**MECW (Maximum Effective Context Window)**: Keep context pressure under 50% of the total window. Beyond this threshold, response quality degrades. Conservation skills monitor and maintain this limit.

**MCP Patterns**: Instead of passing large datasets through conversation context, use MCP tools to process data at the source and return only results. This works well for tool chains that would otherwise consume thousands of tokens.

**Progressive Loading**: Skills load modules on demand rather than all at once, reducing the initial context footprint.

## Commands

### `/bloat-scan` - Detect Codebase Bloat

Identify dead code, duplication, and documentation bloat through progressive analysis.

```bash
/bloat-scan                              # Quick scan (Tier 1, 2-5 min)
/bloat-scan --level 2                    # Targeted analysis (10-20 min)
/bloat-scan --level 2 --focus code       # Focus on code bloat only
/bloat-scan --level 3 --report audit.md  # Deep audit (30-60 min)
```

**Detects:**
- Large files (God classes)
- Stale code (unchanged 6+ months)
- Dead code (0 references)
- Duplicate documentation
- Unused dependencies

**Output:** Prioritized report with confidence levels, token savings, and remediation steps.

### `/unbloat` - Safe Bloat Remediation

Execute safe deletions, refactorings, and consolidations with user approval and automatic backups.

```bash
/unbloat                                 # Integrated: scan + remediate
/unbloat --from-scan bloat-report.md     # Use existing scan results
/unbloat --auto-approve low              # Auto-approve LOW risk changes
/unbloat --dry-run                       # Preview changes only
/unbloat --focus code                    # Focus on code cleanup
```

**Safety Features:**
- **Backup branches**: Automatic timestamped backups before any changes
- **Interactive approval**: Review each change before execution
- **Test verification**: Runs tests after each change, auto-rollback on failure
- **Reversible operations**: Uses `git rm`/`git mv` for easy rollback

**Remediation Types:**
- **DELETE**: Remove dead code with high confidence (0 refs, stale, 90%+ confidence)
- **REFACTOR**: Split God classes into focused modules
- **CONSOLIDATE**: Merge duplicate documentation
- **ARCHIVE**: Move stale but valuable files to archive/

**Example Workflow:**
```bash
# 1. Scan for bloat
/bloat-scan --level 2 --report findings.md

# 2. Review findings, plan approach
# ... review findings.md ...

# 3. Execute safe remediation
/unbloat --from-scan findings.md

# 4. Verify and commit
make test
git add -A
git commit -m "Unbloat: reduce codebase by 14%"
```

## Agents

| Agent | Purpose | Tools | Model |
|-------|---------|-------|-------|
| `bloat-auditor` | Orchestrate bloat detection scans | Bash, Grep, Glob, Read, Write | Sonnet |
| `unbloat-remediator` | Safe bloat remediation workflows | Bash, Grep, Glob, Read, Write, Edit | Sonnet → Opus |
| `context-optimizer` | MECW assessment and optimization | Read, Grep | Sonnet |

**Escalation:** Complex refactorings (>500 lines, core infrastructure) escalate to Opus.

## Skills

| Skill | Purpose |
|-------|---------|
| `context-optimization` | MECW assessment and subagent coordination |
| `token-conservation` | Token budget enforcement and quota tracking |
| `cpu-gpu-performance` | Hardware resource tracking and selective testing |
| `bloat-detector` | Progressive bloat detection (dead code, duplication, docs) |
| `mcp-code-execution` | MCP patterns for data pipelines |
| `optimizing-large-skills` | Breaking down oversized skills |

### Bloat Detection

The `bloat-detector` skill provides the intelligence behind `/bloat-scan` and `/unbloat`:

**Detection Tiers:**
- **Tier 1**: Heuristic-based (no tools required, 2-5 min)
- **Tier 2**: Static analysis integration (Vulture/Knip, 10-20 min)
- **Tier 3**: Deep audit (full tooling, 30-60 min)

**Benefits:**
- Reduces context usage by 10-20% on average
- Identifies technical debt hotspots
- Improves codebase navigability
- See `/bloat-scan` and `/unbloat` commands above for usage

## Thresholds

- **Context**: < 30% LOW | 30-50% MODERATE | > 50% CRITICAL
- **Token Quota**: 5-hour rolling cap + weekly cap
- **CPU/GPU**: Establish baseline before heavy tasks

## Requirements

Python 3.10+, Claude Code

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
