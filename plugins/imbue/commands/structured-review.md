---
name: structured-review
description: Start a structured review workflow with evidence logging and formatted output
usage: /structured-review [target]
---

# Start Review Workflow

Initializes a structured review workflow using imbue's core methodology: context establishment, scope inventory, evidence capture, and deliverable structuring.

## Usage

```bash
# Start review of current branch
/structured-review

# Review specific target
/structured-review src/auth/

# Review with specific focus
/structured-review --focus security src/api/
```

## What It Does

1. **Establishes Context**: Confirms repository, branch, and comparison baseline
2. **Inventories Scope**: Lists relevant artifacts for review
3. **Prepares Evidence Log**: Initializes tracking for commands and citations
4. **Structures Deliverables**: Sets up report template with sections

## Workflow Integration

This command orchestrates multiple imbue skills:
- `review-core` - Core workflow scaffolding
- `evidence-logging` - Reproducible evidence capture
- `structured-output` - Consistent deliverable formatting
- `diff-analysis` - Change categorization (if diffs involved)

## Examples

```bash
/structured-review
# Output:
# Review Workflow Initialized
# ===========================
# Repository: my-project
# Branch: feature/auth-overhaul
# Baseline: main (3 commits behind)
#
# TodoWrite items created:
# - [ ] review-core:context-established
# - [ ] review-core:scope-inventoried
# - [ ] review-core:evidence-captured
# - [ ] review-core:deliverables-structured

/structured-review src/api --focus performance
# Scoped review with performance focus
```

## Output

Creates structured review scaffold with:
- Context summary (repo, branch, baseline)
- Scope inventory (files, configs, specs)
- Evidence log template
- Deliverable outline

## Feature Review Mode

When invoked with `--mode feature` or `--features`, structured-review runs a feature-focused review workflow (formerly the standalone `/feature-review` command). This mode discovers, classifies, scores, and suggests features using evidence-based prioritization.

### Feature Review Usage

```bash
# Full feature review: inventory, score, suggest
/structured-review --mode feature

# Only inventory current features
/structured-review --mode feature --inventory

# Generate new feature suggestions
/structured-review --mode feature --suggest

# Create GitHub issues for accepted suggestions
/structured-review --mode feature --suggest --create-issues

# Validate configuration file
/structured-review --mode feature --validate-config
```

### Feature Review Phases

1. **Discovers** implemented features from codebase (commands, skills, agents, hooks, APIs)
2. **Classifies** features as proactive/reactive and static/dynamic
3. **Scores** features using hybrid RICE+WSJF framework
4. **Analyzes** tradeoffs across quality dimensions (Quality, Latency, Token Usage, Resource Usage, Redundancy, Readability, Scalability, Integration, API Surface)
5. **Suggests** new features based on gaps and opportunities
6. **Creates** GitHub issues for accepted suggestions (with `--create-issues`)

### Scoring

```
Score = (Value Score / Cost Score) * Confidence
```

**Thresholds:**
- **> 2.5:** High priority (implement soon)
- **1.5 - 2.5:** Medium priority (roadmap)
- **< 1.5:** Low priority (backlog)

### Configuration

Create `.feature-review.yaml` in project root to customize scoring weights, classification patterns, tradeoff dimension weights, and GitHub integration settings. See `Skill(imbue:feature-review)` for full configuration reference.

### Feature Review Integration

This mode uses:
- `Skill(imbue:feature-review)` - Core scoring and classification
- `Skill(imbue:scope-guard)` - Budget validation for suggestions
- `Skill(imbue:review-core)` - Evidence-based methodology

## Exit Criteria

- All TodoWrite items from review-core created
- Evidence log initialized with session context
- Deliverable template ready for findings
