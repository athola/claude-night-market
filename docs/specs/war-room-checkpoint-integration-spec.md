# War Room Checkpoint Integration Specification

**Version**: 1.0.0-draft
**Date**: 2026-01-25
**Status**: Draft - Pending Review

---

## Executive Summary

Extend the War Room deliberation system from a standalone command to an **embeddable checkpoint** that any command can invoke at critical decision points. This enables automatic escalation to multi-expert deliberation when decisions exceed complexity thresholds.

### Design Principles

1. **Seamless Integration**: No flags required - auto-triggers based on context
2. **Profile-Based Thresholds**: Reuse existing `startup`, `regulated`, etc. profiles
3. **Auto-Continue with Ambiguity Gate**: War Room orders flow back automatically unless uncertainty warrants user confirmation
4. **Fail-Safe**: If War Room invocation fails, command continues with logged warning

---

## Target Commands

### Phase 1 (Priority)

| Command | Plugin | Integration Point | Trigger Conditions |
|---------|--------|-------------------|-------------------|
| `/do-issue` | sanctum | After Step 3 (Plan), before Step 4 (Implement) | Multiple issues OR high RS on scope |
| `/pr-review` | sanctum | After scope analysis, before verdict | Blocking count > 3 OR architecture changes |
| `/architecture-review` | pensive | After analysis, before recommendation | ADR violations OR coupling score > threshold |
| `/fix-pr` | sanctum | After triage, before fix strategy | Scope=major OR conflicting reviewer feedback |

### Phase 2 (Extended)

| Command | Plugin | Integration Point | Trigger Conditions |
|---------|--------|-------------------|-------------------|
| `/attune:execute` | attune | On blocked task (>2 attempts) | Persistent blocker requiring pivot |
| `/speckit-implement` | spec-kit | On checklist FAIL requiring judgment | Phase-gate failure with ambiguous resolution |
| `/attune:blueprint` | attune | After approach generation | Optional, user-requested only |
| `/update-dependencies` | sanctum | After analysis | Semver-major count >= 3 with breaking changes |

### Phase 3 (Considered)

| Command | Plugin | Trigger Conditions | Notes |
|---------|--------|-------------------|-------|
| `/prepare-pr` | sanctum | Complex multi-file changes | May over-trigger; needs validation |
| `/brainstorm` | attune | Already integrated | Confirm existing integration sufficient |

---

## Architecture

### New Skill: `attune:war-room-checkpoint`

A lightweight skill that can be invoked inline from any command to assess whether War Room escalation is needed.

```yaml
name: war-room-checkpoint
description: Inline reversibility assessment for embedded War Room escalation
triggers: checkpoint, assess complexity, should escalate
use_when: called from other commands at decision points
do_not_use_when: standalone invocation (use war-room instead)
model_preference: claude-sonnet-4
category: strategic-planning
tags: [checkpoint, embedded, escalation, reversibility]
dependencies:
  - attune:war-room
complexity: lightweight
estimated_tokens: 400
```

### Checkpoint Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Command Execution Flow                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌────────────────┐    ┌──────────────────┐   │
│  │ Command  │───▶│ Decision Point │───▶│ war-room-        │   │
│  │ Start    │    │ Detected       │    │ checkpoint       │   │
│  └──────────┘    └────────────────┘    └────────┬─────────┘   │
│                                                  │              │
│                         ┌────────────────────────┴─────┐       │
│                         ▼                              ▼       │
│              ┌──────────────────┐          ┌──────────────────┐│
│              │ RS ≤ threshold   │          │ RS > threshold   ││
│              │ (express mode)   │          │ (escalate)       ││
│              └────────┬─────────┘          └────────┬─────────┘│
│                       │                             │          │
│                       ▼                             ▼          │
│              ┌──────────────────┐          ┌──────────────────┐│
│              │ Return quick     │          │ Invoke full      ││
│              │ recommendation   │          │ War Room         ││
│              └────────┬─────────┘          └────────┬─────────┘│
│                       │                             │          │
│                       ▼                             ▼          │
│              ┌────────────────────────────────────────────────┐│
│              │            War Room Decision                    ││
│              │  ┌─────────────────────────────────────────┐   ││
│              │  │ confidence > 0.8: Auto-continue         │   ││
│              │  │ confidence ≤ 0.8: Prompt user           │   ││
│              │  └─────────────────────────────────────────┘   ││
│              └────────────────────────────────────────────────┘│
│                                │                               │
│                                ▼                               │
│              ┌──────────────────────────────────────┐          │
│              │ Command continues with decision      │          │
│              └──────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Checkpoint Context Object

```python
@dataclass
class CheckpointContext:
    """Context passed to war-room-checkpoint for assessment."""

    # Required
    source_command: str          # e.g., "do-issue", "pr-review"
    decision_needed: str         # Human-readable question

    # Optional context
    files_affected: list[str] = field(default_factory=list)
    issues_involved: list[int] = field(default_factory=list)
    blocking_items: list[dict] = field(default_factory=list)
    conflict_description: str | None = None

    # Override defaults
    profile: str = "default"     # startup, regulated, etc.
    force_mode: str | None = None  # express, lightweight, full_council

    # Metadata
    session_id: str | None = None  # Link to parent session
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
```

