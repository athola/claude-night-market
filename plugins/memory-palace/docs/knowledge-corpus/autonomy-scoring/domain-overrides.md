---
title: "Autonomy Scoring \u2014 Domain Overrides"
source: memory-palace://seed/autonomy-scoring-domain-overrides
author: Memory Palace Seed Bot
date_captured: '2025-12-09'
palace: Governance
district: Trust Engine
maturity: growing
tags:
- autonomy
- autonomy-scoring
- domain_overrides
- governance
- scoring
queries:
- How to apply autonomy scoring to locking sensitive domains at Level 0?
- Autonomy Scoring best practices for python teams
- Domain Overrides guidance for locking sensitive domains at Level 0
---

# Autonomy Scoring — Domain Overrides

## Why it matters

Allow overrides that lock autonomy levels for security/privacy domains.

## Focus Area

- **Language / Runtime**: Python
- **Primary Focus**: locking sensitive domains at Level 0

## Implementation Playbook
1. Store overrides in `domain_controls` map.
2. Expose CLI to toggle locks with reason codes.
3. Audit overrides weekly for stale decisions.
