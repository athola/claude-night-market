---
name: modular-skills
description: Design skills as modular building blocks for predictable token usage and maintainable architecture. Use when creating new skills that need modular structure, refactoring large skills into components, or optimizing skill token consumption.
category: workflow-optimization
tags: [architecture, modularity, tokens, skills, design-patterns]
dependencies: []
tools: [skill-analyzer, token-estimator, module-validator]
usage_patterns:
  - skill-design
  - architecture-review
  - token-optimization
  - refactoring-workflows
complexity: intermediate
estimated_tokens: 1200
---

# Modular Skills Design

## Overview

This skill provides a framework for designing modular skills that maintain predictable token usage and sustainable architecture. It helps users break down complex, monolithic skills into focused, manageable modules that are easier to test, maintain, and optimize.

The framework implements progressive disclosure principles where skills start with essential information and provide deeper details only when needed. This approach keeps context windows efficient while ensuring comprehensive functionality is available when required.

### Key Benefits

- **Predictable Resource Usage**: Modular design keeps token consumption under control and performance consistent
- **Maintainable Architecture**: Shallow dependencies and clear boundaries make skills easier to understand and modify
- **Scalable Development**: Hub-and-spoke model allows skills to grow without becoming unwieldy
- **Better Testing**: Focused modules are easier to test in isolation and compose into larger workflows
- **Tool Integration**: Executable components automate common patterns and reduce manual overhead

### Core Components

- **skill-analyzer**: Complexity analysis and modularization recommendations
- **token-estimator**: Usage forecasting and cost optimization guidance
- **module-validator**: Structural quality checks and compliance validation

### Design Principles

- **Single Responsibility**: Each module serves one clear purpose
- **Loose Coupling**: Minimal dependencies between modules
- **High Cohesion**: Related functionality grouped together
- **Clear Boundaries**: Well-defined interfaces and responsibilities

## What It Is

This skill provides a framework for designing modular skills. We've found that by breaking down large, complex skills into smaller, more manageable modules, we can create a more maintainable and predictable architecture. This approach also helps us keep our token usage in check.

This skill is based on Anthropic's Agent Skills best practices, and it's built around the idea of progressive disclosure: start with a high-level overview, and then provide more detail as needed.

## Quick Start

### Skill Analysis
```bash
# Check if your skill needs modularization (works from skill directory)
python scripts/analyze.py

# Analyze with custom threshold (default: 150 lines)
python scripts/analyze.py --threshold 100

# Or import directly in Python:
from abstract.skill_tools import analyze_skill
analysis = analyze_skill(".", threshold=100)
```

### Token Usage Planning
```bash
# Estimate token consumption for your skill (works from skill directory)
python scripts/tokens.py

# Or import directly in Python:
from abstract.skill_tools import estimate_tokens
tokens = estimate_tokens("SKILL.md")
```

### Module Validation
```bash
# Validate modular structure and patterns
python scripts/abstract_validator.py --scan

# Generate full validation report
python scripts/abstract_validator.py --report

# Auto-fix issues (dry run first)
python scripts/abstract_validator.py --fix --dry-run
```

### Implementation Workflow
1. **Assess**: Use `skill_analyzer.py` to identify complexity and modularization needs
2. **Design**: Break large skills into focused modules based on single responsibility
3. **Estimate**: Use `token_estimator.py` to optimize for context window efficiency
4. **Validate**: Run `abstract_validator.py` to ensure proper structure and patterns
5. **Iterate**: Refine based on validation feedback and usage patterns

## When to Use It

**Use this skill when you're designing or restructuring skills**

 **Perfect for:**
- Creating new skills that will be >150 lines or cover multiple distinct topics
- Breaking down complex, monolithic skills into focused, maintainable modules
- Planning skill architecture with predictable token usage
- Refactoring overlapping skills into clear, single-responsibility modules
- Architecture reviews and maintainability planning

 **Don't use when:**
- Just evaluating existing skill quality (use skills-eval instead)
- Writing prose for humans (use writing-clearly-and-concisely)
- Need specific improvement recommendations (use skills-eval's improvement-suggester)

**Key differentiator:** This skill focuses on **design patterns and architecture**, while skills-eval focuses on **evaluation and improvement**.

### Integration with skills-eval
1. Use **skills-eval** first to identify what needs improvement
2. Switch to **modular-skills** for architectural changes
3. Return to **skills-eval** for quality validation

## Common Tasks

Here are a few common ways we use the tools:

- **To assess the complexity of a skill**, use the `skill-analyzer`. This helps us decide if a skill needs to be modularized.
- **To design the modules**, we follow the detailed workflow in the `guide.md`.
- **To see examples of how to implement the patterns**, we reference the `../../docs/examples/modular-skills/` directory.
- **To validate the structure of our modules**, we run the `module-validator` before deploying.
- **To estimate token usage**, we use the `token-estimator`. This helps us make design decisions based on their impact on the context window.

## Detailed Resources

For comprehensive implementation details and advanced techniques:

- **Core Workflow**: See `modules/core-workflow.md` for detailed modularization process
- **Implementation Patterns**: See `modules/implementation-patterns.md` for coding and structure patterns
- **Migration Guide**: See `modules/antipatterns-and-migration.md` for converting existing skills
- **Design Philosophy**: See `modules/design-philosophy.md` for underlying principles and thinking
- **Troubleshooting**: See `modules/troubleshooting.md` for common issues and solutions
- **Tools**: Python analysis utilities in `../../scripts/` directory:
  - `skill_analyzer.py` - Complexity analysis and recommendations
  - `token_estimator.py` - Token usage estimation with dependencies
  - `abstract_validator.py` - Pattern validation and auto-fixing
- **Examples**: See `../../docs/examples/modular-skills/` directory for concrete implementations
