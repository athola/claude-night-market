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

Conservation optimizes resources by adhering to the **Maximum Effective Context Window (MECW)** principle, which keeps context pressure under 50% to maintain response quality. It also uses **MCP Patterns** to process data at the source, preventing the transmission of large datasets, and employs **Progressive Loading** to fetch modules on demand, thereby reducing the session footprint.

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

`/unbloat` prevents data loss by creating backup branches and requiring interactive approval for modifications. The system runs verification tests after changes and rolls back automatically if failures occur. All file operations use `git rm` and `git mv` to preserve history.

### `/ai-hygiene-audit`

Detect AI-specific code quality issues that traditional bloat detection misses.

```bash
/ai-hygiene-audit                        # Full AI hygiene audit
/ai-hygiene-audit --focus duplication    # Tab-completion bloat
/ai-hygiene-audit --focus tests          # Happy-path-only detection
/ai-hygiene-audit --threshold 70         # CI integration with pass/fail
```

**Detects**: Vibe coding patterns, Tab-completion bloat, happy-path tests, hallucinated dependencies, documentation slop.

**Why It Exists**: AI coding has created qualitatively different bloat. 2024 was the first year copy/pasted lines exceeded refactored lines (GitClear). Traditional bloat detection finds dead code; AI hygiene detection finds *live but problematic* code.

## Agents

| Agent | Purpose | Tools | Model |
|-------|---------|-------|-------|
| `bloat-auditor` | Orchestrate bloat detection scans. | Bash, Grep, Glob, Read, Write | Sonnet |
| `unbloat-remediator` | Execute bloat remediation workflows. | Bash, Grep, Glob, Read, Write, Edit | Sonnet/Opus |
| `ai-hygiene-auditor` | Detect AI-generated code quality issues. | Bash, Grep, Glob, Read | Sonnet |
| `context-optimizer` | Assess and optimize MECW. | Read, Grep | Sonnet |
| `continuation-agent` | Continue work from session state checkpoint. | Read, Write, Edit, Bash, Glob, Grep, Task | default |

## Skills

| Skill | Purpose |
|-------|---------|
| `bloat-detector` | Progressive bloat detection with modular tiers. |
| `clear-context` | **Auto-clear workflow** with session state persistence. |
| `code-quality-principles` | KISS, YAGNI, SOLID guidance with multi-language examples. |
| `context-optimization` | MECW assessment and subagent coordination. |
| `cpu-gpu-performance` | Hardware resource tracking and selective testing. |
| `decisive-action` | Question threshold for autonomous workflow. |
| `mcp-code-execution` | MCP patterns for data pipelines. |
| `optimizing-large-skills` | Modularization of oversized skills. |
| `response-compression` | Eliminate response bloat (emojis, filler, hedging). |
| `token-conservation` | Token budget enforcement and quota tracking. |

### Bloat Detection

The `bloat-detector` skill supports `/bloat-scan`, `/unbloat`, and `/ai-hygiene-audit`.

**Detection Tiers:**
- **Tier 1**: Heuristic-based analysis.
- **Tier 2**: Static analysis integration (Vulture/Knip) + AI-generated bloat patterns.
- **Tier 3**: Deep audit with full tooling.

**AI-Specific Detection (New):**
- Tab-completion bloat (repeated similar blocks)
- Vibe coding signatures (massive single commits)
- Happy-path-only tests
- Hallucinated dependencies
- Documentation slop patterns

### Bloat Detection Outcomes

`bloat-detector` identifies technical debt and redundant code. This typically reduces context usage by 10-20%, lowering token costs and improving session efficiency.

### Response Compression

Eliminates response bloat including:
- Decorative emojis (status indicators preserved)
- Filler words ("just", "simply", "basically")
- Hedging language ("might", "could", "perhaps")
- Hype words ("powerful", "amazing", "robust")
- Conversational framing and unnecessary closings

Typical savings: 150-350 tokens per response.

### Code Quality Principles

Provides language-aware guidance on:
- **KISS**: Prefer obvious solutions over clever ones
- **YAGNI**: Don't implement features until needed
- **SOLID**: SRP, OCP, LSP, ISP, DIP with Python/TypeScript/Rust examples

Includes conflict resolution (e.g., KISS vs SOLID tradeoffs).

