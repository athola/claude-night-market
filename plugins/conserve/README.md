# Conservation

Resource optimization and performance monitoring for Claude Code.

## Quick Start

```bash
# Scan for code bloat
/bloat-scan --level 2

# Remediate identified bloat (with approval)
/unbloat --from-scan report

# Check for AI-generated code issues
/ai-hygiene-audit

# Invoke context optimization skill
Skill(conserve:clear-context)
```

## Overview

Conservation manages token usage and session efficiency through resource monitoring and optimization. The plugin follows the Maximum Effective Context Window (MECW) principle, which maintains context pressure below 50% to preserve response quality. It identifies technical debt, eliminates response bloat, and provides strategies for codebase discovery to reduce the total token footprint.

## Workflow Optimization

MCP patterns process data at the source to avoid transmitting large datasets into the context window. Progressive loading fetches modules only when needed to keep the session footprint small. When context pressure exceeds 80%, the `clear-context` skill saves the session state and transitions to a fresh context window via subagent delegation.

## Commands

### `/bloat-scan`

Identifies dead code, duplication, and documentation bloat. Targeted analysis (level 2) can focus on specific areas, while detailed audits (level 3) generate a full report. It targets large files, code older than 6 months, unused dependencies, and duplicates.

### `/unbloat`

Executes remediation by deleting, refactoring, or consolidating code with user approval. It includes a dry-run mode for previewing changes and can use existing scan reports for execution.

### Safeguards

`/unbloat` creates backup branches and requires interactive approval for all modifications. It runs verification tests after changes and rolls back if failures occur. File operations use `git rm` and `git mv` to maintain project history.

### `/ai-hygiene-audit`

Detects AI-specific code quality issues such as tab-completion bloat (repeated similar blocks), "vibe coding" patterns (massive single commits), and happy-path-only tests. It identifies problematic live code that traditional bloat detection might miss.

## Agents

| Agent | Purpose | Tools | Model |
|-------|---------|-------|-------|
| `bloat-auditor` | Orchestrates bloat detection scans. | Bash, Grep, Glob, Read, Write | Sonnet |
| `unbloat-remediator` | Executes bloat remediation workflows. | Bash, Grep, Glob, Read, Write, Edit | Sonnet/Opus |
| `ai-hygiene-auditor` | Detects AI-generated code quality issues. | Bash, Grep, Glob, Read | Sonnet |
| `context-optimizer` | Assesses and optimizes MECW. | Read, Grep | Sonnet |
| `continuation-agent` | Continues work from session state checkpoints. | Read, Write, Edit, Bash, Glob, Grep | default |

## Skills

The `bloat-detector` skill uses three tiers of analysis, from heuristic-based checks to deep audits with full tooling. `clear-context` persists session state across context windows. `response-compression` eliminates filler words, hedging language, and hype words, saving between 150 and 350 tokens per response. `decisive-action` uses a reversibility/ambiguity matrix to determine when to proceed autonomously versus asking for clarification.

## Token-Conscious Workflows

### Discovery Strategy

Use a three-tier approach for efficient discovery. First, use the Language Server Protocol (LSP) for semantic queries to get symbol-aware results in approximately 50ms. If LSP is unavailable, use targeted file reads to maintain a focused context window. As a secondary strategy, use `ripgrep` via the `Grep` tool for text-based searches. This approach reduces token usage by approximately 90% compared to broad exploratory reading.

### STDOUT Verbosity Control

Verbose command output consumes context. Use quiet or silent flags for package managers (npm, pip) and test runners (pytest). Limit git logs and diffs using `--oneline` or `--stat`. For file listings and search results, use `head` to truncate output. If a command fails three times, stop to verify assumptions or consider a simpler approach instead of retrying further.

### Documentation Format

Agents read Markdown directly; they do not read HTML. Markdown has lower syntax overhead and is version-control friendly. HTML should only be generated for external documentation sites or web-based viewing.

## Hooks

### Setup Hook (Claude Code 2.1.10+)

Init tasks validate dependencies, create the `.claude/` session state directory, and persist the session state path. Maintenance tasks clean backups older than 7 days and rotate continuation audit logs. Run `--init` after cloning and `--maintenance` periodically.

### PermissionRequest Hook

Auto-approves safe patterns like read-only operations, search, and git status. Auto-denies dangerous patterns such as recursive deletes on home/root, privilege escalation (sudo), or pipe-to-shell commands.

## Thresholds

### Context Usage

Monitoring levels trigger actions based on context pressure: LOW (<40%), WARNING (40-50%), CRITICAL (50-80%), and EMERGENCY (80%+). At the EMERGENCY level, the `clear-context` skill saves state to `.claude/session-state.md` and either spawns a continuation agent via Task tool or guides graceful wrap-up if Task tool is unavailable.

### Context Measurement

Two methods are available depending on the use case:

| Method | Use Case | Accuracy | Speed |
|--------|----------|----------|-------|
| File size heuristic | Real-time hooks | Approximate (~800KB ≈ 100%) | Fast |
| CLI `/context` command | Headless/batch automation | Precise token breakdown | Slower |

For headless sessions, use `claude -p "/context" --verbose --output-format json` to get precise token breakdowns. See `/conserve:optimize-context` for full documentation.

## Requirements

Python 3.10+ and Claude Code.
