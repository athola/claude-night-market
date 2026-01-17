# Skill Reference

Skills are methodology guides loaded via `Skill(plugin:skill-name)`. They inject structured workflows, checklists, and decision frameworks into the conversation. Unlike commands, skills don't run a process; they teach Claude Code *how* to approach a problem.

**See also**: [Capabilities Reference](capabilities-reference.md) | [Commands](capabilities-commands.md) | [Agents](capabilities-agents.md) | [Hooks](capabilities-hooks.md) | [Workflows](capabilities-workflows.md)

---

## Invocation Patterns

```bash
# Basic invocation
Skill(plugin:skill-name)

# With context
Skill(imbue:scope-guard) # When evaluating new features
Skill(imbue:proof-of-work) # Before claiming completion

# Chained invocation
Skill(superpowers:brainstorming)
# ... then later ...
Skill(imbue:scope-guard) # Evaluate brainstorm results
```

**Skill Components**: Every skill starts with YAML frontmatter (name, description, tags, dependencies, token estimate). Larger skills split content into a `modules/` directory. Many skills define TodoWrite items as checkpoints and exit criteria that mark the skill complete.

---

## Abstract Plugin

### `abstract:skill-authoring`
TDD methodology for creating new skills.

**Invocation**: `Skill(abstract:skill-authoring)`

**TodoWrite Items**:
- `skill-authoring:test-scenario-defined`
- `skill-authoring:acceptance-criteria-written`
- `skill-authoring:skill-implemented`
- `skill-authoring:validation-passed`

**Usage Example**:
```bash
# When creating a new skill
Skill(abstract:skill-authoring)
# Follow TDD: write test scenario first
# Define acceptance criteria
# Implement skill to pass tests
# Validate with /abstract:test-skill
```

### `abstract:hook-authoring`
Security-first hook development patterns.

**Invocation**: `Skill(abstract:hook-authoring)`

The skill emphasizes input validation before any logic, failing closed (deny by default), logging all actions for auditability, and setting timeouts to prevent runaway hooks.

### `abstract:modular-skills`
Patterns for breaking large skills into modules.

**Invocation**: `Skill(abstract:modular-skills)`

Use this when a skill exceeds ~3000 tokens, covers multiple distinct concerns, or has subcomponents that could be reused elsewhere. The skill guides extracting pieces into a `modules/` directory.

### `abstract:escalation-governance`
Model escalation decision framework.

**Invocation**: `Skill(abstract:escalation-governance)`

**Decision Matrix**:
| Complexity | Model |
|------------|-------|
| Simple, obvious | haiku |
| Standard task | sonnet |
| Complex reasoning | opus |

---

## Imbue Plugin

### `imbue:scope-guard`
Anti-overengineering and scope control.

**Invocation**: `Skill(imbue:scope-guard)`

**Worthiness Formula**:
```
(BusinessValue + TimeCriticality + RiskReduction) / (Complexity + TokenCost + ScopeDrift)
```

**Thresholds**:
- `> 2.0` - Implement now
- `1.0 - 2.0` - Discuss first
- `< 1.0` - Defer to backlog

**TodoWrite Items**:
- `scope-guard:worthiness-scored`
- `scope-guard:backlog-compared`
- `scope-guard:budget-checked`
- `scope-guard:github-issue-created` (if deferring)
- `scope-guard:decision-documented`

**Workflow Example**:
```bash
# During brainstorming
Skill(imbue:scope-guard)
# Score proposed feature: (3 + 2 + 1) / (5 + 2 + 3) = 0.6
# Score < 1.0 -> Defer to backlog
# Create GitHub issue, add to backlog queue
```

### `imbue:proof-of-work`
Evidence-based completion validation.

**Invocation**: `Skill(imbue:proof-of-work)`

**The Iron Law**:
```
NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST
NO COMPLETION CLAIM WITHOUT EVIDENCE FIRST
```

**TodoWrite Items**:
- `proof:problem-reproduced`
- `proof:solution-tested`
- `proof:edge-cases-checked`
- `proof:evidence-captured`
- `proof:completion-proven`
- `proof:iron-law-red` (TDD)
- `proof:iron-law-green` (TDD)
- `proof:iron-law-refactor` (TDD)

**Red Flags**:
| Thought | Action |
|---------|--------|
| "This looks correct" | RUN IT |
| "Should work" | TEST IT |
| "Syntax valid" | FUNCTIONAL TEST |

### `imbue:evidence-logging`
Structured evidence capture methodology.

**Invocation**: `Skill(imbue:evidence-logging)`

**Evidence Format**:
```markdown
[E1] Command: <command executed>
     Output: <actual output>
     Timestamp: <ISO timestamp>
     Conclusion: <what this proves>
```

### `imbue:catchup`
Context recovery after session restart.

**Invocation**: `Skill(imbue:catchup)`

The skill walks through checking git status, reviewing open issues/PRs, reading any session artifacts, and identifying work that was interrupted. Useful after `/clear` or starting a new session on an in-progress branch.

### `imbue:review-core`
Scaffolding for detailed structured reviews.

**Invocation**: `Skill(imbue:review-core)`

