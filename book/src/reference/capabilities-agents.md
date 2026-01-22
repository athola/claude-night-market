# Agent Reference

Agents are specialized subagents that Claude Code can dispatch for focused work. Each agent has a fixed toolset, runs on a specific model tier (haiku/sonnet/opus), and knows when to escalate to a more capable model. The parent session decides whether the task justifies the overhead of spinning up an agent; simple tasks should be handled directly.

**See also**: [Capabilities Reference](capabilities-reference.md) | [Commands](capabilities-commands.md) | [Skills](capabilities-skills.md) | [Hooks](capabilities-hooks.md) | [Workflows](capabilities-workflows.md)

---

## Agent Configuration

**Frontmatter Options**:

```yaml
---
name: agent-name
description: |
  Agent description with triggers and use-cases.
tools: [Read, Write, Edit, Bash, Glob, Grep]  # Available tools
model: haiku|sonnet|opus                        # Base model
permissionMode: acceptEdits                     # Permission automation
skills: plugin:skill1, plugin:skill2            # Auto-loaded skills
escalation:
  to: opus                                      # Escalation target
  hints:
    - security_audit                            # Trigger conditions
    - complex_architecture
hooks:
  PreToolUse:
    - matcher: "Bash"
      command: "echo 'logged'"
---
```

**Permission Modes**:
| Mode | Description |
|------|-------------|
| `default` | Prompt for permissions |
| `acceptEdits` | Auto-accept file edits |
| `plan` | Planning only, no execution |

**Model Selection**:
| Model | Use Case | Cost |
|-------|----------|------|
| `haiku` | Simple, repetitive tasks | Lowest |
| `sonnet` | Standard complexity | Medium |
| `opus` | Complex reasoning | Highest |

---

## Abstract Plugin

### `abstract:plugin-validator`
Validates plugin structure.

```yaml
tools: [Read, Glob, Grep, Bash]
model: haiku
```

**Dispatch**:
```
Use the plugin-validator agent to check the conserve plugin structure.
```

### `abstract:skill-auditor`
Audits skill quality.

```yaml
tools: [Read, Glob, Grep]
model: haiku
escalation:
  to: sonnet
  hints: [quality_assessment, complex_analysis]
```

### `abstract:meta-architect`
Plugin ecosystem design.

```yaml
tools: [Read, Write, Edit, Glob, Grep, Bash]
model: sonnet
```

---

## Conserve Plugin

### `conserve:bloat-auditor`
Orchestrates bloat detection.

```yaml
tools: [Read, Glob, Grep, Bash]
model: haiku
skills: conserve:bloat-detector
```

**Dispatch**:
```
Use the bloat-auditor agent to perform a Tier 2 scan of the sanctum plugin.
```

### `conserve:context-optimizer`
Context optimization.

```yaml
tools: [Read, Glob, Grep, Bash, Write]
model: haiku
skills: conserve:context-optimization, conserve:optimizing-large-skills
escalation:
  to: sonnet
  hints: [complex_modularization]
```

### `conserve:continuation-agent`
Continue work from session state checkpoint. Spawned when parent agent exceeds context thresholds.

```yaml
tools: [Read, Write, Edit, Bash, Glob, Grep, Task, TodoRead, TodoWrite]
model: default
hooks:
  SessionStart: Audit log start
  Stop: Audit log completion
```

**Dispatch**:
```
Use the continuation-agent to resume work from the session state file.
```

### `conserve:unbloat-remediator`
Safe bloat remediation.

```yaml
tools: [Read, Write, Edit, Bash, Glob]
model: haiku
permissionMode: acceptEdits
```

---

## Pensive Plugin

### `pensive:code-reviewer`
Expert code review.

```yaml
tools: [Read, Write, Edit, Bash, Glob, Grep]
model: sonnet
skills: imbue:evidence-logging, pensive:bug-review
escalation:
  to: opus
  hints: [security_audit, complex_architecture]
```

Set `ENABLE_LSP_TOOL=1` for LSP-enhanced review (semantic analysis, reference finding). The agent handles multi-file analysis and produces evidence-based findings with file:line references.

**Dispatch**:
```
Use the code-reviewer agent to perform a security audit of src/auth/.
```

### `pensive:architecture-reviewer`
Principal-level architecture review.

```yaml
tools: [Read, Glob, Grep, Bash]
model: sonnet
escalation:
  to: opus
  hints: [system_design, scalability]
```

### `pensive:rust-auditor`
Rust security audit.

```yaml
tools: [Read, Glob, Grep, Bash]
model: sonnet
skills: pensive:rust-review
```

---

## Sanctum Plugin

