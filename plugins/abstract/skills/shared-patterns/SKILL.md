---
name: shared-patterns
description: 'Provide reusable patterns for validation, error handling, scaffolding. Use for skill consistency.'
alwaysApply: false
category: meta-infrastructure
tags:
- patterns
- templates
- shared
- validation
- reusable
dependencies: []
estimated_tokens: 400
model_hint: standard
modules:
- modules/validation-patterns.md
- modules/error-handling.md
- modules/testing-templates.md
- modules/workflow-patterns.md
- modules/advanced.md
- modules/creation.md
- modules/editing.md
- modules/troubleshooting.md
---
# Shared Patterns

Reusable patterns and templates for skill and hook development.

## Purpose

This skill provides shared patterns that are referenced by other skills in the abstract plugin. It follows DRY principles by centralizing common patterns.

## Pattern Categories

### Validation Patterns

See [modules/validation-patterns.md](modules/validation-patterns.md) for:
- Input validation templates
- Schema validation patterns
- Error reporting formats

### Error Handling

See [modules/error-handling.md](modules/error-handling.md) for:
- Exception hierarchies
- Error message formatting
- Recovery strategies

### Testing Templates

See [modules/testing-templates.md](modules/testing-templates.md) for:
- Unit test scaffolding
- Integration test patterns
- Mock fixtures

### Workflow Patterns

See [modules/workflow-patterns.md](modules/workflow-patterns.md) for:
- Checklist templates
- Feedback loop patterns
- Progressive disclosure structures

## Usage

Reference these patterns from other skills:

```markdown
For validation patterns, see the `shared-patterns` skill's
[validation-patterns](../shared-patterns/modules/validation-patterns.md) module.
```
**Verification:** Run the command with `--help` flag to verify availability.

## Exit Criteria

- [ ] Each of the four module files (`validation-patterns.md`, `error-handling.md`,
  `testing-templates.md`, `workflow-patterns.md`) exists under
  `plugins/abstract/skills/shared-patterns/modules/`.
- [ ] Any cross-skill reference to these modules uses a relative path beginning with
  `../shared-patterns/modules/` and resolves to an existing file on disk.
- [ ] No consuming skill references a path under the deprecated `skills/shared/modules/`
  directory pattern; such references are surfaced as broken links.
- [ ] The hub SKILL.md itself stays under 150 lines with no substantive pattern content
  duplicated from the modules it links.