Provides a framework: gather evidence-based findings, classify by severity, and produce actionable recommendations. Other review skills (pensive, sanctum) build on this foundation.

---

## Conserve Plugin

### `conserve:context-optimization`
MECW principles and 50% context rule.

**Invocation**: `Skill(conserve:context-optimization)`

**MECW Thresholds**:
- Target: 50% context utilization
- Warning: 70% utilization
- Critical: 85% utilization

### `conserve:bloat-detector`
Detection algorithms for dead code and duplication.

**Invocation**: `Skill(conserve:bloat-detector)`

Detects dead code (0 references), stale files (6+ months unchanged), God classes (500+ lines), and documentation duplication (85%+ similar content). The `/bloat-scan` command uses this skill under the hood.

### `conserve:optimizing-large-skills`
Patterns for optimizing oversized skills.

**Invocation**: `Skill(conserve:optimizing-large-skills)`

Covers four strategies: extracting content to modules, removing redundancy, using progressive loading to defer rarely-needed sections, and moving verbose documentation to separate files loaded on demand.

---

## Sanctum Plugin

### `sanctum:git-workspace-review`
Repository state analysis.

**Invocation**: `Skill(sanctum:git-workspace-review)`

Examines staged changes, unstaged modifications, untracked files, and branch status relative to remote.

### `sanctum:pr-prep`
PR preparation guidelines.

**Invocation**: `Skill(sanctum:pr-prep)`

**PR Template**:
```markdown
## Summary
## Changes
## Testing
## Checklist
```

### `sanctum:commit-messages`
Conventional commit formatting.

**Invocation**: `Skill(sanctum:commit-messages)`

**Format**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

### `sanctum:do-issue`
GitHub issue resolution workflow.

**Invocation**: `Skill(sanctum:do-issue)`

Steps: fetch issue details, create branch, implement fix, create PR linking issue.

---

## Pensive Plugin

### `pensive:code-review` (shared)
Shared review patterns.

**Invocation**: `Skill(pensive:shared)`

### `pensive:bug-review`
Systematic bug hunting.

**Invocation**: `Skill(pensive:bug-review)`

Targets logic errors, null/undefined handling, resource leaks, and race conditions.

### `pensive:api-review`
API surface evaluation.

**Invocation**: `Skill(pensive:api-review)`

Reviews naming consistency, error handling, versioning, and documentation.

### `pensive:test-review`
Test quality assessment.

**Invocation**: `Skill(pensive:test-review)`

Evaluates coverage, AAA pattern compliance, flaky test detection, and edge case coverage.

### `pensive:architecture-review`
Architecture assessment.

**Invocation**: `Skill(pensive:architecture-review)`

Analyzes coupling/cohesion, dependency direction, layer violations, and scalability concerns.

### `pensive:rust-review`
Rust-specific patterns.

**Invocation**: `Skill(pensive:rust-review)`

Focuses on unsafe code, lifetime management, memory safety, and idiomatic patterns.

### `pensive:shell-review`
Shell script safety.

**Invocation**: `Skill(pensive:shell-review)`

Checks quoting issues, injection vulnerabilities, POSIX portability, and error handling.

---

## Memory Palace Plugin

### `memory-palace:knowledge-intake`
Knowledge curation and scoring.

**Invocation**: `Skill(memory-palace:knowledge-intake)`

**Scoring Criteria**:
| Criterion | Weight |
|-----------|--------|
| Novelty | 25% |
| Applicability | 25% |
| Durability | 20% |
| Connectivity | 15% |
| Authority | 15% |

### `memory-palace:knowledge-locator`
Spatial search patterns.

**Invocation**: `Skill(memory-palace:knowledge-locator)`

### `memory-palace:digital-garden-cultivator`
Garden maintenance patterns.

**Invocation**: `Skill(memory-palace:digital-garden-cultivator)`

**Maturity Levels**: seedling -> budding -> evergreen

---

## Parseltongue Plugin

### `parseltongue:python-async`
Async/await patterns.

**Invocation**: `Skill(parseltongue:python-async)`

Covers event loop management, concurrent execution, timeout handling, and error propagation.

### `parseltongue:python-packaging`
Packaging with uv.

**Invocation**: `Skill(parseltongue:python-packaging)`

Topics: pyproject.toml configuration, dependency management, build configuration, and publishing.

### `parseltongue:python-performance`
Profiling and optimization.

**Invocation**: `Skill(parseltongue:python-performance)`

Tools covered: cProfile, line_profiler, memory_profiler.

---

## Spec-Kit Plugin

### `spec-kit:speckit-orchestrator`
Workflow coordination.

**Invocation**: `Skill(spec-kit:speckit-orchestrator)`

**Workflow**:
```
startup -> clarify -> specify -> plan -> tasks -> implement
```

### `spec-kit:task-planning`
Task generation patterns.

**Invocation**: `Skill(spec-kit:task-planning)`

Defines task attributes: ID, description, dependencies, and parallel marker [P].

---

**See also**: [Commands](capabilities-commands.md) | [Agents](capabilities-agents.md) | [Hooks](capabilities-hooks.md) | [Workflows](capabilities-workflows.md)
