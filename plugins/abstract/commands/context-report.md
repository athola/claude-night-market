---
name: context-report
description: Generate context optimization report for skill directories
usage: /context-report [directory-path]
---

# Context Optimization Report

Generates a detailed context window optimization report for all skills in a directory. Identifies large files, categorizes by size, and provides actionable optimization recommendations.

## When To Use

Use this command when you need to:
- Assessing overall skill portfolio efficiency
- Pre-publish verification before releasing plugins
- Planning modularization priorities across many skills
- Identifying large files that need optimization

## When NOT To Use

Avoid this command if:
- Analyzing single skill - use /analyze-skill instead
- Evaluating skill quality - use /skills-eval instead

## Usage

```bash
# Analyze skills directory
/context-report skills/

# Analyze specific plugin's skills
/context-report ~/.claude/plugins/my-plugin/skills

# Full statistics with detailed breakdown
/context-report skills/ --stats

# Estimate tokens for a single skill file
/context-report --estimate skills/my-skill/SKILL.md

# Estimate with dependency analysis
/context-report --estimate skills/my-skill/SKILL.md --include-dependencies
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

## Token Estimation

When used with `--estimate`, provides detailed per-file token breakdown:

### Component Breakdown
- **Frontmatter tokens**: YAML metadata overhead
- **Body tokens**: Main content consumption
- **Code tokens**: Embedded code examples
- **Dependency tokens**: Referenced module costs (with `--include-dependencies`)

### Token Thresholds
- **< 800 tokens**: Optimal for quick loading
- **800-2000 tokens**: Good balance of content and efficiency
- **2000-3000 tokens**: Consider modularization
- **> 3000 tokens**: Should modularize for context efficiency

### Token Estimation Examples

```bash
/context-report --estimate skills/modular-skills/SKILL.md
# Output:
# === skills/modular-skills/SKILL.md ===
# Total tokens: 1,847
# Component breakdown:
#   Frontmatter: 45 tokens
#   Body content: 1,402 tokens
#   Code blocks: 400 tokens
# === Recommendations ===
# GOOD: Optimal token range (800-2000 tokens)
```

## Integration

Complements other commands:
- `/analyze-skill` - Deep dive on individual files
- `/skills-eval` - Quality and compliance scoring

## Implementation

```bash
# Directory report mode
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_optimizer.py report "${1:-.}"
# Token estimation mode (--estimate flag)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/token_estimator.py --file "${1:-.}"
```
