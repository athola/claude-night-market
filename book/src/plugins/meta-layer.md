# Meta Layer

The meta layer provides infrastructure for building, evaluating, and maintaining plugins themselves.

## Purpose

While other layers focus on user-facing workflows, the meta layer focuses on:

- **Plugin Development**: Tools for creating new skills, commands, and hooks
- **Quality Assurance**: Evaluation frameworks for plugin quality
- **Architecture Guidance**: Patterns for modular, maintainable plugins

## Plugins

| Plugin | Description |
|--------|-------------|
| [abstract](abstract.md) | Meta-skills infrastructure for plugin development |

## When to Use

Use meta layer plugins when:

- Creating a new plugin for the marketplace
- Evaluating existing skill quality
- Refactoring large skills into modules
- Validating plugin structure before publishing

## Key Capabilities

### Plugin Validation
```bash
/validate-plugin [path]
```
Checks plugin structure against official requirements.

### Skill Creation
```bash
/create-skill
```
Scaffolds new skills using best practices and TDD methodology.

### Quality Assessment
```bash
/skills-eval
```
Scores skill quality and suggests improvements.

## Architecture Position

```
Meta Layer
    |
    v
Foundation Layer (imbue, sanctum, leyline)
    |
    v
Utility Layer (conservation, conjure)
    |
    v
Domain Specialists
```

The meta layer sits above all others, providing tools to build and maintain the entire ecosystem.