### Checkpoint Response Object

```python
@dataclass
class CheckpointResponse:
    """Response from war-room-checkpoint."""

    # Assessment
    reversibility_score: float    # 0.04 - 1.0
    decision_type: str            # Type 2, 1B, 1A, 1A+
    selected_mode: str            # express, lightweight, full_council, delphi

    # Decision (if made)
    recommendation: str | None    # For express mode
    orders: list[str] | None      # For escalated modes
    rationale: str | None

    # Control flow
    should_escalate: bool         # Whether full War Room was invoked
    confidence: float             # 0.0 - 1.0, for auto-continue decision
    requires_user_confirmation: bool  # True if confidence < 0.8

    # Audit
    war_room_session_id: str | None  # If escalated
    assessment_log: dict          # Full RS breakdown
```

---

## Trigger Conditions by Command

### `/do-issue` (Multiple Issues)

**Integration Point**: After Step 3 (Plan), before Step 4 (Implement)

**Trigger Conditions**:
```python
def should_checkpoint_do_issue(analysis_result: IssueAnalysis) -> bool:
    # Always checkpoint when multiple issues
    if len(analysis_result.issues) >= 3:
        return True

    # Checkpoint single issue if high complexity
    if analysis_result.issues:
        issue = analysis_result.issues[0]
        if issue.touches_auth or issue.touches_db_schema:
            return True
        if issue.file_count > 10:
            return True

    # Checkpoint on detected conflicts
    if analysis_result.has_dependency_conflicts:
        return True
    if analysis_result.has_overlapping_file_changes:
        return True

    return False
```

**War Room Questions**:
- "What order minimizes rework and merge conflicts?"
- "Are these issues truly independent or should they be sequenced?"
- "Should we split into multiple PRs for safer rollback?"

**Context Passed**:
```python
CheckpointContext(
    source_command="do-issue",
    decision_needed=f"Execution strategy for issues {issue_nums}",
    issues_involved=issue_nums,
    files_affected=overlapping_files,
    conflict_description=dependency_analysis,
)
```

---

### `/pr-review`

**Integration Point**: After Phase 3 (Code Analysis), before Phase 5 (GitHub Review)

**Trigger Conditions**:
```python
def should_checkpoint_pr_review(review_analysis: ReviewAnalysis) -> bool:
    # Blocking count threshold
    if len(review_analysis.blocking_issues) > 3:
        return True

    # Architecture changes detected
    if review_analysis.has_architecture_changes:
        return True

    # ADR non-compliance
    if review_analysis.adr_violations:
        return True

    # Scope mode is strict with significant findings
    if (review_analysis.scope_mode == "strict" and
        review_analysis.out_of_scope_count > 0):
        return True

    return False
```

**War Room Questions**:
- "Should this PR be split into smaller, reviewable chunks?"
- "Which blocking issues are truly blocking vs. nice-to-have?"
- "Is the architectural change warranted given the scope?"

**Context Passed**:
```python
CheckpointContext(
    source_command="pr-review",
    decision_needed=f"Review verdict for PR #{pr_num}",
    blocking_items=[
        {"type": "blocking", "description": issue.description}
        for issue in review_analysis.blocking_issues
    ],
    files_affected=review_analysis.changed_files,
    conflict_description=review_analysis.architecture_summary,
)
```

---

### `/architecture-review`

**Integration Point**: After Phase 4 (Risk Assessment), before recommendation

**Trigger Conditions**:
```python
def should_checkpoint_architecture_review(analysis: ArchAnalysis) -> bool:
    # ADR violations requiring judgment
    if analysis.adr_violations and not analysis.has_clear_remediation:
        return True

    # High coupling score
    if analysis.coupling_score > 0.7:
        return True

    # Module boundary violations
    if len(analysis.boundary_violations) > 2:
        return True

    # Conflicting principles (e.g., DRY vs. clear boundaries)
    if analysis.has_principle_conflicts:
        return True

    return False
```

**War Room Questions**:
- "Should we recommend blocking or propose remediation?"
- "Does this coupling warrant refactoring or is it acceptable?"
- "Should an ADR be created to document this deviation?"

---

### `/fix-pr` (Major Scope)

**Integration Point**: After Step 2 (Triage), before Step 3 (Plan)

**Trigger Conditions**:
```python
def should_checkpoint_fix_pr(triage_result: TriageResult) -> bool:
    # Scope is major
    if triage_result.scope == "major":
        return True

    # Conflicting reviewer feedback
    if triage_result.has_conflicting_feedback:
        return True

    # Multiple refactoring suggestions
    if len(triage_result.refactor_requests) > 2:
        return True

    # Breaking change required
    if triage_result.requires_breaking_change:
        return True

    return False
```

