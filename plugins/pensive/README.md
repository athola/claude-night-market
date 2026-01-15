# Pensive

Code review skills for Claude Code. Includes domain-specific reviewers for Rust, APIs, tests, and architecture.

## Installation

Add to your Claude Code plugins:
```bash
claude plugins install pensive
```

Or reference directly from the marketplace:
```json
{
  "plugins": ["pensive@claude-night-market"]
}
```

## Features

### Skills

| Skill | Description |
|-------|-------------|
| **unified-review** | Review orchestration and skill selection |
| **api-review** | Public API surface evaluation |
| **architecture-review** | Architecture assessment |
| **bug-review** | Systematic bug detection and fixing |
| **rust-review** | Rust audits (ownership, unsafe, concurrency) |
| **test-review** | TDD/BDD test suite evaluation |
| **math-review** | Mathematical algorithm and numerical stability review |
| **makefile-review** | Build system audit and optimization |
| **shell-review** | Shell script correctness, portability, and safety audit |
| **fpf-review** | FPF (Functional/Practical/Foundation) architecture review |

### Commands

| Command | Description |
|---------|-------------|
| `/full-review` | Unified review with skill selection |
| `/api-review` | API surface and consistency audit |
| `/architecture-review` | Architecture and ADR assessment |
| `/bug-review` | Systematic bug hunting |
| `/rust-review` | Rust-specific safety audit |
| `/test-review` | Test suite quality evaluation |
| `/math-review` | Mathematical correctness review |
| `/makefile-review` | Makefile best practices audit |
| `/shell-review` | Shell script audit (exit codes, portability, safety) |
| `/fpf-review` | FPF architecture review (Functional/Practical/Foundation) |
| `/skill-review` | Skill performance metrics and stability analysis |
| `/skill-history` | Recent skill executions with context |

### Agents

| Agent | Description |
|-------|-------------|
| **code-reviewer** | General code review with bug detection |
| **architecture-reviewer** | Architecture assessment |
| **rust-auditor** | Rust safety and security auditing |

## Quick Start

### Unified Review
```bash
# Auto-detect and run appropriate reviews
/full-review

# Focus on specific domains
/full-review api          # API surface review
/full-review architecture # Architecture review
/full-review bugs         # Bug hunting
/full-review tests        # Test suite review
/full-review all          # Run all applicable
```

### Domain-Specific Reviews
```bash
# Rust project
/rust-review

# API changes
/api-review

# Test improvements
/test-review

# Mathematical code
/math-review

# Architecture analysis (FPF methodology)
/fpf-review
```

### Skill Performance Review
```bash
# View all skill metrics
/skill-review

# Find unstable skills (stability gap > 0.3)
/skill-review --unstable-only

# Deep-dive specific skill
/skill-review --skill abstract:skill-auditor

# Recent execution history
/skill-history --last 1h

# View failures only
/skill-history --failures-only
```

## Review Skill Selection

The unified review automatically selects skills based on:

| Codebase Pattern | Skills Triggered |
|-----------------|-----------------|
| `*.rs`, `Cargo.toml` | rust-review, bug-review, api-review |
| `openapi.yaml`, `routes/` | api-review, architecture-review |
| `test_*.py`, `*_test.go` | test-review, bug-review |
| `Makefile`, `*.mk` | makefile-review |
| `*.sh`, pre-commit hooks | shell-review |
| Math algorithms | math-review, bug-review |
| ADRs, architecture docs | architecture-review |

## Output Format

All reviews produce structured output:

```markdown
## Summary
[Overall assessment]

## Findings
### [F1] Issue Title
- Location: file:line
- Severity: High/Medium/Low
- Issue: [description]
- Fix: [recommendation]

## Action Items
- [action] - Owner - Date

## Recommendation
Approve / Approve with actions / Block
```

## Plugin Structure

```
pensive/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── agents/
│   ├── code-reviewer.md     # General code review
│   ├── architecture-reviewer.md  # Architecture assessment
│   └── rust-auditor.md      # Rust-specific auditing
├── commands/
│   ├── full-review.md       # Unified review command
│   ├── api-review.md
│   ├── architecture-review.md
│   ├── bug-review.md
│   ├── rust-review.md
│   ├── test-review.md
│   ├── math-review.md
│   ├── makefile-review.md
│   └── shell-review.md
├── skills/
│   ├── unified-review/      # Orchestration skill
│   ├── api-review/          # API surface review
│   ├── architecture-review/ # Architecture assessment
│   ├── bug-review/          # Bug detection
│   ├── rust-review/         # Rust auditing
│   ├── test-review/         # Test quality
│   ├── math-review/         # Mathematical review
│   ├── makefile-review/     # Build system review
│   ├── shell-review/        # Shell script review
│   └── fpf-review/          # FPF architecture review
└── README.md
```

## Review Workflow

Reviews analyze the repository and recent changes, then apply domain-specific checks. Findings get documented with file/line references, ranked by severity, and paired with concrete fixes.

## TodoWrite Integration

All skills use TodoWrite for tracking:

```
api-review:surface-inventory
api-review:exemplar-research
api-review:consistency-audit
api-review:docs-governance
api-review:evidence-log
```

## Session Forking Workflows (Claude Code 2.0.73+)

Session forking enables parallel specialized reviews:

```bash
# Fork for security audit
claude --fork-session --session-id "security-audit" --resume
> "/rust-review --focus security"

# Fork for performance analysis
claude --fork-session --session-id "performance-audit" --resume
> "Review focusing on performance"
```

**Best Practices**: One concern per fork, extract findings before closing, synthesize into actionable report.

See `plugins/abstract/docs/claude-code-compatibility.md` for detailed patterns.

## Skill Performance Review

Pensive includes skill review capabilities for analyzing skill execution metrics and identifying unstable skills.

### Stability Gap Detection

The key metric is **stability gap** - the difference between average accuracy and worst-case accuracy:

```
stability_gap = average_accuracy - worst_case_accuracy
```

| Gap | Status | Meaning |
|-----|--------|---------|
| < 0.2 | Stable | Consistent performance |
| 0.2 - 0.3 | Warning | Occasional issues |
| > 0.3 | Unstable | Needs attention |

### Integration with memory-palace

Skill execution data is stored by memory-palace hooks:
- **Storage**: `~/.claude/skills/logs/` (JSONL format)
- **Metrics**: `~/.claude/skills/logs/.history.json`

Use `/memory-palace:skill-logs` to access raw execution logs.

### Example Workflow

```bash
# 1. Check overall skill health
/skill-review --unstable-only

# 2. Investigate a specific skill
/skill-history --skill imbue:proof-of-work --failures-only

# 3. Review metrics over time
/skill-review --skill imbue:proof-of-work

# 4. Access raw logs if needed
/memory-palace:skill-logs --skill imbue:proof-of-work
```

## License

MIT
