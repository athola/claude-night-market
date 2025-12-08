# Skill Authoring Guide

Complete guide for writing effective Claude Code skills using Test-Driven Development (TDD) methodology, persuasion principles, and official Anthropic best practices.

## Overview

This skill teaches how to create behavioral interventions for Claude that are empirically validated and resistant to rationalization. It treats skill writing as process documentation requiring real failure testing rather than theoretical instruction writing.

## Quick Start

```bash
# Validate skill structure
python scripts/skill_validator.py

# From any skill directory
python /path/to/skill-authoring/scripts/skill_validator.py --path SKILL.md
```

## Core Principles

1. **The Iron Law**: NO SKILL WITHOUT A FAILING TEST FIRST
2. **TDD Cycle**: RED (document failures) → GREEN (minimal fix) → REFACTOR (bulletproof)
3. **Persuasion Research**: Based on studies showing 2x compliance improvement
4. **Progressive Disclosure**: Keep SKILL.md under 500 lines, use modules for details
5. **Anti-Rationalization**: Explicitly counter Claude's tendency to bypass requirements

## File Structure

```
skill-authoring/
├── SKILL.md                          # Main skill file (364 lines)
├── modules/                          # Detailed content
│   ├── tdd-methodology.md           # RED-GREEN-REFACTOR cycle
│   ├── persuasion-principles.md     # Compliance research
│   ├── description-writing.md       # Discovery optimization
│   ├── progressive-disclosure.md    # Token efficiency
│   ├── anti-rationalization.md      # Bulletproofing
│   ├── graphviz-conventions.md      # Process diagrams
│   ├── testing-with-subagents.md    # Empirical validation
│   └── deployment-checklist.md      # Final validation
├── scripts/
│   └── skill_validator.py           # Validation tool
└── README.md                         # This file
```

## Key Concepts

### TDD for Skills

- **RED**: Document Claude failing WITHOUT skill (3+ scenarios)
- **GREEN**: Write minimal skill to address failures
- **REFACTOR**: Add counters for rationalizations

### Persuasion Principles

Based on Meincke et al. (2025) research:
- Authority: Directive language for safety-critical
- Commitment: Explicit declarations
- Scarcity: Immediate requirements
- Social Proof: Universal standards
- Unity: Professional identity
- Liking: Collaborative framing

### Description Optimization

Formula: `[WHAT] + [WHEN] + [KEY TERMS]`

Example:
```yaml
description: Teaches API security with validation and error handling. Use when creating endpoints, reviewing security, or implementing authentication. Covers rate limiting, CORS, and common vulnerabilities.
```

### Anti-Rationalization

Common patterns to counter:
- Scope minimization ("This is just...")
- Temporal deferral ("We can add X later")
- Trust assumptions ("Trusted users...")
- Complexity trade-offs ("Too complex...")
- Spirit vs letter ("I understand the principle...")
- Confidence bias ("I know this...")

## Validation

```bash
# Validate current skill
python scripts/skill_validator.py

# Validate other skill
python scripts/skill_validator.py --path /path/to/SKILL.md

# Strict mode (warnings as errors)
python scripts/skill_validator.py --strict
```

Exit codes:
- `0` - Success, ready to deploy
- `1` - Warnings present (should fix)
- `2` - Errors found (must fix)

## Dependencies

- Python 3.8+
- PyYAML (`pip install pyyaml`)

## Usage

### Creating a New Skill

1. Document baseline failures (RED)
2. Write minimal SKILL.md (GREEN)
3. Test and bulletproof (REFACTOR)
4. Validate structure
5. Deploy

### Improving Existing Skill

1. Run pressure scenarios
2. Document rationalizations
3. Add explicit counters
4. Retest for compliance
5. Validate and redeploy

## Module Reference

- **TDD Methodology**: `modules/tdd-methodology.md` - Complete RED-GREEN-REFACTOR cycle
- **Persuasion Principles**: `modules/persuasion-principles.md` - Research-backed compliance techniques
- **Description Writing**: `modules/description-writing.md` - Discovery optimization patterns
- **Progressive Disclosure**: `modules/progressive-disclosure.md` - File structure and token efficiency
- **Anti-Rationalization**: `modules/anti-rationalization.md` - Bulletproofing against bypasses
- **Graphviz Conventions**: `modules/graphviz-conventions.md` - Process diagram standards
- **Testing with Subagents**: `modules/testing-with-subagents.md` - Empirical validation methodology
- **Deployment Checklist**: `modules/deployment-checklist.md` - Final validation gates

## Examples

See individual modules for complete examples:
- TDD baseline documentation template
- Pressure scenario design
- Exception tables
- Red flags lists
- Commitment statements
- A/B testing methodology

## Integration

Works with:
- **modular-skills**: For architectural patterns
- **skills-eval**: For quality assessment

Workflow:
1. Create with skill-authoring (TDD)
2. Structure with modular-skills (architecture)
3. Assess with skills-eval (quality)

## License

Part of the Claude Night Market plugin collection.

## Version

1.0.0 (2025-12-06)
