---
title: "Structured Concurrency \u2014 Cancellation Graphs"
source: memory-palace://seed/structured-concurrency-cancellation-graphs
author: Memory Palace Seed Bot
date_captured: '2025-12-09'
palace: Async Systems
district: Execution Safety
maturity: growing
tags:
- async
- cancellation_graphs
- reliability
- structured-concurrency
queries:
- How to apply structured concurrency to propagating cancellations across goroutine
  trees?
- Structured Concurrency best practices for go teams
- Cancellation Graphs guidance for propagating cancellations across goroutine trees
---

# Structured Concurrency — Cancellation Graphs

## Why it matters

Attach child contexts for each spawned goroutine so cancellation flows downward deterministically.

## Focus Area

- **Language / Runtime**: Go
- **Primary Focus**: propagating cancellations across goroutine trees

## Implementation Playbook
1. Derive child contexts with timeout budgets per subsystem.
2. Log cancellation reasons at the parent before bubbling up errors.
3. Use errgroup.Group to aggregate failures and join goroutines safely.
