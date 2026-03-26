# Mission Report Template

Final mission report with artifacts, decisions, and evidence.

## Purpose

The Mission Report is the definitive record of a completed
mission. It documents what was delivered, why decisions were
made, how success was validated, and what follow-up is needed.
Use it to close missions and hand off to future maintainers.

## When to Use

Generate a Mission Report when:

- A mission completes successfully (outcome: success)
- A mission is terminated early (outcome: partial or failed)
- User requests a final summary
- Handing off work to another agent or session
- Archiving for future reference

Do NOT generate when:

- The mission is still in progress (use Progress Report instead)
- The work was a single trivial change

## Getting Started

1. Copy the template below
2. Fill required fields: `mission`, `duration`, `outcome`,
   `delivered_artifacts`, `decisions`, `validation_evidence`,
   `follow_ups`
3. Add optional `lessons_learned`, `blockers_resolved`, `metrics`
   if relevant
4. Store in mission archive or attach to PR/commit
5. Link from any related issues or discussions

## Why This Pattern

Mission Reports create institutional memory. Without them, the
rationale behind decisions decays: six months later, nobody
remembers why a particular approach was chosen or what alternatives
were considered.

The `decisions` field with `alternatives_considered` is especially
valuable: it prevents future contributors from re-litigating
settled questions without new information.

This pattern emerged from observing that teams with good
documentation of "why" move faster than teams who must re-derive
rationale from code archaeology.

## Template

```yaml
mission_report:
  # REQUIRED: Mission identification
  mission:
    name: "Implement user authentication"
    brief_ref: "docs/project-brief.md"
    spec_ref: "docs/specification.md"
    plan_ref: "docs/implementation-plan.md"

  # REQUIRED: Mission duration
  duration:
    start: "2024-03-20T09:00:00Z"
    end: "2024-03-20T14:30:00Z"
    total: "5h 30m"

  # REQUIRED: Mission outcome
  outcome: success | partial | failed

  # REQUIRED: What was delivered
  delivered_artifacts:
    - path: "src/auth/jwt.py"
      type: created | modified | deleted
      description: "JWT token generation and validation"
    - path: "src/api/middleware/auth.py"
      type: modified
      description: "Authentication middleware for protected routes"
    - path: "tests/auth/test_jwt.py"
      type: created
      description: "Unit tests for JWT module"

  # REQUIRED: Key decisions with rationale
  decisions:
    - decision: "Use RS256 algorithm for JWT signing"
      rationale: |
        Asymmetric encryption allows public key distribution for
        verification without exposing private key.
      alternatives_considered:
        - "HS256 (simpler but symmetric)"
        - "Opaque tokens (requires database lookup)"
      impact: "Requires key management infrastructure"

  # REQUIRED: How success was validated
  validation_evidence:
    - description: "All unit tests pass"
      evidence_type: test
      status: pass
      reference: "pytest tests/auth/ -v"
    - description: "Integration test covers full auth flow"
      evidence_type: test
      status: pass
      reference: "pytest tests/integration/test_auth.py"
    - description: "Security review completed"
      evidence_type: review
      status: pass
      reference: "docs/security-review.md"

  # REQUIRED: Recommended next steps
  follow_ups:
    - action: "Add refresh token rotation"
      priority: medium
      rationale: "Improves security posture"
      estimated_effort: small
    - action: "Implement token revocation"
      priority: low
      rationale: "Required for logout across devices"
      estimated_effort: medium

  # OPTIONAL: Lessons learned
  lessons_learned:
    - lesson: "Start with integration tests earlier"
      context: "Found integration issues late that required rework"
      application: "Write integration test first in future auth work"
    - lesson: "Document key rotation strategy before implementation"
      context: "Had to retrofit key management"
      application: "Include key rotation in initial design"

  # OPTIONAL: Blockers encountered
  blockers_resolved:
    - blocker: "API documentation was outdated"
      resolution: "Tested actual API behavior, updated tests"
      time_impact: "30 minutes"

  # OPTIONAL: Metrics
  metrics:
    files_changed: 5
    lines_added: 342
    lines_removed: 23
    tests_added: 12
    tests_passed: 12
    readiness_level_peak: 2
```

