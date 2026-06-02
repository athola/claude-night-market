# Architecture-Aware Initialization Example

This example demonstrates the complete workflow of architecture-aware project initialization.

## Example Scenario

**Project**: Fintech Transaction API
**Team**: 8 developers (mixed experience)
**Requirements**:
- RESTful API for financial transactions
- Complex business rules (validations, limits, compliance)
- High security and auditability
- Integration with legacy banking systems
- Support for 100K+ transactions/day

## Complete Workflow

### Step 1: Brainstorming (Optional but Recommended)

```bash
/attune:brainstorm --domain "fintech transaction api"
```

**Output**: `docs/project-brief.md` with:
- Problem statement
- Constraints (security, compliance, audit requirements)
- Approaches comparison
- Selected approach: **CQRS + Event Sourcing for auditability**

### Step 2: Architecture-Aware Initialization

```bash
/attune:arch-init --name transaction-api
```

#### Interactive Session

```
════════════════════════════════════════════════════════════════
Architecture-Aware Project Initialization
════════════════════════════════════════════════════════════════

📋 Project Context
--------------------------------------------------------------

Project Type:
  1. web-api
  2. web-application
  3. cli-tool
  4. data-pipeline
  5. library
  6. microservice
  7. desktop-app
  8. mobile-app
  9. real-time-system
  10. streaming-app

Select project type (1-10) or enter custom: 1

Domain Complexity:
  1. Simple
  2. Moderate
  3. Complex
  4. Highly-Complex

Select complexity (1-4): 3

Team Size:
  1. < 5
  2. 5-15
  3. 15-50
  4. 50+

Select team size (1-4): 2

Programming Language:
  1. Python
  2. Rust
  3. TypeScript

Select language (1-3): 1

Framework (optional, press Enter to skip): fastapi

Scalability Needs:
  1. Low (< 1000 users)
  2. Moderate (< 100K users)
  3. High (< 1M users)
  4. Extreme (> 1M users)

Select scalability (1-4, default 2): 3

Security Requirements:
  1. Standard
  2. High
  3. Critical (finance, health, etc.)

Select security level (1-3, default 1): 3

Time to Market:
  1. Rapid (ASAP)
  2. Normal
  3. Not Urgent

Select timeline (1-3, default 2): 2
```

#### Research Phase

```
════════════════════════════════════════════════════════════════
🔍 Online Research Phase
════════════════════════════════════════════════════════════════

For thorough research, run these queries:

1. web-api architecture best practices 2026
   WebSearch("web-api architecture best practices 2026")

2. python web-api architecture patterns 2026
   WebSearch("python web-api architecture patterns 2026")

3. fastapi architecture patterns web-api
   WebSearch("fastapi architecture patterns web-api")

4. complex domain architecture patterns python
   WebSearch("complex domain architecture patterns python")

5. secure architecture patterns web-api
   WebSearch("secure architecture patterns web-api")

6. scalable architecture patterns web-api
   WebSearch("scalable architecture patterns web-api")

------------------------------------------------------------
⚠️  Note: In actual usage, Claude would run WebSearch for each query.
For now, proceeding with algorithmic recommendation.
```

#### Recommendation

```
════════════════════════════════════════════════════════════════
🎯 Architecture Recommendation
════════════════════════════════════════════════════════════════

Primary Paradigm: **Cqrs Es**
Secondary Paradigm: Event Driven

Confidence: HIGH

📝 Rationale:
**Selected Based On**: matrix selection
**Team Size**: 5-15
**Domain Complexity**: complex
**Project Type**: web-api

⚖️  Trade-offs:
  - **Complexity and eventual consistency**: Start with single bounded context, evolve as needed

🔄 Alternatives Considered:
  - **Layered**: Audit requirements don't justify CQRS complexity
  - **Hexagonal**: CQRS/ES better fits audit requirements
  - **Functional Core, Imperative Shell**: CQRS/ES better fits audit requirements

════════════════════════════════════════════════════════════════

Accept this recommendation? [y/N]: y
```

#### Template Customization

```
════════════════════════════════════════════════════════════════
🏗️  Customizing Templates
════════════════════════════════════════════════════════════════

Architecture: CQRS + Event Sourcing - separate reads/writes with audit trail
```

#### Project Creation

```
════════════════════════════════════════════════════════════════
📁 Creating Project Structure
════════════════════════════════════════════════════════════════

✓ Git repository initialized: /path/to/transaction-api/.git
✓ Created: .gitignore
✓ Created: .pre-commit-config.yaml
✓ Created: Makefile
✓ Created: pyproject.toml
✓ Created: .github/workflows/test.yml
✓ Created: .github/workflows/lint.yml
✓ Created: .github/workflows/typecheck.yml
✓ Created: src/transaction_api/__init__.py
✓ Created: tests/__init__.py

✓ Created 6 architecture-specific directories

════════════════════════════════════════════════════════════════
📚 Generating Documentation
════════════════════════════════════════════════════════════════

✓ Created: ARCHITECTURE.md
✓ Created: docs/adr/001-architecture-paradigm.md
✓ Created: .attune/arch-init-session.json
```

#### Completion

```
════════════════════════════════════════════════════════════════
✓ Architecture-Aware Initialization Complete!
════════════════════════════════════════════════════════════════

Project: transaction-api
Architecture: Cqrs Es
Secondary: Event Driven

📁 Created 11 files
📁 Created 6 architecture-specific directories

📚 Documentation:
  - ARCHITECTURE.md - Architecture overview
  - docs/adr/001-architecture-paradigm.md - Decision record

🔗 Next Steps:
  1. cd transaction-api
  2. make dev-setup
  3. Review ARCHITECTURE.md for implementation guidance
  4. Load paradigm skill: Skill(architecture-paradigm-cqrs-es)

════════════════════════════════════════════════════════════════
```

