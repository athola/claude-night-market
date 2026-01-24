# Imbue

Analysis methodologies and workflow patterns for evidence gathering and structured reporting.

## Overview

Imbue provides technical evidence capture for reproducible analysis across git diffs, specifications, and logs. It focuses on audit trails and empirical verification rather than theoretical assessments. These methodologies back recommendations with specific data points and command outputs.

## Analysis and Review Patterns

### Review Methodology
The `review-core` skill establishes scope and baselines for architecture, security, or code quality audits. It requires validating assumptions and documenting artifacts before starting the analysis. Findings are logged with direct command evidence to support final deliverables.

### Change Analysis
`diff-analysis` categorizes changes and evaluates risks in code reviews or release notes. This involves establishing a clear baseline between "before" and "after" states to understand functional impact. For project activity summaries, `catchup` gathers raw change information to extract specific insights and action items.

## Workflow Guards and Enforcement

### Scope and Reasoning
`scope-guard` helps prevent overengineering by using a decision framework to score feature worthiness against opportunity costs. This includes threshold monitoring and baseline scenarios to keep development focused on essential work.

To counter sycophantic reasoning, `rigorous-reasoning` uses checklist-based analysis that prioritizes truth-seeking over social comfort. It requires committing to conclusions without hedging and following an incremental reasoning protocol for complex problem-solving.

### Proof of Work
The `proof-of-work` skill requires functional verification before a claim of completion is accepted. This is enforced by the `tdd_bdd_gate.py` PreToolUse hook, which checks for corresponding test files during write operations to implementation files. Completion claims must be backed by evidence of problem reproduction and verified fixes with actual test runs.

## Feature Planning and Monitoring

### Feature Review
`feature-review` uses a hybrid RICE+WSJF scoring framework to prioritize features based on quality dimensions and tradeoffs. This process involves cataloging features and identifying improvement gaps to guide development decisions.

### Monitoring
`workflow-monitor` tracks execution for inefficiencies or errors. When a failure or timeout occurs, it automatically captures relevant logs and context to create GitHub issues for remediation.

## Output and Documentation

Analysis results are structured through `evidence-logging` and `structured-output`. We record all commands, citations, and artifacts to provide a traceable record of the work. Final reports use established templates to define findings and action items.

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

## Usage

Use `Skill(imbue:review-core)` for review scaffolding and `Skill(imbue:diff-analysis)` or `Skill(imbue:catchup)` for analysis methodologies. `Skill(imbue:scope-guard)` and `Skill(imbue:rigorous-reasoning)` provide workflow guardrails. Feature planning uses `Skill(imbue:feature-review)`, while `Skill(imbue:proof-of-work)` handles verification. `Skill(imbue:workflow-monitor)` tracks execution, and output patterns are managed via `Skill(imbue:evidence-logging)` and `Skill(imbue:structured-output)`.

Commands include `/feature-review` for full inventory, scoring, and suggestions. Append `--inventory` to only discover features, or `--suggest` to include new feature suggestions. Use `--create-issues` to automate GitHub issue creation for suggestions.

## Session Forking (Claude Code 2.0.73+)

Session forking allows parallel evidence analysis from multiple perspectives without context overlap.

### Use Cases

For **Multi-Perspective Code Analysis**, fork sessions to isolate security, performance, or maintainability audits. This allows for focused analysis before consolidating findings. **Parallel Feature Evaluation** uses separate forks for RICE and WSJF scoring to inform prioritization decisions. **Alternative Evidence Collection** strategies can compare bottom-up and top-down review approaches in parallel.

### Standards

Each fork must maintain a clear analytical scope. Save evidence logs to files before closing a fork. Synthesize findings from all forks into a final summary. Use perspective-based names for session IDs, such as `security-audit-pr-42`.
