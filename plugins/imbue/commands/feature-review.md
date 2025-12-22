---
name: feature-review
description: Review implemented features and suggest new features with GitHub integration
usage: /feature-review [--inventory] [--suggest] [--create-issues] [--validate-config]
---

# Feature Review

Review currently implemented features using evidence-based prioritization and suggest new features. Accepted suggestions can be uploaded to GitHub as issues.

## Usage

```bash
# Full review: inventory, score, suggest
/feature-review

# Only inventory current features
/feature-review --inventory

# Generate new feature suggestions
/feature-review --suggest

# Create GitHub issues for accepted suggestions
/feature-review --suggest --create-issues

# Validate configuration file
/feature-review --validate-config

# Override configuration values
/feature-review --threshold.high_priority=3.0
```

## What It Does

1. **Discovers** implemented features from codebase
2. **Classifies** features as proactive/reactive and static/dynamic
3. **Scores** features using hybrid RICE+WSJF framework
4. **Analyzes** tradeoffs across quality dimensions
5. **Suggests** new features based on gaps and opportunities
6. **Creates** GitHub issues for accepted suggestions

## Workflow

### Phase 1: Feature Inventory

Scan the codebase to discover implemented features:
- Commands, skills, agents, hooks
- Public APIs and exports
- Documented features in README/CHANGELOG

### Phase 2: Classification

Classify each feature along two axes:

**Type Axis:**
- **Proactive:** Anticipates user needs (suggestions, prefetching)
- **Reactive:** Responds to explicit input (commands, forms)

**Data Axis:**
- **Static:** Updated incrementally (configs, schemas)
- **Dynamic:** Updated continuously (sessions, real-time data)

### Phase 3: Scoring

Apply hybrid prioritization scoring:

```
Score = (Value Score / Cost Score) * Confidence
```

**Value Factors:** Reach, Impact, Business Value, Time Criticality
**Cost Factors:** Effort, Risk, Complexity

**Thresholds:**
- **> 2.5:** High priority (implement soon)
- **1.5 - 2.5:** Medium priority (roadmap)
- **< 1.5:** Low priority (backlog)

### Phase 4: Tradeoff Analysis

Evaluate across nine quality dimensions:
- Quality, Latency, Token Usage
- Resource Usage, Redundancy, Readability
- Scalability, Integration, API Surface

### Phase 5: Suggestions

Based on analysis, suggest:
- New features addressing gaps
- Improvements to low-scoring features
- Deprecation of obsolete features

### Phase 6: GitHub Integration

For accepted suggestions:
1. Generate issue from template
2. Apply priority and classification labels
3. Prompt for user confirmation
4. Create issue via GitHub CLI

## Arguments

| Argument | Description |
|----------|-------------|
| `--inventory` | Only run feature discovery, skip scoring |
| `--suggest` | Include new feature suggestions |
| `--create-issues` | Create GitHub issues (requires `--suggest`) |
| `--validate-config` | Validate configuration file |
| `--dry-run` | Show what would be created without creating |

## Configuration

Create `.feature-review.yaml` in project root to customize:
- Scoring weights and thresholds
- Classification patterns
- Tradeoff dimension weights
- GitHub integration settings

See `Skill(imbue:feature-review)` for full configuration reference.

## Examples

### Full Review

```bash
/feature-review

# Output:
Feature Review Report
=====================

## Inventory (12 features found)

| Feature | Type | Data | Score | Priority |
|---------|------|------|-------|----------|
| skill-loader | Reactive | Static | 2.8 | High |
| auto-complete | Proactive | Dynamic | 2.3 | Medium |
| ...

## Tradeoff Analysis

skill-loader:
  Quality: 5/5 | Latency: 4/5 | Token Usage: 3/5
  Readability: 4/5 | Integration: 5/5 | API Surface: 5/5

## Suggestions

1. [High] Add caching for skill lookups (Score: 2.6)
2. [Medium] Improve error messages (Score: 1.9)
```

### Create Issues

```bash
/feature-review --suggest --create-issues

# Output:
Suggestions ready for GitHub:

1. Add caching for skill lookups
   Score: 2.6 | Classification: Proactive/Static
   Labels: enhancement, priority/high, type/proactive

   Create issue? [y/n]: y

   Created: https://github.com/owner/repo/issues/123
```

## Integration

This command uses:
- `Skill(imbue:feature-review)` - Core scoring and classification
- `Skill(imbue:scope-guard)` - Budget validation for suggestions
- `Skill(imbue:review-core)` - Evidence-based methodology

## Exit Criteria

- Feature inventory complete
- All features classified and scored
- Tradeoff analysis documented
- Suggestions generated (if requested)
- GitHub issues created (if requested)
