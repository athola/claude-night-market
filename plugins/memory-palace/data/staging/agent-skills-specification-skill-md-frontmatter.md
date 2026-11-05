---
title: 'Agent Skills specification: SKILL.md frontmatter limits'
source:
  type: web_fetch
  identifier: https://agentskills.io/specification
author: claude
date_captured: '2026-10-30'
palace: Agent Tooling
district: Cross-agent formats
maturity: probation
tags:
- agent-skills
- skill-format
- frontmatter
- cross-agent
---

# Agent Skills specification: SKILL.md frontmatter limits

## Marginal Value Summary

- **Integration Decision**: standalone
- **Confidence**: 90%
- **Novelty Tags**: agent-skills, skill-format, frontmatter, cross-agent

## Intake Content

# Agent Skills specification: SKILL.md frontmatter limits

Source: https://agentskills.io/specification, fetched 2026-10-14.

A skill is a directory containing at minimum a `SKILL.md`, with optional
`scripts/`, `references/` and `assets/`. `SKILL.md` is YAML frontmatter
followed by Markdown.

| Field | Required | Constraint |
|---|---|---|
| `name` | yes | 1-64 characters; lowercase letters, numbers, hyphens; must not start or end with a hyphen |
| `description` | yes | non-empty, max 1024 characters; what the skill does and when to use it |
| `license` | no | license name or bundled license file |
| `compatibility` | no | max 500 characters; environment requirements |
| `metadata` | no | string-to-string map |
| `allowed-tools` | no | space-separated pre-approved tools (experimental) |

Relevance here: night-market caps descriptions at 160 characters
(`plugins/abstract/scripts/validate_budget.py`, ADR-0004). That cap is a
context-budget decision, not a format limit: the spec allows 1024. Cursor
additionally requires `name` to match the parent folder name.
