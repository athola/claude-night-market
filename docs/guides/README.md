# Claude Night Market Guides

Guides for advanced topics in the plugin ecosystem.

---

## Core Guides

### [Skills Separation: Development vs Runtime](development-vs-runtime-skills-separation.md)

**Problem**: Avoid namespace collision between development skills (Claude Code assisting you) and runtime skills (your agent's capabilities).

**You'll Learn**:
- 4 separation patterns (directory, namespace, forking, scoped loading)
- SDK integration for composing system prompts
- Complete example project structure
- Troubleshooting common issues

**Resources**:
- **Full Guide**: [development-vs-runtime-skills-separation.md](development-vs-runtime-skills-separation.md)
- **Quick Reference**: [skills-separation-quickref.md](skills-separation-quickref.md)
- **Visual Diagrams**: [skills-separation-diagram.md](skills-separation-diagram.md)

---

### [Skill Observability Guide](skill-observability-guide.md)

Minimal-dependency continual learning system using PreToolUse and PostToolUse hooks.

This system provides per-iteration skill execution logging and stability gap detection. JSONL storage enables easy querying and real-time performance monitoring. This helps build production plugins that require reliable performance metrics.

---

### [Error Handling Guide](error-handling-guide.md)

Structured exception hierarchy and error recovery patterns.

**Topics**:
- Error classification (validation, runtime, system)
- Recovery strategies
- User-friendly error messages
- Testing error scenarios

---

### [LSP Native Support](lsp-native-support.md)

Language Server Protocol integration for symbol-aware search.

**Benefits**:
- 50ms vs 45s for reference finding (900x faster)
- Symbol-aware navigation
- Reduced token usage
- Improved accuracy

**Requirements**: Claude Code v2.0.74+

---

## Architecture Guides

### [Agent Boundaries](agent-boundaries.md)

Defining clean boundaries between agents and sub-agents in multi-agent systems.

**Covers**:
- Single responsibility principle for agents
- Communication patterns
- State management
- Context isolation

---

### [Plugin Dependency Patterns](plugin-dependency-pattern.md)

Manage dependencies between plugins without tight coupling by detecting optional dependencies, using capability detection, implementing secondary strategies, and ensuring version compatibility.

---

## Integration Guides

### [Superpowers Integration](../../book/src/reference/superpowers-integration.md)

Integrating with the [obra/superpowers](https://github.com/obra/superpowers) marketplace. See the [book reference](../../book/src/reference/superpowers-integration.md) for full details.

---

## Documentation Standards

### [Documentation Standards](documentation-standards.md)

Writing high-quality documentation for plugins, skills, and commands.

**Standards**:
- README structure
- Skill documentation format
- API reference guidelines
- Example quality criteria

---

## Optimization Guides

### [Data Extraction Pattern](data-extraction-pattern.md)

Systematic approach for separating embedded data from code into YAML configuration files.

**Use when scripts contain over 100 lines of embedded data (catalogs, templates, lookup tables).**

**Benefits**:
- 75% average code reduction
- Non-programmer editable configurations
- Cleaner version control diffs
- Runtime configuration flexibility

**Five-step process**:
1. Identify embedded data
2. Extract to YAML files
3. Add deserialization functions
4. Update script to load data
5. Validate functionality preserved

**Real Examples**: 4 production refactorings achieving 3,343 → ~795 lines (10,192 tokens saved)

---

### [Optimization Patterns](../optimization-patterns.md)

Systematic methodology for context reduction in Claude Code projects.

**Result**: 28-33% context reduction through nine optimization phases (~70,772 tokens saved)

**8 Patterns**:
- Archive cleanup (high impact)
- Hub-and-spoke documentation
- Data extraction to YAML
- Shared utilities abstraction
- Examples repository pattern
- Progressive disclosure
- TODO audit
- Anti-pattern removal

**Workflow**: Discovery → Analysis → Planning → Execution → Validation

**Use When**: Project approaching context limits, quarterly maintenance, onboarding friction

---

## Quick References

| Guide | Quick Ref |
|-------|-----------|
| Skills Separation | [quickref](skills-separation-quickref.md) |
| Data Extraction | _(embedded in guide)_ |
| Optimization Patterns | _(embedded in guide)_ |
| Error Handling | _(TODO)_ |
| LSP Setup | _(TODO)_ |

---

## Contributing

Have a guide topic suggestion? Open an issue on the repository with the `documentation` label.

**Criteria for New Guides**:
- Solves a common, non-obvious problem
- Includes complete working examples
- Provides troubleshooting section
- References related plugins/skills

---

## Index

**By Topic**:
- **Skill Development**: Skills Separation, Skill Observability
- **Architecture**: Agent Boundaries, Plugin Dependencies
- **Integration**: LSP Support, Superpowers Integration
- **Quality**: Error Handling, Documentation Standards
- **Optimization**: Data Extraction Pattern, Optimization Patterns

**By Plugin**:
- abstract: Skills Separation, Skill Observability, Data Extraction
- conserve: Optimization Patterns
- pensive: Error Handling
- All plugins: Documentation Standards

---

**Last Updated**: 2026-01-10