**War Room Questions**:
- "How do we reconcile conflicting reviewer suggestions?"
- "Should we push back on any suggestions as out-of-scope?"
- "Is a multi-commit or multi-PR approach appropriate?"

---

## Threshold Profiles

Reuse existing War Room profiles with command-specific adjustments:

```yaml
profiles:
  default:
    express_ceiling: 0.40
    lightweight_ceiling: 0.60
    full_council_ceiling: 0.80
    description: "Balanced for general use"

  startup:
    express_ceiling: 0.55
    lightweight_ceiling: 0.75
    full_council_ceiling: 0.90
    description: "Speed over process - higher escalation thresholds"

  regulated:
    express_ceiling: 0.25
    lightweight_ceiling: 0.45
    full_council_ceiling: 0.65
    description: "Compliance-heavy - lower thresholds, more deliberation"

  fast:
    express_ceiling: 0.50
    lightweight_ceiling: 0.70
    full_council_ceiling: 0.90
    description: "Speed optimization - skip War Room more often"

  cautious:
    express_ceiling: 0.30
    lightweight_ceiling: 0.50
    full_council_ceiling: 0.70
    description: "Higher stakes environment - deliberate more"

# Command-specific profile overrides
command_profiles:
  do-issue:
    # Lower thresholds for multiple issues (higher risk)
    multi_issue_adjustment: -0.10

  pr-review:
    # Strict mode lowers thresholds
    strict_mode_adjustment: -0.15

  architecture-review:
    # Architecture decisions are inherently higher stakes
    base_adjustment: -0.05
```

### Profile Selection

Effective thresholds = base profile + command-specific adjustments. For example, `do-issue` with 3+ issues applies `-0.10` to all ceilings, while `pr-review` in strict mode applies `-0.15`.

---

## Auto-Continue Logic

### Confidence Scoring

Confidence starts at 1.0 and is adjusted by:

| Factor | Adjustment | Condition |
|--------|-----------|-----------|
| Dissenting views | -0.1 each | Any expert dissent |
| Narrow voting margin | -0.2 | Margin < 30% |
| High RS (Type 1A+) | -0.15 | RS > 0.80 |
| Novel domain | -0.1 | No precedent |
| Compound decisions | -0.1 | Multiple sub-decisions |
| Unanimous agreement | +0.2 | All experts agree |

### Auto-Continue vs. Prompt Decision

- **Express mode**: Always auto-continues with recommendation
- **Confidence > 0.8**: Auto-continues with War Room orders
- **Confidence ≤ 0.8**: Prompts user with formatted confirmation

### Confirmation Prompt Format

Displays: source command, decision needed, RS/decision type/mode/confidence, recommendation with rationale, dissenting views (if any), and Y/N/D options (Yes/No/Details).

---

## Configuration

### User Settings

```json
// ~/.claude/settings.json
{
  "war_room": {
    "checkpoint": {
      "enabled": true,
      "profile": "default",
      "auto_continue_threshold": 0.8,
      "log_all_checkpoints": true,
      "command_overrides": {
        "do-issue": {
          "enabled": true,
          "profile": "cautious"
        },
        "pr-review": {
          "enabled": true,
          "strict_mode_profile": "regulated"
        },
        "architecture-review": {
          "enabled": true
        },
        "fix-pr": {
          "enabled": true,
          "major_scope_only": true
        }
      }
    }
  }
}
```

### Per-Project Override

```json
// .claude/settings.local.json
{
  "war_room": {
    "checkpoint": {
      "profile": "startup",
      "auto_continue_threshold": 0.7
    }
  }
}
```

## Audit Trail

All checkpoint invocations are logged to `~/.claude/memory-palace/strategeion/checkpoints/{date}/{session-id}.yaml` with: session ID, source command, RS assessment, selected mode, outcome (orders, confidence, whether auto-continued), and timing metadata.

---

## Success Criteria

### Functional

- [ ] Checkpoint triggers correctly for each target command
- [ ] RS calculation matches standalone War Room
- [ ] Auto-continue works for confidence > 0.8
- [ ] User prompt appears for ambiguous decisions
- [ ] War Room orders flow back to originating command
- [ ] Audit trail captures all checkpoints

### Performance

- [ ] Express mode checkpoint < 2 seconds
- [ ] Lightweight checkpoint < 30 seconds
- [ ] Full council checkpoint < 5 minutes

### User Experience

- [ ] No visible difference for simple cases (RS ≤ threshold)
- [ ] Clear explanation when War Room engages
- [ ] Seamless continuation after War Room decision
- [ ] Easy override via settings if user dislikes auto-escalation

## Related Documents

- [War Room Specification: Overview](war-room-spec-overview.md)
- [War Room Specification: Integration](war-room-spec-integration.md)
- [Reversibility Assessment Framework](../../plugins/attune/skills/war-room/modules/reversibility-assessment.md)
