# Progress Report Template

Checkpoint status report for mission progress tracking.

## Purpose

Progress Reports provide structured checkpoints during mission
execution. They track progress, surface blockers, monitor budget
consumption, and update risk status. Use them at natural phase
boundaries or when significant changes occur.

## Template

```yaml
progress_report:
  # REQUIRED: When this report was generated
  timestamp: "2024-03-20T14:30:00Z"

  # REQUIRED: Current phase in the mission lifecycle
  phase: brainstorm | specify | plan | execute

  # REQUIRED: Task progress summary
  progress:
    tasks_complete: 3
    tasks_total: 8
    tasks_blocked: 1
    tasks_in_progress: 2

  # REQUIRED: Items blocking progress (empty if none)
  blockers:
    - description: "Waiting for API key from ops team"
      impact: "Cannot test production integration"
      owner: "user"
      ETA: "2024-03-21"

  # REQUIRED: Budget consumption
  budget:
    tokens_used: 45000
    tokens_budget: 80000        # null if unlimited
    time_elapsed: "1h 30m"
    time_budget: "3 hours"      # null if unlimited

  # REQUIRED: Risk status updates
  risks:
    current_readiness_level: 1  # 0-3 scale
    new_risks:
      - "Third-party API has stricter rate limits than documented"
    resolved_risks:
      - "Database migration approach validated"
    escalated_risks: []         # Risks moved to higher level

  # REQUIRED: Immediate next steps
  next_actions:
    - "Complete task T004 (API client implementation)"
    - "Resolve blocker: obtain API key"
    - "Run integration tests before checkpoint"

  # OPTIONAL: Decisions made since last report
  decisions:
    - choice: "Use Redis for caching instead of Memcached"
      rationale: "Better support for our data structures"
      alternatives_considered: ["Memcached", "In-memory"]

  # OPTIONAL: Notes for the record
  notes: |
    Discovered that the legacy API returns different error codes
    than documented. Updated test expectations accordingly.
```

## Example Reports

### Example 1: Mid-Execution Checkpoint

```yaml
progress_report:
  timestamp: "2024-03-20T14:30:00Z"
  phase: execute

  progress:
    tasks_complete: 5
    tasks_total: 12
    tasks_blocked: 0
    tasks_in_progress: 2

  blockers: []

  budget:
    tokens_used: 52000
    tokens_budget: 100000
    time_elapsed: "2h 15m"
    time_budget: "4 hours"

  risks:
    current_readiness_level: 1
    new_risks: []
    resolved_risks:
      - "API authentication approach confirmed working"
    escalated_risks: []

  next_actions:
    - "Complete T006: Add pagination to list endpoint"
    - "Complete T007: Write integration tests"
    - "Review all API endpoints for consistency"

  decisions:
    - choice: "Use cursor-based pagination"
      rationale: "Better performance for large datasets"
      alternatives_considered: ["Offset-based pagination"]

  notes: |
    All API endpoints now return consistent error responses.
    Ready to proceed with frontend integration.
```

### Example 2: Blocked Checkpoint

```yaml
progress_report:
  timestamp: "2024-03-20T16:00:00Z"
  phase: execute

  progress:
    tasks_complete: 7
    tasks_total: 12
    tasks_blocked: 2
    tasks_in_progress: 0

  blockers:
    - description: "Database migration requires DBA approval"
      impact: "Cannot test schema changes in staging"
      owner: "DBA team"
      ETA: "2024-03-21T10:00:00Z"
    - description: "Feature flag not configured in production"
      impact: "Cannot verify production behavior"
      owner: "Platform team"
      ETA: "2024-03-21"

  budget:
    tokens_used: 68000
    tokens_budget: 100000
    time_elapsed: "3h 45m"
    time_budget: "4 hours"

  risks:
    current_readiness_level: 2
    new_risks:
      - "Time budget nearly exhausted with blockers pending"
    resolved_risks: []
    escalated_risks: []

  next_actions:
    - "Follow up with DBA team on migration approval"
    - "Request feature flag configuration from platform"
    - "Document current state for handoff if needed"

  decisions: []

  notes: |
    Mission paused pending external dependencies.
    All implementable tasks complete. Ready to resume
    once blockers clear.
```

### Example 3: Risk Escalation Checkpoint

```yaml
progress_report:
  timestamp: "2024-03-20T11:00:00Z"
  phase: plan

  progress:
    tasks_complete: 2
    tasks_total: 5
    tasks_blocked: 0
    tasks_in_progress: 1

  blockers: []

  budget:
    tokens_used: 25000
    tokens_budget: 80000
    time_elapsed: "45m"
    time_budget: "2 hours"

  risks:
    current_readiness_level: 2  # Escalated from 1
    new_risks: []
    resolved_risks: []
    escalated_risks:
      - risk: "Authentication changes affect production users"
        from_level: 1
        to_level: 2
        reason: "Discovered 10x more active users than expected"

  next_actions:
    - "Request war-room checkpoint for Level 2 review"
    - "Complete implementation plan with additional controls"
    - "Add staged rollout to plan"

  decisions:
    - choice: "Add feature flag for gradual rollout"
      rationale: "Mitigates risk of widespread auth failure"
      alternatives_considered: ["Direct deploy", "Canary only"]

  notes: |
    Discovered production user count is 10x higher than
    documented. Escalating to Level 2 for additional controls.
```

## Checkpoint Rhythm

When to generate Progress Reports:

1. **Phase boundaries**: Between brainstorm→specify→plan→execute
2. **Blocker identification**: When progress is blocked
3. **Risk escalation**: When readiness level increases
4. **Budget thresholds**: At 50%, 75%, 90% budget consumption
5. **Time intervals**: Every 30-60 minutes for long missions
6. **User request**: When user asks for status

## Integration with Mission Charter

Progress Reports reference the original Mission Charter:

```yaml
mission_charter_ref: "docs/project-brief.md"
charter_status:
  outcome_progress: "60% complete"
  success_metric_status: "On track"
  constraints_status: "Within budget, no forbidden actions"
  scope_adherence: "No scope drift detected"
```

## Integration with Mission Orchestrator

The mission-orchestrator skill uses Progress Reports to:

1. **Track phase progress** - Update mission state with task
   completion
2. **Surface blockers** - Alert user to items requiring attention
3. **Monitor budget** - Warn when approaching limits
4. **Update risk status** - Adjust readiness level as needed

## Related References

- `mission-charter.md` - Original mission definition
- `../modules/mission-state.md` - State persistence schema
- `../../project-execution/references/mission-report.md` - Final mission report
