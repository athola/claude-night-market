---
name: optimizing-large-skills
description: |
  Systematic methodology to reduce skill file size through externalization,
  consolidation, and progressive loading patterns.

  Triggers: large skill, skill optimization, skill size, 300 lines, inline code,
  skill refactoring, skill context reduction, skill modularization

  Use when: skills exceed 300 lines, multiple code blocks (10+) with similar
  functionality, heavy Python inline with markdown, functions >20 lines embedded

  DO NOT use when: skill is under 300 lines and well-organized.
  DO NOT use when: creating new skills - use modular-skills instead.

  Consult this skill when skills-eval shows "Large skill file" warnings.
token_budget: 25
progressive_loading: true
---

# Optimizing Large Skills

## Overview
Systematic methodology for reducing skill file size while preserving functionality
through separation of concerns and strategic code organization.

## When to Use

**Symptoms that trigger this skill:**
- Skills-eval validation shows "[WARN] Large skill file" warnings
- SKILL.md files exceed 300 lines
- Multiple code blocks (10+) with similar functionality
- Heavy Python implementations inline with markdown
- Functions >20 lines embedded in documentation

**Quick Analysis:**
```bash
# Analyze any skill file for optimization opportunities
python skills/optimizing-large-skills/tools/optimization-patterns.py \
  skills/path/SKILL.md --verbose --generate-plan
```

## Core Pattern: Externalize-Consolidate-Progress

### Transformation Pattern

**Before**: 654-line skill with heavy inline Python implementations
**After**: ~150-line skill with external tools and references

**Key Changes:**
- Externalize heavy implementations (>20 lines) to dedicated tools
- Consolidate similar functions with parameterization
- Replace code blocks with structured data and tool references
- Implement progressive loading for non-essential content

## Quick Reference

### Size Reduction Strategies
Use analysis tool: `python tools/optimization-patterns.py SKILL.md --generate-plan`

| Strategy | Impact | When to Use |
|----------|--------|-------------|
| **Externalize Python modules** | 60-70% reduction | Heavy implementations (>20 lines) |
| **Consolidate similar functions** | 15-20% reduction | Repeated patterns with minor variations |
| **Replace code with structured data** | 10-15% reduction | Configuration-driven logic |
| **Progressive loading patterns** | 5-10% reduction | Multi-stage workflows |

### File Organization
```
skill-name/
  SKILL.md              # Core documentation (~150-200 lines)
  tools/
    analyzer.py         # Heavy implementations
    controller.py       # Control logic
    config.yaml         # Structured data
  examples/
    basic-usage.py      # Minimal working example
```

## Implementation

### Analysis & Planning
```bash
# Generate detailed optimization plan
python skills/optimizing-large-skills/tools/optimization-patterns.py \
  your-skill.md --verbose --generate-plan

# JSON output for automation
python skills/optimizing-large-skills/tools/optimization-patterns.py your-skill.md --output-json
```

### Externalization Pattern
**Move heavy implementations to tools with CLI interfaces:**
- Functions >20 lines → dedicated tool files
- Always include `argparse` CLI interface
- Add `if __name__ == "__main__"` execution block
- Provide help documentation and JSON output options

### Consolidation Pattern
**Merge similar functions with parameterization:**
- Identify repeated logic patterns
- Create unified functions with method parameters
- Replace multiple code blocks with single configurable function

### Progressive Loading Pattern
**Use frontmatter for focused context loading:**
- Set `token_budget: 25` for optimized skills
- Enable `progressive_loading: true` for conditional content
- Use `<!-- progressive: feature -->` blocks for optional sections

## Common Mistakes

| Mistake | Why Bad | Fix |
|---------|---------|-----|
| **Externalizing without CLI** | Hard to use and test | Always include command-line interface |
| **Too many small files** | Increases complexity | Consolidate related functionality |
| **Removing essential docs** | Reduces discoverability | Keep core concepts inline |
| **Complex dependencies** | Hard to maintain | Simple, explicit imports only |
| **No usage examples** | Unclear how to use tools | Always include working examples |

## Rationalization Prevention

**Violating the letter of the rules is violating the spirit of the rules.**

| Excuse | Reality |
|--------|---------|
| "I'm already halfway through manual editing" | Incomplete work wastes time.
  Use hybrid approach combining your progress with systematic patterns. |
| "Deadline is too tight for systematic approach" | Fast, messy work creates more problems.
  Systematic approach is faster overall when done right. |
| "Just extract code, keep same structure" | Externalizing without optimization
  = same problems in different files. Apply full methodology. |
| "I'll do it properly later" | "Later" never comes. Technical debt accumulates. Do it right now. |
| "This skill is different, needs special handling" | All skills follow same
  context optimization principles. No exceptions. |
| "The team lead wants a quick fix" | Quick fixes create long-term problems.
  Educate with concrete examples of systematic benefits. |
| "I don't have time to create CLI tools" | CLI tools take 15 minutes,
  save hours of manual work. Always invest in automation. |
| "The existing code is already optimized" | If skills-eval flags it as large,
  it needs optimization regardless of perceived quality. |

## Red Flags - STOP and Start Over

- "I'll optimize this one file manually"
- "Let me just extract the big functions"
- "The methodology doesn't apply here"
- "I'll come back and fix it properly"
- "The existing structure is fine"
- "No time for proper tools"

**All of these mean: Stop. Re-read the skill. Apply the full methodology.**

## Optimization Checklist

**Phase 1: Analysis**
- [ ] Identify files >300 lines
- [ ] Count code blocks and functions
- [ ] Measure inline code vs documentation ratio
- [ ] Find repeated patterns and similar functions

**Phase 2: Externalization**
- [ ] Move heavy implementations (>20 lines) to separate files
- [ ] Add CLI interfaces to externalized tools
- [ ] Create tool directory structure
- [ ] Add usage examples for each tool

**Phase 3: Consolidation**
- [ ] Merge similar functions with parameterization
- [ ] Replace code blocks with structured data where appropriate
- [ ] Implement progressive loading for non-essential content
- [ ] Update skill documentation to reference external tools

**Phase 4: Validation**
- [ ] Verify line count <300 (target: 150-200)
- [ ] Test all externalized tools work correctly
- [ ] Confirm progressive loading functions
- [ ] Run skills-eval validation to verify size reduction

## Real-World Impact

**Before optimization:**
- growth-management skill: 654 lines (6 code blocks, 12 Python functions)
- Skills-eval: [WARN] Large skill file warning
- Loading time: High (full context usage)
- Maintainability: Poor (everything mixed together)

**After optimization:**
- growth-management skill: 178 lines (3 tool references, 0 inline functions)
- Skills-eval: OK No warnings
- Loading time: Low (focused context)
- Maintainability: Excellent (separation of concerns)

**Result:** 73% size reduction while preserving all functionality
through external tools and progressive loading patterns.

## Anti-Patterns to Avoid

###  Narrative Documentation
"During the session on 2025-11-27, we discovered that context growth was problematic..."

###  Template Code
Don't create fill-in-the-blank templates in the skill itself - put them in examples/

###  Multiple Languages
One excellent Python example beats mediocre JavaScript and Go examples.

###  Tool References
"For advanced pattern analysis, use `tools/analyzer.py` with appropriate context data."

###  Focused Scope
Each tool should do one thing well with clear parameters and outputs.
