---
name: feature-review
description: |
  Feature review and prioritization with RICE/WSJF/Kano scoring. Creates GitHub issues for suggestions.

  Triggers: feature review, prioritization, RICE, WSJF, roadmap, backlog
  Use when: reviewing features or suggesting new features
  DO NOT use when: evaluating single feature scope - use scope-guard.
category: workflow-methodology
tags: [feature-review, prioritization, RICE, WSJF, Kano, roadmap, backlog]
dependencies:
  - imbue:scope-guard
  - imbue:review-core
tools:
  - gh (GitHub CLI)
usage_patterns:
  - feature-inventory
  - prioritization-scoring
  - suggestion-generation
  - github-integration
complexity: intermediate
estimated_tokens: 3500
modules:
  - modules/scoring-framework.md
  - modules/classification-system.md
  - modules/tradeoff-dimensions.md
  - modules/configuration.md
---

# Feature Review

Review currently implemented features and suggest new features using evidence-based prioritization. Features can be uploaded to GitHub as issues after user acceptance.

## Philosophy

**Core Belief:** Feature decisions should be data-driven, not gut-driven. Every feature has tradeoffs that deserve explicit evaluation.

**Three Pillars:**
1. **Evidence-Based Scoring** - Hybrid RICE+WSJF with Kano classification
2. **Configurable Heuristics** - Opinionated defaults, flexible customization
3. **Actionable Output** - GitHub issues, not just reports

## When to Use

- Periodic roadmap reviews (sprint planning, quarterly reviews)
- When deciding what to build next
- After shipping a major feature (retrospective evaluation)
- When stakeholders ask "why aren't we building X?"
- Before starting a new development cycle

## When NOT to Use

- Emergency bug fixes (just fix it)
- Simple documentation updates
- During active implementation (use scope-guard instead)

## Quick Start

### 1. Inventory Current Features

Discover and categorize existing features:
```bash
/feature-review --inventory
```

### 2. Score and Classify

Evaluate features against prioritization framework:
```bash
/feature-review
```

### 3. Generate Suggestions

Review gaps and suggest new features:
```bash
/feature-review --suggest
```

### 4. Upload to GitHub

Create issues for accepted suggestions:
```bash
/feature-review --suggest --create-issues
```

## Core Workflow

### Phase 1: Feature Discovery (`feature-review:inventory-complete`)

Identify implemented features by analyzing:

1. **Code artifacts**
   - Entry points (commands, skills, agents, hooks)
   - Public APIs and exports
   - Configuration surfaces

2. **Documentation**
   - README features lists
   - CHANGELOG entries
   - User-facing docs

3. **Git history**
   - Recent feature commits
   - Feature branches

**Output:** Feature inventory table with metadata

### Phase 2: Classification (`feature-review:classified`)

Classify each feature along two axes:

**Axis 1: Proactive vs Reactive**

| Type | Definition | Latency Tolerance | Examples |
|------|------------|-------------------|----------|
| **Proactive** | Anticipates user needs | Higher (background OK) | Suggestions, prefetching, auto-saves |
| **Reactive** | Responds to explicit input | Low (must feel instant) | Form handling, click actions, validation |

**Axis 2: Static vs Dynamic**

| Type | Update Pattern | Storage Model | Lookup Cost |
|------|---------------|---------------|-------------|
| **Static** | Incremental, versioned | File-based, cached | O(1), deterministic |
| **Dynamic** | Continuous, streaming | Database, real-time | O(log n), variable |

See [classification-system.md](modules/classification-system.md) for details.

### Phase 3: Scoring (`feature-review:scored`)

Apply hybrid RICE+WSJF scoring:

```
Feature Score = Value Score / Cost Score

Value Score = (Reach + Impact + Business Value + Time Criticality) / 4
Cost Score = (Effort + Risk + Complexity) / 3

Adjusted Score = Feature Score * Confidence
```

**Scoring Scale:** Fibonacci (1, 2, 3, 5, 8, 13)

**Thresholds:**
- **> 2.5** - High priority (implement soon)
- **1.5 - 2.5** - Medium priority (roadmap candidate)
- **< 1.5** - Low priority (backlog or defer)

See [scoring-framework.md](modules/scoring-framework.md) for full framework.

### Phase 4: Tradeoff Analysis (`feature-review:tradeoffs-analyzed`)

Evaluate each feature across quality dimensions:

| Dimension | Question | Scale |
|-----------|----------|-------|
| **Quality** | Does it deliver correct results? | 1-5 |
| **Latency** | Does it meet timing requirements? | 1-5 |
| **Token Usage** | Is it context-efficient? | 1-5 |
| **Resource Usage** | Is CPU/memory reasonable? | 1-5 |
| **Redundancy** | Does it handle failures gracefully? | 1-5 |
| **Readability** | Can others understand it? | 1-5 |
| **Scalability** | Will it handle 10x load? | 1-5 |
| **Integration** | Does it play well with others? | 1-5 |
| **API Surface** | Is it backward compatible? | 1-5 |

