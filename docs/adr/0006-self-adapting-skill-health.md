# ADR 0006: Self-Adapting Skill Health

## Status

Accepted - 2026-02-15

## Context

Skills degrade over time as codebases evolve, dependencies shift, and usage patterns change. Without automated monitoring, skill regressions go unnoticed until users report failures. We need a system that detects degrading skills, triggers improvements, and safeguards against regressions -- all with minimal human intervention.

### Requirements

- Detect skill degradation from execution metrics (stability gap)
- Automatically queue degrading skills for improvement
- Version skill definitions to enable rollback
- Gate rollbacks on human review to avoid discarding beneficial changes
- Capture successful improvement patterns for reuse

## Decision

Adopt a **hybrid approach** combining Homeostatic Skill Health monitoring with an Experience Library.

### Architecture

Six components form a closed feedback loop:

1. **Homeostatic Monitor Hook** (`PostToolUse`): Reads stability gap from execution history after every Skill invocation. Flags skills with gap > 0.3 as "degrading" (> 0.5 as "critical") in an improvement queue.

2. **Improvement Queue**: JSON file (`~/.claude/skills/improvement-queue.json`) tracking flagged skills with gap values, flag counts, and execution IDs.

3. **Auto-Improvement Trigger**: When a skill accumulates 3+ flags, spawns the `abstract:skill-improver` agent with LEARNINGS.md data, recent execution logs, current metrics, and previous improvement history.

4. **Skill Versioning**: YAML frontmatter `adaptation` block tracks version history, metric baselines, and rollback availability. Each improvement bumps the minor version.

5. **Re-evaluation Window**: After improvement, monitors the next 10 executions. If the new gap improves over baseline, the change is promoted. If regression is detected, the system flags for human review via GitHub issue (no auto-rollback).

6. **Experience Library**: Stores successful execution trajectories in `~/.claude/skills/experience-library/`. Retrieved via keyword similarity matching and injected as context (max 3 exemplars, 500 tokens each) into future skill invocations.

### Cross-Plugin Data Flow

- **Memory-Palace**: Provides stability metrics, stores experience library entries
- **Abstract**: Provides skill-improver agent, execution logging, LEARNINGS.md
- **Integration**: `homeostatic_monitor.py` hook bridges both plugins

### Human-Gated Rollback

When regression is detected, the system does NOT auto-rollback. Instead it creates a GitHub issue (labeled `skill-regression`) with before/after metrics, the improvement diff, and a ready-to-use rollback command. A human then decides whether to rollback, accept, or investigate further.

**Rationale**: Auto-rollback can discard improvements that appear regressive short-term but are beneficial long-term (e.g., handling more edge cases widens the stability gap temporarily).

## Consequences

### Positive

- Autonomous detection and improvement of degrading skills
- Data-driven decisions grounded in execution metrics
- Version history enables safe experimentation with rollback capability
- Experience library accelerates future improvements with proven patterns
- Human oversight on rollback prevents premature reversions

### Negative

- Added complexity: six interacting components across two plugins
- Potential for silent failures if monitoring hook errors are swallowed
- Queue file I/O on every Skill invocation adds minor latency
- Experience library keyword matching is approximate (no vector search)

### Mitigations

- Narrow exception handling in hooks to surface unexpected errors
- Atomic writes for queue persistence to prevent corruption
- Stderr logging for all error paths

## References

- Implementation branch: `skill-atrophy-1.4.3`
- Homeostatic monitor: `plugins/abstract/hooks/homeostatic_monitor.py`
- Improvement queue: `plugins/abstract/src/abstract/improvement_queue.py`
- Skill versioning: `plugins/abstract/src/abstract/skill_versioning.py`