## Example Reports

### Example 1: Successful Feature Implementation

```yaml
mission_report:
  mission:
    name: "Add rate limiting to API"
    brief_ref: "docs/project-brief-ratelimit.md"
    spec_ref: "docs/specification-ratelimit.md"
    plan_ref: "docs/implementation-plan-ratelimit.md"

  duration:
    start: "2024-03-19T10:00:00Z"
    end: "2024-03-19T15:30:00Z"
    total: "5h 30m"

  outcome: success

  delivered_artifacts:
    - path: "src/middleware/rate_limit.py"
      type: created
      description: "Token bucket rate limiter"
    - path: "src/api/routes.py"
      type: modified
      description: "Added rate limit decorator to endpoints"
    - path: "tests/middleware/test_rate_limit.py"
      type: created
      description: "Unit and integration tests"
    - path: "docs/api/rate-limiting.md"
      type: created
      description: "API documentation for rate limits"

  decisions:
    - decision: "Use Redis for distributed rate limiting"
      rationale: |
        Multiple API instances need shared state for accurate
        rate limiting. Redis provides atomic operations needed
        for token bucket algorithm.
      alternatives_considered:
        - "In-memory (doesn't work with multiple instances)"
        - "Database (too slow for rate limit checks)"
      impact: "Requires Redis in infrastructure"

    - decision: "Return 429 with Retry-After header"
      rationale: |
        Standard HTTP response for rate limiting. Retry-After
        helps clients implement backoff correctly.
      alternatives_considered:
        - "200 with error body (non-standard)"
      impact: "None, follows best practices"

  validation_evidence:
    - description: "Unit tests pass"
      evidence_type: test
      status: pass
      reference: "pytest tests/middleware/ -v"
    - description: "Load test shows correct rate limiting"
      evidence_type: test
      status: pass
      reference: "locust -f tests/load/rate_limit.py"
    - description: "Code review approved"
      evidence_type: review
      status: pass
      reference: "PR #123 approval"

  follow_ups:
    - action: "Add per-endpoint rate limit configuration"
      priority: medium
      rationale: "Some endpoints need different limits"
      estimated_effort: small
    - action: "Add rate limit metrics to monitoring"
      priority: high
      rationale: "Visibility into rate limit behavior"
      estimated_effort: small

  lessons_learned:
    - lesson: "Test with realistic request patterns"
      context: "Initial tests used uniform distribution, production
        has bursts"
      application: "Include burst scenarios in load tests"

  metrics:
    files_changed: 4
    lines_added: 287
    lines_removed: 12
    tests_added: 15
    tests_passed: 15
    readiness_level_peak: 1
```

### Example 2: Partial Completion

```yaml
mission_report:
  mission:
    name: "Migrate to new payment provider"
    brief_ref: "docs/project-brief-payment.md"
    spec_ref: "docs/specification-payment.md"
    plan_ref: "docs/implementation-plan-payment.md"

  duration:
    start: "2024-03-18T09:00:00Z"
    end: "2024-03-18T17:00:00Z"
    total: "8h 0m"

  outcome: partial

  delivered_artifacts:
    - path: "src/payments/new_provider.py"
      type: created
      description: "New payment provider integration (untested)"
    - path: "src/api/webhooks/payments.py"
      type: modified
      description: "Webhook handlers for new provider"
    - path: "docs/payment-migration-status.md"
      type: created
      description: "Migration status and remaining work"

  decisions:
    - decision: "Feature flag for gradual migration"
      rationale: |
        Cannot migrate all users at once. Feature flag allows
        testing with subset before full migration.
      alternatives_considered:
        - "Big bang migration (too risky)"
      impact: "Need to maintain both providers during transition"

  validation_evidence:
    - description: "Unit tests pass for new provider"
      evidence_type: test
      status: pass
      reference: "pytest tests/payments/ -v"
    - description: "Integration tests with sandbox"
      evidence_type: test
      status: fail
      reference: "Sandbox API returns unexpected errors"
    - description: "Webhook signature verification"
      evidence_type: test
      status: blocked
      reference: "Waiting on provider documentation"

  follow_ups:
    - action: "Resolve sandbox API issues"
      priority: critical
      rationale: "Blocks integration testing"
      estimated_effort: medium
    - action: "Complete webhook signature verification"
      priority: high
      rationale: "Security requirement"
      estimated_effort: small
    - action: "Run production migration with 1% traffic"
      priority: high
      rationale: "Validate real-world behavior"
      estimated_effort: small

  lessons_learned:
    - lesson: "Verify sandbox behavior matches production"
      context: "Sandbox API had different behavior than documented"
      application: "Request production access earlier"

  blockers_resolved:
    - blocker: "Provider API documentation incomplete"
      resolution: "Contacted provider support, received clarification"
      time_impact: "2 hours"

  metrics:
    files_changed: 3
    lines_added: 456
    lines_removed: 34
    tests_added: 8
    tests_passed: 5
    tests_failed: 2
    tests_blocked: 1
    readiness_level_peak: 2
```

