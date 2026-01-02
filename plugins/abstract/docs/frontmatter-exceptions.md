# YAML Frontmatter Exceptions Documentation

## Overview

This document documents markdown files in the skills directory that intentionally lack YAML frontmatter and why they are exceptions.

## Files Without YAML Frontmatter (Exceptions)

The following 23 files intentionally lack YAML frontmatter because they serve as documentation, examples, or reference material rather than as loadable skills:

### README Files (6 files)
- `modular-skills/README.md` - Project overview and setup instructions
- `modular-skills/examples/advanced-patterns/README.md` - Advanced patterns examples overview
- `modular-skills/examples/basic-implementation/README.md` - Basic implementation examples overview
- `modular-skills/examples/complete-skills/README.md` - Complete skill examples overview
- `skills-eval/README.md` - Skills evaluation framework overview
- `skills-eval/scripts/README.md` - Scripts documentation

### Example Documentation Files (12 files)
- `modular-skills/examples/advanced-patterns/modules/cross-cutting-concerns.md` - Example of cross-cutting concerns
- `modular-skills/examples/advanced-patterns/modules/dynamic-loading.md` - Example of dynamic loading patterns
- `modular-skills/examples/advanced-patterns/modules/hierarchical-dependencies.md` - Example of dependency hierarchies
- `modular-skills/examples/sample-migration.md` - Migration case study overview
- `modular-skills/examples/sample-migration/modules/focused-modules.md` - Example of focused module extraction
- `modular-skills/examples/sample-migration/modules/hub-extraction.md` - Example of hub pattern extraction
- `modular-skills/examples/sample-migration/modules/migration-results.md` - Migration results documentation
- `modular-skills/examples/sample-migration/modules/original-analysis.md` - Original monolithic analysis
- `modular-skills/examples/sample-migration/modules/shared-scripts.md` - Shared scripts documentation

### Framework Documentation Files (5 files)
- `skills-eval/modules/advanced-tool-use-analysis.md` - Advanced tool use analysis framework
- `skills-eval/modules/evaluation-framework.md` - Evaluation criteria and scoring system
- `skills-eval/modules/evaluation-workflows.md` - Evaluation process workflows
- `skills-eval/modules/integration-testing.md` - Integration testing framework
- `skills-eval/modules/integration.md` - Integration patterns and approaches
- `skills-eval/modules/performance-benchmarking.md` - Performance benchmarking framework
- `skills-eval/modules/quality-metrics.md` - Quality metrics definitions
- `skills-eval/modules/troubleshooting.md` - Troubleshooting guide for evaluation framework

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
