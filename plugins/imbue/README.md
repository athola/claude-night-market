# Imbue Plugin

Reusable workflow patterns for analysis, evidence gathering, and structured reporting.

## Overview

Imbue provides analysis methodologies, offering a framework for approaching common problems independent of specific tools.

Principles:
- **Generalizable**: Patterns apply to various inputs like git diffs, specs, and logs.
- **Composable**: Skills chain together for complex workflows.
- **Evidence-based**: Focus on capturing evidence for reproducibility.

## Skills

### Review Patterns

#### review-core
Structure for starting reviews.

**When to Use:**
Use for architecture, security, or code quality reviews to establish scope and structure before analysis.

**Required TodoWrite Items:**
1. `review-core:context-established`: Verify scope, baseline, and stakeholders.
2. `review-core:scope-inventoried`: List artifacts and assumptions.
3. `review-core:evidence-captured`: Log commands and outputs.
4. `review-core:deliverables-structured`: Prepare report skeleton.
5. `review-core:contingencies-documented`: Document contingency plans.

### Analysis Methods

#### diff-analysis
Analyze "before and after" states to categorize changes and assess risks.

**When to Use:**
Use to understand the impact of changes in code reviews, release notes, or config updates.

**Required TodoWrite Items:**
1. `diff-analysis:baseline-established`: Define "before" and "after".
2. `diff-analysis:changes-categorized`: Group changes by function.
3. `diff-analysis:risks-assessed`: Evaluate potential impact.
4. `diff-analysis:summary-prepared`: Summarize changes and implications.

#### catchup
Summarize recent project activity.

**When to Use:**
Use to get up to speed after time away or when joining a team.

**Required TodoWrite Items:**
1. `catchup:context-confirmed`: Define scope and time period.
2. `catchup:delta-captured`: Gather raw change information.
3. `catchup:insights-extracted`: Summarize changes and implications.
4. `catchup:followups-recorded`: List action items.

### Workflow Guards

#### scope-guard
Prevent overengineering via scoring and opportunity cost comparison. Components include:
- `decision-framework`: Worthiness formula and scoring system.
- `anti-overengineering`: Rules to prevent scope creep.
- `branch-management`: Threshold monitoring.
- `baseline-scenarios`: Validated test scenarios.

**When to Use:**
Use during planning to evaluate if features should be implemented now or deferred.

**Required TodoWrite Items:**
1. `scope-guard:worthiness-scored`: Calculate feature score.
2. `scope-guard:backlog-compared`: Compare against queued items.
3. `scope-guard:budget-checked`: Verify branch budget.
4. `scope-guard:decision-documented`: Record decision.

### Feature Planning

#### feature-review
Evidence-based feature prioritization using hybrid RICE+WSJF scoring. Components include:
- `scoring-framework`: Hybrid RICE+WSJF scoring.
- `classification-system`: Feature classification.
- `tradeoff-dimensions`: Quality dimensions based on ISO 25010.
- `configuration`: YAML configuration with guardrails.

**When to Use:**
Use to inventory features, score and prioritize them, and analyze tradeoffs.

**Required TodoWrite Items:**
1. `feature-review:inventory-complete`: Catalog features.
2. `feature-review:classification-applied`: Classify features.
3. `feature-review:scoring-complete`: Calculate priority scores.
4. `feature-review:tradeoffs-analyzed`: Evaluate quality dimensions.
5. `feature-review:gaps-identified`: Identify improvement opportunities.
6. `feature-review:issues-created`: Create GitHub issues if requested.

### Output Patterns

#### evidence-logging
Capture evidence used in analysis for traceability.

**When to Use:**
Use during analysis to create a record of work and back recommendations with data.

**Required TodoWrite Items:**
1. `evidence-logging:log-initialized`: Set up evidence log.
2. `evidence-logging:commands-captured`: Record commands.
3. `evidence-logging:citations-recorded`: Note external sources.
4. `evidence-logging:artifacts-indexed`: Catalog generated files.

#### structured-output
Format final analysis output.

**When to Use:**
Use when preparing the final report for consistency.