### Example 3: Failed Mission

```yaml
mission_report:
  mission:
    name: "Upgrade database to PostgreSQL 16"
    brief_ref: "docs/project-brief-pg16.md"
    spec_ref: "docs/specification-pg16.md"
    plan_ref: "docs/implementation-plan-pg16.md"

  duration:
    start: "2024-03-17T14:00:00Z"
    end: "2024-03-17T16:30:00Z"
    total: "2h 30m"

  outcome: failed

  delivered_artifacts:
    - path: "docs/pg16-incompatibility-report.md"
      type: created
      description: "Analysis of PostgreSQL 16 incompatibilities"

  decisions:
    - decision: "Abort upgrade mission"
      rationale: |
        Critical incompatibility discovered: our ORM generates
        queries that are invalid in PG16. Fixing would require
        ORM upgrade which is out of scope.
      alternatives_considered:
        - "Proceed with ORM upgrade (estimated 2 weeks)"
        - "Rewrite affected queries manually (high risk)"
      impact: "Remain on PostgreSQL 15"

  validation_evidence:
    - description: "Incompatibility identified"
      evidence_type: test
      status: fail
      reference: "docs/pg16-incompatibility-report.md#L45"

  follow_ups:
    - action: "Schedule ORM upgrade project"
      priority: medium
      rationale: "Prerequisite for PostgreSQL 16"
      estimated_effort: large
    - action: "Review PostgreSQL 16 changelog for other changes"
      priority: low
      rationale: "Prepare for future upgrade"
      estimated_effort: small

  lessons_learned:
    - lesson: "Test major version upgrades earlier"
      context: "Found incompatibility 2.5 hours into mission"
      application: "Run compatibility tests before mission start"
    - lesson: "Check ORM compatibility matrix"
      context: "ORM didn't support PG16 at our version"
      application: "Verify all dependencies support target version"

  blockers_resolved: []

  metrics:
    files_changed: 1
    lines_added: 87
    lines_removed: 0
    tests_added: 0
    readiness_level_peak: 3
```

## Required vs Optional Fields

| Field | Required | Notes |
|-------|----------|-------|
| mission | Yes | Links to planning artifacts |
| duration | Yes | Track time investment |
| outcome | Yes | success/partial/failed |
| delivered_artifacts | Yes | What changed |
| decisions | Yes | Why choices were made |
| validation_evidence | Yes | How success verified |
| follow_ups | Yes | Handoff to future work |
| lessons_learned | No | Retrospective insights |
| blockers_resolved | No | Obstacles overcome |
| metrics | No | Quantitative summary |

## Integration with Mission Orchestrator

The mission-orchestrator skill produces a Mission Report when:

1. All phases complete successfully (outcome: success)
2. Mission is terminated early (outcome: partial or failed)
3. User requests final report

## Related References

- `../../mission-orchestrator/references/mission-charter.md` - Original mission definition
- `../../mission-orchestrator/references/progress-report.md` - Checkpoint reports during execution
- `../modules/mission-state.md` - State persistence schema
