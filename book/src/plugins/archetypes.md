# archetypes

Architecture paradigm selection and implementation planning.

## Overview

Archetypes helps you choose the right architecture for your system. It provides an interactive paradigm selector and detailed implementation guides for 13 architectural patterns.

## Installation

```bash
/plugin install archetypes@claude-night-market
```

## Skills

### Orchestrator

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `architecture-paradigms` | Interactive paradigm selector | Choosing architecture for new systems |

### Paradigm Guides

| Skill | Architecture | Best For |
|-------|-------------|----------|
| `architecture-paradigm-layered` | N-tier | Simple web apps, internal tools |
| `architecture-paradigm-hexagonal` | Ports & Adapters | Infrastructure independence |
| `architecture-paradigm-microservices` | Distributed services | Large-scale enterprise |
| `architecture-paradigm-event-driven` | Async communication | Real-time processing |
| `architecture-paradigm-serverless` | Function-as-a-Service | Event-driven with minimal infra |
| `architecture-paradigm-pipeline` | Pipes-and-filters | ETL, media processing |
| `architecture-paradigm-cqrs-es` | CQRS + Event Sourcing | Audit trails, event replay |
| `architecture-paradigm-microkernel` | Plugin-based | Minimal core with extensions |
| `architecture-paradigm-modular-monolith` | Internal boundaries | Module separation without distribution |
| `architecture-paradigm-space-based` | Data-grid | High-scale stateful workloads |
| `architecture-paradigm-service-based` | Coarse-grained SOA | Modular without microservices |
| `architecture-paradigm-functional-core` | Functional Core, Imperative Shell | Superior testability |
| `architecture-paradigm-client-server` | Client-server | Clear client/server responsibilities |

## Usage Examples

### Interactive Selection

```bash
Skill(archetypes:architecture-paradigms)

# Claude will:
# 1. Ask about your requirements
# 2. Evaluate trade-offs
# 3. Recommend paradigms
# 4. Provide implementation guidance
```

### Direct Paradigm Access

```bash
# Get specific paradigm details
Skill(archetypes:architecture-paradigm-hexagonal)

# Returns:
# - Core concepts
# - When to use
# - Implementation patterns
# - Example code
# - Trade-offs
```

## Paradigm Comparison

### By Complexity

| Level | Paradigms |
|-------|-----------|
| Low | Layered, Client-Server |
| Medium | Modular Monolith, Service-Based, Functional Core |
| High | Microservices, Event-Driven, CQRS-ES, Space-Based |

### By Team Size

| Team | Recommended |
|------|-------------|
| 1-3 | Layered, Functional Core, Modular Monolith |
| 4-10 | Hexagonal, Service-Based, Pipeline |
| 10+ | Microservices, Event-Driven |

### By Scalability Need

| Need | Paradigms |
|------|-----------|
| Single server | Layered, Modular Monolith |
| Horizontal | Microservices, Serverless |
| Extreme | Space-Based, Event-Driven |

## Selection Criteria

The paradigm selector evaluates:

1. **Team size and structure**
2. **Scalability requirements**
3. **Deployment constraints**
4. **Data consistency needs**
5. **Development velocity priorities**
6. **Operational maturity**

## Example Output

### Hexagonal Architecture

```
## Hexagonal Architecture (Ports & Adapters)

### Core Concepts
- Domain logic at center
- Ports define interfaces
- Adapters implement ports
- Infrastructure is pluggable

### When to Use
- Need to swap databases/frameworks
- Test-driven development focus
- Long-lived applications
- Multiple integration points

### Structure
src/
├── domain/           # Pure business logic
│   ├── models/
│   └── services/
├── ports/            # Interface definitions
│   ├── inbound/
│   └── outbound/
└── adapters/         # Implementations
    ├── web/
    ├── persistence/
    └── external/

### Trade-offs
+ Easy testing via port mocking
+ Framework-agnostic domain
+ Clear dependency direction
- More initial structure
- Learning curve
```

## Best Practices

1. **Start Simple**: Begin with layered, evolve as needed
2. **Match Team**: Don't use microservices with a small team
3. **Consider Ops**: Complex architectures need operational maturity
4. **Plan Evolution**: Design for change, not perfection

## Decision Tree

```
Start
  |
  v
Simple CRUD? --> Yes --> Layered
  |
  No
  |
  v
Need testability? --> Yes --> Functional Core or Hexagonal
  |
  No
  |
  v
High scale? --> Yes --> Event-Driven or Space-Based
  |
  No
  |
  v
Multiple teams? --> Yes --> Microservices or Service-Based
  |
  No
  |
  v
Modular Monolith
```

## Related Plugins

- **pensive**: Architecture review complements paradigm selection
- **spec-kit**: Use after paradigm selection for implementation planning
