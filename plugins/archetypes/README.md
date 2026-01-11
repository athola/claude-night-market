# Architecture Paradigms Collection

Claude Skills for software architecture decision-making and implementation guidance across 14 architectural paradigms.

## Quick Start

- **Orchestrator**: Use `Skill(architecture-paradigms)` to select a paradigm.
- **Comparison**: See [Quick Reference Matrix](#quick-reference-matrix).
- **Learning**: Follow [Learning Paths](#learning-paths).

## Collection Overview

- **1 Orchestrator**: `architecture-paradigms` - Selects and plans architecture.
- **13 Paradigms**: Implementation guides for specific patterns.
- **Resources**: Case studies, decision frameworks, and integration patterns.

## Featured Paradigms

### Core Architectural Patterns
- **Layered Architecture**: Traditional N-tier separation of concerns.
- **Hexagonal (Ports & Adapters)**: Infrastructure independence and flexibility.
- **Functional Core, Imperative Shell**: Business logic isolation for testability.

### Distributed Systems
- **Microservices**: Independent business capability services.
- **Service-Based Architecture**: Coarse-grained services (SOA-lite).
- **Event-Driven Architecture**: Asynchronous, decoupled communication.
- **CQRS + Event Sourcing**: Command/query separation with audit trails.

### Specialized Patterns
- **Modular Monolith**: Single deployable with strong internal boundaries.
- **Serverless**: Function-as-a-Service systems.
- **Space-Based**: In-memory data grids for linear scalability.
- **Pipeline**: Processing stages for ETL workflows.
- **Microkernel**: Plugin architecture for extensible platforms.
- **Client-Server**: Traditional centralized or P2P systems.

## Learning Paths

### 1. Architecture Fundamentals (Beginner)
**Duration**: 2-3 weeks
**Goal**: Learn basic architectural concepts and patterns.

1. **Start**: `architecture-paradigms` (overview and selection).
2. **Core**: Study `architecture-paradigm-layered` (fundamental pattern).
3. **Progress**: Learn `architecture-paradigm-functional-core` (testability principles).
4. **Practice**: Apply layered architecture to a simple project.

**Skills Covered**: Layered, Functional Core, basic architecture principles.

### 2. Modern Architecture Patterns (Intermediate)
**Duration**: 3-4 weeks
**Goal**: Learn contemporary architectural approaches.

1. **Foundation**: Complete Architecture Fundamentals path.
2. **Flexibility**: Study `architecture-paradigm-hexagonal` (infrastructure independence).
3. **Evolution**: Learn `architecture-paradigm-modular-monolith` (strong boundaries).
4. **Integration**: Practice combining paradigms in a single system.

**Skills Covered**: Hexagonal, Modular Monolith, paradigm combination.

### 3. Distributed Systems Architecture (Advanced)
**Duration**: 4-6 weeks
**Goal**: Design and implement distributed architectures.

1. **Prerequisites**: Complete Modern Architecture Patterns path.
2. **Distributed Basics**: Study `architecture-paradigm-microservices` (independent services).
3. **Communication**: Learn `architecture-paradigm-event-driven` (asynchronous systems).
4. **Advanced**: Learn `architecture-paradigm-cqrs-es` (complex collaboration domains).
5. **Specialization**: Choose serverless, space-based, or service-based patterns.

**Skills Covered**: Microservices, Event-Driven, CQRS/ES, specialized patterns.

### 4. Domain-Specific Architecture (Specialized)
**Duration**: 2-3 weeks each
**Goal**: Gain expertise in specific architectural domains.

#### Real-time & Streaming Systems
- **Primary**: Event-Driven Architecture.
- **Secondary**: Space-Based Architecture.
- **Tertiary**: Pipeline Architecture.
- **Use Case**: IoT, financial trading, logistics platforms.

#### High-Throughput Web Applications
- **Primary**: Microservices.
- **Secondary**: Serverless.
- **Tertiary**: CQRS/ES.
- **Use Case**: Social media, e-commerce, content platforms.

#### Enterprise Integration
- **Primary**: Service-Based Architecture.
- **Secondary**: Hexagonal Architecture.
- **Tertiary**: Modular Monolith.
- **Use Case**: ERP systems, banking, legacy modernization.

#### Extensible Platforms
- **Primary**: Microkernel Architecture.
- **Secondary**: Plugin-based design patterns.
- **Use Case**: IDEs, marketplaces, integration platforms.

## Quick Reference Matrix

| Paradigm | Complexity | Team Size | Best For | Key Benefits | Common Use Cases |
|----------|------------|------------|-----------|--------------|------------------|
| **Layered** | Low | Small-Medium | Simple domains | Simplicity, familiarity | Basic web apps, internal tools |
| **Functional Core** | Medium | Small-Large | Complex business logic | Testability, clarity | Financial systems, rule engines |
| **Hexagonal** | Medium | Small-Large | Infrastructure changes | Flexibility, isolation | Framework migrations, integrations |
| **Modular Monolith** | Medium | Medium-Large | Evolving systems | Strong boundaries, single deploy | Growing applications, team scaling |
| **Microservices** | High | Large | Complex domains | Team autonomy, scaling | Enterprise applications, platforms |
| **Service-Based** | Medium | Medium-Large | Shared database needs | Coarse-grained services | ERPs, legacy system evolution |
| **Event-Driven** | High | Medium-Large | Real-time processing | Scalability, decoupling | IoT, analytics, notifications |
| **CQRS/ES** | High | Medium-Large | Audit requirements | Immutable history | Financial systems, collaboration |
| **Serverless** | Medium | Small-Medium | Bursty workloads | Minimal operations | APIs, cron jobs, data processing |
| **Space-Based** | High | Medium-Large | High traffic stateful | Linear scalability | Trading platforms, gaming |
| **Pipeline** | Medium | Small-Medium | ETL workflows | Stage isolation | Data processing, CI/CD |
| **Microkernel** | Medium | Small-Medium | Extensible platforms | Plugin architecture | IDEs, marketplaces, frameworks |
| **Client-Server** | Low | Small-Medium | Traditional apps | Simple deployment | Web apps, mobile backends |

## Paradigm Evolution Path

### Typical Architecture Evolution Journey

```
Startup Phase (1-10 engineers)
    ↓ Layered Architecture
Growth Phase (10-50 engineers)
    ↓ Modular Monolith
Scale Phase (50-200 engineers)
    ↓ Microservices OR Service-Based
Maturity Phase (200+ engineers)
    ↓ Event-Driven + Specialized Patterns
```

### Common Migration Paths

**From Monolith to Distributed**
```
Layered → Modular Monolith → Microservices → Event-Driven
```

**From Simple to Complex**
```
Layered → Hexagonal → Functional Core → CQRS/ES
```

**From Traditional to Cloud-Native**
```
Layered → Modular Monolith → Serverless → Event-Driven
```

### Architecture Decision Triggers

**Scale Triggers** (When to evolve architecture):
- Team size crosses threshold (5, 15, 50, 200 engineers).
- Deployment frequency needs increase.
- Independent scaling requirements emerge.
- Geographic distribution becomes necessary.

**Complexity Triggers** (When to adopt patterns):
- Business rules become complex (Functional Core).
- Integration points increase (Hexagonal).
- Real-time requirements emerge (Event-Driven).
- Audit/compliance needs arise (CQRS/ES).

**Technology Triggers** (When to change patterns):
- Framework migration needed (Hexagonal).
- Cloud migration planned (Serverless/Microservices).
- Performance bottlenecks appear (Space-Based/Pipeline).
- Platform requirements emerge (Microkernel).

## Repository Structure

```
archetypes/
├── plugin.json                              # Plugin configuration
├── README.md                               # This guide
└── skills/
    ├── architecture-paradigms/             # Main orchestrator skill
    │   └── SKILL.md                        # Interactive paradigm selection
    ├── architecture-paradigm-layered/      # Individual paradigm skills
    ├── architecture-paradigm-functional-core/
    ├── architecture-paradigm-hexagonal/
    ├── architecture-paradigm-modular-monolith/
    ├── architecture-paradigm-microservices/
    ├── architecture-paradigm-service-based/
    ├── architecture-paradigm-event-driven/
    ├── architecture-paradigm-cqrs-es/
    ├── architecture-paradigm-serverless/
    ├── architecture-paradigm-space-based/
    ├── architecture-paradigm-pipeline/
    ├── architecture-paradigm-microkernel/
    └── architecture-paradigm-client-server/
        └── SKILL.md                        # Detailed guidance
```

## Usage Guidelines

### For Architecture Reviews
```bash
# Start with paradigm selection
Skill(architecture-paradigms)

# Deep dive on specific paradigms
Skill(architecture-paradigm-hexagonal)
Skill(architecture-paradigm-microservices)
```

### For New Projects
```bash
# Use orchestrator for guided selection
Skill(architecture-paradigms)

# Load chosen paradigm for implementation
Skill(architecture-paradigm-[selected-pattern])
```

### For Legacy Modernization
```bash
# Start with modular monolith assessment
Skill(architecture-paradigm-modular-monolith)

# Plan evolution to distributed systems
Skill(architecture-paradigm-microservices)
```

## Integration with Other Skills

This collection integrates with:

- **architecture-review**: Architecture evaluation.
- **writing-plans**: Detailed implementation planning.
- **systematic-debugging**: Architecture refactoring approaches.
- **brainstorming**: Architecture design refinement.

## Community and Contributions

These patterns reflect industry standards. Each paradigm skill includes:

- Implementation patterns.
- Case studies and examples.
- Technology-specific guidance.
- Risk mitigation strategies.
- Evolution pathways.

## License

MIT License.
