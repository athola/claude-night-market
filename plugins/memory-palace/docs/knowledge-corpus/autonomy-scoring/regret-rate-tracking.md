---
title: "Autonomy Scoring \u2014 Regret Rate Tracking"
source: memory-palace://seed/autonomy-scoring-regret-rate-tracking
author: Memory Palace Seed Bot
date_captured: '2025-12-09'
palace: Governance
district: Trust Engine
maturity: growing
tags:
- autonomy
- autonomy-scoring
- governance
- regret_rate_tracking
- scoring
queries:
- How to apply autonomy scoring to monitoring regret rate spikes?
- Autonomy Scoring best practices for python teams
- Regret Rate Tracking guidance for monitoring regret rate spikes
---

# Autonomy Scoring — Regret Rate Tracking

## Why it matters

Compute regret rate and emit alerts if it spikes >5% WoW.

## Focus Area

- **Language / Runtime**: Python
- **Primary Focus**: monitoring regret rate spikes

## Implementation Playbook
1. Log regret events in telemetry CSV.
2. Compare week-over-week rates in scoring job.
3. Auto-demote levels when thresholds breached.
