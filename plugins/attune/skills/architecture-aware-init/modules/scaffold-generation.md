---
module: scaffold-generation
category: project-scaffolding
dependencies: []
estimated_tokens: 800
---

# Scaffold Generation

Steps 4-5 of the architecture-aware-init workflow: customize
project templates to the chosen paradigm, then record the
decision in an ADR.

## Step 4: Customize Templates

Adaptation strategy:

1. Load base templates for the chosen language (Python, Rust,
   TypeScript, etc.).
2. Apply paradigm-specific modifications.
3. Generate configuration that reflects the architectural
   choices (test layout, dependency hints, lint targets).
4. Create an in-repo doc explaining the architecture for future
   contributors.

### Example: Functional Core, Imperative Shell

```
src/
├── core/                    # Pure business logic
│   ├── domain.py            # Domain models
│   ├── operations.py        # Pure functions
│   └── commands.py          # Command objects
└── adapters/                # Side effects
    ├── database.py          # DB operations
    ├── api.py               # HTTP operations
    └── filesystem.py        # File operations
```

### Example: Hexagonal Architecture

```
src/
├── domain/                  # Business logic (no framework deps)
│   ├── models.py
│   ├── services.py
│   └── ports/               # Interfaces
│       ├── input.py         # Use cases
│       └── output.py        # Repository interfaces
└── infrastructure/          # Framework-specific code
    ├── persistence/         # Repositories
    ├── web/                 # Controllers
    └── messaging/           # Event handlers
```

### Example: Microservices

```
project/
├── services/
│   ├── service-a/           # Independent service
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── service-b/           # Independent service
│       ├── src/
│       ├── tests/
│       ├── Dockerfile
│       └── pyproject.toml
├── api-gateway/
├── shared/
│   └── events/
└── docker-compose.yml
```

For paradigms not shown, consult the corresponding
`archetypes:architecture-paradigm-{name}` skill for the canonical
template.

Mark `arch-init:templates-customized` once the directory layout
matches the paradigm and the documentation is in place.

## Step 5: Architecture Decision Record

Generate an ADR using this template:

```markdown
# Architecture Decision Record: [Paradigm Name]

## Date
[Current date]

## Status
Accepted | Proposed | Deprecated | Superseded by [link]

## Context
[Project type, team size, domain complexity, key requirements]

## Decision
[Chosen architecture paradigm]

## Rationale

### Research Findings
[Summarize the brief produced in Step 2]

### Key Considerations
- Team Fit: [why this matches team size and experience]
- Domain Fit: [why this matches problem complexity]
- Technology Fit: [why this works with the chosen stack]
- Scalability: [how this addresses scaling needs]

### Alternatives Considered
1. [Alternative 1]: rejected because [reason]
2. [Alternative 2]: rejected because [reason]

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Trade-off 1] with mitigation: [strategy]
- [Trade-off 2] with mitigation: [strategy]

## Implementation
- Templates: [which templates were customized]
- Key Patterns: [patterns to follow]
- Anti-Patterns: [what to avoid]
- Resources: [links to paradigm skill, examples, references]

## References
- [Paradigm skill link]
- [Research sources from Step 2]
- [Example projects]
```

Mark `arch-init:decision-recorded` once the ADR is committed in
the repo (typically `docs/adr/0001-architecture-choice.md`).
