---
title: Where coding agents read skills, agents, rules and MCP config (Oct 2026)
source:
  type: web_fetch
  identifier: https://cursor.com/docs/context/skills
author: claude
date_captured: '2026-10-30'
palace: Agent Tooling
district: Cross-agent formats
maturity: probation
tags:
- cross-agent
- skills
- subagents
- rules
- mcp
- cross-framework-publish
---

# Where coding agents read skills, agents, rules and MCP config (Oct 2026)

## Marginal Value Summary

- **Integration Decision**: standalone
- **Confidence**: 90%
- **Novelty Tags**: cross-agent, skills, subagents, rules, mcp, cross-framework-publish

## Intake Content

# Where coding agents read skills, agents, rules and MCP config

Compiled 2026-10-30 from WebFetch captures taken 2026-10-14 to 10-16. Each
row quotes the vendor docs as captured. Verify before relying on a path:
these products change quickly.

## Skills directories

| Agent | Project | User | Notes |
|---|---|---|---|
| Cursor | `.agents/skills/`, `.cursor/skills/`, and for compatibility `.claude/skills/`, `.codex/skills/` | `~/.agents/skills/`, `~/.cursor/skills/`, `~/.claude/skills/`, `~/.codex/skills/` | Walks roots recursively. `name` must match the parent folder. A nested `.cursor/skills/` applies only below it |
| GitHub Copilot CLI | `.github/skills`, `.claude/skills`, `.agents/skills` | `~/.copilot/skills`, `~/.agents/skills` | `~/.claude/skills` is not listed. `/skills add` adds a location |

Neither page says how a duplicate skill name across locations is
resolved.

## Instructions and rules

- **Copilot CLI:** `$HOME/.copilot/copilot-instructions.md`,
  `$HOME/.copilot/instructions/**/*.instructions.md`,
  `.github/copilot-instructions.md`,
  `.github/instructions/**/*.instructions.md` (frontmatter `applyTo` glob,
  optional `excludeAgent`), and `AGENTS.md`, `CLAUDE.md`,
  `.claude/CLAUDE.md`, `GEMINI.md`. `COPILOT_HOME` relocates `~/.copilot`.
- **Antigravity CLI:** `~/.gemini/AGENTS.md`, `~/.gemini/GEMINI.md`,
  `~/.gemini/config/rules/*.md`, `~/.gemini/antigravity-cli/rules/*.md`.
  Files in `rules/` need frontmatter with `trigger` (`always_on`,
  `model_decision`, `glob`, `manual`); a missing or invalid trigger is
  silently discarded. 24 KB per file; always-on rules share a
  20,000-token budget.

## Subagents

- **opencode:** `~/.config/opencode/agents/`, `.opencode/agents/`. File
  name is the agent name. `description` is the only required field;
  `mode` is `primary`, `subagent` or `all`. A subagent without `model`
  uses the model of the primary agent that invoked it.
- **Gemini CLI:** `.gemini/agents/*.md`, `~/.gemini/agents/*.md`. Fields
  `name`, `description` required; `model` defaults to `inherit`;
  `max_turns` 30; `timeout_mins` 10. The page banner says Gemini CLI was
  replaced by Antigravity CLI on 2026-06-18.

## MCP configuration

- **Copilot CLI:** `~/.copilot/mcp-config.json`, top-level `mcpServers`;
  local `{type: "local", command, args, env}`, remote `{type: "http", url,
  headers}`; every example sets `tools: ["*"]`.
- **Gemini CLI:** `~/.gemini/settings.json` `mcpServers.<name>` with
  `command`, `args`, `env`, `cwd`, `url` (SSE), `httpUrl` (streamable
  HTTP), `headers`, `timeout`, `trust`, `includeTools`, `excludeTools`.

## Codex

The Codex docs moved from developers.openai.com to learn.chatgpt.com
(308 redirects); the skills and subagents pages were not captured. From
the non-interactive page: `codex exec -` reads the whole prompt from
stdin, and `CODEX_API_KEY` should be set only on the invocation that
needs it, never as a job-level variable in workflows that run
repository code.

Relevance here: `.github/workflows/cross-framework-publish.yml` and
`scripts/clawhub_export.py` publish skills to other agents. The
`.agents/skills` directory is the one location Cursor and Copilot CLI
share.
