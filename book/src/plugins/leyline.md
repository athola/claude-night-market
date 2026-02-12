# leyline

Infrastructure and pipeline building blocks for plugins.

## Overview

Leyline provides reusable infrastructure patterns that other plugins build on. Think of it as a standard library for plugin development - error handling, authentication, storage, and testing patterns.

## Installation

```bash
/plugin install leyline@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `quota-management` | Rate limiting and quotas | Building services that consume APIs |
| `usage-logging` | Telemetry tracking | Logging tool usage for analytics |
| `service-registry` | Service discovery patterns | Managing external tool connections |
| `damage-control` | Agent-level error recovery for multi-agent coordination | Crash recovery, context overflow, merge conflicts |
| `error-patterns` | Standardized error handling | Implementing production-grade error recovery |
| `authentication-patterns` | Auth flow patterns | Handling API keys and OAuth |
| `evaluation-framework` | Decision thresholds | Building evaluation criteria |
| `mecw-patterns` | MECW implementation | Minimal Effective Context Window |
| `progressive-loading` | Dynamic content loading | Lazy loading strategies |
| `risk-classification` | Inline 4-tier risk classification for agent tasks | Risk-based task routing with war-room escalation |
| `pytest-config` | Pytest configuration | Standardized test configuration |
| `storage-templates` | Storage abstraction | File and database patterns |
| `testing-quality-standards` | Test quality guidelines | Ensuring high-quality tests |

## Commands

| Command | Description |
|---------|-------------|
| `/reinstall-all-plugins` | Uninstall and reinstall all plugins to refresh cache |
| `/update-all-plugins` | Update all installed plugins from marketplaces |

## Usage Examples

### Plugin Management

```bash
# Refresh all plugins (fixes version mismatches)
/reinstall-all-plugins

# Update to latest versions
/update-all-plugins
```

### Using as Dependencies

Leyline skills are typically used as dependencies in other plugins:

```yaml
# In your skill's SKILL.md frontmatter
dependencies:
  - leyline:error-patterns
  - leyline:quota-management
```

### Error Handling Pattern

```bash
Skill(leyline:error-patterns)

# Provides:
# - Structured error types
# - Recovery strategies
# - Logging standards
# - User-friendly messages
```

### Authentication Pattern

```bash
Skill(leyline:authentication-patterns)

# Covers:
# - API key management
# - OAuth flows
# - Token refresh
# - Secret storage
```

### Testing Standards

```bash
Skill(leyline:testing-quality-standards)

# Enforces:
# - Test naming conventions
# - Coverage requirements
# - Mocking guidelines
# - Fixture patterns
```

## Pattern Categories

### Rate Limiting

```python
# quota-management pattern
from leyline import QuotaManager

manager = QuotaManager(
    daily_limit=1000,
    hourly_limit=100,
    burst_limit=10
)

if manager.can_proceed():
    # Make API call
    manager.record_usage()
```

### Telemetry

```python
# usage-logging pattern
from leyline import UsageLogger

logger = UsageLogger(output="telemetry.csv")
logger.log_tool_use("WebFetch", tokens=500, latency_ms=1200)
```

### Storage Abstraction

```python
# storage-templates pattern
from leyline import Storage

storage = Storage.from_config()
storage.save("key", data)
data = storage.load("key")
```

## MECW Patterns

The `mecw-patterns` skill implements Minimum Effective Context Window principles:

| Pattern | Description |
|---------|-------------|
| Summarize Early | Compress context before it grows |
| Load on Demand | Fetch details only when needed |
| Evict Stale | Remove outdated information |
| Prioritize Recent | Weight recent context higher |

## Integration

Leyline is used by:

- **abstract**: Plugin validation uses error patterns
- **conjure**: Delegation uses quota management
- **conservation**: Context optimization uses MECW patterns

## Best Practices

1. **Don't Duplicate**: Use leyline patterns instead of reimplementing
2. **Compose Patterns**: Combine multiple patterns for complex needs
3. **Test with Standards**: Use pytest-config for consistent testing
4. **Log Everything**: Use usage-logging for debugging and analytics

## Related Plugins

- **abstract**: Uses leyline for plugin infrastructure
- **conjure**: Uses leyline for quota and service management
- **conservation**: Uses leyline for MECW implementation
