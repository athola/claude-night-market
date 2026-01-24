# Imbue

Analysis methodologies and workflow patterns for evidence gathering and structured reporting.

## Overview

Imbue provides technical evidence capture for reproducible analysis across git diffs, specifications, and logs. We focus on audit trails and empirical verification rather than theoretical assessments. These methodologies ensure that recommendations are backed by specific data points and actual command outputs.

## Analysis and Review Patterns

### Review Methodology
The `review-core` skill establishes scope and baselines for architecture, security, or code quality audits. It requires verifying assumptions and documenting artifacts before starting the analysis. Findings are logged with direct command evidence to support the final deliverables.

### Change Analysis
We use `diff-analysis` to categorize changes and evaluate risks in code reviews or release notes. This involves establishing a clear baseline between "before" and "after" states to understand the functional impact of modifications. For project activity summaries, `catchup` gathers raw change information to extract specific insights and action items.

## Workflow Guards and Enforcement

### Scope and Reasoning
`scope-guard` prevents overengineering by using a decision framework to score feature worthiness against opportunity costs. This includes threshold monitoring and baseline scenarios to ensure that development remains focused on essential work.

To counter sycophantic reasoning, `rigorous-reasoning` uses checklist-based analysis that prioritizes truth-seeking over social comfort. It requires committing to conclusions without inappropriate hedging and following an incremental reasoning protocol for complex problem-solving.

### Proof of Work
The `proof-of-work` skill requires functional verification before any claim of completion is accepted. This is enforced by the `tdd_bdd_gate.py` PreToolUse hook, which checks for corresponding test files during write operations to implementation files. Completion claims must be backed by evidence of problem reproduction and verified fixes with actual test runs.

## Feature Planning and Monitoring

### Feature Review
`feature-review` uses a hybrid RICE+WSJF scoring framework to prioritize features based on quality dimensions and tradeoffs. This process involves cataloging features and identifying improvement gaps to guide development decisions.

### Monitoring
`workflow-monitor` tracks execution for inefficiencies or errors. When a failure or timeout is detected, it automatically captures the relevant logs and context to create GitHub issues for remediation.

## Output and Documentation

Analysis results are structured through `evidence-logging` and `structured-output`. We record all commands, citations, and artifacts to provide a traceable record of the work. Final reports use established templates to ensure that findings and action items are clearly defined.

## Plugin Structure

## Plugin Structure

```
imbue/
├── plugin.json              # Plugin configuration
├── README.md               # This file
├── hooks/
│   ├── hooks.json           # Hook configuration
│   ├── session-start.sh     # Session initialization
│   ├── user-prompt-submit.sh # Per-prompt threshold checks
│   ├── pre-pr-scope-check.sh # Branch threshold monitoring
│   └── tdd_bdd_gate.py      # PreToolUse: Iron Law enforcement
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
    ├── rigorous-reasoning/ # Anti-sycophancy guardrails
    ├── feature-review/     # Feature prioritization framework
    ├── proof-of-work/      # Verification enforcement
    └── workflow-monitor/   # Execution monitoring and issue creation
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
Skill(imbue:rigorous-reasoning)

# Feature planning
Skill(imbue:feature-review)

# Verification
Skill(imbue:proof-of-work)

# Workflow monitoring
Skill(imbue:workflow-monitor)

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

Session forking allows parallel evidence analysis from multiple perspectives without context overlap.

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
