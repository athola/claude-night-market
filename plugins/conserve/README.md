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

Conservation skills load automatically via hooks. This optimizes performance, token usage, and context management for each session.

### Modes

Set the `CONSERVATION_MODE` environment variable:

| Mode | Command | Behavior |
|------|---------|----------|
| `normal` | `claude` | Standard conservation guidance. |
| `quick` | `CONSERVATION_MODE=quick claude` | Skip guidance for speed. |
| `deep` | `CONSERVATION_MODE=deep claude` | Use additional resources for analysis. |

## Core Principles

The Conservation plugin is built on three primary principles designed to optimize resource usage. The Maximum Effective Context Window (MECW) principle aims to keep context pressure under 50% to maintain high response quality. We also utilize MCP patterns, which focus on processing data at the source to prevent the transmission of large datasets through the context window. Finally, progressive loading ensures that modules are only loaded on demand, further reducing the overall footprint of each session.

## Commands

### `/bloat-scan`

Identify dead code, duplication, and documentation bloat.

```bash
/bloat-scan                              # Quick scan
/bloat-scan --level 2                    # Targeted analysis
/bloat-scan --level 2 --focus code       # Focus on code
/bloat-scan --level 3 --report audit.md  # Detailed audit
```

**Targets**: Large files, stale code (6+ months), dead code, duplicates, unused deps.

### `/unbloat`

Safely delete, refactor, and consolidate code with user approval.

```bash
/unbloat                                 # Scan and remediate
/unbloat --from-scan report.md           # Use existing scan
/unbloat --auto-approve low              # Auto-approve low risk
/unbloat --dry-run                       # Preview changes
```

### Safeguards

To prevent accidental data loss, the `/unbloat` command includes several safeguards. It automatically creates backup branches before making any changes and requires interactive user approval for each modification. After changes are applied, the system runs verification tests and can perform an automatic rollback if any failures are detected. All deletions and moves are handled through `git rm` and `git mv` to maintain a clear history.

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

### Bloat Detection Outcomes

The `bloat-detector` skill identifies technical debt and improves codebase navigability by detecting redundant or stale code. On average, this process reduces context usage by 10% to 20%, resulting in more efficient Claude sessions and lower token costs.

## Token-Conscious Workflows

### Discovery Strategy: LSP, Targeted Reads, and Secondary Search

For efficient discovery, we recommend a three-tier approach. First, utilize the Language Server Protocol (LSP) for semantic queries if enabled, as it provides symbol-aware results in approximately 50ms. If the LSP is unavailable or experimental, use targeted file reads based on initial findings to maintain a focused context window. As a secondary strategy, employ `ripgrep` via the `Grep` tool for reliable, text-based searches across all file types. This methodology typically reduces token usage by approximately 90% compared to broad, exploratory file reading.

### STDOUT Verbosity Control

**Problem**: Verbose command output consumes context unnecessarily.

**Solutions**:

| Command Type | Avoid | Use Instead |
|-------------|---------|---------------|
| Package install | `npm install` | `npm install --silent` or `npm install --quiet` |
| Python install | `pip install package` | `pip install --quiet package` |
| Git logs | `git log` | `git log --oneline -10` |
| Git diffs | `git diff` | `git diff --stat` (or `-U1` for minimal context) |
| File listing | `ls -la` | `ls -1 \| head -20` |
| Search results | `find .` | `find . -name "*.py" \| head -10` |
| Docker builds | `docker build .` | `docker build --quiet .` |
| Test runs | `pytest` | `pytest --quiet` or `pytest -q` |

**Retries & Self-Reflection**: If a command fails repeatedly (3+ attempts), pause to:
1. Check if there's a simpler approach
2. Verify assumptions about the codebase
3. Consider token cost of continued retries vs. asking for clarification

### Documentation Format (Markdown vs. HTML)

**Agent Consumption**: Agents read **Markdown** directly, NOT HTML.

**Why Markdown**:
- Minimal syntax overhead (lower token count)
- Directly parseable by Claude
- Version control friendly
- Human-readable in raw form

**HTML** is only generated for:
- External documentation sites (via `.github/workflows/docs.yml`)
- Web-based viewing (e.g., GitHub Pages)

**Trade-off**: Markdown is slightly more verbose than structured data (JSON/YAML), but offers better navigability for humans while remaining agent-friendly.

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

## Related Documentation

- **[Agent Boundaries Guide](../../docs/guides/agent-boundaries.md)** - Understand which agents to use and how they relate
- **[LSP Native Support](../../docs/guides/lsp-native-support.md)** - LSP setup and troubleshooting
- **[MECW Principles](skills/context-optimization/modules/mecw-principles.md)** - Deep dive into Maximum Effective Context Window

See `docs/` for MCP optimization patterns and architecture decisions.

## License

MIT
