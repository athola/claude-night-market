# Modes and Fading

How to choose an assistance mode per task and reduce it over time.

## The Two Modes

| | Explain mode | Produce mode |
|---|---|---|
| Agent role | Narrates reasoning, writes scaffolding only | Writes the implementation |
| Human role | Writes the load-bearing code | Reviews the diff |
| Optimizes for | Understanding and skill retention | Throughput |
| Learning value | High (productive failure, retrieval) | Low (offloaded) |
| Use when | Unfamiliar area, high stakes, skill-building | Boilerplate, known patterns, reversible work |

Explain mode is not "produce mode with a paragraph attached." In
explain mode the human writes the part that matters, and the agent
withholds the finished answer so the struggle that builds judgment
actually happens. The agent models the approach, points at the
relevant interfaces, and reviews what the human writes.

## Choosing the Mode

Tie the choice to risk and to whose skill is at stake:

1. Classify the task risk (see `leyline:risk-classification`).
2. Ask: is the goal to ship this, or to build the human's skill in
   this area?
3. Map:

| Risk / goal | Mode |
|-------------|------|
| Low risk, ship goal | Produce |
| Low risk, skill goal | Explain |
| High risk (auth, migration, money, concurrency) | Explain, regardless of goal |
| Agent showed repeated confusion or failure | Drop a tier (see below) |

State the chosen mode explicitly. A silent default to produce mode
is how scaffolding becomes permanent.

## The Fade Protocol

Expertise reversal means constant help eventually hurts. On any
area the human is deliberately building skill in, assistance should
decrease across encounters:

```
produce  ->  explain  ->  manual with review  ->  manual
(agent writes)  (human writes,   (human writes,        (human writes,
                 agent narrates)  agent reviews)         agent silent)
```

Move one step toward manual each time the human demonstrates they
can do the previous step unaided. This is the apprenticeship
fading model: support is withdrawn on purpose as competence grows,
the opposite of permanent dependence.

## Dropping a Tier on Confusion

Borrowed from aviation's "children of the magenta" lesson: when the
automation is not doing what is needed, the operator must downgrade
the level of automation rather than re-issue the same command at
the same level. For coding agents:

- After two consecutive failed attempts of the same shape (same
  file, same error class, same tool), do not try a third blind
  variation. Drop to a lower tier: switch to explain mode, run a
  read-only diagnostic, and have the human state what they believed
  and what the evidence now says.

This is the two-challenge rule already encoded in the project's
global guidance, applied as a deliberate automation downgrade.
