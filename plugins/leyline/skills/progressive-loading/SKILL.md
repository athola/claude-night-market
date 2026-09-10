---
name: progressive-loading
description: Implements hub-and-spoke lazy loading to minimize token usage in large skills. Use when building multi-module skills that need conditional on-demand loading.
alwaysApply: false
category: infrastructure
tags:
- progressive-disclosure
- context-management
- modularity
- token-optimization
- lazy-loading
dependencies:
- conserve:context-optimization
tools: []
provides:
  infrastructure:
  - progressive-loading
  - context-based-selection
  - load-on-demand
  patterns:
  - hub-and-spoke
  - conditional-loading
  - context-awareness
usage_patterns:
- skill-optimization
- context-aware-loading
- dynamic-module-selection
- token-budget-management
complexity: intermediate
model_hint: standard
estimated_tokens: 800
progressive_loading: true
modules:
- modules/selection-strategies.md
- modules/loading-patterns.md
- modules/performance-budgeting.md
- modules/advanced-patterns.md
- modules/api-patterns.md
- modules/api-review.md
- modules/cargo-patterns.md
- modules/document-analysis-patterns.md
- modules/git-catchup-patterns.md
- modules/git-patterns.md
- modules/large-reference.md
- modules/legacy-python.md
- modules/linux-patterns.md
- modules/log-analysis-patterns.md
- modules/macos-patterns.md
- modules/modern-python.md
- modules/performance.md
- modules/python-packaging.md
- modules/python-patterns.md
- modules/python-testing.md
- modules/rust-review.md
- modules/troubleshooting.md
- modules/windows-patterns.md
---

# Progressive Loading Patterns

## Overview

Progressive loading provides standardized patterns for building skills that load modules dynamically based on context, user intent, and available token budget. This prevents loading unnecessary content while ensuring required functionality is available when needed.

The core principle: **Start minimal, expand intelligently, monitor continuously.**

## When To Use

Use progressive loading when building skills that:
- Cover multiple distinct workflows or domains
- Need to manage context window efficiently
- Have modules that are mutually exclusive based on context
- Require MECW compliance for long-running sessions
- Want to optimize for common paths while supporting edge cases

## When NOT To Use

- Project doesn't use the leyline infrastructure patterns
- Simple scripts without service architecture needs

## Quick Start

### Basic Hub Pattern

```markdown
## Progressive Loading

**Context A**: Load `modules/loading-patterns.md` for scenario A
**Context B**: Load `modules/selection-strategies.md` for scenario B

**Always Available**: Core utilities, exit criteria, integration points
```
**Verification:** Run the command with `--help` flag to verify availability.

### Context-Based Selection

Modules are declared in the skill's YAML frontmatter and
loaded on demand with a `@modules/` directive. The hub reads
the detected context, then loads only the spokes that match:

```markdown
---
modules:
- modules/git-catchup-patterns.md
- modules/python-testing.md
---

When the intent is a branch or PR catch-up, load
`@modules/git-catchup-patterns.md`. When the artifacts include
Python tests, also load `@modules/python-testing.md`.
```

To keep loads within the MECW token budget, check whether a
module fits before pulling it in. The `MECWMonitor` in
`plugins/leyline/src/leyline/mecw.py` exposes the methods used
here:

```python
from leyline.mecw import MECWMonitor

monitor = MECWMonitor()
monitor.track_usage(current_context_tokens)

# module_estimated_tokens comes from the module frontmatter
can_load, reasons = monitor.can_handle_additional(module_estimated_tokens)
```

Load the next module only when `can_load` is true. Each
module records its cost in its frontmatter `estimated_tokens`
field.

## Hub-and-Spoke Architecture

### Hub Responsibilities
1. **Context Detection**: Identify user intent, artifacts, workflow type
2. **Module Selection**: Choose which modules to load based on context
3. **Budget Management**: Verify MECW compliance before loading
4. **Integration Coordination**: Provide integration points with other skills
5. **Exit Criteria**: Define completion criteria across all paths

### Spoke Characteristics
1. **Single Responsibility**: Each module serves one workflow or domain
2. **Self-Contained**: Modules don't depend on other modules
3. **Context-Tagged**: Clear indicators of when module applies
4. **Token-Budgeted**: Known token cost for selection decisions
5. **Independently Testable**: Can be evaluated in isolation

## Selection Strategies

