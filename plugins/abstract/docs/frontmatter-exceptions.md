# YAML Frontmatter Exceptions Documentation

## Overview

This document documents markdown files in the skills directory that intentionally lack YAML frontmatter and why they are exceptions.

## Files Without YAML Frontmatter (Exceptions)

The following 22 files intentionally lack YAML frontmatter because they serve as documentation, examples, or reference material rather than as loadable skills:


### README Files (6 files)

- `skills/modular-skills/README.md` - Project overview and setup instructions
- `docs/examples/modular-skills/advanced-patterns/README.md` - Advanced patterns examples overview
- `docs/examples/modular-skills/basic-implementation/README.md` - Basic implementation examples overview
- `docs/examples/modular-skills/complete-skills/README.md` - Complete skill examples overview
- `skills/skills-eval/README.md` - Skills evaluation framework overview
- `skills/skills-eval/scripts/README.md` - Scripts documentation

### Example Documentation Files (9 files)

- `docs/examples/modular-skills/advanced-patterns/modules/cross-cutting-concerns.md` - Example of cross-cutting concerns
- `docs/examples/modular-skills/advanced-patterns/modules/dynamic-loading.md` - Example of dynamic loading patterns
- `docs/examples/modular-skills/advanced-patterns/modules/hierarchical-dependencies.md` - Example of dependency hierarchies
- `docs/examples/modular-skills/sample-migration.md` - Migration case study overview
- `docs/examples/modular-skills/sample-migration/modules/focused-modules.md` - Example of focused module extraction
- `docs/examples/modular-skills/sample-migration/modules/hub-extraction.md` - Example of hub pattern extraction
- `docs/examples/modular-skills/sample-migration/modules/migration-results.md` - Migration results documentation
- `docs/examples/modular-skills/sample-migration/modules/original-analysis.md` - Original monolithic analysis
- `docs/examples/modular-skills/sample-migration/modules/shared-scripts.md` - Shared scripts documentation

### Framework Documentation Files (7 files)

- `skills/skills-eval/modules/advanced-tool-use-analysis.md` - Advanced tool use analysis framework
- `skills/skills-eval/modules/evaluation-framework.md` - Evaluation criteria and scoring system
- `skills/skills-eval/modules/evaluation-workflows.md` - Evaluation process workflows
- `skills/skills-eval/modules/integration-testing.md` - Integration testing framework
- `skills/skills-eval/modules/integration.md` - Integration patterns and approaches
- `skills/skills-eval/modules/performance-benchmarking.md` - Performance benchmarking framework
- `skills/skills-eval/modules/troubleshooting.md` - Troubleshooting guide for evaluation framework
## Exception Rationale

### Documentation Files
README files serve as project documentation and should remain as simple markdown files without skill metadata.

### Example Files
Example files demonstrate patterns and approaches but are not meant to be loaded as active skills. They serve as educational material.

### Framework Documentation
Framework documentation describes evaluation methodologies, quality criteria, and processes. These are reference materials rather than executable skills.

## Files With YAML Frontmatter

The following core module files have been updated with proper YAML frontmatter:

1. `modular-skills/guide.md` - Implementation guide
2. `modular-skills/modules/core-workflow.md` - Core design workflow
3. `modular-skills/modules/implementation-patterns.md` - Implementation best practices
4. `modular-skills/modules/design-philosophy.md` - Design principles
5. `modular-skills/modules/antipatterns-and-migration.md` - Anti-patterns and migration
6. `modular-skills/modules/troubleshooting.md` - Troubleshooting guide

## Maintenance Guidelines

When adding new markdown files to the skills directory:

1. **Skills** (files in `skills/*/SKILL.md` or core module files) - Should have YAML frontmatter
2. **Documentation** (README.md, guide.md for reference purposes) - Should be exceptions
3. **Examples** (files in `examples/` directories) - Should be exceptions
4. **Framework docs** (describing processes, criteria, methodologies) - Should be exceptions

This approach validates that only loadable skill content has metadata while preserving documentation clarity.
