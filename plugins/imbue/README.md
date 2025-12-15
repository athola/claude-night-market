# Imbue Plugin

Reusable workflow patterns for analysis, evidence gathering, and structured reporting.

## Overview

Imbue skills provide methodologies for analysis tasks. They offer a framework for approaching common problems independent of specific tools.

Principles:
- **Generalizable**: Patterns apply to various inputs (git diffs, specs, logs).
- **Composable**: Skills chain together for complex workflows.
- **Evidence-based**: Emphasizes capturing evidence for reproducibility.

## Skills

### Review Patterns

#### review-core
Structure for starting detailed reviews.

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
Analyzes "before and after" states to categorize changes and assess risks.

**When to Use:**
Use to understand the impact of changes (code reviews, release notes, config changes). Answers "What changed and why does it matter?".

**Required TodoWrite Items:**
1. `diff-analysis:baseline-established`: Define "before" and "after".
2. `diff-analysis:changes-categorized`: Group changes by function.
3. `diff-analysis:risks-assessed`: Evaluate potential impact.
4. `diff-analysis:summary-prepared`: Summarize changes and implications.

#### catchup
Summarizes recent project activity.

**When to Use:**
Use to get up to speed after time away or when joining a team. Helps understand current state and plan future work.

**Required TodoWrite Items:**
1. `catchup:context-confirmed`: Define scope and time period.
2. `catchup:delta-captured`: Gather raw change information.
3. `catchup:insights-extracted`: Summarize changes and implications.
4. `catchup:followups-recorded`: List action items.

### Workflow Guards

#### scope-guard
Prevents overengineering via scoring and opportunity cost comparison.

**When to Use:**
Use during planning to evaluate if features should be implemented now or deferred. Also triggered by hooks for branch metrics.

**Required TodoWrite Items:**
1. `scope-guard:worthiness-scored`: Calculate feature score.
2. `scope-guard:backlog-compared`: Compare against queued items.
3. `scope-guard:budget-checked`: Verify branch budget.
4. `scope-guard:decision-documented`: Record decision.

### Output Patterns

#### evidence-logging
Captures evidence used in analysis for traceability.

**When to Use:**
Use during analysis to create a record of work and back recommendations with data.

**Required TodoWrite Items:**
1. `evidence-logging:log-initialized`: Set up evidence log.
2. `evidence-logging:commands-captured`: Record commands.
3. `evidence-logging:citations-recorded`: Note external sources.
4. `evidence-logging:artifacts-indexed`: Catalog generated files.

#### structured-output
Formats final analysis output.

**When to Use:**
Use when preparing the final report to ensure consistency and readability.

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
│   └── pre-pr-scope-check.sh  # Branch threshold monitoring
└── skills/
    ├── review-core/        # Review workflow scaffolding
    ├── evidence-logging/   # Evidence capture methodology
    ├── structured-output/  # Output formatting patterns
    ├── diff-analysis/      # Change analysis methodology
    ├── catchup/            # Summarization methodology
    └── scope-guard/        # Anti-overengineering guardrails
```

## Dependencies

None - this is a foundational methodology plugin.

## Usage

```bash
# Review scaffolding
Skill(imbue:review-core)

# Analysis methodologies
Skill(imbue:diff-analysis)
Skill(imbue:catchup)

# Workflow guards
Skill(imbue:scope-guard)

# Output patterns
Skill(imbue:evidence-logging)
Skill(imbue:structured-output)
```

## Integration

Use these skills for architecture reviews, code audits, and security assessments. For git-based work, run `Skill(sanctum:git-workspace-review)` first, then apply imbue's analysis patterns.

## License

MIT