See `modules/selection-strategies.md` for detailed strategies:
- **Intent-based**: Load based on detected user goals
- **Artifact-based**: Load based on detected files/systems
- **Budget-aware**: Load within available token budget
- **Progressive**: Load core first, expand as needed
- **Mutually-exclusive**: Load one path from multiple options

## Loading Patterns

See `modules/loading-patterns.md` for implementation patterns:
- **Conditional includes**: Dynamic module references
- **Lazy loading**: Load on first use
- **Tiered disclosure**: Core → common → edge cases
- **Context switching**: Change loaded modules mid-session
- **Preemptive unloading**: Remove unused modules under pressure

## Common Use Cases

- **Multi-Domain Skills**: `imbue:catchup` loads git/docs/logs modules by context
- **Context-Heavy Analysis**: Load relevant modules only, defer deep-dives, unload completed
- **Plugin Infrastructure**: Mix-and-match infrastructure modules with version checks

## Best Practices

1. **Design Hub First**: Define all possible contexts and module boundaries
2. **Tag Modules Clearly**: Use YAML frontmatter to indicate context triggers
3. **Measure Token Cost**: Know the cost of each module for selection
4. **Monitor Loading**: Track which modules are actually used
5. **Validate Paths**: Verify all context paths have required modules
6. **Document Triggers**: Make context detection logic transparent

## Module References

### Core (always available to the hub)

- **Selection Strategies**: See `modules/selection-strategies.md` for choosing modules
- **Loading Patterns**: See `modules/loading-patterns.md` for implementation techniques
- **Performance Budgeting**: See `modules/performance-budgeting.md` for token budget model and optimization workflow
- **Advanced Patterns**: See `modules/advanced-patterns.md` for nested hubs, multi-tier disclosure, and cross-skill module sharing
- **Troubleshooting**: See `modules/troubleshooting.md` when modules fail to load, context detection misfires, or token budgets are exceeded

### Context-Specific Pattern Modules

These modules are loaded on demand by the hub based on
detected artifacts and user intent. They are listed in
frontmatter so the selector can match them, but the hub
should only load the ones whose activation context fires.

**Operating-system patterns** (load on detected platform):

- `modules/linux-patterns.md`: Linux-specific shell, paths, and process patterns
- `modules/macos-patterns.md`: macOS-specific tooling and platform quirks
- `modules/windows-patterns.md`: Windows shell, path, and PowerShell patterns

**Language and runtime patterns** (load on detected ecosystem):

- `modules/modern-python.md`: Python 3.11+ idioms, typing, async
- `modules/legacy-python.md`: Python 2 / pre-3.8 compatibility patterns
- `modules/python-packaging.md`: pyproject.toml, uv, pip, hatch, poetry
- `modules/python-patterns.md`: General Python authoring patterns
- `modules/python-testing.md`: pytest, fixtures, parametrization, mocking
- `modules/cargo-patterns.md`: Rust Cargo workspace and dependency patterns
- `modules/rust-review.md`: Rust code-review patterns

**Workflow patterns** (load on detected task):

- `modules/api-patterns.md`: API design and endpoint conventions
- `modules/api-review.md`: API surface review patterns
- `modules/git-patterns.md`: Git workflow and history patterns
- `modules/git-catchup-patterns.md`: Catching up on a branch or PR diff
- `modules/document-analysis-patterns.md`: Reading and analyzing documents
- `modules/log-analysis-patterns.md`: Parsing and reasoning over logs
- `modules/performance.md`: Performance investigation patterns

**Reference material** (load only when explicitly cited):

- `modules/large-reference.md`: Large reference tables and lookups (load
  last; tokens are non-trivial)

## Integration with Other Skills

This skill provides foundational patterns referenced by:
- `abstract:modular-skills` - Uses progressive loading for skill design
- `conserve:context-optimization` - Uses for MECW-compliant loading
- `imbue:catchup` - Uses for context-based module selection
- Plugin authors building multi-workflow skills

Reference in your skill's frontmatter:
```yaml
dependencies: [leyline:progressive-loading, conserve:context-optimization]
progressive_loading: true
```
**Verification:** Run the command with `--help` flag to verify availability.

## Exit Criteria

- Hub clearly defines all module loading contexts
- Each module is tagged with activation context
- Module selection respects MECW constraints
- Token costs measured for all modules
- Context detection logic documented
- Loading paths validated for completeness
