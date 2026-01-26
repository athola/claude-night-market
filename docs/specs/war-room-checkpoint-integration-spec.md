# War Room Checkpoint Integration Specification

**Version**: 1.0.0-draft
**Date**: 2026-01-25
**Status**: Draft - Pending Review
**Branch**: conserve-updates-1.3.5

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
| `/attune:plan` | attune | After approach generation | Optional, user-requested only |
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

```python
def get_effective_profile(
    command: str,
    user_profile: str = "default",
    context: CheckpointContext = None
) -> dict:
    """Calculate effective thresholds for this checkpoint."""

    base = PROFILES[user_profile].copy()

    # Apply command-specific adjustments
    if command in COMMAND_PROFILES:
        cmd_profile = COMMAND_PROFILES[command]

        # Multi-issue adjustment for do-issue
        if (command == "do-issue" and
            context and len(context.issues_involved) >= 3):
            for key in ["express_ceiling", "lightweight_ceiling", "full_council_ceiling"]:
                base[key] += cmd_profile.get("multi_issue_adjustment", 0)

        # Strict mode adjustment for pr-review
        if command == "pr-review" and context and "strict" in str(context):
            for key in ["express_ceiling", "lightweight_ceiling", "full_council_ceiling"]:
                base[key] += cmd_profile.get("strict_mode_adjustment", 0)

        # Base adjustment for architecture-review
        if "base_adjustment" in cmd_profile:
            for key in ["express_ceiling", "lightweight_ceiling", "full_council_ceiling"]:
                base[key] += cmd_profile["base_adjustment"]

    return base
```

---

## Auto-Continue Logic

### Confidence Scoring

```python
def calculate_confidence(war_room_result: WarRoomSession) -> float:
    """
    Calculate confidence score for auto-continue decision.

    Returns:
        float: 0.0-1.0, where > 0.8 means auto-continue
    """
    confidence = 1.0

    # Reduce confidence for dissenting views
    if war_room_result.dissenting_views:
        dissent_count = len(war_room_result.dissenting_views)
        confidence -= 0.1 * dissent_count

    # Reduce confidence for narrow voting margin
    if war_room_result.voting_margin < 0.3:  # Less than 30% margin
        confidence -= 0.2

    # Reduce confidence for high reversibility score (Type 1A+)
    if war_room_result.reversibility_score > 0.80:
        confidence -= 0.15

    # Reduce confidence for novel problem domain
    if war_room_result.is_novel_domain:
        confidence -= 0.1

    # Reduce confidence for compound decisions
    if len(war_room_result.sub_decisions) > 1:
        confidence -= 0.1

    # Boost confidence for unanimous agreement
    if war_room_result.is_unanimous:
        confidence = min(confidence + 0.2, 1.0)

    return max(confidence, 0.0)
```

### Auto-Continue vs. Prompt Decision

```python
async def handle_checkpoint_response(
    response: CheckpointResponse,
    original_command: str
) -> CommandContinuation:
    """
    Determine whether to auto-continue or prompt user.
    """

    # Express mode always auto-continues
    if response.selected_mode == "express":
        return CommandContinuation(
            continue_automatically=True,
            orders=response.recommendation,
            log_message=f"Express mode: {response.rationale}"
        )

    # Check confidence threshold
    if response.confidence > 0.8:
        return CommandContinuation(
            continue_automatically=True,
            orders=response.orders,
            log_message=f"War Room decision (confidence={response.confidence:.2f}): {response.rationale}"
        )

    # Prompt user for ambiguous cases
    return CommandContinuation(
        continue_automatically=False,
        orders=response.orders,
        prompt_message=format_confirmation_prompt(response),
        log_message=f"War Room decision requires confirmation (confidence={response.confidence:.2f})"
    )
```

### Confirmation Prompt Format

```markdown
## War Room Checkpoint: {source_command}

**Decision**: {decision_needed}

**War Room Assessment**:
- Reversibility Score: {rs} ({decision_type})
- Deliberation Mode: {selected_mode}
- Confidence: {confidence:.0%}

**Recommendation**:
{recommendation_or_orders}

**Rationale**:
{rationale}

{dissenting_views_if_any}

**Proceed with War Room recommendation?**
- [Y] Yes, continue with this approach
- [N] No, let me reconsider
- [D] Show full War Room session details
```

---

## Command Integration Examples

### `/do-issue` Integration

