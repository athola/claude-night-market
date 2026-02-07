---
name: shared
description: 'DO NOT use directly: this skill is infrastructure for other spec-kit
  skills. Provides reusable patterns consumed by all spec-kit commands and skills.
  Use when developing new spec-kit skills, referencing standard patterns, ensuring
  consistency across specification workflows.'
category: infrastructure
tags:
- shared
- patterns
- templates
- specification
provides:
  infrastructure:
  - tech-stack-patterns
  - checklist-dimensions
  - artifact-structure
reusable_by:
- all spec-kit skills and commands
estimated_tokens: 200
version: 1.4.0
---

# Shared Infrastructure

## Overview

Provides common patterns, templates, and infrastructure modules used across all spec-kit commands and skills. This skill exists to reduce duplication and maintain consistency in specification-driven development workflows.

## Purpose

This skill consolidates reusable components:
- Technology-specific patterns (ignore files, tooling configurations)
- Quality validation dimensions for requirements
- Artifact structure documentation (spec.md, plan.md, tasks.md, checklists)

## Modules

### tech-stack-patterns.md
See `modules/tech-stack-patterns.md` for technology-specific patterns:
- Language-specific ignore patterns (Node.js, Python, Rust, Go, Java, C#)
- Common tool configurations (Docker, ESLint, Prettier, Terraform)
- Universal exclusions (.DS_Store, .vscode, .idea)

### checklist-dimensions.md
See `modules/checklist-dimensions.md` for quality validation dimensions:
- Completeness, Clarity, Consistency
- Measurability, Coverage, Edge Cases
- Non-Functional Requirements
- How to write "unit tests for requirements"

### artifact-structure.md
See `modules/artifact-structure.md` for spec-kit artifact organization:
- spec.md structure and role
- plan.md structure and role
- tasks.md structure and role
- checklists/ directory organization
- .specify/ feature directory layout

## Usage

This skill is automatically loaded by `speckit-orchestrator` and referenced by other spec-kit skills. It should not be loaded directly by commands.

## Related Skills

- `speckit-orchestrator`: Workflow coordination
- `spec-writing`: Specification creation
- `task-planning`: Task generation
## Troubleshooting

### Common Issues

**Command not found**
Ensure all dependencies are installed and in PATH

**Permission errors**
Check file permissions and run with appropriate privileges

**Unexpected behavior**
Enable verbose logging with `--verbose` flag
