---
name: context-report
description: |
  Generate context optimization report for skill directories.

  Triggers: context report, context optimization, skill portfolio, context analysis,
  optimization report, large files, context budget, skill efficiency

  Use when: assessing overall skill portfolio efficiency, pre-publish verification
  before releasing plugins, planning modularization priorities across many skills,
  identifying large files that need optimization

  DO NOT use when: analyzing single skill - use /analyze-skill instead.
  DO NOT use when: estimating specific file tokens - use /estimate-tokens.
  DO NOT use when: evaluating skill quality - use /skills-eval instead.

  Use this command for portfolio-level context optimization.
usage: /context-report [directory-path]
---

# Context Optimization Report

Generates a detailed context window optimization report for all skills in a directory. Identifies large files, categorizes by size, and provides actionable optimization recommendations.

## Usage

```bash
# Analyze skills directory
/context-report skills/

# Analyze specific plugin's skills
/context-report ~/.claude/plugins/my-plugin/skills

# Full statistics with detailed breakdown
/context-report skills/ --stats
```

## What It Reports

### Size Categories
Skills are categorized by byte size for optimization priority:

| Category | Size Range | Recommendation |
|----------|------------|----------------|
| Small | < 2KB | Optimal, no action needed |
| Medium | 2-5KB | Good, monitor growth |
| Large | 5-15KB | Consider modularization |
| XLarge | > 15KB | Should modularize |

### Report Contents
- **Total skills count**: Number of SKILL.md files found
- **Total size**: Combined bytes across all skills
- **Estimated tokens**: Aggregate context impact
- **Size distribution**: Breakdown by category
- **Individual file details**: Per-file metrics (in detailed mode)

## Examples

```bash
/context-report skills/
# Output:
# Context Optimization Analysis
# ==================================================
# Total Skills: 12
# Total Size: 45,230 bytes
# Estimated Tokens: 11,842
#
# Size Distribution:
#   Small (<2KB):   8 files
#   Medium (2-5KB): 3 files
#   Large (5-15KB): 1 files
#   XLarge (>15KB): 0 files
#
# Recommendation: 1 file(s) exceed 5KB
# Consider using progressive disclosure or modularization

/context-report skills/ --report
# Adds detailed per-file breakdown:
# Path                              Size     Category    Tokens
# ----------------------------------------------------------------
# skills-eval/SKILL.md             4,521    medium      1,180
# modular-skills/SKILL.md          3,892    medium        985
# ...
```

## Use Cases

### Portfolio Assessment
Get a bird's-eye view of your entire skill collection's context efficiency:
```bash
/context-report ~/.claude/skills
```

### Pre-Publish Check
Before publishing a plugin, validate all skills are within optimal bounds:
```bash
/context-report ./skills
```

### Optimization Planning
Identify which skills need the most attention for modularization.

## Integration

Complements other commands:
- `/analyze-skill` - Deep dive on individual files
- `/estimate-tokens` - Detailed token breakdown
- `/skills-eval` - Quality and compliance scoring

## Implementation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_optimizer.py report "${1:-.}"
```
