# Skill Review

Analyze skill performance metrics and identify improvement opportunities.

## Arguments

- `--plugin <name>` - Review skills for a specific plugin
- `--all-plugins` - Review skills across all plugins
- `--recommendations` - Include actionable recommendations
- `--threshold <float>` - Stability gap threshold (default: 0.3)

## What It Does

1. **Scans skill directories** for SKILL.md files
2. **Analyzes skill structure** for quality indicators:
   - Proper frontmatter (name, description, tags, estimated_tokens)
   - Module organization (modules/ directory for large skills)
   - Documentation completeness
3. **Checks for common issues**:
   - Missing or incomplete frontmatter
   - Skills exceeding token budget (>2000 tokens)
   - Missing test coverage
   - Unused or orphaned modules
4. **Generates recommendations** based on findings

## Workflow

### Basic Usage

```bash
# Review all skills in a plugin
/skill-review --plugin conserve

# Review all plugins with recommendations
/skill-review --all-plugins --recommendations
```

### Manual Review Process

If automated tooling isn't available, perform manual review:

#### Step 1: List All Skills

```bash
find plugins/<plugin-name>/skills -name "SKILL.md" -type f
```

#### Step 2: Check Frontmatter Quality

Each SKILL.md should have:
```yaml
---
name: skill-name
description: |
  Triggers: keyword1, keyword2
  Clear description of what the skill does.
category: development|workflow|optimization|review
tags: [relevant, tags]
tools: []
complexity: low|medium|high
estimated_tokens: <number>
---
```

#### Step 3: Assess Token Budget

Skills should target:
- **Low complexity**: 300-600 tokens
- **Medium complexity**: 600-1200 tokens
- **High complexity**: 1200-2000 tokens

Skills exceeding 2000 tokens should be modularized.

#### Step 4: Check Module Structure

For skills with modules:
```bash
ls plugins/<plugin>/skills/<skill-name>/modules/
```

Verify modules are:
- Referenced from main SKILL.md
- Not orphaned (loaded but never used)
- Appropriately sized

### Quality Indicators

| Indicator | Good | Warning | Critical |
|-----------|------|---------|----------|
| Frontmatter | Complete | Missing tags/tokens | Missing name/description |
| Token count | Under budget | 10% over | >50% over |
| Modules | All referenced | Some orphaned | Circular refs |
| Tests | Unit tests exist | Integration only | No tests |

## Output Format

```
## Skill Review: <plugin-name>

### Summary
- Skills reviewed: N
- Healthy: N
- Warnings: N
- Critical: N

### Issues Found

#### Critical
- [ ] skill-name: Missing frontmatter description
- [ ] skill-name: Exceeds token budget by 150%

#### Warnings
- [ ] skill-name: Missing estimated_tokens
- [ ] skill-name: No test coverage

### Recommendations
1. Add frontmatter to skill-name
2. Modularize skill-name (currently 3500 tokens)
3. Add tests for skill-name
```

## Integration

This command is invoked automatically by `/update-plugins` Phase 2.

Related commands:
- `/skill-logs` - View execution history and failures
- `/update-plugins` - Full plugin registration audit
- `abstract:skill-auditor` - Deep skill quality analysis

## See Also

- `abstract:validate-plugin-structure` - Plugin structure validation
- `conserve:bloat-detector` - General bloat detection
