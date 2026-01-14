# Skills Showcase - Claude Code Development Workflows

This tutorial demonstrates the foundational concept of **skills** in the claude-night-market ecosystem. Skills are the primary abstraction that transforms Claude Code from a general-purpose assistant into a specialized development partner.

![Skills Showcase Demo](../../../assets/gifs/skills-showcase.gif)

*A detailed walkthrough of skill discovery, structure, validation, and composition patterns.*

---

## Overview

The claude-night-market contains 105+ skills across 14 plugins, each skill representing a reusable, composable unit of functionality. This tutorial explores:

- Skill Discovery: How to find and catalog available skills
- Skill Anatomy: Understanding the structure and metadata of skills
- Skill Validation: Verifying that skills follow proper conventions
- Skill Composition: How skills chain together into workflows

---

## Part 1: Skill Discovery and Cataloging

### Exploring Plugin Skills

Skills are organized within plugin directories under a `skills/` subdirectory. Each skill is a directory containing:

- `SKILL.md` - The skill definition with frontmatter and workflow instructions
- `modules/` (optional) - Modular components loaded progressively
- `scripts/` (optional) - Executable scripts for automation

To explore available skills in a plugin:

```bash
ls plugins/abstract/skills/
```

**Output:**
```
dogfood/  plugin-auditor/  plugin-validator/  skill-auditor/  skill-creator/
```

Each of these directories represents a **meta-skill** for plugin development.

### Counting Total Skills

To get a project-wide count of all skills:

```bash
find plugins -name 'SKILL.md' -type f | wc -l
```

**Output:**
```
105
```

This count represents the total capability surface of the marketplace. Each skill is:
- **Self-contained:** Can be invoked independently
- **Documented:** Includes description, usage, and examples
- **Testable:** Follows structured patterns for validation

---

## Part 2: Skill Anatomy and Structure

### Skill Definition Format

Skills follow a **two-part structure:**

1. **YAML Frontmatter** - Metadata and configuration
2. **Markdown Body** - Workflow instructions and context

Let's examine a real skill:

```bash
head -30 plugins/abstract/skills/plugin-validator/SKILL.md
```

**Sample Output:**
```yaml
---
name: plugin-validator
description: |
  Validate plugin structure, metadata, and skill definitions.
  Checks frontmatter, dependencies, and file organization.
category: validation
tags: [plugin, validation, quality]
tools: [Read, Glob, Bash]
complexity: medium
estimated_tokens: 800
dependencies:
  - abstract:shared
---

# Plugin Validator Skill

Validates that a plugin follows the claude-night-market conventions...
```

### Frontmatter Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | Unique identifier | `plugin-validator` |
| `description` | What the skill does | Multi-line description |
| `category` | Skill category | `validation`, `workflow`, `analysis` |
| `tags` | Searchable keywords | `[plugin, validation]` |
| `tools` | Required Claude Code tools | `[Read, Write, Bash]` |
| `complexity` | Complexity level | `low`, `medium`, `high` |
| `estimated_tokens` | Approximate token usage | `800` |
| `dependencies` | Required skills | `[abstract:shared]` |

### Progressive Loading

Some skills use **progressive loading** to reduce initial token cost:

```yaml
progressive_loading: true
modules:
  - manifest-parsing
  - markdown-generation
  - tape-validation
```

Modules are loaded on-demand when specific functionality is needed.

---

## Part 3: Skill Validation

### Why Validate Skills?

The `abstract:plugin-validator` skill verifies that skills follow project conventions. This validation checks for structural integrity by confirming required files exist, ensures that YAML frontmatter is well-formed, and resolves dependencies between skills. It also assesses documentation quality by checking for clear descriptions and examples.

### Using the Validator

In Claude Code, invoke with:

```
Skill(abstract:plugin-validator, plugin_name='sanctum')
```

The validator performs these checks:

