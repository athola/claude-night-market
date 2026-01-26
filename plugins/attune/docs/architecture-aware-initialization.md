# Architecture-Aware Initialization

## Overview

The architecture-aware initialization system combines deep online research with proven architectural paradigms to provide intelligent project initialization recommendations.

## Key Capabilities

1. **Deep Online Research**: Generates 2026 best-practice queries for your project type
2. **Paradigm Matching**: Uses decision matrix to recommend from 14 architectural patterns
3. **Template Customization**: Creates project structures tailored to chosen architecture
4. **Decision Documentation**: Generates ADRs explaining architectural choices
5. **Implementation Guidance**: Integrates with archetypes plugin for detailed patterns

## Quick Start

```bash
# Interactive mode (recommended)
/attune:arch-init --name my-project

# You'll be prompted for:
# - Project type (web-api, cli-tool, data-pipeline, etc.)
# - Domain complexity (simple, moderate, complex, highly-complex)
# - Team size (<5, 5-15, 15-50, 50+)
# - Language (Python, Rust, TypeScript)
# - Scalability and security requirements
```

## Workflow

```
User Input (Project Context)
         ↓
   Online Research (WebSearch)
         ↓
  Paradigm Matching (Matrix + Special Cases)
         ↓
   Recommendation Presentation
         ↓
   User Confirmation
         ↓
  Template Customization
         ↓
  Project Creation + Documentation
         ↓
  Load Paradigm Skill (Implementation Guidance)
```

## Decision Matrix

The system recommends paradigms based on team size and domain complexity:

| Team/Domain | Simple | Moderate | Complex | Highly Complex |
|-------------|--------|----------|---------|----------------|
| **< 5** | Layered | Layered + Hex | Hexagonal + FC | FC + Hex |
| **5-15** | Layered | Mod. Monolith | Mod. Monolith + FC | Hex + FC |
| **15-50** | Mod. Monolith | Microservices | Microservices + Event | CQRS/ES + Event |
| **50+** | Microservices | Microservices + Event | Event-Driven | Microkernel/Space |

**Special Cases**:
- Real-time/Streaming → Event-Driven + Pipeline
- Cloud-Native/Bursty → Serverless + Microservices
- Extensible Platform → Microkernel
- Data Processing → Pipeline + Event-Driven
- Legacy Integration → Hexagonal

## Example Scenarios

### Example 1: Fintech API

**Context**: Web API, team of 8, complex domain, critical security

```bash
/attune:arch-init --name transaction-api
```

**Recommendation**: **CQRS + Event Sourcing**
- Rationale: Audit requirements, complex business logic, regulatory compliance
- Structure: `commands/`, `queries/`, `events/`, `aggregates/`

### Example 2: Data Pipeline

**Context**: ETL pipeline, team of 4, moderate complexity

```bash
/attune:arch-init --name etl-pipeline
```

**Recommendation**: **Pipeline + Event-Driven**
- Rationale: Data processing workflows, streaming requirements
- Structure: `stages/` (extract, transform, load), `pipeline/`

### Example 3: Microservice Platform

**Context**: Extensible platform, team of 25, moderate domain

```bash
/attune:arch-init --name plugin-platform --arch microkernel
```

**Recommendation**: **Microkernel Architecture**
- Rationale: Plugin architecture requirements
- Structure: Multi-service with plugin API

## Components

### 1. Core Skill

**File**: `skills/architecture-aware-init/SKILL.md`

Defines the 5-step workflow:
- Context gathering (project type, team, domain)
- Research phase (online best practices)
- Paradigm selection (algorithmic matching)
- Template customization (paradigm-specific structures)
- Documentation (ADR generation)

### 2. Architecture Researcher

**File**: `scripts/architecture_researcher.py`

Python module that:
- Defines `ProjectContext` dataclass
- Generates search queries for online research
- Implements paradigm decision matrix
- Handles special case overrides
- Identifies trade-offs for each paradigm
- Generates alternative recommendations with rejection reasons

### 3. Template Customizer

**File**: `scripts/template_customizer.py`

Creates architecture-specific directory structures for:
- Functional Core, Imperative Shell (`core/`, `adapters/`)
- Hexagonal (`domain/`, `infrastructure/`)
- Layered (`presentation/`, `business/`, `data/`)
- Microservices (multi-service layout)
- CQRS + Event Sourcing (`commands/`, `queries/`, `events/`)
- Event-Driven (`events/`, `processors/`, `sagas/`)
- Pipeline (`stages/`, `pipeline/`)

### 4. CLI Tool

**File**: `scripts/attune_arch_init.py`

Interactive command-line tool that:
- Gathers project context
- Performs research (shows WebSearch queries)
- Presents recommendations with rationale
- Creates customized project structure
- Generates documentation (ARCHITECTURE.md, ADR)

### 5. Command Documentation

**File**: `commands/attune:arch-init`

Comprehensive reference with:
- Usage examples for all modes
- Integration with attune workflow
- Available paradigms list
- Output artifacts description

## Integration

