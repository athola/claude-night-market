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

## Key Concepts

**MECW (Maximum Effective Context Window)**: Keep context pressure under 50% of the total window. Beyond this threshold, response quality degrades. Conservation skills enforce this.

**MCP Patterns**: Instead of passing large datasets through conversation context, use MCP tools to process data at the source and return only results. This works well for tool chains that would otherwise consume thousands of tokens.

**Progressive Loading**: Skills load modules on demand rather than all at once, reducing the initial context footprint.

## Skills

| Skill | Purpose |
|-------|---------|
| `context-optimization` | MECW assessment and subagent coordination |
| `mcp-code-execution` | MCP patterns for data pipelines |
| `performance-monitoring/cpu-gpu-performance` | Hardware resource tracking |
| `resource-management/token-conservation` | Token budget enforcement |

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
