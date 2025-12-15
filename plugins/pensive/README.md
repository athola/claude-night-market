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
```

## Review Skill Selection

The unified review automatically selects skills based on:

| Codebase Pattern | Skills Triggered |
|-----------------|-----------------|
| `*.rs`, `Cargo.toml` | rust-review, bug-review, api-review |
| `openapi.yaml`, `routes/` | api-review, architecture-review |
| `test_*.py`, `*_test.go` | test-review, bug-review |
| `Makefile`, `*.mk` | makefile-review |
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
│   └── makefile-review.md
├── skills/
│   ├── unified-review/      # Orchestration skill
│   ├── api-review/          # API surface review
│   ├── architecture-review/ # Architecture assessment
│   ├── bug-review/          # Bug detection
│   ├── rust-review/         # Rust auditing
│   ├── test-review/         # Test quality
│   ├── math-review/         # Mathematical review
│   └── makefile-review/     # Build system review
└── README.md
```

## Review Workflow

Reviews start by analyzing the repository and recent changes, then apply domain-specific checks. Findings get documented with file/line references, ranked by severity, and paired with concrete fixes.

## TodoWrite Integration

All skills use TodoWrite for tracking:

```
api-review:surface-inventory
api-review:exemplar-research
api-review:consistency-audit
api-review:docs-governance
api-review:evidence-log
```

## License

MIT
