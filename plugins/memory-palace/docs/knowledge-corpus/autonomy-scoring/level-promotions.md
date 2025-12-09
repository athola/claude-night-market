---
title: "Autonomy Scoring \u2014 Level Promotions"
source: memory-palace://seed/autonomy-scoring-level-promotions
author: Memory Palace Seed Bot
date_captured: '2025-12-09'
palace: Governance
district: Trust Engine
maturity: growing
tags:
- autonomy
- autonomy-scoring
- governance
- level_promotions
- scoring
queries:
- How to apply autonomy scoring to criteria for promoting autonomy levels?
- Autonomy Scoring best practices for python teams
- Level Promotions guidance for criteria for promoting autonomy levels
---

# Autonomy Scoring — Level Promotions

## Why it matters

Define multi-window accuracy thresholds before promoting autonomy levels.

## Focus Area

- **Language / Runtime**: Python
- **Primary Focus**: criteria for promoting autonomy levels

## Implementation Playbook
1. Track rolling accuracy windows (7d, 30d).
2. Require consecutive windows above threshold before promotion.
3. Log promotions in `autonomy-state.yaml` with rationale.
