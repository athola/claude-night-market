# Pull Request Template Structure

A description exists to pre-load the model a reviewer would otherwise
rebuild from the diff. Everything below serves that one job. The
decision behind this structure, with sources, is ADR-0021.

## The structure

Six dimensions in two registers. Who, Where, and When are lookups and
cost one table row each. Why and What-and-how are arguments and get
headings. Test plan and Checklist follow when they apply.

```markdown
| | |
|---|---|
| **Who** | audience for the change; out-of-band reviewer if any |
| **Where** | internal blast radius; external consumers or contracts |
| **When** | when it lands; when it is fully integrated |

## Why

## What and how

## Test plan

## Checklist
```

The title carries the summary. Write it imperative and self-contained,
so it still reads correctly a year later in `git log`: "Delete the
FizzBuzz RPC", never "Fix bug" or "Phase 1".

## Worked example

```markdown
Add symmetric to_pdf and read_yaml I/O methods

| | |
|---|---|
| **Who** | resume authors calling the Python API; @docs-owner for the migration note |
| **Where** | `src/simple_resume/io.py`, 4 files. External: breaks the public `generate_pdf()` entry point used by the CLI wrapper |
| **When** | on merge. `generate_pdf()` stays as a shim until 2.0 (est. 2026-10) |

## Why

Callers had to remember two unrelated spellings for the same
operation, and the asymmetry showed up in three separate bug reports
(#478, #481, #482). Merging this closes the API inconsistency before
2.0 freezes the surface.

## What and how

Adds `read_yaml()` and `to_pdf()` on `Resume`, mirroring the pandas
I/O naming the rest of the API already follows. `generate_pdf()`
becomes a deprecation shim that forwards to `to_pdf()`.

A mapper layer between the old and new signatures was considered and
dropped: the shapes have not diverged, so a passthrough mapper would
be a file to keep in sync for no gain.

## Test plan

1. `make test`: 147/147 passing, 5 new cases for the shim path.
2. `make lint`: clean.
3. Manual, CLI wrapper still works on the old entry point:
   `simple-resume build examples/basic.yaml --pdf out.pdf`
   Expected: `out.pdf` opens, one `DeprecationWarning` on stderr,
   exit code 0.
4. Manual, new API path:
   `python -c "from simple_resume import read_yaml;
   read_yaml('examples/basic.yaml').to_pdf('new.pdf')"`
   Expected: `new.pdf` is byte-identical to `out.pdf`.

## Checklist

- [x] Tests fail if the change is reverted
- [x] Docs updated (`README`, migration note in `CHANGELOG`)
- [x] Breaking change called out in the Where row
```

## Section guidance

### The facts table

Three rows, always present. A row that does not apply states that
(`external: none`, `on merge`) instead of being deleted, because a
reader cannot tell a missing blast radius from a blast radius of none.

**Who**: who feels this change. Name the audience, not the author.
Codeowners handle routine reviewer assignment, so only name a person
when the change needs routing they would not get automatically
(security review, a docs owner, a downstream team).

**Where**: two halves, and the second is the one people forget.
Internal is the module or package plus a file count. External is any
consumer outside this repository: published APIs, wire formats, CLI
contracts, database schemas, downstream services. Write
`External: none` when the change is fully contained.

**When**: when the change takes effect and when it is finished. For
most PRs both are `on merge`. Say more when a feature flag, migration
window, deprecation shim, or scheduled rollout means landing and
integration are different dates.

### Why

One to three sentences. The motivating problem, and why merging it now
matters. Link the issue. Source code shows what the software does and
never why it exists, so this is the section a future reader cannot
reconstruct from the diff.

Ground it. "Three bug reports traced to this" beats "improves
consistency".

### What and how

What changed, in the reader's terms rather than a restatement of the
file list. Then how, but only when a real decision point existed:
a non-obvious approach, a tradeoff, or an alternative someone will
predictably ask about. Naming the rejected alternative pre-empts the
review comment that would otherwise cost a round trip.

Mechanical changes skip the how entirely.

## Manual test plans

Attach a test plan when any of these hold:

- The change has no automated coverage.
- It touches a user-facing or CLI-facing flow.
- It is a bug fix. Give reproduce, fix, and verify steps.
- It changes an external contract.

Skip it when automated tests fully cover the change and the diff is
internal. In that case list the commands and results under Test plan
and stop.

**Format**: numbered steps, each with the expected result. Gherkin
belongs in a persisted BDD suite, not a PR body.

```markdown
## Test plan

