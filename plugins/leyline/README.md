# Leyline

Infrastructure and pipeline building blocks for Claude Code plugins.

## Overview

Leyline provides shared utilities and services to maintain consistent plugin functionality. It handles resource tracking, service integration, and pipeline patterns such as error handling and circuit breakers. While Abstract manages evaluation and design, Leyline delivers the technical components required for cross-plugin communication and system stability.

## Skills

| Skill | Purpose | Use When |
|-------|---------|----------|
| `quota-management` | Track and enforce resource limits. | Implementing services with rate limits. |
| `usage-logging` | Session-aware usage tracking. | Capturing audit trails or cost metrics. |
| `service-registry` | Manage external service connections. | Coordinating multiple external services. |
| `error-patterns` | Standardized error handling. | Implementing error recovery logic. |
| `authentication-patterns` | Common auth flows. | Connecting to external APIs. |

## Workflow and Integration

Other plugins call Leyline for quota enforcement and standardized error recovery. The `quota_tracker` and `service_registry` utilities provide real-time monitoring of service health and rate limit compliance. These patterns use loose coupling to allow for progressive adoption throughout the codebase.

## Plugin Metadata Standards (Claude Code 2.0.73+)

Claude Code 2.0.73+ supports search filtering in the plugin discovery screen. Descriptions should start with a direct statement of functionality, such as "Infrastructure and pipeline building blocks for shared utilities." Include searchable keywords like "quota management" or "error handling" and mention specific capabilities like "circuit breakers" or "auth flows." Descriptions should remain between 50 and 150 characters to ensure clarity in search results.
