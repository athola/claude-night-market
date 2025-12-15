---
title: "Knowledge Indexing \u2014 Keyword Curation"
source: memory-palace://seed/knowledge-indexing-keyword-curation
author: Memory Palace Seed Bot
date_captured: '2025-12-09'
palace: Knowledge Brain
district: Index Fabric
maturity: growing
tags:
- indexing
- keyword_curation
- knowledge-indexing
- metadata
- search
queries:
- How to apply knowledge indexing to standardizing keyword vocabularies?
- Knowledge Indexing best practices for python teams
- Keyword Curation guidance for standardizing keyword vocabularies
---

# Knowledge Indexing — Keyword Curation

## Why it matters

Maintain a single source of truth for index vocabularies to prevent drift.

## Focus Area

- **Language / Runtime**: Python
- **Primary Focus**: standardizing keyword vocabularies

## Implementation Playbook
1. Lint keywords via `scripts/validate_indexes.py`.
2. Normalize casing + hyphenation.
3. Emit warnings for orphaned entries.
