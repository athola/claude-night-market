# pensive

Code review and analysis toolkit with specialized review skills.

## Overview

Pensive provides deep code review capabilities across multiple dimensions: architecture, APIs, bugs, tests, and more. It orchestrates reviews intelligently, selecting the right skills for each codebase.

## Installation

```bash
/plugin install pensive@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `unified-review` | Review orchestration | Starting reviews (Claude picks tools) |
| `api-review` | API surface evaluation | Reviewing OpenAPI specs, library exports |
| `architecture-review` | Architecture assessment | Checking ADR alignment, design principles |
| `bug-review` | Bug hunting | Systematic search for logic errors |
| `rust-review` | Rust-specific checking | Auditing unsafe code, borrow patterns |
| `test-review` | Test quality review | Ensuring tests verify behavior |
| `makefile-review` | Makefile best practices | Reviewing Makefile quality |
| `math-review` | Mathematical correctness | Reviewing mathematical logic |
| `shell-review` | Shell script auditing | Exit codes, portability, safety patterns |
| `fpf-review` | FPF architecture review | Functional/Practical/Foundation analysis |

## Commands

| Command | Description |
|---------|-------------|
| `/full-review` | Unified review with intelligent skill selection |
| `/api-review` | Run API surface review |
| `/architecture-review` | Run architecture assessment |
| `/bug-review` | Run bug hunting |
| `/rust-review` | Run Rust-specific review |
| `/test-review` | Run test quality review |
| `/makefile-review` | Run Makefile review |
| `/math-review` | Run mathematical review |
| `/shell-review` | Run shell script safety review |
| `/fpf-review` | Run FPF architecture review |
| `/skill-review` | Analyze skill metrics and stability gaps |
| `/skill-history` | View recent skill executions |

## Agents

| Agent | Description |
|-------|-------------|
| `code-reviewer` | Expert code review for bugs, security, quality |
| `architecture-reviewer` | Principal-level architecture specialist |
| `rust-auditor` | Expert Rust security and safety auditor |

## Usage Examples

### Full Review

```bash
/full-review

# Claude will:
# 1. Analyze codebase structure
# 2. Select relevant review skills
# 3. Execute reviews in priority order
# 4. Synthesize findings
# 5. Provide actionable recommendations
```

### Specific Reviews

```bash
# Architecture review
/architecture-review

# API review
/api-review

# Bug hunting
/bug-review

# Test quality
/test-review
```

### Manual Skill Invocation

```bash
Skill(pensive:architecture-review)

# Checks:
# - ADR compliance
# - Dependency direction
# - Layer violations
# - Design pattern usage
```

## Review Depth

Each review skill operates at multiple levels:

| Level | Description | Time |
|-------|-------------|------|
| Quick | High-level scan | 1-2 min |
| Standard | Thorough review | 5-10 min |
| Deep | Exhaustive analysis | 15+ min |

Specify depth when invoking:

```bash
/architecture-review --depth deep
```

## Review Categories

### Architecture Review

- ADR alignment
- Dependency analysis
- Layer boundary violations
- Pattern consistency
- Coupling metrics

### API Review

- Endpoint consistency
- Error response patterns
- Authentication/authorization
- Versioning strategy
- Documentation completeness

### Bug Review

- Logic errors
- Edge cases
- Race conditions
- Resource leaks
- Error handling gaps

### Test Review

- Coverage gaps
- Test isolation
- Assertion quality
- Mocking patterns
- Edge case coverage

### Rust Review

- Unsafe code audit
- Borrow checker patterns
- Memory safety
- Concurrency safety
- Idiomatic usage

## Dependencies

Pensive builds on foundation plugins:

```
pensive
    |
    +--> imbue (review-core, evidence-logging)
    |
    +--> sanctum (git-workspace-review)
```

## Workflow Integration

### Pre-PR Review

```bash
# Before opening PR
Skill(sanctum:git-workspace-review)
/full-review

# Address findings
# Then create PR
```

### Post-Merge Review

```bash
# After merge, deep review
/architecture-review --depth deep
```

### Targeted Review

```bash
# Review specific area
/api-review src/api/
```

## Superpowers Integration

| Command | Enhancement |
|---------|-------------|
| `/full-review` | Uses `systematic-debugging` for four-phase analysis |
| `/full-review` | Uses `verification-before-completion` for evidence |

## Output Format

Reviews produce structured output:

```markdown
## Review Summary

### Critical Issues
1. [BUG] Race condition in UserService.update()
   - Location: src/services/user.ts:45
   - Impact: Data corruption under load
   - Recommendation: Add mutex lock

### Warnings
1. [ARCH] Layer violation detected
   - Controllers importing from repositories
   - Recommendation: Add service layer

### Suggestions
1. [TEST] Missing edge case coverage
   - UserService.delete() lacks null check test
```

## Related Plugins

- **imbue**: Provides review scaffolding
- **sanctum**: Provides workspace context
- **archetypes**: Paradigm context for architecture review
