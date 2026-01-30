# conserve

Resource optimization and performance monitoring for context window management.

## Overview

Conserve helps you work efficiently within Claude's context limits. It automatically loads optimization guidance at session start and provides tools for monitoring and reducing context usage.

## Installation

```bash
/plugin install conserve@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `context-optimization` | MECW principles and 50% context rule | When context usage > 30% |
| `token-conservation` | Token usage strategies and quota tracking | Session start, before heavy loads |
| `cpu-gpu-performance` | Resource monitoring and selective testing | Before builds, tests, or training |
| `mcp-code-execution` | MCP patterns for data pipelines | Processing data outside context |
| `optimizing-large-skills` | Large skill optimization | Breaking down oversized skills |
| `bloat-detector` | Detect bloated documentation, dead code, dead wrappers | During documentation reviews, code cleanup |
| `clear-context` | Context window management strategies | When approaching context limits |

## Commands

| Command | Description |
|---------|-------------|
| `/bloat-scan` | Detect code bloat, dead code, and dead wrapper scripts |
| `/unbloat` | Remove detected bloat with progressive analysis |
| `/optimize-context` | Analyze and optimize context window usage |
| `/analyze-growth` | Predict context budget impact of skill growth |

## Agents

| Agent | Description |
|-------|-------------|
| `context-optimizer` | Autonomous context optimization and MECW compliance |

## Hooks

| Hook | Type | Description |
|------|------|-------------|
| `session-start.sh` | SessionStart | Loads conservation guidance at startup |

## Usage Examples

### Context Optimization

```bash
/optimize-context

# Analyzes:
# - Current context usage
# - Token distribution
# - Compression opportunities
# - MECW compliance
```

### Growth Analysis

```bash
/analyze-growth

# Predicts:
# - Skill growth patterns
# - Context budget impact
# - Optimization priorities
```

### Manual Skill Invocation

```bash
Skill(conservation:context-optimization)

# Provides:
# - MECW principles
# - 50% context rule
# - Compression strategies
# - Eviction priorities
```

## Bypass Modes

Control conservation behavior via environment variables:

| Mode | Command | Behavior |
|------|---------|----------|
| Normal | `claude` | Full conservation guidance |
| Quick | `CONSERVATION_MODE=quick claude` | Skip guidance for fast processing |
| Deep | `CONSERVATION_MODE=deep claude` | Extended resource allowance |

### Examples

```bash
# Quick mode for simple tasks
CONSERVATION_MODE=quick claude

# Deep mode for complex analysis
CONSERVATION_MODE=deep claude
```

## Key Thresholds

### Context Usage

| Level | Usage | Action |
|-------|-------|--------|
| LOW | < 30% | Normal operation |
| MODERATE | 30-50% | Consider optimization |
| CRITICAL | > 50% | Optimize immediately |

### Token Quotas

- **5-hour rolling cap**: Prevents burst usage
- **Weekly cap**: validates sustainable usage
- **Check status**: Use `/status` to see current usage

## MECW Principles

Minimum Effective Context Window strategies:

1. **Summarize Early**: Compress large outputs before they accumulate
2. **Load on Demand**: Fetch file contents only when needed
3. **Evict Stale**: Remove information no longer relevant
4. **Prioritize Recent**: Weight recent context higher than old

## Optimization Strategies

### For Large Files

```bash
# Don't load entire file
# Instead, use targeted reads
Read file.py --offset 100 --limit 50
```

### For Search Results

```bash
# Limit search output
Grep --head_limit 20
```

### For Git Operations

```bash
# Use stats instead of full diffs
git diff --stat
git log --oneline -10
```

## CPU/GPU Performance

The `cpu-gpu-performance` skill monitors resource usage:

```bash
Skill(conservation:cpu-gpu-performance)

# Provides:
# - Baseline establishment
# - Resource monitoring
# - Selective test execution
# - Build optimization
```

## MCP Code Execution

For processing data too large for context:

```bash
Skill(conservation:mcp-code-execution)

# Patterns for:
# - External data processing
# - Pipeline optimization
# - Result summarization
```

## Superpowers Integration

| Command | Enhancement |
|---------|-------------|
| `/optimize-context` | Uses `condition-based-waiting` for smart optimization |

## Related Plugins

- **leyline**: Provides MECW pattern implementations
- **abstract**: Uses conservation for skill optimization
- **conjure**: Delegates to external services when context limited