See [tradeoff-dimensions.md](modules/tradeoff-dimensions.md) for evaluation criteria.

### Phase 5: Gap Analysis & Suggestions (`feature-review:suggestions-generated`)

Based on inventory and scores:

1. **Identify gaps** - Missing Kano basics, underserved user needs
2. **Surface opportunities** - High-value, low-effort features
3. **Flag technical debt** - Features with declining scores
4. **Recommend actions** - Build, improve, deprecate, or maintain

### Phase 6: GitHub Integration (`feature-review:issues-created`)

For accepted suggestions:

1. Generate issue title and body from suggestion
2. Apply appropriate labels (feature, enhancement, priority/*)
3. Link to related existing issues
4. Prompt user for confirmation before creation

## Configuration

Feature-review uses opinionated defaults but allows project customization.

### Configuration File

Create `.feature-review.yaml` in project root to customize:

```yaml
# .feature-review.yaml
version: 1

# Scoring weights (must sum to 1.0 within category)
weights:
  value:
    reach: 0.25
    impact: 0.30
    business_value: 0.25
    time_criticality: 0.20
  cost:
    effort: 0.40
    risk: 0.30
    complexity: 0.30

# Score thresholds
thresholds:
  high_priority: 2.5      # > this = implement soon
  medium_priority: 1.5    # > this = roadmap
  # below medium = backlog

# Classification defaults
classification:
  default_type: reactive  # proactive | reactive
  default_data: static    # static | dynamic

# Tradeoff dimension weights (0.0 to disable, 1.0 = normal)
tradeoffs:
  quality: 1.0
  latency: 1.0
  token_usage: 1.0
  resource_usage: 0.8
  redundancy: 0.5
  readability: 1.0
  scalability: 0.8
  integration: 1.0
  api_surface: 1.0

# GitHub integration
github:
  auto_label: true
  label_prefix: "priority/"
  default_labels:
    - enhancement
  issue_template: |
    ## Feature Request

    **Classification:** {{ classification }}
    **Priority Score:** {{ score }}

    ### Description
    {{ description }}

    ### Value Proposition
    {{ value_proposition }}

    ### Tradeoff Considerations
    {{ tradeoffs }}
```

See [configuration.md](modules/configuration.md) for all options.

### Guardrails (Always Enforced)

These rules apply regardless of configuration:

1. **Minimum dimensions** - At least 5 tradeoff dimensions must be evaluated
2. **Confidence requirement** - Scores below 50% confidence flagged for review
3. **Breaking change warning** - API surface changes require explicit acknowledgment
4. **Backlog limit** - Max 25 items in suggestion queue (forces prioritization)

## Required TodoWrite Items

When running feature-review, create these todos:

1. `feature-review:inventory-complete`
2. `feature-review:classified`
3. `feature-review:scored`
4. `feature-review:tradeoffs-analyzed`
5. `feature-review:suggestions-generated`
6. `feature-review:issues-created` (if --create-issues)

## Integration Points

### With imbue:scope-guard

Feature-review feeds scope-guard decisions:
- New feature suggestions get Worthiness Scores
- High-priority features inform branch budgets
- Backlog items ranked by Feature Score

### With sanctum:fix-issue

When fixing issues, check feature-review scores:
- High-score features get priority attention
- Low-score features may warrant scope discussion

### With superpowers:brainstorming

During brainstorming, invoke feature-review to:
- Compare new ideas against existing features
- Identify gaps that new ideas could fill
- Score proposals before planning

## Output Format

### Feature Inventory Table

```markdown
| Feature | Type | Data | Score | Priority | Status |
|---------|------|------|-------|----------|--------|
| Auth middleware | Reactive | Dynamic | 2.8 | High | Stable |
| Skill loader | Reactive | Static | 2.3 | Medium | Needs improvement |
| Auto-suggestions | Proactive | Dynamic | 1.8 | Medium | New opportunity |
```

### Suggestion Report

```markdown
## Feature Suggestions

### High Priority (Score > 2.5)

1. **[Feature Name]** (Score: 2.7)
   - Classification: Proactive/Dynamic
   - Value: High reach, addresses user pain point
   - Cost: Moderate effort, low risk
   - Recommendation: Build in next sprint

### Medium Priority (Score 1.5-2.5)

...

### Backlog (Score < 1.5)

...
```

## Related Skills

- `imbue:scope-guard` - Prevents overengineering during implementation
- `imbue:review-core` - Structured review methodology
- `sanctum:pr-review` - Code-level feature review

## Module Reference

- **[scoring-framework.md](modules/scoring-framework.md)** - RICE+WSJF hybrid, Kano classification
- **[classification-system.md](modules/classification-system.md)** - Proactive/reactive, static/dynamic axes
- **[tradeoff-dimensions.md](modules/tradeoff-dimensions.md)** - Quality attribute evaluation
- **[configuration.md](modules/configuration.md)** - Customization options and guardrails