```markdown
## Modified Step 3: Plan (Task Breakdown)

### 3.1 Identify Components to Change
[... existing content ...]

### 3.2 Create Task Breakdown
[... existing content ...]

### 3.3 Dependency Analysis (Multiple Issues)
[... existing content ...]

### 3.4 War Room Checkpoint [NEW]

**Automatic checkpoint when:**
- 3+ issues being implemented
- Dependency conflicts detected
- Overlapping file changes identified

**Checkpoint invocation:**
```bash
# Internal: invoke war-room-checkpoint
Skill(attune:war-room-checkpoint) {
  source_command: "do-issue"
  decision_needed: "Execution strategy for issues #42, #43, #44"
  issues_involved: [42, 43, 44]
  files_affected: ["src/auth/", "src/api/users.py"]
  conflict_description: "Issues #42 and #44 both modify auth middleware"
}
```

**If RS > threshold:**
- War Room convenes (lightweight or full council)
- Returns execution order and PR strategy
- Command continues with War Room orders

**If RS ≤ threshold:**
- Express recommendation returned
- Command continues immediately

**Step 3 Output**: Task breakdown with War Room-validated execution order
```

### `/pr-review` Integration

```markdown
## Modified Workflow

### Phase 3: Code Analysis
[... existing content ...]

### Phase 4: War Room Checkpoint [NEW]

**Automatic checkpoint when:**
- >3 blocking issues identified
- Architecture changes detected
- ADR non-compliance found
- Scope-mode=strict with out-of-scope findings

**Checkpoint invocation:**
```bash
Skill(attune:war-room-checkpoint) {
  source_command: "pr-review"
  decision_needed: "Review verdict for PR #123"
  blocking_items: [
    {type: "blocking", description: "Missing error handling in auth flow"},
    {type: "blocking", description: "API contract change without migration"},
    {type: "architecture", description: "New service added without ADR"},
    {type: "scope", description: "Unrelated refactoring in payment module"}
  ]
  files_affected: ["src/auth/", "src/api/", "src/payment/"]
}
```

**War Room determines:**
- Which blocking issues are truly blocking
- Whether PR should be split
- Specific feedback to provide

### Phase 5: GitHub Review
[... continues with War Room guidance ...]
```

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

---

## Audit Trail

All checkpoint invocations are logged to Strategeion:

```yaml
# ~/.claude/memory-palace/strategeion/checkpoints/{date}/{session-id}.yaml
checkpoint:
  session_id: "checkpoint-20260125-143022"
  source_command: "do-issue"
  decision_needed: "Execution strategy for issues #42, #43, #44"

  assessment:
    reversibility_score: 0.56
    decision_type: "Type 1B"
    selected_mode: "lightweight"
    profile_used: "default"
    effective_thresholds:
      express: 0.40
      lightweight: 0.60
      full_council: 0.80

  outcome:
    escalated: true
    war_room_session_id: "war-room-20260125-143025"
    confidence: 0.85
    auto_continued: true
    orders:
      - "Implement #42 first (auth base)"
      - "Then #43 (depends on #42)"
      - "Defer #44 to separate PR (scope creep)"

  metadata:
    timestamp: "2026-01-25T14:30:22Z"
    duration_ms: 12500
    user_confirmed: null  # null if auto-continued
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

1. **Create `war-room-checkpoint` skill**
   - SKILL.md with lightweight assessment logic
   - Integration with existing reversibility-assessment module
   - Express mode fast-path

2. **Update `/do-issue` command**
   - Add checkpoint invocation after Step 3
   - Implement trigger conditions
   - Test with multiple issues

3. **Add configuration system**
   - User settings support
   - Profile loading
   - Command overrides

### Phase 2: Core Commands (Week 3-4)

4. **Update `/pr-review` command**
   - Add checkpoint after code analysis
   - Integrate with scope modes
   - Handle blocking issue routing

5. **Update `/architecture-review` command**
   - Add checkpoint before recommendation
   - Integrate with ADR validation

6. **Update `/fix-pr` command**
   - Add checkpoint after triage
   - Handle conflicting feedback routing

### Phase 3: Polish (Week 5)

7. **Audit trail implementation**
   - Strategeion checkpoint logging
   - Integration with Memory Palace

8. **Testing and documentation**
   - Integration tests for each command
   - Update command documentation
   - User guide for configuration

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

---

## Related Documents

- [War Room Specification: Overview](war-room-spec-overview.md)
- [War Room Specification: Integration](war-room-spec-integration.md)
- [Reversibility Assessment Framework](../../plugins/attune/skills/war-room/modules/reversibility-assessment.md)