### With Archetypes Plugin

```
attune:arch-init
    ↓ (paradigm selection)
archetypes plugin (14 paradigms)
    ↓ (implementation guidance)
Skill(architecture-paradigm-{selected})
    ↓ (detailed patterns)
Implementation
```

### With Attune Workflow

```bash
/attune:brainstorm           # 1. Explore needs
/attune:arch-init            # 2. ⭐ Select architecture
Skill(architecture-paradigm-*) # 3. Load guidance
/attune:specify              # 4. Detailed specs
/attune:plan                 # 5. Implementation plan
/attune:execute              # 6. Build system
```

## Benefits

### For Users
- **Informed Decisions**: Based on 2026 best practices
- **Appropriate Architecture**: Matches team and project
- **Reduced Decision Fatigue**: Algorithmic recommendations
- **Complete Documentation**: ADRs explain the "why"
- **Implementation Guidance**: Paradigm skill integration

### For Teams
- **Shared Understanding**: ADR provides alignment
- **Evolution Path**: Clear when to evolve architecture
- **Best Practices**: Current industry standards
- **Consistency**: Repeatable process

### For Organizations
- **Architecture Governance**: Standardized process
- **Knowledge Capture**: Research sessions and ADRs
- **Risk Mitigation**: Trade-offs documented
- **Scalability**: Architecture matched to growth

## Output Artifacts

After running `/attune:arch-init`, you get:

1. **Customized Structure**: Architecture-appropriate directories
2. **Base Templates**: Language-specific configs (Makefile, CI/CD)
3. **ARCHITECTURE.md**: Paradigm overview and structure
4. **ADR**: Formal decision record with rationale
5. **Research Session**: JSON with context and queries
6. **Next Steps**: Links to paradigm skill

## Compared to /attune:project-init

| Feature | `/attune:project-init` | `/attune:arch-init` |
|---------|---------------|---------------------|
| Language Selection | ✅ | ✅ |
| Base Templates | ✅ | ✅ |
| Git Init | ✅ | ✅ |
| Architecture Decision | ❌ | ✅ |
| Online Research | ❌ | ✅ |
| Paradigm Matching | ❌ | ✅ |
| Custom Structures | ❌ | ✅ |
| ADR Generation | ❌ | ✅ |

**When to use**:
- `/attune:project-init`: When architecture is already decided
- `/attune:arch-init`: When you need architecture guidance

## Available Paradigms

All 13 architectural paradigms are fully supported with templates for Python, Rust, and TypeScript:

### Monolithic Patterns
- **layered** - Traditional N-tier separation (presentation/business/data)
- **hexagonal** - Ports & Adapters for infrastructure independence
- **functional-core** - Functional Core, Imperative Shell for testability
- **modular-monolith** - Single deployable with strong module boundaries

### Distributed Patterns
- **microservices** - Fine-grained independent services
- **service-based** - Coarse-grained distributed services (SOA-lite)
- **client-server** - Traditional centralized server with clients

### Event & Stream Patterns
- **event-driven** - Asynchronous, decoupled communication
- **cqrs-es** - Command/query separation with event sourcing
- **pipeline** - ETL processing stages for data workflows

### Scalability Patterns
- **serverless** - Function-as-a-Service with managed infrastructure
- **space-based** - In-memory data grids for extreme scalability

### Extensibility Patterns
- **microkernel** - Plugin-based extensible core system

## Next Steps

### To Use

```bash
# Interactive mode
/attune:arch-init --name your-project

# Load paradigm skill for implementation
Skill(architecture-paradigm-{selected})

# Continue workflow
/attune:specify
/attune:plan
/attune:execute
```

### To Extend

1. Add more paradigms to `STRUCTURE_TEMPLATES`
2. Integrate actual WebSearch execution
3. Add TypeScript/Rust structure templates
4. Implement ML-based paradigm matching
5. Add architecture evolution tracking

## Project Type Examples

The following examples demonstrate architecture-aware initialization for different project types:

| Example | Project Type | Recommended Architecture | Team Size |
|---------|-------------|-------------------------|-----------|
| [Fintech API](../examples/architecture-aware-example.md) | Web API | CQRS + Event Sourcing | 5-15 |
| [File Organizer](../examples/cli-tool-example.md) | CLI Tool | Layered | < 5 |
| [Analytics ETL](../examples/data-pipeline-example.md) | Data Pipeline | Pipeline + Event-Driven | 5-15 |
| [Schema Validator](../examples/library-example.md) | Library | Hexagonal | < 5 |
| [E-Commerce Platform](../examples/microservices-example.md) | Microservices | Microservices + Event-Driven | 15-50 |

Each example includes:
- Complete workflow walkthrough
- Generated project structure
- Implementation guidance with code samples
- Trade-off analysis
- Next steps for development

## See Also

- [Architecture-Aware Init Skill](../skills/architecture-aware-init/SKILL.md)
- [Archetypes Plugin](../../archetypes/README.md)
- [Project Brainstorming](brainstorm-attune-plugin.md)
