# Conservation Plugin

Resource optimization and performance monitoring for Claude Code. Uses MCP patterns and the Maximum Effective Context Window (MECW) principle to reduce token usage and keep context pressure low.

## Quick Start

```bash
# Install as plugin
claude plugin install conservation

# Development setup
git clone https://github.com/athola/conservation
cd conservation
make deps
```

## Session Start Integration

Conservation skills are automatically loaded at session start via hooks. This ensures optimized performance, token usage, and context management from the beginning of every Claude Code session.

### Bypass Modes

Set the `CONSERVATION_MODE` environment variable to control behavior:

| Mode | Command | Behavior |
|------|---------|----------|
| `normal` | `claude` | Full conservation guidance (default) |
| `quick` | `CONSERVATION_MODE=quick claude` | Skip guidance for fast processing |
| `deep` | `CONSERVATION_MODE=deep claude` | Extended resources for thorough analysis |

## Key Concepts

**MECW (Maximum Effective Context Window)**: Keep context pressure under 50% of the total window. Beyond this threshold, response quality degrades. Conservation skills enforce this.

**MCP Patterns**: Instead of passing large datasets through conversation context, use MCP tools to process data at the source and return only results. This works well for tool chains that would otherwise consume thousands of tokens.

**Progressive Loading**: Skills load modules on demand rather than all at once, reducing the initial context footprint.

## Skills

| Skill | Purpose |
|-------|---------|
| `context-optimization` | MECW assessment and subagent coordination |
| `token-conservation` | Token budget enforcement and quota tracking |
| `cpu-gpu-performance` | Hardware resource tracking and selective testing |
| `mcp-code-execution` | MCP patterns for data pipelines |
| `optimizing-large-skills` | Breaking down oversized skills |

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
