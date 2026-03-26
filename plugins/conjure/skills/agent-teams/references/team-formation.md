# Team Formation: Sizing and Roles

Rules for forming agent teams based on mission complexity.

## Purpose

Team Formation ensures the right team size and roles for
coordinated agent work. Too few agents underutilize parallelism;
too many create coordination overhead. Clear roles prevent
confusion and ensure accountability.

## Role Definitions

### Coordinator (Always 1)

**Responsibility**: Mission coordination and final synthesis

**Duties**:

- Receives mission charter and forms the team
- Delegates tasks to agents
- Resolves blockers and conflicts
- Monitors budget and progress
- Produces final mission report

**Selection criteria**:

- Strong context awareness
- Good at summarization and synthesis
- Can make trade-off decisions

### Agent (2-7)

**Responsibility**: Own individual tasks and deliverables

**Duties**:

- Execute assigned tasks independently
- Report progress and blockers to coordinator
- Validate own work before marking complete
- Coordinate with other agents on shared interfaces

**Selection criteria**:

- Domain expertise relevant to task
- Self-directed execution capability
- Clear communication

### Reviewer (0-1)

**Responsibility**: Adversarial review and challenge

**Duties**:

- Challenge assumptions in plans
- Validate outputs against requirements
- Check rollback readiness
- Provide "what could go wrong" perspective

**When included**:

- Medium to high risk missions (Level 2+)
- Complex multi-component changes
- Security or compliance sensitive work

**Selection criteria**:

- Different perspective from task agents
- Critical thinking skills
- Can be adversarial constructively

## Team Sizing Rules

### Simple Mission

```yaml
complexity: simple
mode: single-session
team_size: 1
roles:
  - 1 Coordinator (Claude works solo)
includes_reviewer: false
example: "Fix a bug in a single function"
```

### Moderate Mission

```yaml
complexity: moderate
mode: subagents
team_size: 2-4
roles:
  - 1 Coordinator (main session)
  - 1-3 Agents (task executors)
includes_reviewer: false
example: "Add a new feature with tests across 2-3 files"
```

### Complex Mission

```yaml
complexity: complex
mode: subagents
team_size: 5-7
roles:
  - 1 Coordinator (main session)
  - 4-6 Agents (task executors)
includes_reviewer: true
example: "Refactor authentication across API, frontend, and database"
```

### Critical Mission

```yaml
complexity: critical
mode: agent-team
team_size: 5-10
roles:
  - 1 Coordinator (main session)
  - 4-8 Agents (task executors)
  - 1 Reviewer (challenger)
includes_reviewer: true
example: "Migrate payment system from Stripe v2 to v3"
```

## Maximum Team Size

**Hard limit**: 10 agents total

**Rationale**:

- Coordination overhead grows quadratically with team size
- Communication channels = n(n-1)/2
- At 10 agents: 45 potential communication paths
- Beyond 10: consider splitting into separate missions

## Team Formation Checklist

Before dispatching a team:

- [ ] Mission complexity assessed (simple/moderate/complex/critical)
- [ ] Team size determined using rules above
- [ ] Coordinator designated (main session or lead agent)
- [ ] Agents assigned to tasks
- [ ] Reviewer included if Level 2+
- [ ] File ownership defined (no overlapping writes)
- [ ] Communication protocol established (report to coordinator)

## File Ownership Rules

To prevent conflicts, each file should have exactly one agent
responsible for writes:

```
# GOOD: Clear ownership
Agent A: src/api/auth.py, tests/api/test_auth.py
Agent B: src/api/users.py, tests/api/test_users.py

# BAD: Overlapping ownership
Agent A: src/api/auth.py
Agent B: src/api/auth.py  # Conflict!
```

If multiple agents need to modify the same file:

1. Serialize the modifications (Agent A goes first, then B)
2. Or use git worktrees for isolation
3. Or combine into a single agent's scope

## Example Team Formations

### Example 1: API Refactor (Moderate)

```
Mission: Refactor API error handling for consistency

Team:
  Coordinator: Main Claude session
  Agent 1: src/api/errors.py, tests/api/test_errors.py
  Agent 2: src/api/handlers/, tests/api/test_handlers.py
  Reviewer: Not included (Level 1)

Mode: subagents
Team size: 3
```

### Example 2: Auth Migration (Complex)

```
Mission: Migrate from session-based to JWT authentication

Team:
  Coordinator: Main Claude session
  Agent 1: src/auth/jwt.py, tests/auth/
  Agent 2: src/api/middleware/, src/api/decorators/
  Agent 3: Frontend auth integration
  Agent 4: Database token storage
  Reviewer: Agent for security review

Mode: subagents
Team size: 6
```

### Example 3: Payment System (Critical)

```
Mission: Migrate payment processing from Stripe v2 to v3

Team:
  Coordinator: Main Claude session
  Agent 1: src/payments/stripe_v3.py
  Agent 2: src/api/webhooks/, tests/webhooks/
  Agent 3: Database migration scripts
  Agent 4: Frontend payment forms
  Agent 5: Monitoring and alerting
  Reviewer: Agent for edge case testing

Mode: agent-team (experimental)
Team size: 7
```

## Integration with Execution Modes

| Mode | Team Size | Reviewer | Use Case |
|------|-----------|----------|----------|
| single-session | 1 | Never | Simple, sequential tasks |
| subagents | 2-7 | Optional | Parallel independent tasks |
| agent-team | 5-10 | Required | Complex coordinated work |

See `../../delegation-core/references/execution-modes.md` for mode selection guidance.
