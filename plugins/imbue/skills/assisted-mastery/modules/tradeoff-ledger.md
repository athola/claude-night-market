# Tradeoff Ledger

A lightweight record of a consequential design decision: the
options, the axis each wins on, the choice, and the reasoning. It
makes the decision auditable later and challengeable now, which is
how working through tradeoffs builds the judgment that blind
acceptance never does.

## When to Record

Record a ledger entry when a decision has more than one defensible
answer and is costly to reverse:

- Choosing a data structure, schema, or interface that others will
  build on.
- Selecting a library or pattern over alternatives.
- Trading off simplicity against flexibility, or speed against
  clarity.

Do not record trivial or obvious choices. A ledger full of
ceremony entries trains people to skip it.

## Entry Format

```markdown
## Decision: <one line>

- Date: <YYYY-MM-DD>
- Context: <what forced this decision>
- Options:
  - A. <option>: wins on <axis>, loses on <axis>
  - B. <option>: wins on <axis>, loses on <axis>
  - C. <option>: wins on <axis>, loses on <axis>
- Choice: <which, and the deciding axis>
- Ramifications: <what this makes easy, what it makes hard,
  what reversing it would cost>
```

## Where It Lives

For a session-local decision, keep the entry in the working notes
or PR description. For a decision that should outlive the session,
promote it to the project decision journal via
`leyline:decision-journal`, which is the durable, indexed home for
tradeoffs and lessons learned. The ledger format above maps
directly onto a decision-journal entry.

## Why Three Options

Two options is a yes/no framed as a choice; it hides the real
design space. Forcing a third viable option surfaces the axis the
binary was concealing. Stop at the point of diminishing returns,
usually three to five, rather than enumerating every theoretical
possibility. The global guidance to "generate 3-5 approaches
before choosing" is the same rule, applied to design decisions.
