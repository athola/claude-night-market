---
name: architecture-paradigm-serverless
description: |
  Build serverless, Function-as-a-Service (FaaS) systems for event-driven or
  operations-light workloads with minimal infrastructure management.

  Triggers: serverless, FaaS, Lambda, Azure Functions, Cloud Functions, event-driven,
  pay-per-use, cold start, stateless functions, managed infrastructure

  Use when: workloads are event-driven with bursty traffic, minimal operations
  overhead desired, pay-per-use cost model is advantageous

  DO NOT use when: selecting from multiple paradigms - use architecture-paradigms first.
  DO NOT use when: long-running processes or stateful operations required.
  DO NOT use when: cold start latency is unacceptable.

  Consult this skill when designing serverless architectures or migrating to FaaS.
version: 1.0.0
category: architectural-pattern
tags: [architecture, serverless, faas, event-driven, cost-optimization]
dependencies: []
tools: [cloud-sdk, serverless-framework, IaC-tools]
usage_patterns:
  - paradigm-implementation
  - event-driven-architectures
  - cost-optimization
complexity: medium
estimated_tokens: 700
---

# The Serverless Architecture Paradigm

## When to Employ This Paradigm
- When workloads are event-driven and exhibit intermittent or "bursty" traffic patterns.
- When the goal is to minimize infrastructure management and adopt a pay-per-execution cost model.
- When latency constraints from "cold starts" are acceptable for the use case or can be effectively mitigated.

## Adoption Steps
1. **Identify Functions**: Decompose workloads into small, stateless function handlers triggered by events such as HTTP requests, message queues, or scheduled timers.
2. **Externalize State**: Utilize managed services like databases and queues for all persistent state. Design handlers to be idempotent to ensure that repeated executions do not have unintended side effects.
3. **Plan Cold-Start Mitigation**: For latency-sensitive paths, keep function dependencies minimal. Employ strategies such as provisioned concurrency or "warmer" functions to reduce cold-start times.
4. **Implement Instrumentation and Security**: Enable detailed tracing and logging for all functions. Adhere to the principle of least privilege with IAM roles and set per-function budgets to control costs.
5. **Automate Deployment**: Use Infrastructure-as-Code (IaC) frameworks like SAM, CDK, or Terraform to create repeatable and reliable release processes.

## Key Deliverables
- An Architecture Decision Record (ADR) that describes function triggers, runtime choices, state management strategies, and cost projections.
- A complete Infrastructure-as-Code (IaC) and CI/CD pipeline for automatically packaging and deploying functions.
- Observability dashboards to monitor key metrics including function duration, error rates, cold-start frequency, and cost.

## Risks & Mitigations
- **Vendor Lock-in**:
  - **Mitigation**: Where feasible, abstract away provider-specific APIs behind your own interfaces or adopt portable frameworks (e.g., Serverless Framework) to reduce dependency on a single cloud vendor.
- **Debugging Challenges**:
  - **Mitigation**: Tracing execution across distributed functions can be complex. Standardize on specific instrumentation libraries and structured logging to simplify debugging.
- **Resource Limits**:
  - **Mitigation**: Actively monitor provider-imposed limits, such as concurrency and memory quotas. Design workloads to be shardable or horizontally scalable to stay within these constraints.
