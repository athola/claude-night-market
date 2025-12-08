---
name: estimate-tokens
description: Estimate token usage for skill files and their dependencies
usage: /estimate-tokens [skill-path]
---

# Estimate Token Usage

Estimates token consumption for skill files, including optional dependency analysis. Essential for context window budgeting and optimization decisions.

## Usage

```bash
# Estimate tokens for a skill file
/estimate-tokens skills/my-skill/SKILL.md

# Estimate with dependency analysis
/estimate-tokens skills/my-skill/SKILL.md --include-dependencies

# Estimate for entire directory
/estimate-tokens skills/
```

## What It Measures

### Component Breakdown
- **Frontmatter tokens**: YAML metadata overhead
- **Body tokens**: Main content consumption
- **Code tokens**: Embedded code examples
- **Dependency tokens**: Referenced module costs (optional)

### Token Thresholds
- **< 800 tokens**: Optimal for quick loading
- **800-2000 tokens**: Good balance of content and efficiency
- **2000-3000 tokens**: Consider modularization
- **> 3000 tokens**: Should modularize for context efficiency

## Examples

```bash
/estimate-tokens skills/modular-skills/SKILL.md
# Output:
# === skills/modular-skills/SKILL.md ===
# Total tokens: 1,847
# Component breakdown:
#   Frontmatter: 45 tokens
#   Body content: 1,402 tokens
#   Code blocks: 400 tokens
# === Recommendations ===
# GOOD: Optimal token range (800-2000 tokens)

/estimate-tokens skills/skills-eval --include-dependencies
# Includes token costs from referenced modules
```

## Use Cases

### Context Budget Planning
Before adding new content to a skill, estimate current usage to ensure you stay within optimal bounds.

### Modularization Decisions
Compare token costs of monolithic vs modular approaches:
```bash
# Check current monolithic skill
/estimate-tokens skills/big-skill/SKILL.md

# After modularization, check hub + modules
/estimate-tokens skills/big-skill/
```

### Progressive Disclosure Validation
Verify that hub files remain lightweight while modules contain detailed content.

## Integration

Works alongside:
- `/analyze-skill` - Complexity metrics
- `/context-report` - Directory-wide analysis
- `/skills-eval` - Quality scoring

## Implementation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/token_estimator.py --file "${1:-.}"
```
