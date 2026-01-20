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
| [attune](attune.md) | Projects | Full-cycle project development |
| [scry](scry.md) | Media | Documentation recordings |
| [scribe](scribe.md) | Documentation | AI slop detection and cleanup |

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

### attune
Use when you need to:
- Brainstorm project ideas
- Create specifications from concepts
- Plan architecture and tasks
- Initialize projects with tooling
- Execute systematic implementation

### scry
Use when you need to:
- Record terminal demos with VHS
- Capture browser sessions with Playwright
- Generate GIFs for documentation
- Compose multi-source tutorials

### scribe
Use when you need to:
- Detect AI-generated content markers
- Clean up documentation slop
- Learn and apply writing styles
- Verify documentation accuracy

## Dependencies

Most domain plugins depend on foundation layers:

```
archetypes (standalone)
pensive --> imbue, sanctum
parseltongue (standalone)
memory-palace (standalone)
spec-kit --> imbue
minister (standalone)
attune --> spec-kit, imbue
scry (standalone)
scribe --> imbue, conserve
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
/speckit-specify Add user authentication
/speckit-plan
/speckit-tasks
/speckit-implement
```

### Full Project Lifecycle
```bash
/attune:brainstorm
# Socratic questioning to explore project idea

/attune:specify
# Create specification from brainstorm

/attune:plan
# Design architecture and break down tasks

/attune:init
# Initialize project with tooling

/attune:execute
# Execute implementation with TDD
```

### Media Recording
```bash
/record-terminal
# Creates VHS tape script and records terminal to GIF

/record-browser
# Records browser session with Playwright
```

### Documentation Cleanup
```bash
/slop-scan docs/
# Scans for AI-generated content markers

/doc-polish README.md
# Interactive cleanup of AI slop

/doc-verify README.md
# Validates documentation claims
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

# Full-cycle project development
/plugin install attune@claude-night-market

# Media recording
/plugin install scry@claude-night-market

# Documentation review
/plugin install scribe@claude-night-market
```

<div class="achievement-hint" data-achievement="domain-master">
Use all domain specialist plugins to unlock: Domain Master
</div>
