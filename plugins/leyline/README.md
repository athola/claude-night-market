# Leyline

Infrastructure and pipeline building blocks for Claude Code plugins.

## Quick Start

```bash
# Use quota management for rate-limited services
Skill(leyline:quota-management)

# Implement standardized error handling
Skill(leyline:error-patterns)

# Set up authentication flows
Skill(leyline:authentication-patterns)
```

## Overview

Leyline provides shared utilities
and services to maintain consistent plugin functionality.
It handles resource tracking, service integration,
and pipeline patterns such as error handling and circuit breakers.
While Abstract manages evaluation and design,
Leyline delivers the technical components required for cross-plugin
communication and system stability.

## Skills

| Skill | Purpose | Use When |
|-------|---------|----------|
| `quota-management` | Track and enforce resource limits. | Implementing services with rate limits. |
| `usage-logging` | Session-aware usage tracking. | Capturing audit trails or cost metrics. |
| `service-registry` | Manage external service connections. | Coordinating multiple external services. |
| `error-patterns` | Standardized error handling. | Implementing error recovery logic. |
| `authentication-patterns` | Common auth flows. | Connecting to external APIs. |
| `content-sanitization` | Sanitize external content. | Loading Issues, PRs, or WebFetch results. |
| `damage-control` | Agent crash recovery. | Context overflow, merge conflicts, broken state. |
| `evaluation-framework` | Decision thresholds and scoring. | Building evaluation criteria. |
| `git-platform` | Cross-platform git forge commands. | Abstracting GitHub/GitLab/Bitbucket. |
| `markdown-formatting` | Line wrapping and style conventions. | Generating or editing markdown prose. |
| `progressive-loading` | Dynamic content loading. | Lazy loading strategies. |
| `pytest-config` | Pytest configuration patterns. | Standardized test configuration. |
| `risk-classification` | Inline 4-tier risk model. | Risk-based task routing. |
| `stewardship` | Stewardship principles and virtues. | Codebase improvement and health. |
| `storage-templates` | Storage abstraction. | File and database patterns. |
| `testing-quality-standards` | Test quality guidelines. | Ensuring high-quality tests. |

## Commands

| Command | Purpose |
|---------|---------|
| `/reinstall-all-plugins` | Refresh all plugins (fixes cache issues). |
| `/update-all-plugins` | Update all installed plugins. |
| `/verify-plugin` | Query ERC-8004 Reputation Registry for trust scores. |

## Workflow and Integration

Other plugins call Leyline for quota enforcement
and standardized error recovery.
The `quota_tracker` and `service_registry` utilities provide real-time
monitoring of service health and rate limit compliance.
These patterns use loose coupling to allow for progressive adoption throughout
the codebase.

## Optional Dependencies

| Package | Purpose | Fallback |
|---------|---------|----------|
| tiktoken | Accurate token estimation | Heuristic (~4 chars/token) |

For accurate token counts, install tiktoken:
```bash
pip install tiktoken
```

## Plugin Metadata Standards (Claude Code 2.0.73+)

Claude Code 2.0.73+ supports search filtering in the plugin discovery screen.
Descriptions should start with a direct statement of functionality,
such as "Infrastructure and pipeline building blocks for shared utilities."
Include searchable keywords like "quota management" or "error handling"
and mention specific capabilities like "circuit breakers"
or "auth flows." Descriptions should remain between 50
and 150 characters to ensure clarity in search results.

## Stewardship

Ways to leave this plugin better than you found it:

- An opportunity to document the quota tracker API so
  downstream plugins can integrate without reading source
- Error pattern examples could cover more recovery
  scenarios that other plugins encounter in practice
- The tiktoken fallback heuristic deserves a brief note
  explaining when it diverges from actual token counts
- Cross-plugin integration tests would help catch
  breakage early when Leyline interfaces change

See [STEWARDSHIP.md](../../STEWARDSHIP.md) for the full
stewardship principles guiding this project.
