# Utility Layer

The utility layer provides resource optimization and external integration capabilities.

## Purpose

Utility plugins handle:

- **Resource Management**: Context window optimization, token conservation
- **External Delegation**: Offloading tasks to external LLM services
- **Performance Monitoring**: CPU/GPU and memory tracking

## Plugins

| Plugin | Description | Key Use Case |
|--------|-------------|--------------|
| [conservation](conservation.md) | Resource optimization | Context management |
| [conjure](conjure.md) | External delegation | Long-context tasks |

## When to Use

### conservation
Use when you need to:
- Monitor context window usage
- Optimize token consumption
- Handle large codebases efficiently
- Track resource usage patterns

### conjure
Use when you need to:
- Process files too large for Claude's context
- Delegate bulk processing tasks
- Use specialized external models
- Manage API quotas across services

## Key Capabilities

### Context Optimization
```bash
/optimize-context
```
Analyzes current context usage and suggests MECW (Minimum Effective Context Window) strategies.

### Growth Analysis
```bash
/analyze-growth
```
Predicts context budget impact of skill growth patterns.

### External Delegation
```bash
make delegate-auto PROMPT="Summarize" FILES="src/"
```
Auto-selects the best external service for a task.

## Conservation Modes

The conservation plugin supports different modes via environment variables:

| Mode | Command | Behavior |
|------|---------|----------|
| Normal | `claude` | Full conservation guidance |
| Quick | `CONSERVATION_MODE=quick claude` | Skip guidance for fast tasks |
| Deep | `CONSERVATION_MODE=deep claude` | Extended resource allowance |

## Key Thresholds

### Context Usage
- **< 30%**: LOW - Normal operation
- **30-50%**: MODERATE - Consider optimization
- **> 50%**: CRITICAL - Optimize immediately

### Token Quotas
- 5-hour rolling cap
- Weekly cap
- Check with `/status`

## Installation

```bash
# Resource optimization
/plugin install conservation@claude-night-market

# External delegation
/plugin install conjure@claude-night-market
```

## Integration with Other Layers

Utility plugins enhance all other layers:

```
Domain Specialists
       |
       v
   Utility Layer (optimization, delegation)
       |
       v
 Foundation Layer
```

For example, conjure can delegate large file processing before sanctum analyzes the results.
