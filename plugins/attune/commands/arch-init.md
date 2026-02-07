---
name: arch-init
description: "Initialize projects with architecture-aware templates using paradigm research and selection guidance"
usage: /attune:arch-init [--name NAME] [--lang python|rust|typescript] [--arch PARADIGM]
---

# Attune Architecture-Aware Init Command

Research-driven project initialization that selects appropriate architectural paradigms based on project needs.

## When To Use

Use this command when you need to:
- Start a new project with architecture guidance
- Choose between architectural paradigms (hexagonal, clean, etc.)
- Get research-backed architecture recommendations
- Initialize project with paradigm-specific templates
- Understand trade-offs of different architectures

## When NOT To Use

Avoid this command if:
- Architecture already decided (use `/attune:project-init` directly)
- Simple project without architectural complexity
- Modifying existing project structure
- Standard patterns sufficient without special architecture

## Usage

```bash
# Interactive mode (recommended) - guides through architecture selection
/attune:arch-init --name my-project

# Specify language and let it recommend architecture
/attune:arch-init --name my-project --lang python

# Specify both language and architecture
/attune:arch-init --name my-project --lang python --arch hexagonal

# Accept recommended architecture without prompting
/attune:arch-init --name my-project --lang python --accept-recommendation
```

## What This Command Does

1. **Gathers project context**:
   - Project type (Web API, CLI, data pipeline, etc.)
   - Domain complexity
   - Team size and experience
   - Non-functional requirements
   - Timeline constraints

2. **Researches best practices**:
   - Searches for current industry standards (2026)
   - Identifies emerging patterns
   - Notes anti-patterns to avoid
   - Finds technology-specific considerations

3. **Recommends architecture paradigm** from 14 available options:
   - Layered Architecture
   - Functional Core, Imperative Shell
   - Hexagonal (Ports & Adapters)
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

4. **Customizes templates** based on chosen paradigm

5. **Creates Architecture Decision Record (ADR)** documenting the choice

## When to Use This vs project-init

| Scenario | Command |
|----------|---------|
| Architecture already decided | `/attune:project-init` |
| Need architecture guidance | `/attune:arch-init` |
| Exploring multiple architectures | Use `Skill(archetypes:architecture-paradigms)` first |
| Quick setup with defaults | `/attune:project-init` |

## Workflow

```bash
# 1. Invoke skill to guide architecture-aware initialization
Skill(attune:architecture-aware-init)

# 2. The skill will:
#    - Gather project context
#    - Research best practices online
#    - Recommend paradigm based on decision matrix
#    - Customize templates for chosen paradigm
#    - Create ADR

# 3. After architecture selected, initializes project
python3 plugins/attune/scripts/attune_arch_init.py \
  --name my-project \
  --lang python \
  --arch hexagonal
```

## Arguments

- `--name <name>` - Project name
- `--lang <language>` - Project language (python, rust, typescript)
- `--arch <paradigm>` - Architecture paradigm (e.g., hexagonal, functional-core, cqrs-es)
- `--accept-recommendation` - Accept recommended architecture without prompting
- `--skip-research` - Skip online research phase (use decision matrix only)

## Architecture Decision Matrix

The command uses a decision matrix based on team size and domain complexity:

| Team Size | Simple Domain | Moderate | Complex | Highly Complex |
|-----------|---------------|----------|---------|----------------|
| < 5       | Layered       | Layered/Hexagonal | Hexagonal | Functional Core |
| 5-15      | Layered       | Modular Monolith | Modular Monolith | Hexagonal + FC |
| 15-50     | Modular Monolith | Microservices | Microservices | CQRS/ES |
| 50+       | Microservices | Microservices | Event-Driven | Space-Based |

## Examples

### Example 1: Web API for Fintech

```bash
/attune:arch-init --name payment-service --lang python
```

Interactive flow:
```
Project type: Web API
Domain complexity: Highly Complex (fintech regulations)
Team size: 8 engineers
Requirements: Audit trails, security, compliance

Research results:
- CQRS/Event Sourcing recommended for audit requirements
- Hexagonal also suitable for clean separation

Recommended: CQRS + Event Sourcing
Rationale: Complete audit trail via event log, complex business rules...

Accept recommendation? [Y/n]: y

Creating project structure for CQRS/ES architecture...
```

### Example 2: CLI Tool with Explicit Architecture

```bash
/attune:arch-init --name my-cli --lang python --arch functional-core
```

Creates Functional Core, Imperative Shell structure:
```
my-cli/
├── src/
│   └── my_cli/
│       ├── core/           # Pure business logic
│       │   ├── domain.py
│       │   ├── operations.py
│       │   └── commands.py
│       └── adapters/       # Side effects
│           ├── cli.py
│           ├── filesystem.py
│           └── config.py
├── tests/
├── docs/
│   └── adr/
│       └── 001-functional-core-architecture.md
└── ...
```

## Output

After completion, you'll have:

1. **Project structure** customized to chosen architecture
2. **Configuration files** with architecture-appropriate settings
3. **ADR document** explaining the architecture choice
4. **Links to paradigm skill** for implementation guidance

## Related Commands

- `/attune:project-init` - Standard initialization (when architecture is decided)
- `/attune:brainstorm` - Explore project needs before architecture selection
- `/attune:war-room` - Multi-expert deliberation for complex decisions

## Related Skills

- `Skill(attune:architecture-aware-init)` - Full architecture-aware flow
- `Skill(archetypes:architecture-paradigms)` - Paradigm selection guide
- `Skill(archetypes:architecture-paradigm-*)` - Specific paradigm implementation
