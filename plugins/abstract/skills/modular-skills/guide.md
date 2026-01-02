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

This guide explains how we implement modular skills. We've found that by breaking down our skills into smaller, more manageable modules, we can create a more maintainable and predictable architecture. This guide explains how we do it.

## The Hub-and-Spoke Structure

We use a "hub-and-spoke" pattern for our modular skills. This means we have a primary "hub" skill that contains the core metadata and an overview, and then optional "spoke" submodules that contain more detailed information.

Here's an example of what the structure looks like:

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

Note: The scripts directory now contains Python wrappers that use the shared
`abstract.skill_tools` module, eliminating code duplication while providing
convenient CLI access from within skill directories.

This modular structure helps us keep our token usage down. The core workflow is only about 300 tokens, and the other modules are loaded on-demand.

## How to Use the Modules

- **If you're creating a new skill**, you should start with the `core-workflow.md` document, which will walk you through the process of evaluating the scope of your skill and designing the module architecture. Then, you can move on to the `implementation-patterns.md` document for more detailed guidance on how to implement your skill.

- **If you're migrating an existing skill**, you should start with the `antipatterns-and-migration.md` document, which will help you identify common anti-patterns and give you a plan for migrating your skill to our modular framework.

- **If you're troubleshooting a skill**, the `antipatterns-and-migration.md` document is a good place to look for common issues and their solutions.

You can find concrete examples of our modular design patterns in the `examples/` directory.
