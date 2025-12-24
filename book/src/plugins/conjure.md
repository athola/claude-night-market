# conjure

Delegation to external LLM services for long-context or bulk tasks.

## Overview

Conjure provides a framework for delegating tasks to external LLM services (Gemini, Qwen) when Claude's context window is insufficient or when specialized models are better suited.

## Installation

```bash
/plugin install conjure@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `delegation-core` | Framework for delegation decisions | Assessing if tasks should be offloaded |
| `gemini-delegation` | Gemini CLI integration | Processing massive context windows |
| `qwen-delegation` | Qwen MCP integration | Tasks requiring specific privacy needs |

## Commands (Makefile)

| Command | Description | Example |
|---------|-------------|---------|
| `make delegate-auto` | Auto-select best service | `make delegate-auto PROMPT="Summarize" FILES="src/"` |
| `make quota-status` | Show current quota usage | `make quota-status` |
| `make usage-report` | Summarize token usage and costs | `make usage-report` |

## Hooks

| Hook | Type | Description |
|------|------|-------------|
| `bridge.on_tool_start` | PreToolUse | Suggests delegation when files exceed thresholds |
| `bridge.after_tool_use` | PostToolUse | Suggests delegation if output is truncated |

## Usage Examples

### Auto-Delegation

```bash
make delegate-auto PROMPT="Summarize all files" FILES="src/"

# Conjure will:
# 1. Assess file sizes
# 2. Check quota availability
# 3. Select optimal service
# 4. Execute delegation
# 5. Return results
```

### Check Quota Status

```bash
make quota-status

# Output:
# Gemini: 450/1000 tokens used (5h rolling)
# Qwen: 200/500 tokens used (5h rolling)
```

### Usage Report

```bash
make usage-report

# Output:
# This week:
#   Gemini: 2,500 tokens, $0.05
#   Qwen: 800 tokens, $0.02
# Total: 3,300 tokens, $0.07
```

### Manual Service Selection

```bash
# Force Gemini for large context
Skill(conjure:gemini-delegation)

# Force Qwen for privacy-sensitive tasks
Skill(conjure:qwen-delegation)
```

## Delegation Decision Framework

The `delegation-core` skill evaluates:

| Factor | Weight | Description |
|--------|--------|-------------|
| Context Size | High | Does input exceed Claude's context? |
| Task Type | Medium | Is task better suited for another model? |
| Privacy Needs | High | Are there data residency requirements? |
| Quota Available | High | Do we have capacity on target service? |
| Cost | Low | Is delegation cost-effective? |

## Service Comparison

| Service | Strengths | Best For |
|---------|-----------|----------|
| **Gemini** | Large context (1M+ tokens) | Bulk file processing, long documents |
| **Qwen** | Local/private inference | Sensitive data, offline work |

## Hook Behavior

### Pre-Tool Use Hook

When reading large files:

```
[Conjure Bridge] File exceeds context threshold
Suggested action: Delegate to Gemini
Estimated tokens: 125,000
Quota available: Yes
```

### Post-Tool Use Hook

When output is truncated:

```
[Conjure Bridge] Output truncated at 100,000 chars
Suggested action: Re-run with delegation
Recommended service: Gemini
```

## Configuration

### Environment Variables

```bash
# Gemini API key
export GEMINI_API_KEY=your-key

# Qwen MCP endpoint
export QWEN_MCP_ENDPOINT=http://localhost:8080
```

### Quota Configuration

Edit `conjure/config/quotas.yaml`:

```yaml
gemini:
  hourly_limit: 1000
  daily_limit: 10000

qwen:
  hourly_limit: 500
  daily_limit: 5000
```

## Integration Patterns

### With Conservation

```bash
# Conservation detects high context usage
# Suggests delegation via conjure
Skill(conservation:context-optimization)
# -> Recommends: Skill(conjure:delegation-core)
```

### With Sanctum

```bash
# Large repo analysis
Skill(sanctum:git-workspace-review)
# If repo too large:
# -> Suggests: make delegate-auto FILES="."
```

## Dependencies

Conjure uses leyline for infrastructure:

```
conjure
    |
    v
leyline (quota-management, service-registry)
```

## Best Practices

1. **Check Quota First**: Run `make quota-status` before large delegations
2. **Use Auto Mode**: Let conjure select the optimal service
3. **Monitor Costs**: Review `make usage-report` weekly
4. **Cache Results**: Store delegation results locally to avoid repeat calls

## Related Plugins

- **leyline**: Provides quota management and service registry
- **conservation**: Detects when delegation is beneficial