### Step 3: Review Generated Artifacts

#### ARCHITECTURE.md

```markdown
# Architecture

This project uses **Cqrs Es Architecture**.

## Overview

CQRS + Event Sourcing - separate reads/writes with audit trail

## Structure

- `src/transaction_api/commands/__init__.py`
- `src/transaction_api/commands/handlers.py`
- `src/transaction_api/queries/__init__.py`
- `src/transaction_api/queries/handlers.py`
- `src/transaction_api/queries/projections.py`
- `src/transaction_api/events/__init__.py`
- `src/transaction_api/events/store.py`
- `src/transaction_api/aggregates/__init__.py`
- `src/transaction_api/aggregates/base.py`

## Implementation

For detailed implementation guidance, see:
```bash
Skill(architecture-paradigm-cqrs-es)
```

## Key Principles

1. **Separation of Concerns**: Clear boundaries between layers/components
2. **Testability**: Architecture enables thorough testing
3. **Maintainability**: Structure supports evolution and growth
4. **Documentation**: Keep architectural decisions documented

## Evolution

As the project grows, consider:
- Monitoring architecture metrics
- Periodic architecture reviews
- Evolution patterns to next paradigm if needed
```

#### docs/adr/001-architecture-paradigm.md

```markdown
# Architecture Decision Record: Cqrs Es

## Date
2026-01-02

## Status
Accepted

## Context
This project required an architecture that supports:
- Team size and structure
- Domain complexity
- Technology choices
- Scalability and performance requirements

## Decision
Adopted **Cqrs Es Architecture**.

## Rationale
CQRS + Event Sourcing - separate reads/writes with audit trail

### Key Benefits
- Clear separation of concerns
- Improved testability
- Better maintainability
- Support for team growth

### Trade-offs
- **Complexity and eventual consistency**: Start with single bounded context, evolve as needed

## Implementation
- **Structure**: See ARCHITECTURE.md for detailed structure
- **Patterns**: Follow guidance in `Skill(architecture-paradigm-cqrs-es)`
- **Examples**: Refer to paradigm skill for case studies

## Consequences
### Positive
- Architecture supports current and future needs
- Clear boundaries enable independent testing and evolution
- Team can work autonomously within boundaries

### Negative
- [Potential downsides and mitigations]

## References
- Paradigm skill: `Skill(architecture-paradigm-cqrs-es)`
- Architecture documentation: ARCHITECTURE.md
```

#### .attune/arch-init-session.json

```json
{
  "context": {
    "project_type": "web-api",
    "domain_complexity": "complex",
    "team_size": "5-15",
    "language": "python"
  },
  "search_queries": [
    "web-api architecture best practices 2026",
    "python web-api architecture patterns 2026",
    "fastapi architecture patterns web-api",
    "complex domain architecture patterns python",
    "secure architecture patterns web-api",
    "scalable architecture patterns web-api"
  ],
  "research_results": {}
}
```

### Step 4: Load Paradigm Skill for Implementation

```bash
# Within the transaction-api directory
cd transaction-api

# Load the CQRS/ES paradigm skill for implementation guidance
Skill(architecture-paradigm-cqrs-es)
```

This provides:
- Detailed implementation patterns
- Code examples
- Testing strategies
- Technology recommendations
- Anti-patterns to avoid

### Step 5: Continue with Standard Workflow

```bash
# Create detailed specification
/attune:specify

# Plan implementation tasks
/attune:blueprint

# Execute implementation
/attune:execute
```

## Result: Production-Ready CQRS/ES Project

```
transaction-api/
├── .attune/
│   └── arch-init-session.json          # Research context
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── lint.yml
│       └── typecheck.yml
├── docs/
│   └── adr/
│       └── 001-architecture-paradigm.md # Decision record
├── src/
│   └── transaction_api/
│       ├── commands/                   # Write operations
│       │   ├── __init__.py
│       │   └── handlers.py
│       ├── queries/                    # Read operations
│       │   ├── __init__.py
│       │   ├── handlers.py
│       │   └── projections.py
│       ├── events/                     # Event store
│       │   ├── __init__.py
│       │   └── store.py
│       ├── aggregates/                 # Domain aggregates
│       │   ├── __init__.py
│       │   └── base.py
│       └── __init__.py
├── tests/
│   └── __init__.py
├── .gitignore
├── .pre-commit-config.yaml
├── ARCHITECTURE.md                     # Architecture overview
├── Makefile
├── pyproject.toml
└── README.md
```

## Key Benefits of This Approach

1. **Informed Decisions**: Based on 2026 best practices research
2. **Appropriate Architecture**: Matches team size and domain complexity
3. **Customized Structure**: Directories tailored to chosen paradigm
4. **Documented Rationale**: Clear ADR explaining the choice
5. **Implementation Guidance**: Links to paradigm skills for detailed guidance
6. **Evolution Path**: Clear understanding of when/how to evolve architecture

## Comparison: Traditional vs Architecture-Aware

### Traditional Init (`/attune:project-init`)

```bash
/attune:project-init --name transaction-api --lang python
```

**Result**: Generic Python project structure
- `src/transaction_api/`
- `tests/`
- Standard configs
- **No architecture guidance**

### Architecture-Aware Init (`/attune:arch-init`)

```bash
/attune:arch-init --name transaction-api
```

**Result**: Architecture-optimized Python project structure
- `src/transaction_api/commands/`
- `src/transaction_api/queries/`
- `src/transaction_api/events/`
- `src/transaction_api/aggregates/`
- `ARCHITECTURE.md` with CQRS/ES guidance
- `docs/adr/001-architecture-paradigm.md`
- **Complete architecture decision framework**
