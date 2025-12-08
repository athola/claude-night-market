# Imbue Plugin

A collection of reusable workflow patterns for analysis, evidence gathering, and structured reporting.

## Overview

Imbue skills provide structured, repeatable methodologies for analyzing information. They are not tied to a specific tool or domain, but instead offer a framework for how to approach common analysis tasks.

The core principles are:
- **Generalizable**: The patterns can be applied to various inputs, such as git diffs, API specifications, or system logs.
- **Composable**: Skills can be chained together to build complex analysis workflows.
- **Evidence-based**: Each step emphasizes capturing evidence to ensure analysis is reproducible and traceable.

## Skills

### Review Patterns

#### review-core
A foundational workflow for starting and structuring any detailed review.

**When to Use:**
This skill provides a consistent starting point for any in-depth review, such as for architecture, security, or code quality. It helps establish scope and reporting structure before the main analysis begins.

**Required TodoWrite Items:**
1. `review-core:context-established` - Verify scope, baseline, and stakeholders.
2. `review-core:scope-inventoried` - List artifacts under review and state assumptions.
3. `review-core:evidence-captured` - Log commands and outputs.
4. `review-core:deliverables-structured` - Prepare a skeleton for the final report.
5. `review-core:contingencies-documented` - Document any contingency plans.

### Analysis Methods

#### diff-analysis
A method for analyzing a "before and after" to categorize changes, assess risks, and create a summary of what is important.

**When to Use:**
Use this skill to understand the impact of changes between two versions of something. It is useful for code reviews, preparing release notes, or analyzing configuration changes. The goal is to answer "What changed and why does it matter?".

**Application Examples:** Git diffs, API specification changes, infrastructure configuration migrations, database schema updates, or document revisions.

**Required TodoWrite Items:**
1. `diff-analysis:baseline-established` - Define the "before" and "after" for comparison.
2. `diff-analysis:changes-categorized` - Group changes by their function or purpose.
3. `diff-analysis:risks-assessed` - Evaluate the potential impact and risks of the changes.
4. `diff-analysis:summary-prepared` - Write a summary of the important changes and their implications.

#### catchup
A method for quickly understanding the recent activity in a project to identify what happened and what to do next.

**When to Use:**
Use this when you need to get up to speed on a project, for example, after being away or when joining a new team. It helps in understanding the current state and planning future work.

**Application Examples:** Reviewing a git branch, checking sprint progress, summarizing a series of meetings, or reviewing document revisions.

**Required TodoWrite Items:**
1. `catchup:context-confirmed` - Define the scope and time period for the catch-up.
2. `catchup:delta-captured` - Gather the raw information about what has changed.
3. `catchup:insights-extracted` - Summarize what changed, why it changed, and what the implications are.
4. `catchup:followups-recorded` - List any action items or next steps.

### Output Patterns

#### evidence-logging
A workflow for capturing the evidence used in an analysis, so that findings can be traced back to their source.

**When to Use:**
Use this throughout any analysis to create a record of your work. This is important when recommendations need to be backed by verifiable data.

**Required TodoWrite Items:**
1. `evidence-logging:log-initialized` - Set up a structured log for evidence.
2. `evidence-logging:commands-captured` - Record the commands used to generate evidence.
3. `evidence-logging:citations-recorded` - Note any external sources that were used.
4. `evidence-logging:artifacts-indexed` - Create a catalog of any generated files or artifacts.

#### structured-output
A pattern for formatting the final output of an analysis for clarity and consistency.

**When to Use:**
Use this skill when preparing the final report or deliverable. It helps make the results easy to understand and act on.

**Required TodoWrite Items:**
1. `structured-output:template-selected` - Choose a suitable format for the output.
2. `structured-output:findings-formatted` - Structure the findings in a consistent way.
3. `structured-output:actions-assigned` - Clearly define any action items.
4. `structured-output:appendix-attached` - Attach any supporting materials.

## Plugin Structure

```
imbue/
├── plugin.json              # Plugin configuration
├── README.md               # This file
└── skills/
    ├── review-core/        # Review workflow scaffolding
    ├── evidence-logging/   # Evidence capture methodology
    ├── structured-output/  # Output formatting patterns
    ├── diff-analysis/      # Change analysis methodology
    └── catchup/            # Summarization methodology
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

# Output patterns
Skill(imbue:evidence-logging)
Skill(imbue:structured-output)
```

## Integration

These skills work well as foundations for architecture reviews, code audits, and security assessments. For git-based work, run `Skill(sanctum:git-workspace-review)` first to gather data, then apply imbue's analysis patterns.

## License

MIT
