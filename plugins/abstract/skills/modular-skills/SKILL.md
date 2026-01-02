---
name: modular-skills
description: |
  Design skills as modular building blocks for predictable token usage.

  Triggers: skill design, skill architecture, modularization, token optimization,
  skill structure, refactoring skills, new skill creation, skill complexity

  Use when: creating new skills that will be >150 lines, breaking down complex
  monolithic skills, planning skill architecture, refactoring overlapping skills,
  reviewing skill maintainability, designing skill module structure

  DO NOT use when: evaluating existing skill quality - use skills-eval instead.
  DO NOT use when: writing prose for humans - use writing-clearly-and-concisely.
  DO NOT use when: need improvement recommendations - use skills-eval.

  Use this skill BEFORE creating any new skill. Check even if unsure.
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

A framework for designing modular skills to maintain predictable token usage. It breaks complex skills into focused modules that are easier to test and optimize.

The framework implements progressive disclosure: skills start with essential information and provide deeper details only when needed. This approach keeps context windows efficient while ensuring functionality is available.

### Key Benefits

- **Predictable Resource Usage**: Modular design keeps token consumption controlled.
- **Maintainable Architecture**: Shallow dependencies and clear boundaries.
- **Scalable Development**: Hub-and-spoke model allows growth.
- **Better Testing**: Focused modules are easier to test in isolation.
- **Tool Integration**: Executable components automate patterns.

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

This skill provides a framework for designing modular skills. Breaking down large skills into smaller modules creates a more maintainable architecture and controls token usage.

This skill is based on Anthropic's Agent Skills best practices, using progressive disclosure: start with a high-level overview, then provide detail as needed.

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
4. **Validate**: Run `abstract_validator.py` to validate proper structure and patterns
5. **Iterate**: Refine based on validation feedback and usage patterns

## Common Tasks

Here are a few common ways we use the tools:

- **To assess the complexity of a skill**, use the `skill-analyzer`. This helps us decide if a skill needs to be modularized.
- **To design the modules**, we follow the detailed workflow in the `guide.md`.
- **To see examples of how to implement the patterns**, we reference the `../../docs/examples/modular-skills/` directory.
- **To validate the structure of our modules**, we run the `module-validator` before deploying.
- **To estimate token usage**, we use the `token-estimator`. This helps us make design decisions based on their impact on the context window.

## Detailed Resources

For detailed implementation details and advanced techniques:

### Shared Modules (Cross-Skill Patterns)
- **Trigger Patterns**: See [trigger-patterns.md](../../shared-modules/trigger-patterns.md) for description field templates
- **Enforcement Language**: See [enforcement-language.md](../../shared-modules/enforcement-language.md) for intensity calibration
- **Anti-Rationalization**: See [anti-rationalization.md](../../shared-modules/anti-rationalization.md) for bypass prevention

### Skill-Specific Modules
- **Enforcement Patterns**: See `modules/enforcement-patterns.md` for frontmatter design patterns
- **Core Workflow**: See `modules/core-workflow.md` for detailed modularization process
- **Implementation Patterns**: See `modules/implementation-patterns.md` for coding and structure patterns
- **Migration Guide**: See `modules/antipatterns-and-migration.md` for converting existing skills
- **Design Philosophy**: See `modules/design-philosophy.md` for underlying principles and thinking
- **Troubleshooting**: See `modules/troubleshooting.md` for common issues and solutions

### Tools and Examples
- **Tools**: Python analysis utilities in `../../scripts/` directory:
  - `skill_analyzer.py` - Complexity analysis and recommendations
  - `token_estimator.py` - Token usage estimation with dependencies
  - `abstract_validator.py` - Pattern validation and auto-fixing
- **Examples**: See `../../docs/examples/modular-skills/` directory for concrete implementations
