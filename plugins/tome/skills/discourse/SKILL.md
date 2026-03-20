---
name: discourse
description: >-
  Scan community discussion channels (HN, Lobsters, Reddit,
  tech blogs) for experience reports and opinions on a
  topic. Use when the user wants community perspectives
  on a technology or approach.
category: research
tags:
  - hackernews
  - reddit
  - lobsters
  - blogs
  - discourse
estimated_tokens: 200
---

# Discourse Search

Scan community channels for discussions on a topic.

## Channels

- **Hacker News**: Algolia API at hn.algolia.com
- **Lobsters**: WebSearch with site:lobste.rs
- **Reddit**: JSON API (append .json to URLs)
- **Tech blogs**: WebSearch targeting curated domains

## Workflow

1. Build search URLs/queries per channel using
   `tome.channels.discourse.*` functions
2. Execute via WebFetch (APIs) or WebSearch (fallback)
3. Parse responses into Finding objects
4. Merge across sources with source attribution
