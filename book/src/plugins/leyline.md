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
| `service-registry` | Service discovery, rate limiting and quotas, telemetry | Managing external tool connections, consuming rate-limited APIs, logging tool usage |
| `error-patterns` | Standardized error handling patterns | Production-grade error recovery |
| `damage-control` | Recovery protocols for broken agent state | Crash recovery, context overflow, merge conflicts |
| `content-sanitization` | Sanitization for external content | Loading Issues, PRs, Discussions, or WebFetch results |
| `markdown-formatting` | Line wrapping and style conventions | Generating or editing markdown prose |
| `authentication-patterns` | Auth flow patterns | Handling API keys and OAuth |
| `evaluation-framework` | Decision thresholds and utility-guided action selection | Building evaluation criteria or gating agent dispatch |
| `progressive-loading` | Dynamic content loading | Lazy loading strategies |
| `risk-classification` | Inline 4-tier risk classification for agent tasks | Risk-based task routing with war-room escalation |
| `stewardship` | Cross-cutting stewardship principles with five virtues (Care, Curiosity, Humility, Diligence, Foresight) | Working with project health, codebase improvement, or virtue-aligned development |
| `testing-quality-standards` | Test quality guidelines and pytest configuration | Ensuring high-quality tests and standardized test configuration |
| `decision-journal` | Contracts for the decision journal, deferred-item capture, and storage templates | Recording a tradeoff or lesson, building a deferred-capture wrapper, or organizing stored knowledge |
| `git-platform` | Git platform detection and cross-platform commands | Abstracting GitHub/GitLab/Bitbucket differences |
| `ticket-writing` | Glanceable tickets with the why inline or one link away | Creating or editing Jira, GitLab, or GitHub tickets |
| `supply-chain-advisory` | Known-bad version detection, lockfile auditing, incident response | After supply chain advisories, dependency audits, or suspected compromise |
| `sem-integration` | sem CLI detection, install-on-first-use, fallback patterns | Skills consuming git diff output that benefit from entity-level diffs |
| `additive-bias-defense` | Scrutiny questions challenging unnecessary additions | Reviewing proposals that add new code, files, or abstractions |
| `utility` | Expected-gain scoring for candidate agent actions | Guiding action selection in agentic workflows |

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
  - leyline:service-registry  # quota-management module
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
# service-registry quota-management module
from leyline.quota_tracker import QuotaTracker

tracker = QuotaTracker(service="my-service")
level, warnings = tracker.get_quota_status()
if level != "critical":
    # Make the API call, then record it
    tracker.record_request(tokens=500)
```

### Telemetry

```python
# service-registry usage-logging module
from leyline.usage_logger import UsageEvent, UsageLogger

logger = UsageLogger(service="my-service")
logger.log_usage(UsageEvent("WebFetch", tokens=500, duration=1.2))
```

### Storage Abstraction

The decision-journal `storage-templates` module is guidance with no Python API: it gives
directory layouts and file templates for a plugin to copy, not a class
to import.

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

An async `auto-star-repo.sh` SessionStart hook checks whether the repository
is starred and, if not, asks Claude to offer a star on the next conversation
turn. It stars only after the user agrees, never unstars, and fails silently
if no auth method is available.

## Integration

Leyline is used by:

- **abstract**: Plugin validation uses error patterns
- **conjure**: Delegation uses quota management
- **conservation**: Context optimization uses MECW patterns

## Best Practices

1. **Don't Duplicate**: Use leyline patterns instead of reimplementing
2. **Compose Patterns**: Combine multiple patterns for complex needs
3. **Test with Standards**: Use the testing-quality-standards pytest-config module for consistent testing
4. **Log Everything**: Use service-registry usage logging for debugging and analytics

## Related Plugins

- **abstract**: Uses leyline for plugin infrastructure
- **conjure**: Uses leyline for quota and service management
- **conservation**: Uses leyline for MECW implementation
