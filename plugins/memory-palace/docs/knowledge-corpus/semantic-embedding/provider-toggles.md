---
title: "Semantic Embedding \u2014 Provider Toggles"
source: memory-palace://seed/semantic-embedding-provider-toggles
author: Memory Palace Seed Bot
date_captured: '2025-12-09'
palace: Knowledge Brain
district: Search Upgrades
maturity: growing
tags:
- embedding
- provider_toggles
- search
- semantic
- semantic-embedding
queries:
- How to apply semantic embedding to toggling embedding providers?
- Semantic Embedding best practices for yaml teams
- Provider Toggles guidance for toggling embedding providers
---

# Semantic Embedding — Provider Toggles

## Why it matters

Expose config flag to switch between none/local/api embedding providers.

## Focus Area

- **Language / Runtime**: YAML
- **Primary Focus**: toggling embedding providers

## Implementation Playbook
1. Update config schema with `embedding_provider`.
2. Teach unified search to branch accordingly.
3. Add CLI showing current provider + health.
