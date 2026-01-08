---
name: modular-skills-guide
description: detailed guide for implementing modular skills with hub-and-spoke architecture patterns. Use when learning modular skill design, understanding hub-and-spoke architecture, or following step-by-step implementation tutorials.
category: documentation
tags: [guide, modular-skills, architecture, implementation, patterns]
dependencies: [modular-skills]
tools: []
complexity: intermediate
estimated_tokens: 600
---

# A Guide to Implementing Modular Skills

This guide details the implementation of modular skills. Breaking skills into smaller, manageable modules creates a maintainable and predictable architecture.

## The Hub-and-Spoke Structure

The framework uses a "hub-and-spoke" pattern for modular skills. A primary "hub" skill contains core metadata and an overview, while optional "spoke" submodules contain detailed information.

Structure example:

```
modular-skills/
├── SKILL.md (this is the hub, with metadata and an overview)
├── guide.md (this file, which provides an overview of the modules)
├── modules/
│   ├── core-workflow.md (for designing new skills)
│   ├── implementation-patterns.md (for implementing skills)
│   └── antipatterns-and-migration.md (for migrating existing skills)
├── scripts/
│   ├── analyze.py (Python wrapper for skill analysis)
│   └── tokens.py (Python wrapper for token estimation)
└── examples/
    ├── basic-implementation/
    └── advanced-patterns/
```

Note: The scripts directory contains Python wrappers that use the shared `abstract.skill_tools` module, eliminating code duplication while providing convenient CLI access from within skill directories.

This modular structure reduces token usage. The core workflow consumes approximately 300 tokens, loading other modules on-demand.

## How to Use the Modules

- **For new skills**, start with `core-workflow.md` to evaluate scope and design the module architecture. Then, refer to `implementation-patterns.md` for implementation guidance.

- **For migrating existing skills**, start with `antipatterns-and-migration.md` to identify common anti-patterns and plan the migration.

- **For troubleshooting**, refer to `antipatterns-and-migration.md` for common issues and solutions.

Concrete examples of modular design patterns are available in the `examples/` directory.
