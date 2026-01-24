# Pensive

Code review skills for Claude Code. Specialized reviewers cover Rust, APIs, tests, and architecture.

## Installation

Install via the Claude Code plugin manager:
```bash
claude plugins install pensive
```

Or reference from the marketplace:
```json
{
  "plugins": ["pensive@claude-night-market"]
}
```

## Features

### Skills

| Skill | Description |
|-------|-------------|
| **unified-review** | Orchestrates reviews and selects appropriate domain-specific skills. |
| **api-review** | Evaluates public API surfaces and consistency. |
| **architecture-review** | Assesses architectural design and ADR compliance. |
| **bug-review** | Identifies logic errors and security vulnerabilities. |
| **rust-review** | Audits Rust code for ownership, safety, and concurrency issues. |
| **test-review** | Evaluates test suite coverage and quality. |
| **math-review** | Reviews mathematical algorithms and numerical stability. |
| **makefile-review** | Audits and optimizes build systems. |
| **shell-review** | Checks shell scripts for correctness, portability, and safety. |
| **fpf-review** | Functional/Practical/Foundation architecture review. |

### Commands

| Command | Description |
|---------|-------------|
| `/full-review` | Executes a unified review with automated skill selection. |
| `/api-review` | Audits API surface consistency. |
| `/architecture-review` | Evaluates design patterns and ADR alignment. |
| `/bug-review` | Scans for bugs and potential exploits. |
| `/rust-review` | Performs a safety audit for Rust projects. |
| `/test-review` | Analyzes test suite quality. |
| `/math-review` | Verifies mathematical correctness. |
| `/makefile-review` | Audits Makefiles against best practices. |
| `/shell-review` | Checks shell script safety and portability. |
| `/fpf-review` | Executes an FPF architecture review. |
| `/skill-review` | Analyzes skill performance and stability. |
| `/skill-history` | Displays recent skill execution data with context. |

### Agents

| Agent | Description |
|-------|-------------|
| **code-reviewer** | General review agent with bug detection capabilities. |
| **architecture-reviewer** | Agent specialized in architectural assessment. |
| **rust-auditor** | Agent focused on Rust safety and security. |

## Quick Start

### Unified Review

Run `/full-review` to automatically detect and execute relevant checks. Focus on specific areas by appending the domain, such as `/full-review api` or `/full-review bugs`. Use `/full-review all` to execute all applicable domain reviews.

### Domain-Specific Reviews

Trigger specialized reviews directly for focused audits: `/rust-review`, `/api-review`, `/test-review`, or `/fpf-review` for architectural analysis.

### Skill Performance Review

Use `/skill-review` to view health metrics across all skills. Append `--unstable-only` to identify skills with a stability gap greater than 0.3. Use `/skill-history` to view executions from the last hour or filter by failures using `--failures-only`.

## Skill Selection Logic

Unified reviews select skills based on codebase patterns. Rust files (`*.rs`, `Cargo.toml`) trigger `rust-review`, `bug-review`, and `api-review`. API definitions (`openapi.yaml`) trigger `api-review` and `architecture-review`. Test files trigger `test-review`, and build scripts trigger `makefile-review` or `shell-review`.

## Output Standards

Reviews produce structured output including an overall assessment, high/medium/low severity findings with file and line references, actionable tasks with owners and dates, and a final recommendation to approve, block, or approve with actions.

## Review Workflow

Reviews identify modified files and apply domain-specific checks. Findings are documented with precise location data, severity rankings, and specific remediation steps.

## Progress Tracking

Skills use `TodoWrite` for lifecycle tracking, moving from surface inventory and exemplar research to consistency audits and evidence logging.

## Session Forking (Claude Code 2.0.73+)

Fork sessions for parallel specialized reviews. For example, use `claude --fork-session --session-id "security-audit"` to isolate a security audit while maintaining the main review context. Extract findings before closing the fork and synthesize them into the final report.

## Skill Performance Monitoring

Pensive tracks skill execution to identify brittle tools by calculating the stability gap (the difference between average and worst-case accuracy). A gap below 0.2 indicates stable performance, while a gap above 0.3 requires investigation. Data is stored in `~/.claude/skills/logs/` in JSONL format, with history aggregated in `.history.json`.
