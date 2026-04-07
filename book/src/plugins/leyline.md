# leyline

Infrastructure and pipeline building blocks for plugins.

## Overview

Leyline provides reusable infrastructure patterns that other plugins build on.
Think of it as a standard library for plugin development - error handling,
authentication, storage, and testing patterns.

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
| `error-patterns` | Standardized error handling patterns | Production-grade error recovery |
| `damage-control` | Recovery protocols for broken agent state | Crash recovery, context overflow, merge conflicts |
| `content-sanitization` | Sanitization for external content | Loading Issues, PRs, Discussions, or WebFetch results |
| `markdown-formatting` | Line wrapping and style conventions | Generating or editing markdown prose |
| `authentication-patterns` | Auth flow patterns | Handling API keys and OAuth |
| `evaluation-framework` | Decision thresholds | Building evaluation criteria |
| `progressive-loading` | Dynamic content loading | Lazy loading strategies |
| `risk-classification` | Inline 4-tier risk classification for agent tasks | Risk-based task routing with war-room escalation |
| `pytest-config` | Pytest configuration | Standardized test configuration |
| `storage-templates` | Storage abstraction | File and database patterns |
| `stewardship` | Cross-cutting stewardship principles with five virtues (Care, Curiosity, Humility, Diligence, Foresight) | Working with project health, codebase improvement, or virtue-aligned development |
| `testing-quality-standards` | Test quality guidelines | Ensuring high-quality tests |
| `deferred-capture` | Contract for unified deferred-item capture across plugins | Implementing or testing deferred-capture wrappers |
| `git-platform` | Git platform detection and cross-platform commands | Abstracting GitHub/GitLab/Bitbucket differences |
| `supply-chain-advisory` | Known-bad version detection, lockfile auditing, incident response | After supply chain advisories, dependency audits, or suspected compromise |
| `sem-integration` | sem CLI detection, install-on-first-use, fallback patterns | Skills consuming git diff output that benefit from entity-level diffs |

## Commands

| Command | Description |
|---------|-------------|
| `/reinstall-all-plugins` | Uninstall and reinstall all plugins to refresh cache |
| `/update-all-plugins` | Update all installed plugins from marketplaces |
| `/verify-plugin` | Verify plugin trust via ERC-8004 Reputation Registry |

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

## Modules

### frontmatter

Canonical YAML frontmatter parser shared across plugins.

```python
from leyline.frontmatter import parse_frontmatter

content = """---
name: my-skill
category: testing
---

# My Skill
"""
meta = parse_frontmatter(content)
# {'name': 'my-skill', 'category': 'testing'}
```

When PyYAML is installed, it uses `yaml.safe_load`. When unavailable,
it falls back to a minimal key-value parser that handles simple `key: value`
pairs (no nested structures). Returns `None` for content without frontmatter.

Other plugins should import this instead of reimplementing frontmatter parsing.

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

## Discussion Operations (GitHub Only)

The `git-platform` skill's `command-mapping` module provides GraphQL templates
for GitHub Discussions. These templates are consumed by attune (war room
publishing), imbue (scope-guard linking), memory-palace (knowledge promotion),
and minister (playbook rituals).

Supported operations: create, comment, threaded reply, mark-as-answer, search,
get-by-number, update, and list-by-category.
Category resolution from slug to `nodeId` is included as a prerequisite step.

On non-GitHub platforms (GitLab, Bitbucket),
all Discussion operations are skipped with a warning.

A `fetch-recent-discussions.sh` SessionStart hook queries the 5 most recent
"Decisions" discussions at session start
and injects a summary (<600 tokens) so that new sessions can discover prior
deliberations.

An `auto-star-repo.sh` SessionStart hook stars the repository if not already
starred. The hook is idempotent (checks status before acting), never unstars,
and fails silently if no auth method is available.

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