1. Plugin structure: Confirms `skills/`, `commands/`, `.claude-plugin/` exist
2. Skill frontmatter: Validates YAML syntax and required fields
3. Command definitions: Checks command markdown files are valid
4. Dependencies: Verifies all referenced skills exist

**Example Validation Output:**
```
Plugin structure valid
19 skills found with valid frontmatter
12 commands defined correctly
All dependencies resolved
WARNING: skill-x missing 'estimated_tokens' field
```

---

## Part 4: Skills in Real Workflows

### Example: Git Workspace Review

The `sanctum:git-workspace-review` skill is commonly invoked at the start of development sessions:

```
Skill(sanctum:git-workspace-review)
```

**What it does:**

1. Repository State: Runs `git status` to identify uncommitted changes
2. Commit History: Runs `git log` to show recent commits and context
3. File Analysis: Analyzes changed files to understand impact areas
4. Session Context: Provides Claude Code with a full view of the current work

**Value Proposition:**

- Context Recovery: Quickly understand what's in progress
- Change Impact: See which parts of the codebase are affected
- Commit Quality: Understand recent work to maintain consistency

### Example: PR Preparation Workflow

Complex workflows compose multiple skills sequentially:

```
PR Preparation Workflow:
  1. Skill(sanctum:git-workspace-review) - Understand changes
  2. Skill(imbue:scope-guard) - Check scope drift
  3. Skill(sanctum:commit-messages) - Generate commit message
  4. Skill(sanctum:pr-prep) - Prepare PR description
```

#### Benefits of Skill Composition

Composing skills into workflows provides several advantages. Each skill maintains a focus on a single responsibility, which increases reusability across different projects and tasks. This modular approach maintains a consistent standard for complex operations like PR preparation and integrates quality gates that automatically check for scope drift and code quality issues.

---

## Part 5: Skills Enable Workflow Automation

### The Skills Philosophy

Skills transform the assistant's capabilities by encoding team best practices directly into the workflow. This automation removes the need to manually describe repetitive tasks such as code review steps or documentation updates. By following the same process every time, skills maintain consistency across the project and provide the assistant with the necessary context to understand specific project structures and conventions.

### Skill Composition Patterns

#### Sequential Composition
Skills execute in order, each building on the previous:
```
Skill(A) → Skill(B) → Skill(C)
```

#### Conditional Composition
Skills invoke others based on context:
```
if scope_drift_detected:
    Skill(imbue:scope-guard)
```

#### Parallel Composition
Independent skills can run in parallel (conceptually):
```
Skill(pensive:api-review) + Skill(pensive:architecture-review)
```

---

## Key Insights

### Design Principles

1. **Single Responsibility:** Each skill does one thing well
2. **Clear Dependencies:** Skills declare what they need
3. **Progressive Disclosure:** Complex skills load modules on-demand
4. **Self-Documentation:** Skills explain their purpose and usage

### Quality Metrics

- 105 skills across 14 plugins
- Structured workflows for git, review, specs, testing
- Composable and reusable across projects
- Self-documenting with clear dependencies
- Validated structure supports overall quality

### Workflow Value

- **Git Operations:** 19 skills in sanctum for branch management, commits, PRs
- **Code Review:** 12 skills in pensive for multi-discipline review
- **Specification:** 8 skills in spec-kit for spec-driven development
- **Testing:** 6 skills in parseltongue for Python test analysis
- **Meta-Development:** 5 skills in abstract for plugin creation

---

## Further Reading

- **[Plugin Architecture](../architecture/plugin-system.md):** Deep dive into plugin design
- **[Skill Authoring Guide](../guides/creating-skills.md):** How to create new skills
- **[Workflow Patterns](../guides/workflow-patterns.md):** Common skill composition patterns
- **[Capabilities Reference](../reference/capabilities-reference.md):** Full catalog of all 105 skills

---

**Duration:** ~90 seconds
**Difficulty:** Beginner
**Prerequisites:** Basic understanding of Claude Code
**Tags:** skills, workflows, claude-code, development, getting-started, architecture