**Required TodoWrite Items:**
1. `structured-output:template-selected`: Choose format.
2. `structured-output:findings-formatted`: Structure findings.
3. `structured-output:actions-assigned`: Define action items.
4. `structured-output:appendix-attached`: Attach supporting materials.

## Plugin Structure

```
imbue/
├── plugin.json              # Plugin configuration
├── README.md               # This file
├── hooks/
│   ├── hooks.json           # Hook configuration
│   ├── session-start.sh     # Session initialization
│   ├── user-prompt-submit.sh # Per-prompt threshold checks
│   └── pre-pr-scope-check.sh # Branch threshold monitoring
├── commands/
│   ├── full-review.md       # Structured review command
│   ├── catchup.md           # Quick catchup command
│   └── feature-review.md    # Feature prioritization command
└── skills/
    ├── review-core/        # Review workflow scaffolding
    ├── evidence-logging/   # Evidence capture methodology
    ├── structured-output/  # Output formatting patterns
    ├── diff-analysis/      # Change analysis methodology
    ├── catchup/            # Summarization methodology
    ├── scope-guard/        # Anti-overengineering guardrails
    └── feature-review/     # Feature prioritization framework
```

## Dependencies

None.

## Usage

```bash
# Review scaffolding
Skill(imbue:review-core)

# Analysis methodologies
Skill(imbue:diff-analysis)
Skill(imbue:catchup)

# Workflow guards
Skill(imbue:scope-guard)

# Feature planning
Skill(imbue:feature-review)

# Output patterns
Skill(imbue:evidence-logging)
Skill(imbue:structured-output)

# Commands
/feature-review              # Full review: inventory, score, suggest
/feature-review --inventory  # Only discover features
/feature-review --suggest    # Include new feature suggestions
/feature-review --suggest --create-issues  # Create GitHub issues
```

## Integration

Use these skills for architecture reviews, code audits, and security assessments. For git-based work, run `Skill(sanctum:git-workspace-review)` first, then apply imbue's analysis patterns.

## Session Forking Workflows (Claude Code 2.0.73+)

Session forking enables parallel evidence analysis from multiple perspectives without context contamination.

### Use Cases

**Multi-Perspective Code Analysis**
```bash
# Main session: Initial analysis
claude "Analyze this codebase for issues"

# Fork for security perspective
claude --fork-session --session-id "security-evidence" --resume
> "Analyze the same codebase exclusively from a security perspective"

# Fork for performance perspective
claude --fork-session --session-id "performance-evidence" --resume
> "Analyze the same codebase exclusively from a performance perspective"

# Fork for maintainability perspective
claude --fork-session --session-id "maintainability-evidence" --resume
> "Analyze the same codebase exclusively from a maintainability perspective"

# Consolidate findings from all perspectives
```

**Parallel Feature Evaluation**
```bash
# Main session: Feature request received
claude "Evaluate this feature request"

# Fork for RICE scoring
claude --fork-session --session-id "rice-scoring" --resume
> "Skill(imbue:feature-review) using RICE methodology"

# Fork for WSJF scoring
claude --fork-session --session-id "wsjf-scoring" --resume
> "Skill(imbue:feature-review) using WSJF methodology"

# Compare scores and make informed decision
```

**Alternative Evidence Collection Strategies**
```bash
# Main session: Review needed
claude "Review this architecture"

# Fork A: Bottom-up analysis
claude --fork-session --session-id "bottom-up-review" --resume
> "Skill(imbue:review-core) starting from implementation details"

# Fork B: Top-down analysis
claude --fork-session --session-id "top-down-review" --resume
> "Skill(imbue:review-core) starting from high-level architecture"

# Combine insights for full review
```

### Best Practices

- **Clear scope per fork**: Each fork should focus on one analytical perspective.
- **Evidence extraction**: Save evidence logs to files before closing forks.
- **Consolidation workflow**: Create a summary that synthesizes findings from all forks.
- **Descriptive session IDs**: Use the perspective name in the ID (e.g., "security-audit-pr-42").

See `plugins/abstract/docs/claude-code-compatibility.md` for detailed session forking patterns.

## License

MIT
