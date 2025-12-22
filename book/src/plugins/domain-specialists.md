# Domain Specialists

Domain specialist plugins provide deep expertise in specific areas of software development.

## Purpose

Domain plugins offer:

- **Deep Expertise**: Specialized knowledge for specific domains
- **Workflow Automation**: End-to-end processes for common tasks
- **Best Practices**: Curated patterns and anti-patterns

## Plugins

| Plugin | Domain | Key Use Case |
|--------|--------|--------------|
| [archetypes](archetypes.md) | Architecture | Paradigm selection |
| [pensive](pensive.md) | Code Review | Multi-faceted reviews |
| [parseltongue](parseltongue.md) | Python | Modern Python development |
| [memory-palace](memory-palace.md) | Knowledge | Spatial memory organization |
| [spec-kit](spec-kit.md) | Specifications | Spec-driven development |
| [minister](minister.md) | Releases | Initiative tracking |

## When to Use

### archetypes
Use when you need to:
- Choose an architecture for a new system
- Evaluate trade-offs between patterns
- Get implementation guidance for a paradigm

### pensive
Use when you need to:
- Conduct thorough code reviews
- Audit security and architecture
- Review APIs, tests, or Makefiles

### parseltongue
Use when you need to:
- Write modern Python (3.12+)
- Implement async patterns
- Package projects with uv
- Profile and optimize performance

### memory-palace
Use when you need to:
- Organize complex knowledge
- Build spatial memory structures
- Maintain digital gardens
- Cache research efficiently

### spec-kit
Use when you need to:
- Define features before implementation
- Generate structured task lists
- Maintain specification consistency
- Track implementation progress

### minister
Use when you need to:
- Track GitHub initiatives
- Monitor release readiness
- Generate stakeholder reports

## Dependencies

Most domain plugins depend on foundation layers:

```
archetypes (standalone)
pensive --> imbue, sanctum
parseltongue (standalone)
memory-palace (standalone)
spec-kit --> imbue
minister (standalone)
```

## Example Workflows

### Architecture Decision
```bash
Skill(archetypes:architecture-paradigms)
# Interactive paradigm selection
# Returns: Detailed implementation guide
```

### Full Code Review
```bash
/full-review
# Runs multiple review types:
# - architecture-review
# - api-review
# - bug-review
# - test-review
```

### Python Project Setup
```bash
Skill(parseltongue:python-packaging)
Skill(parseltongue:python-testing)
```

### Feature Development
```bash
/speckit.specify Add user authentication
/speckit.plan
/speckit.tasks
/speckit.implement
```

## Installation

Install based on your needs:

```bash
# Architecture work
/plugin install archetypes@claude-night-market

# Code review
/plugin install pensive@claude-night-market

# Python development
/plugin install parseltongue@claude-night-market

# Knowledge management
/plugin install memory-palace@claude-night-market

# Specification-driven development
/plugin install spec-kit@claude-night-market

# Release management
/plugin install minister@claude-night-market
```

<div class="achievement-hint" data-achievement="domain-master">
Use all domain specialist plugins to unlock: Domain Master
</div>
