# The Four Review Questions

A review answers four questions. They are asked in order, because each
answer bounds the next. The decision and its sources are ADR-0031.

| Question | Best answered | In this review |
|----------|---------------|----------------|
| Q1: Is this change needed? | Before the PR: issue, brief, RFC, tech meeting | Check the record exists and the diff serves it |
| Q2: Is the approach right? | Before the PR: design doc, ADR, plan, pairing | Check the diff against the record |
| Q3: Does the code do what it claims? | In the PR | Read the risky parts first |
| Q4: Does it fit the team's understanding of the system? | In the PR | Read every changed file |

## Locate the decision record (Phase 1)

Look for where Q1 and Q2 were decided, in this order:

1. The plan, spec or tasks found by the Phase 1 scope search
2. A linked issue with an accepted discussion
3. An ADR under `docs/adr/`, or a design doc, RFC or RFD the description
   links
4. An attune brief or specification

Record each question as `settled (<link>)` or `unsettled`.

A PR description that only restates the diff is not a record. A record
says why, and names the alternative that lost.

## Q1 and Q2 settled: check the diff against the record

Review whether the diff conforms to the decision. The diff should do what the
record decided, in the way it decided. A finding that the decision itself
is wrong is a REVISIT, addressed to the record rather than to the
author. It does not block the merge.

Posting a REVISIT is outward-facing, so ask first, as Phase 5 does for
issues. When the record is an issue or a discussion, the REVISIT is a
comment there. When it is a file, such as an ADR or a plan, the REVISIT
is a report entry naming the file and section, with an offer to open an
issue against it. Under `--local` or `--dry-run`, REVISIT findings
appear in the report only. The exception is a
PR that surfaces facts the decision did not have, such as a constraint
the design missed. That is BLOCKING, with the new fact as its evidence.

A deviation from the record is IN-SCOPE. Either the code returns to the
record, or the record is amended in the same PR.

## Q1 or Q2 unsettled

A change is design-bearing when it adds a component, a public contract,
a data model, a dependency, or a cross-team behavior. A routine change
with no record is not a finding: a bug fix, a rename, or a contained
refactor carries its own justification in the description.

A design-bearing change with no record is a process finding. Review the
design in this PR, since nobody has yet. Put it first, before any line
comment. When the design objection is large, recommend pausing line
review until the approach is agreed. Design feedback that arrives
mid-review is associated with abandoned changes.

## Q3: order attention, then disclose it

Read the risky hunks first, at full attention:

- where the agreed design meets existing code: boundaries, adapters,
  migrations
- state, concurrency, error paths, and trust boundaries
- external contracts: APIs, schemas, CLI flags, file formats
- files with a history of defects, high churn, or no test coverage
- whatever the author named under "Where to look"

Weigh by effort as well as risk. A large low-risk file may need less of
your time than a small file on a trust boundary. Attention fades with
size: later files in a large PR get fewer comments and carry more
latent bugs. Read the risky hunks while attention is fresh.

The rest gets a lighter read. Say so in the report under "Read lightly",
by file. A reader then knows which files had a full bug-hunting pass.

That an agreed design shrinks the space where bugs hide is an unmeasured
hypothesis. No study located in the research for ADR-0031 measures
it. The ordering is justified by risk concentration and attention limits
alone.

## Q4: every file

Q4 applies to every changed file, whatever its Q3 order. Review's best
evidenced outcomes are knowledge transfer and team awareness, and most
of what reviewers find concerns understandability. For each file, ask:

- Does it change behavior another team or module relies on?
  Phase 4.6 (invariant conflicts) runs the mechanical half.
- Could a teammate explain this change from the code and the description?
- Does it introduce a new pattern where the codebase already has one?

## Report block

```markdown
### Review Questions
- Q1 need: settled (#123) | unsettled
- Q2 approach: settled (docs/adr/0042-...) | unsettled (design-bearing) | unsettled (routine)
- Q3 read in full: `path/a.py`, `path/b.py`
- Read lightly: `docs/x.md`, `tests/fixtures/...`
- Q4: no expectation changes | <findings>
```
