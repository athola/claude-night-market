---
name: web-search
description: Searches the open web for docs, comparisons, and news via You.com MCP or WebSearch. Use when a topic needs knowledge beyond GitHub, forums, or academia.
alwaysApply: false
category: research
tags:
  - web
  - search
  - youcom
  - documentation
estimated_tokens: 200
model_hint: standard
---
# Web Search

## When To Use

- Finding vendor documentation, standards, or official guides
- Comparisons and benchmarks across products or approaches
- News, release notes, and recent status for a technology
- Standalone searches, or as one channel of a `/tome:research`
  session: the planner dispatches `tome:web-searcher` from medium
  depth, and the channel runs a positive control (RFC 2119) before
  its topic queries so its silence can count in the coverage verdict

## When NOT To Use

- Code implementations (use `Skill(tome:code-search)`)
- Community opinions (use `Skill(tome:discourse)`)
- Academic literature (use `Skill(tome:papers)`)

Search the open web for pages about a topic. This is the
general-knowledge channel: the pages no domain-specific channel
targets.

## Sources (Priority Order)

1. You.com MCP server (`you-search` tool) when configured
2. WebSearch tool as fallback (no configuration needed)

The You.com MCP server is optional. Without it the channel runs
entirely on the built-in WebSearch tool, so a session never fails
because the server is absent.

## Setup (Optional)

To prefer You.com results, add the MCP server to your Claude Code
config once:

```bash
# Keyless free profile
claude mcp add you --transport http https://api.you.com/mcp?profile=free

# Authenticated (higher rate limits; YDC_API_KEY from you.com)
claude mcp add you --transport http https://api.you.com/mcp \
  --header "Authorization: Bearer $YDC_API_KEY"
```

A key is only needed for the authenticated endpoint. The free
profile needs no key and no account.

## Workflow

1. Build search queries using
   `tome.channels.web.expand_web_queries()`
2. Run each query through the You.com MCP `you-search` tool if the
   server is configured, otherwise through WebSearch
3. Parse results via `parse_you_mcp_result()` (raises `ValueError` on
   a response shape that is not a you-search envelope) or
   `parse_websearch_result()` (raises `ValueError` on a result with
   no URL)
4. Rank via `rank_web_findings()`
5. Return Finding objects

## Failure Handling

- If the You.com MCP tool errors or is unreachable, retry the
  query through WebSearch and record the fallback in the query log
  so the report can show the channel ran degraded rather than ok
- If both paths fail for every query, report the failure
  explicitly rather than returning fabricated or empty findings

## Exit Criteria

- [ ] At least one web search query built and executed for the
      requested topic, through You.com MCP or WebSearch
- [ ] Results parsed into Finding objects with title, URL, and a
      relevance score, marked `channel="web"`
- [ ] Findings returned from `rank_web_findings()` sorted by
      relevance score descending
- [ ] If the You.com path failed and WebSearch was used, the
      fallback is reported rather than passed off as the primary
      source
- [ ] If no results are found for any query, this is reported
      explicitly rather than returning an empty list silently
