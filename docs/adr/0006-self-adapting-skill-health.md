# ADR 0006: Self-Adapting Skill Health

## Status

Accepted - 2026-02-15

Amended 2026-10-28: components 4 to 6 had no production caller. They are
now wired in, and this record describes what runs.

## Context

Skills degrade over time as codebases evolve, dependencies shift,
and usage patterns change. Without automated monitoring,
skill regressions go unnoticed until users report failures.
We need a system that detects degrading skills, triggers improvements,
and safeguards against regressions, all with minimal human intervention.

### Requirements

- Detect skill degradation from execution metrics (stability gap)
- Automatically queue degrading skills for improvement
- Version skill definitions to enable rollback
- Gate rollbacks on human review to avoid discarding beneficial changes
- Capture successful improvement patterns for reuse

## Decision

Adopt a **hybrid approach** combining Homeostatic Skill Health monitoring with
an Experience Library.

### Architecture

Six components form a feedback loop. All of them are in the abstract
plugin and keep their state under `~/.claude/skills/` (or
`$CLAUDE_HOME/skills/`).

1. **Homeostatic Monitor Hook** (`PostToolUse`,
   `hooks/homeostatic_monitor.py`): reads the stability gap from
   `logs/.history.json`, which `hooks/skill_execution_logger.py` writes,
   after every Skill invocation. A skill under evaluation has the run
   counted toward its window (component 5). Any other skill with a gap
   above 0.3 is flagged "degrading" (above 0.5, "critical") in the
   improvement queue.

2. **Improvement Queue** (`src/abstract/improvement_queue.py`): a JSON
   file (`improvement-queue.json`) tracking flagged skills with gap
   values, flag counts, execution IDs and evaluation state. Writes are
   atomic and taken under a file lock.

3. **Improvement Trigger**: when a skill reaches 3 flags, the monitor
   reports `improvement_triggered: true` in its hook output and on
   stderr. No hook starts an agent. The operator runs
   `/abstract:improve-skills`, which uses the `abstract:skill-improver`
   agent and its LEARNINGS.md, log, and ImprovementMemory inputs.

4. **Skill Versioning** (`src/abstract/skill_versioning.py`): after
   applying an improvement, skill-improver runs
   `scripts/record_skill_improvement.py <SKILL.md> --summary TEXT`. The
   script bumps the minor version in the frontmatter `adaptation` block
   and records the current gap and success rate as that version's
   baseline. Only the `adaptation` block is rewritten. Every other
   frontmatter line stays byte-identical. This block is the only skill
   version scheme: the agent no longer bumps a top-level `version:` key,
   which 1 of 206 skills carried and which held no history or baseline.

5. **Re-evaluation Window**: the same script marks the skill
   `evaluating` with the current gap as `baseline_gap`. The monitor
   records each later execution of that skill, healthy or not. The script
   stores how many outcomes the history held when the window opened, and
   the monitor judges the window on the outcomes after that position
   only, so the failures that flagged the skill do not count against the
   change. After 10 executions it decides: a window gap below the
   baseline sets `promoted`, anything else sets `pending_rollback_review`.
   It also records the closed window in `ImprovementMemory` (success
   rate before the window as `before_score`, inside it as `after_score`)
   and in `PerformanceTracker`. The decision appears in the hook
   output as `evaluation_decision` and on stderr. A skill with no
   execution history, or not in the queue, gets the version bump and no
   window, and the script says so. The window advances only when the
   skill runs. A skill that is never invoked again stays `evaluating`,
   which blocks nothing, because flagging also happens only on
   invocation.

6. **Experience Library** (`src/abstract/experience_library.py`): the
   PostToolUse logger stores each successful Skill call that carried
   `args` in `experience-library/<plugin>_<skill>/`, keeping 20 per
   skill. The stored task is the sanitized args (up to 2,000
   characters), the only description of the task the hook receives.
   Approach and tools stay empty, and the duration is null when the
   call was not timed. A call without args is not stored. The PreToolUse hook
   (`hooks/pre_skill_execution.py`) adds the 3 most recent entries for
   the invoked skill to its `additionalContext`, each capped at 2,000
   characters (about 500 tokens). Selection is by recency.

   Scope: the library sits under `~/.claude`, which every project
   shares, and the args can carry text a third party wrote. Each entry
   therefore records a project key, the hash of the git toplevel (the
   working directory outside a repository), and the hook recalls only
   entries with the current project's key. Entries stored before the key
   existed carry none and are never recalled. The recalled block is
   fenced in `<recalled-data>` markers under a line stating that it is
   data, not instructions. Sanitizing redacts secrets only and does not
   neutralize instructions, so the fence and the project filter are the
   protection.

### Human-Gated Rollback

When the window ends in `pending_rollback_review`, the system does NOT
auto-rollback and files no issue. The hook reports the decision, and the
queue holds the skill out of flagging until a human edits its status.
The `adaptation` history keeps each version's baseline and change
summary. The SKILL.md change is a git commit, and `git revert` undoes
it.

**Rationale**: Auto-rollback can discard improvements that appear regressive
short-term but are beneficial long-term (e.g.,
handling more edge cases widens the stability gap temporarily).

## Consequences

### Positive

- Autonomous detection and improvement of degrading skills
- Data-driven decisions grounded in execution metrics
- Version history enables safe experimentation with rollback capability
- Experience library accelerates future improvements with proven patterns
- Human oversight on rollback prevents premature reversions

### Negative

- Added complexity: six interacting components
- Potential for silent failures if monitoring hook errors are swallowed
- Queue file I/O on every Skill invocation adds minor latency
- Experience exemplars carry only the task args, chosen by recency

### Mitigations

- Narrow exception handling in hooks to surface unexpected errors
- Atomic writes for queue persistence to prevent corruption
- Stderr logging for all error paths

## References

- Implementation branch: `skill-atrophy-1.4.3`
- Homeostatic monitor: `plugins/abstract/hooks/homeostatic_monitor.py`
- Improvement queue: `plugins/abstract/src/abstract/improvement_queue.py`
- Skill versioning: `plugins/abstract/src/abstract/skill_versioning.py`
- Experience library: `plugins/abstract/src/abstract/experience_library.py`
- Improvement recorder: `plugins/abstract/scripts/record_skill_improvement.py`
- Loop tests: `plugins/abstract/tests/hooks/test_self_adapting_loop.py`
