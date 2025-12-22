---
name: architecture-paradigms
description: |
  Interactive selector and implementation planner for architecture paradigms.

  Triggers: architecture selection, pattern comparison, system design, ADR creation,
  architecture decision, paradigm evaluation, new system architecture, architecture
  planning, which architecture, compare architectures

  Use when: selecting architecture patterns for new systems, comparing paradigm
  trade-offs, creating architecture decision records, evaluating architecture fit
  for team size and domain complexity, planning implementation roadmaps

  DO NOT use when: implementing a specific known paradigm - use the specific
  architecture-paradigm-* skill (hexagonal, layered, microservices, etc.) instead.
  DO NOT use when: reviewing existing architecture - use architecture-review instead.

  Use this skill BEFORE making architecture decisions. Check even if unsure about needs.
version: 1.0.0
category: architecture-decision
tags: [architecture, patterns, selection, implementation, adr]
dependencies: [architecture-paradigm-functional-core, architecture-paradigm-hexagonal, architecture-paradigm-cqrs-es, architecture-paradigm-event-driven, architecture-paradigm-layered, architecture-paradigm-modular-monolith, architecture-paradigm-microkernel, architecture-paradigm-microservices, architecture-paradigm-service-based, architecture-paradigm-space-based, architecture-paradigm-pipeline, architecture-paradigm-serverless, architecture-paradigm-client-server]
tools: [paradigm-selector, implementation-planner, compatibility-checker]
usage_patterns:
  - paradigm-selection
  - architecture-review
  - implementation-planning
  - adr-creation
complexity: intermediate
estimated_tokens: 560
---

# Architecture Paradigm Selector & Implementation Planner

## Quick Start

**For decisions**: Jump to Common Scenarios (below) or use the selection matrix.

**For planning**: Complete the 3-step workflow to generate implementation roadmaps.

## Common Scenarios

### Enterprise Application with Multiple Teams
**Primary**: Microservices or Modular Monolith
**Secondary**: Hexagonal for infrastructure independence

### Complex Business Rules & Testing
**Primary**: Functional Core, Imperative Shell
**Secondary**: Hexagonal for external integrations

### Real-time/Event Processing
**Primary**: Event-Driven Architecture
**Secondary**: CQRS + Event Sourcing for audit trails

### Legacy System Modernization
**Primary**: Hexagonal (Ports & Adapters)
**Secondary**: Modular Monolith as interim step

### Cloud-Native/Bursty Workloads
**Primary**: Serverless
**Secondary**: Microservices for sustained workloads

### ETL/Data Processing Pipeline
**Primary**: Pipeline Architecture
**Secondary**: Event-Driven for streaming

---

## Required TodoWrite Items
1. `paradigms:needs-defined`
2. `paradigms:paradigms-evaluated`
3. `paradigms:roadmap-created`

## 3-Step Selection Workflow

### Step 1: Define Your Needs (`paradigms:needs-defined`)

**Primary Concerns** (select all):
- [ ] **Testability**: Isolate business logic from infrastructure
- [ ] **Team Autonomy**: Independent deployment capabilities
- [ ] **Infrastructure Flexibility**: Swap databases/frameworks easily
- [ ] **Real-time Scaling**: Variable loads with event processing
- [ ] **Simplicity**: Maintainable without distributed complexity
- [ ] **Legacy Integration**: Work with existing systems

**System Context**:
- **Team Size**: `< 5` | `5-15` | `15-50` | `50+`
- **Domain Complexity**: `Simple` | `Moderate` | `Complex` | `Highly Complex`

### Step 2: Evaluate Paradigms (`paradigms:paradigms-evaluated`)

**Testability & Business Logic**
- **Primary**: Functional Core, Imperative Shell - Isolates business logic from infrastructure
- **Alternative**: Hexagonal/Ports & Adapters - Clear domain/infrastructure boundaries

**Team Autonomy**
- **Primary**: Microservices - Independent deployment and scaling
- **Alternative**: Modular Monolith - Team autonomy without distributed complexity

**Infrastructure Flexibility**
- **Primary**: Hexagonal/Ports & Adapters - Swap infrastructure without domain changes

**Simplicity & Maintainability**
- **Primary**: Layered Architecture - Simple, well-understood separation