### `sanctum:commit-agent`
Commit message generation.

```yaml
tools: [Read, Write, Bash]
model: haiku
permissionMode: acceptEdits
escalation:
  to: sonnet
  hints: [ambiguous_input, high_stakes]
```

**Complexity Check**: The parent should commit directly if it's a single file under 20 lines or an obvious type (typo fix, version bump). Only dispatch this agent for multi-file changes or when the commit type classification is genuinely ambiguous.

### `sanctum:pr-agent`
PR preparation.

```yaml
tools: [Read, Write, Edit, Bash, Glob, Grep]
model: sonnet
```

### `sanctum:git-workspace-agent`
Repository state analysis.

```yaml
tools: [Read, Bash, Glob]
model: haiku
```

### `sanctum:dependency-updater`
Dependency version management.

```yaml
tools: [Read, Write, Edit, Bash, Glob]
model: haiku
```

### `sanctum:workflow-improvement-*`
Workflow improvement pipeline (multiple agents).

```yaml
# Analysis agent
model: haiku
# Planner agent
model: sonnet
# Implementer agent
model: haiku
# Validator agent
model: haiku
```

---

## Memory Palace Plugin

### `memory-palace:palace-architect`
Palace design.

```yaml
tools: [Read, Write, Glob]
model: sonnet
```

### `memory-palace:knowledge-librarian`
Knowledge routing.

```yaml
tools: [Read, Write, Glob, Grep]
model: haiku
```

### `memory-palace:garden-curator`
Digital garden maintenance.

```yaml
tools: [Read, Write, Edit, Glob]
model: haiku
```

### `memory-palace:knowledge-navigator`
Palace search.

```yaml
tools: [Read, Glob, Grep]
model: haiku
```

---

## Parseltongue Plugin

### `parseltongue:python-pro`
Python 3.12+ expertise.

```yaml
tools: [Read, Write, Edit, Bash, Glob, Grep]
model: sonnet
```

### `parseltongue:python-tester`
Testing expertise.

```yaml
tools: [Read, Write, Edit, Bash, Glob, Grep]
model: haiku
```

### `parseltongue:python-optimizer`
Performance optimization.

```yaml
tools: [Read, Write, Edit, Bash, Glob, Grep]
model: sonnet
```

### `parseltongue:python-linter`
Linting and style.

```yaml
tools: [Read, Bash, Glob, Grep]
model: haiku
```

---

## Spec-Kit Plugin

### `spec-kit:spec-analyzer`
Spec consistency.

```yaml
tools: [Read, Glob, Grep]
model: haiku
```

### `spec-kit:task-generator`
Task creation.

```yaml
tools: [Read, Write, Glob]
model: haiku
```

### `spec-kit:implementation-executor`
Task executor.

```yaml
tools: [Read, Write, Edit, Bash, Glob, Grep]
model: sonnet
```

---

## Attune Plugin

### `attune:project-architect`
Full-cycle workflow guidance.

```yaml
tools: [Read, Write, Edit, Bash, Glob, Grep]
model: sonnet
```

### `attune:project-implementer`
TDD implementation.

```yaml
tools: [Read, Write, Edit, Bash, Glob, Grep]
model: sonnet
permissionMode: acceptEdits
```

---

## Imbue Plugin

### `imbue:review-analyst`
Structured reviews.

```yaml
tools: [Read, Glob, Grep]
model: haiku
skills: imbue:review-core, imbue:evidence-logging
```

---

## Scribe Plugin

### `scribe:doc-editor`
Interactive documentation editing.

```yaml
tools: [Read, Write, Edit, Glob, Grep]
model: sonnet
skills: scribe:slop-detector, scribe:doc-generator
```

**Use When**: Cleaning up AI-generated content, polishing documentation, applying learned styles.

### `scribe:doc-verifier`
QA validation using proof-of-work methodology.

```yaml
tools: [Read, Bash, Glob, Grep]
model: sonnet
skills: imbue:proof-of-work, scribe:slop-detector
```

**Use When**: Validating documentation claims, verifying command examples work, checking version accuracy.

### `scribe:slop-hunter`
Full-coverage AI slop detection.

```yaml
tools: [Read, Glob, Grep]
model: haiku
skills: scribe:slop-detector
```

**Use When**: Scanning large document sets for AI-generated content markers.

---

## Scry Plugin

### `scry:media-recorder`
Recording orchestration.

```yaml
tools: [Read, Write, Bash, Glob]
model: haiku
```

---

**See also**: [Commands](capabilities-commands.md) | [Skills](capabilities-skills.md) | [Hooks](capabilities-hooks.md) | [Workflows](capabilities-workflows.md)