1. `make test`: 142/142 passing.
2. Start the dev server: `make serve`.
3. POST an empty body to `/api/resume`.
   Expected: HTTP 422 with `{"detail": "resume body required"}`,
   not the HTTP 500 from #481.
4. POST a 12 MB payload.
   Expected: HTTP 413, and the worker process stays up
   (check `make ps`).
```

State the expected result for every step. A step without one is a
step the reviewer cannot fail.

If a step could not be run locally, say which and why, and what was
done instead.

## Optional sections

Add these only when the change calls for them.

**Screenshots**, for UI or CLI output changes. Before and after.

**Migration guide**, for breaking changes. Show the old call and the
new one side by side.

**Performance**, with before and after numbers plus the benchmark
command. No numbers means no claim.

**Security**, when the change touches authentication, input handling,
secrets, or permissions.

**Follow-up work**, for anything deliberately deferred, each item
linked to a tracked issue. An unlinked follow-up is a `TODO` that
will not survive the merge.

**Issue references**: `Fixes #456`, `Related to #789`, `Part of #101`.

## Checklist

Keep it to items that are machine-checkable or genuinely never
skippable. Every soft item added lowers the scrutiny the hard items
get, and belongs in `CONTRIBUTING` instead.

```markdown
## Checklist

- [ ] Tests fail if the change is reverted
- [ ] Docs updated
- [ ] Breaking changes stated in the Where row
```

Extend it only where the change type earns it: a migration guide for
breaking changes, a benchmark for performance work, a threat note for
security work.

## Size variations

### Small fix

The table plus two short sections. No test plan when automated
coverage is complete.

```markdown
Reject empty resume bodies with 422 instead of 500

| | |
|---|---|
| **Who** | API callers hitting `/api/resume` |
| **Where** | `src/api/routes.py`, 1 file. External: changes the status code on an empty POST from 500 to 422 |
| **When** | on merge |

## Why

An empty POST raised an unhandled `KeyError` and returned 500, so
clients retried a request that could never succeed (#481).

## What and how

Validates the body at the route boundary and returns 422. The guard
sits at the trust boundary rather than deeper in the handler, so the
model layer keeps its invariant that a body is present.

## Test plan

1. `pytest tests/test_routes.py`: 18/18, 2 new cases.
2. `curl -X POST localhost:8000/api/resume -d '{}'`
   Expected: HTTP 422, body `{"detail": "resume body required"}`.

## Checklist

- [x] Tests fail if the change is reverted
- [x] Docs updated
```

### Feature

The full structure. The how section carries the design decision and
the rejected alternative. Test plan covers the new path manually if
any part is user-facing.

### Breaking change

Same structure, plus two hard requirements. The External half of the
Where row names every consumer that breaks, and the When row states
the deprecation window. Add a Migration guide section showing the old
and new call.

## Writing quality

Apply `Skill(scribe:slop-detector)` before finalizing.

### Vocabulary

| Instead of | Use |
|------------|-----|
| leverage, utilize | use |
| comprehensive | thorough, complete |
| robust | solid, reliable |
| facilitate | help |
| streamline | simplify |
| seamless | smooth |
| delve | explore |

### Patterns to cut

- "In order to" becomes "To".
- "It should be noted that" becomes the statement itself.
- "This ensures that" becomes the specific guarantee.
- Marketing language: "enterprise-ready", "cutting-edge",
  "best-in-class".
- Tool or AI attribution of any kind.
- Work-in-progress notes. Squash or finish them first.

### Before finalizing

- [ ] Title is imperative and reads correctly out of context
- [ ] All three table rows filled, including `External:`
- [ ] Why is grounded in a number, an issue, or an incident
- [ ] Test plan steps each state an expected result
- [ ] No tier-1 slop words
- [ ] Active voice, no formulaic openers or closers
- [ ] No tool or AI attribution