**Real-time Event Processing**
- **Primary**: Event-Driven Architecture - Scalable, decoupled processing

### Step 3: Generate Implementation Roadmap (`paradigms:roadmap-created`)

**Implementation Steps**:
1. Load the specific paradigm skill for detailed guidance
2. Generate ADR template using the paradigm's templates
3. Create migration checklist for existing systems
4. Estimate effort and timeline based on team size and complexity
5. Identify risks and mitigations specific to your context

**Load paradigm skills for implementation**:
- `architecture-paradigm-functional-core` - Business logic isolation
- `architecture-paradigm-hexagonal` - Infrastructure independence
- `architecture-paradigm-microservices` - Independent services
- `architecture-paradigm-event-driven` - Event processing
- `architecture-paradigm-layered` - N-tier separation
- `architecture-paradigm-cqrs-es` - Command query separation with audit trails
- `architecture-paradigm-modular-monolith` - Single deployable with strong boundaries
- `architecture-paradigm-service-based` - Coarse-grained services with shared database
- `architecture-paradigm-serverless` - Stateless functions with minimal infrastructure
- `architecture-paradigm-microkernel` - Plugin architecture for extensible platforms
- `architecture-paradigm-space-based` - In-memory data grids for linear scalability
- `architecture-paradigm-pipeline` - Processing stages for ETL workflows
- `architecture-paradigm-client-server` - Traditional client-server architectures

## Paradigm Comparison Matrix

| Paradigm | Complexity | Team Size | Best For | Main Benefits |
|----------|------------|------------|----------|---------------|
| **Functional Core** | Medium | Small-Large | Complex business logic | Testability, clarity |
| **Hexagonal** | Medium | Small-Large | Infrastructure changes | Flexibility, isolation |
| **Layered** | Low | Small-Medium | Simple domains | Simplicity, familiarity |
| **Modular Monolith** | Medium | Medium-Large | Evolving systems | Boundaries, single deploy |
| **Microservices** | High | Large | Complex domains | Autonomy, scaling |
| **Event-Driven** | High | Medium-Large | Real-time processing | Scalability, decoupling |

## Future Tooling

### Paradigm Selector Tool
```bash
# Interactive paradigm selection
paradigm-selector --interactive --team-size 5-15 --complexity moderate

# Compare specific paradigms
paradigm-selector --compare functional-core hexagonal --context current-project

# Get recommendations based on concerns
paradigm-selector --concerns testability,team-autonomy --scale medium
```

### Implementation Planner Tool
```bash
# Generate a detailed roadmap
implementation-planner --paradigm hexagonal --project-size large --team-count 3

# Estimate effort and timeline
implementation-planner --paradigm microservices --complexity high --effort-estimate

# Risk assessment
implementation-planner --paradigm event-driven --context financial --risk-analysis
```

### Compatibility Checker Tool
```bash
# Check paradigm combinations
compatibility-checker --paradigms functional-core,hexagonal --validate

# Migration path analysis
compatibility-checker --from layered --to hexagonal --migration-path

# Team readiness assessment
compatibility-checker --paradigm microservices --team-profile current-team
```

## Integration with Other Skills

### During Architecture Review
- Load this skill first to select paradigms.
- Then load `/architecture-review` for evaluation.
- Use specific paradigm skills for implementation guidance.

### During Implementation Planning
- Load this skill for paradigm selection and roadmap creation.
- Load `/writing-plans` for detailed task breakdown.
- Use paradigm-specific skills for implementation checklists.

### During Refactoring
- Load this skill to identify target paradigms.
- Load `systematic-debugging` for a refactoring approach.
- Use paradigm-specific skills for migration strategies.

## Exit Criteria
- TodoWrite items are completed.
- At least one paradigm is selected with a clear rationale.
- An implementation roadmap has been generated.
- The specific paradigm skill has been loaded for detailed guidance.
- Follow-up ADR and documentation tasks have been identified.

## Next Steps
1. **Load the specific paradigm skill** for implementation guidance.
2. **Generate an ADR** using the paradigm templates.
3. **Create an implementation plan** with detailed tasks and timelines.
4. **Set up monitoring** for the success metrics of the paradigm adoption.
