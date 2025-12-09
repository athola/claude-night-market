---
title: "Garden Tending \u2014 Evergreen Guards"
source: memory-palace://seed/garden-tending-evergreen-guards
author: Memory Palace Seed Bot
date_captured: '2025-12-09'
palace: Knowledge Garden
district: Lifecycle
maturity: growing
tags:
- evergreen_guards
- garden
- garden-tending
- lifecycle
- tending
queries:
- How to apply garden tending to regressions preventing evergreen deletions?
- Garden Tending best practices for python teams
- Evergreen Guards guidance for regressions preventing evergreen deletions
---

# Garden Tending — Evergreen Guards

## Why it matters

Add regression tests that fail when evergreen entries disappear without archive notes.

## Focus Area

- **Language / Runtime**: Python
- **Primary Focus**: regressions preventing evergreen deletions

## Implementation Playbook
1. Map evergreen ids to docs referencing them.
2. Fail CI when references break.
3. Require archive note or replacement entry id.
