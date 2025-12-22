---
name: architecture-paradigm-space-based
description: |
  Employ space-based or data-grid architectures to scale high-traffic, stateful
  workloads across multiple nodes with linear scalability.

  Triggers: space-based, data grid, in-memory, linear scaling, high traffic,
  stateful workloads, tuple space, distributed cache, replication

  Use when: traffic overwhelms single database nodes, linear scalability needed,
  in-memory processing provides significant performance gains

  DO NOT use when: selecting from multiple paradigms - use architecture-paradigms first.
  DO NOT use when: data doesn't fit in memory or isn't performance-critical.
  DO NOT use when: simpler caching strategies would suffice.

  Consult this skill when designing high-scale data grid architectures.
version: 1.0.0
category: architectural-pattern
tags: [architecture, space-based, data-grid, scalability, in-memory, stateful]
dependencies: []
tools: [data-grid-platform, replication-manager, load-tester]
usage_patterns:
  - paradigm-implementation
  - high-traffic-workloads
  - linear-scalability
complexity: high
estimated_tokens: 800
---

# The Space-Based Architecture Paradigm

## When to Employ This Paradigm
- When traffic or state volume overwhelms a single database node.
- When latency requirements demand in-memory data grids located close to processing units.
- When linear scalability is required, achieved by partitioning workloads across many identical, self-sufficient units.

## Adoption Steps
1. **Partition Workloads**: Divide traffic and data into processing units, each backed by a replicated data cache.
2. **Design the Data Grid**: Select the appropriate caching technology, replication strategy (synchronous vs. asynchronous), and data eviction policies.
3. **Coordinate Persistence**: Implement a write-through or write-behind strategy to a durable data store, including reconciliation processes.
4. **Implement Failover Handling**: Design a mechanism for leader election or heartbeats to ensure recovery from node loss without data loss.
5. **Validate Scalability**: Conduct load and chaos testing to confirm the system's elasticity and self-healing capabilities.

## Key Deliverables
- An Architecture Decision Record (ADR) detailing the chosen grid technology, partitioning scheme, and durability strategy.
- Runbooks for scaling processing units and for recovering from "split-brain" scenarios.
- A monitoring suite to track cache hit rates, replication lag, and failover events.

## Risks & Mitigations
- **Eventual Consistency Issues**:
  - **Mitigation**: Formally document data-freshness Service Level Agreements (SLAs) and implement compensation logic for data that is not immediately consistent.
- **Operational Complexity**:
  - **Mitigation**: The orchestration of a data grid requires mature automation. Invest in robust tooling and automation early in the process.
- **Cost**:
  - **Mitigation**: In-memory grids can be resource-intensive. Implement aggressive monitoring of utilization and auto-scaling policies to manage costs effectively.
