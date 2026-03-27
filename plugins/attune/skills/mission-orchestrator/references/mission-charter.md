# Mission Charter Template

Structured mission definition for coordinated agent work.

## Purpose

A Mission Charter defines the boundaries and success criteria for a
mission before execution begins. It prevents scope drift,
establishes clear completion criteria, and provides a reference
point for checkpoint reviews.

## When to Use

Use a Mission Charter when:

- Starting a new mission that will span multiple phases
- Coordinating work across multiple agents or sessions
- You need clear scope boundaries to prevent drift
- Success criteria need to be explicit and measurable
- Resource constraints (tokens, time) must be tracked

Do NOT use when:

- The task is a single, self-contained change
- Scope is obvious and doesn't need formalization
- The work is exploratory and boundaries are unknown

## Getting Started

1. Copy the template below into your mission planning document
2. Fill in the required fields: `outcome`, `success_metric`,
   `deadline`, `scope`, `stop_criteria`
3. Add optional constraints if you have token/time budgets
4. Store in `.attune/mission-state.json` or your planning document
5. Reference during checkpoint reviews to verify scope adherence

## Why This Pattern

Mission Charters prevent the common failure mode of "scope creep by
accident." Without explicit boundaries, missions tend to expand to
fill available time and tokens. The charter creates a contract that
forces explicit decisions when scope changes are proposed.

This pattern emerged from observing that agents with clear
boundaries complete missions faster and with fewer reworks than
agents who discover scope as they go.

## Template

```yaml
mission_charter:
  # REQUIRED: What success looks like
  outcome: |
    Clear description of the desired end state.
    Should be specific enough to verify completion.

  # REQUIRED: How we measure success
  success_metric: |
    Measurable criteria for mission completion.
    Example: "All tests pass, no lint errors, feature works in demo"

  # REQUIRED: Time boundary
  deadline: session | YYYY-MM-DD | "<duration>"
    # session = complete within this Claude session
    # date = absolute deadline
    # duration = relative (e.g., "2 hours", "3 days")

  # OPTIONAL: Resource and action constraints
  constraints:
    token_budget: 50000      # Maximum tokens to spend (optional)
    time_budget: "2 hours"   # Maximum time (optional)
    forbidden:               # Actions that must NOT be taken
      - "No database schema changes"
      - "No API breaking changes"

  # REQUIRED: Scope boundaries
  scope:
    in_scope:                # Areas to work on
      - "src/api/"
      - "tests/api/"
    out_of_scope:            # Areas to avoid
      - "Frontend code"
      - "Database migrations"

  # REQUIRED: Conditions that halt the mission
  stop_criteria:
    - "Token budget exceeded"
    - "Blocker identified that requires user decision"
    - "External dependency unavailable"
```

## Examples

### Example 1: Feature Implementation

```yaml
mission_charter:
  outcome: |
    Implement user authentication with JWT tokens, including
    login, logout, and token refresh endpoints.

  success_metric: |
    - All auth endpoints return correct responses
    - Token validation works for protected routes
    - Test coverage > 90% for auth module

  deadline: session

  constraints:
    token_budget: 80000
    forbidden:
      - "No changes to existing user schema"
      - "No breaking changes to public API"

  scope:
    in_scope:
      - "src/auth/"
      - "tests/auth/"
      - "docs/api/auth.md"
    out_of_scope:
      - "Frontend login UI"
      - "OAuth integration"

  stop_criteria:
    - "Token budget exceeded"
    - "Security vulnerability discovered"
    - "User requirement clarification needed"
```

### Example 2: Bug Fix

```yaml
mission_charter:
  outcome: |
    Fix the race condition in the order processing queue that
    causes duplicate orders under high load.

  success_metric: |
    - Load test with 1000 concurrent requests shows no duplicates
    - All existing tests pass
    - Fix verified in staging environment

  deadline: "2024-03-20"

  constraints:
    time_budget: "4 hours"
    forbidden:
      - "No changes to queue infrastructure"
      - "No breaking API changes"

  scope:
    in_scope:
      - "src/queue/order_processor.py"
      - "tests/queue/"
    out_of_scope:
      - "Other queue handlers"
      - "Database schema"

  stop_criteria:
    - "Root cause requires architectural changes"
    - "Fix would impact other queue handlers"
```

### Example 3: Refactoring

```yaml
mission_charter:
  outcome: |
    Extract the validation logic from the monolithic service
    class into separate validator modules following SRP.

  success_metric: |
    - All validators have single responsibility
    - Test coverage maintained or improved
    - No behavior changes (same test results)

  deadline: session

  constraints:
    token_budget: 60000
    forbidden:
      - "No public API changes"
      - "No new dependencies"

  scope:
    in_scope:
      - "src/services/order_service.py"
      - "src/validators/"
      - "tests/validators/"
    out_of_scope:
      - "Other service classes"
      - "Frontend validation"

  stop_criteria:
    - "Refactoring reveals deeper architectural issues"
    - "Tests start failing unexpectedly"
```

## Integration with Mission Orchestrator

The mission-orchestrator skill uses Mission Charters to:

1. **Initialize mission state** - Store charter in `.attune/mission-state.json`
2. **Guide phase execution** - Each phase checks scope boundaries
3. **Enable checkpoint reviews** - Progress Reports reference
   original charter
4. **Determine completion** - Success metric verified before
   mission close

## Related References

- `progress-report.md` - Checkpoint template that references
  mission charter
- `../modules/mission-types.md` - Mission type definitions
- `../modules/phase-routing.md` - Phase execution protocol
