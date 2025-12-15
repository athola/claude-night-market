---
title: "Structured Concurrency \u2014 Observability Hooks"
source: memory-palace://seed/structured-concurrency-observability
author: Memory Palace Seed Bot
date_captured: '2025-12-09'
palace: Async Systems
district: Execution Safety
maturity: growing
tags:
- async
- observability
- reliability
- structured-concurrency
queries:
- How to apply structured concurrency to instrumenting structured tasks with trace
  spans?
- Structured Concurrency best practices for python teams
- Observability Hooks guidance for instrumenting structured tasks with trace spans
---

# Structured Concurrency — Observability Hooks

## Why it matters

Wrap TaskGroup creation with OpenTelemetry spans to trace child task lifecycles.

## Focus Area

- **Language / Runtime**: Python
- **Primary Focus**: instrumenting structured tasks with trace spans

## Implementation Playbook
1. Use contextvars to carry trace ids into TaskGroup scopes.
2. Record start/stop events for each spawned task.
3. Tag spans with cancellation causes for root-cause analysis.
