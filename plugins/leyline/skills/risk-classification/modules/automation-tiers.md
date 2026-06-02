# Automation Tiers

Risk classification answers "how carefully must this be verified."
Automation tiers answer a second, distinct question: "how much
should the agent do on its own, and when must it hand control
back." A task can be correctly classified RED and still fail
because the agent acted at full autonomy when it should have
proposed and paused.

## Why Graduated Autonomy

Aviation learned this the hard way. When automation does not do
what is needed, the safe move is to *downgrade the level of
automation* (autopilot to flight director to hand-flying) rather
than re-issue the same command at the same level. Crews who could
not or would not downgrade are the "children of the magenta line";
automation dependency was implicated in a large share of accidents.
Classifying the flight as risky was never the gap. Failing to drop
a tier when the automation drifted was.

The transfer to coding agents: pair every risk tier with a default
automation tier, and make downgrading an explicit, pre-licensed
move rather than something the agent has to be talked into.

## The Tiers

| Automation tier | Agent does | Human does | Default for |
|-----------------|-----------|-----------|-------------|
| **A3 Autonomous** | Writes and commits | Spot-checks after | GREEN |
| **A2 Proposed** | Writes a diff, waits | Approves per hunk | YELLOW |
| **A1 Assisted** | Drafts scaffolding, narrates reasoning | Writes load-bearing code, approves | RED |
| **A0 Manual** | Reviews, explains | Writes the change | CRITICAL |

The mapping is a default, not a floor. A human may raise autonomy
when they have strong context, and must be able to lower it freely.

## The Downgrade Trigger

Drop one automation tier, do not re-prompt at the same tier, when
any of these fire:

- **Repeated failure**: two consecutive failed attempts of the same
  shape (same file, same error class, same tool). This is the
  two-challenge rule: no third blind retry.
- **Confidence drop**: the agent cannot state its assumptions, the
  alternatives it considered, or why the change is correct.
- **Stakes spike**: the change reaches into auth, migrations, money,
  concurrency, or a destructive operation mid-task.
- **Mode mismatch**: the agent's stated model of the repo state does
  not match reality (the coding analog of cockpit mode confusion).

On a downgrade, switch to the lower tier's division of labor, run a
read-only diagnostic, and have the human (or an independent checker)
re-establish what is actually true before proceeding.

## Relationship to Verification Gates

Verification gates (see `verification-gates.md`) and automation
tiers are complementary. The gate says what must pass before the
change is accepted; the automation tier says who holds the pen
while it is produced. A RED change runs both: A1 assisted authorship
*and* the RED verification gate, including independent verification
(see `imbue:proof-of-work` module `independent-verification.md`).

## Integration

For orchestrators, carry the automation tier alongside the risk
tier in task metadata:

```json
{
  "metadata": {
    "risk_tier": "RED",
    "automation_tier": "A1",
    "downgrade_reason": null
  }
}
```

When a downgrade trigger fires, record the new tier and the reason,
so the audit trail shows where autonomy was reduced and why. Mode
selection in `imbue:assisted-mastery` reads the automation tier:
A0/A1 imply explain mode, A2/A3 imply produce mode.
