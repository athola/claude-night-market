---
module: paradigm-selection
category: decision-support
dependencies:
- archetypes:architecture-paradigms
estimated_tokens: 700
---

# Paradigm Selection

Step 3 of the architecture-aware-init workflow: pick the
architecture paradigm using either the archetypes plugin or the
decision matrix below.

## Option A: Use the archetypes plugin

Invoke the catalog directly:

```
Skill(architecture-paradigms)
```

This guides through the 14 paradigms with comparison tables and
trade-off discussion. Use this when the user wants to explore
options or learn the paradigm space.

Available paradigms:

- Layered Architecture
- Functional Core, Imperative Shell
- Hexagonal (Ports and Adapters)
- Modular Monolith
- Microservices
- Service-Based Architecture
- Event-Driven Architecture
- CQRS + Event Sourcing
- Serverless
- Space-Based Architecture
- Pipeline Architecture
- Microkernel Architecture
- Client-Server Architecture

## Option B: Decision matrix

Use this when the user has a clear context and wants a fast
recommendation.

```
+---------------------+---------+---------+----------+-------------+
| Project Context     | Simple  | Moderate| Complex  | Highly      |
|                     | Domain  | Domain  | Domain   | Complex     |
+---------------------+---------+---------+----------+-------------+
| < 5 engineers       | Layered | Layered | Hexagonal| Functional  |
|                     |         | Hexag.  | Function.| Core        |
+---------------------+---------+---------+----------+-------------+
| 5-15 engineers      | Layered | Modular | Modular  | Hexagonal   |
|                     |         | Monolith| Monolith | + FC,IS     |
+---------------------+---------+---------+----------+-------------+
| 15-50 engineers     | Modular | Micro-  | Micro-   | CQRS/ES     |
|                     | Monolith| services| services | + Event     |
+---------------------+---------+---------+----------+-------------+
| 50+ engineers       | Micro-  | Micro-  | Event-   | Microkernel |
|                     | services| services| Driven   | or Space-   |
|                     |         | + Event |          | Based       |
+---------------------+---------+---------+----------+-------------+
```

## Special cases (override the matrix)

| Workload                  | Paradigm                     |
|---------------------------|------------------------------|
| Real-time / Streaming     | Event-Driven + Pipeline      |
| Bursty / Cloud-Native     | Serverless                   |
| Extensible Platform       | Microkernel                  |
| Data Processing           | Pipeline + Event-Driven      |
| Legacy Integration        | Hexagonal                    |
| High-Throughput Stateful  | Space-Based                  |

## Output of Step 3

Mark `arch-init:paradigm-selected` only after both:

1. The paradigm name is recorded.
2. The reasoning is captured (which row of the matrix or which
   special-case rule applied, and why).

The reasoning feeds the ADR generated in Step 5.