### Decisive Action

Decision matrix for when to ask clarifying questions vs proceed autonomously:

| Reversibility | Ambiguity | Action |
|---------------|-----------|--------|
| Reversible | Low | Proceed |
| Reversible | High | Proceed with preview |
| Irreversible | Low | Proceed with confirmation |
| Irreversible | High | Ask |

Reduces interaction rounds while preventing wrong assumptions.

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

## Hooks

### Setup Hook (Claude Code 2.1.10+)

One-time initialization and periodic maintenance tasks. Triggered via CLI flags:

```bash
# Initialize conserve (creates directories, validates dependencies)
claude --init

# Run maintenance (cleans old backups, rotates logs)
claude --maintenance
```

**Init tasks:**
- Validates jq dependency (warns if missing)
- Creates `.claude/` session state directory
- Generates `session-state.md` template for continuation workflows
- Persists `CONSERVE_SESSION_STATE_PATH` environment variable

**Maintenance tasks:**
- Cleans session state backups older than 7 days
- Rotates continuation audit logs (keeps last 500 lines)
- Validates hook dependencies

**Why use Setup vs SessionStart?** Setup hooks run only when explicitly invoked, avoiding overhead on every session. Use `--init` after cloning a repo, and `--maintenance` periodically for cleanup.

### PermissionRequest Hook

Auto-approve or auto-deny Bash commands based on pattern matching (Claude Code 2.0.54+).

**Safe patterns (auto-approved):**
- Read-only file operations (`ls`, `cat`, `head`, `tail`)
- Search operations (`grep`, `rg`, `find`)
- Git read operations (`git status`, `git log`, `git diff`)
- Help commands (`--help`, `-h`, `man`)

**Dangerous patterns (auto-denied):**
- Recursive deletes on root/home (`rm -rf /`, `rm -rf ~`)
- Privilege escalation (`sudo`)
- Pipe-to-shell patterns (`curl ... | bash`)
- Force push to main (`git push --force origin main`)

**Setup:**
```json
{
  "hooks": {
    "PermissionRequest": [{
      "command": "python plugins/conserve/hooks/permission_request.py"
    }]
  }
}
```

## Thresholds

### Context Usage (Three-Tier MECW Alerts)

| Level | Threshold | Action |
|-------|-----------|--------|
| LOW | < 40% | Continue normally |
| WARNING | 40-50% | Monitor, plan optimization |
| CRITICAL | 50-80% | Immediate optimization required |
| EMERGENCY | 80%+ | **Auto-clear workflow triggered** |

**Configuration:**
- `CONSERVE_EMERGENCY_THRESHOLD`: Override 80% default (e.g., `0.75` for 75%)
- `CONSERVE_SESSION_STATE_PATH`: Override `.claude/session-state.md` default

### Auto-Clear Workflow

At EMERGENCY level (80%+), the `clear-context` skill enables automatic continuation without manual `/clear`:

1. **Save session state** to `.claude/session-state.md`
2. **Spawn continuation agent** with fresh context
3. **Continuation agent reads state** and resumes work

This pattern uses subagent delegation to achieve effective "auto-clear" - subagents have their own fresh context windows.

**Invoke manually:** `Skill(conserve:clear-context)`

### Other Thresholds

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

## Rules Templates

The plugin provides `.claude/rules/` templates for project-level context injection. Rules are injected automatically every session (`alwaysApply: true`).

```bash
# Symlink conserve rules into your project
ln -s ~/.claude-plugins/conserve/rules/conserve.md .claude/rules/
```

**`rules/conserve.md` includes:**
- MECW thresholds and actions
- Command verbosity control table
- Discovery strategy (LSP → targeted reads → Grep)
- Retry/self-reflection guidance

## Related Documentation

- **[Agent Boundaries Guide](../../docs/guides/agent-boundaries.md)** - Understand which agents to use and how they relate
- **[LSP Native Support](../../docs/guides/lsp-native-support.md)** - LSP setup and troubleshooting
- **[MECW Principles](skills/context-optimization/modules/mecw-principles.md)** - Deep dive into Maximum Effective Context Window
- **[Rules Templates Guide](../../docs/guides/rules-templates.md)** - Plugin rules for project context

See `docs/` for MCP optimization patterns and architecture decisions.

## License

MIT
