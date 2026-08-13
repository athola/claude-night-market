# ADR-0021: PR Descriptions Carry Six Dimensions in Two Registers

**Date**: 2026-08-12
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Related**: ADR-0019 (superpowers design consolidation)

## Context

A pull request description in this ecosystem is generated in three
places that were never wired to each other:

| Location | Sections it declared |
|----------|----------------------|
| `plugins/sanctum/skills/pr-prep/modules/pr-template.md` | Summary, Changes, Testing, Checklist (4-item) |
| `plugins/sanctum/commands/prepare-pr.md` | the same four plus Quality Gates and a 6-item checklist |
| `plugins/sanctum/agents/pr-agent.md` | Summary, Changes, Testing, Checklist |

No test anchored any of them, and they had already drifted: the command
grew two sections and two checklist items the module never learned
about. This repository also had no `.github/PULL_REQUEST_TEMPLATE.md`,
so PRs opened against it inherited nothing.

The ask that prompted this ADR was to make descriptions short while
covering six dimensions: who the change is for, what it consists of,
where it applies inside the codebase and across external connections,
when it lands and when it is fully integrated, why it was undertaken,
and how it was built. Manual test plans attach when applicable.

Those two goals pull against each other, so the decision below is
mostly about which dimensions earn a heading.

## Research basis

A five-channel research pass ran before the design (GitHub template
corpus, academic literature, practitioner discourse). Four findings
constrained the outcome.

**Review is an understanding activity.** Bacchelli and Bird's study at
Microsoft classified review comments and interviewed participants
across teams, and found review is "less about defects than expected",
serving understanding and knowledge transfer first. A description earns
its place by pre-loading the model a reviewer would otherwise rebuild
from the diff.

**Why outranks what.** Google's `eng-practices` prescribes an
imperative, self-contained first line, then a body carrying what and
especially why, on the grounds that source code shows what software
does but never why it exists. Their named negative examples are
"Fix bug" and "Phase 1".

**Fixed-length forms decay.** Attention is a fixed budget, so a
fifteen-item checklist gets less real scrutiny per item than a
five-item one. Once a contributor learns that a section is safely left
blank, the credibility of every other section falls with it. This is
the mechanism that kills templates, and it is the reason six mandatory
prose headings were rejected.

**Length is not the lever.** No study located isolates description
length against review latency. Patch size is the validated predictor
(arXiv:2109.15141, alongside author experience, reviewer experience,
and queue depth). One study of PR description characteristics
associates long descriptions on new features with slower, more
hesitant reviewer engagement. Claims of the form "template X made
review 40% faster" circulate without a primary source and are not
relied on here.

Sources are listed at the end of this ADR.

## Decision

A description carries all six dimensions, in two registers chosen by
how much prose each dimension actually needs.

**Register one, a facts table.** Who, Where, and When are lookups, not
arguments. Each is one table row, so all three cost three lines
together:

```markdown
| | |
|---|---|
| **Who** | who the change is for, and any out-of-band reviewer |
| **Where** | internal blast radius; external consumers or contracts |
| **When** | when it lands, and when it is fully integrated |
```

A row that does not apply says so (`external: none`, `on merge`)
rather than being deleted. Three rows stay cheap enough to fill
honestly, which is the property the checklist-fatigue finding says a
fifteen-item form loses.

**Register two, prose.** Why and What-and-how are arguments, and they
get headings:

- `## Why` states the motivating problem and why merging matters now.
  This is the highest-value section per both Google and Bacchelli.
- `## What and how` states the change and, when a real decision point
  existed, the approach and the alternative that was rejected. Purely
  mechanical changes skip the how.

**Register three, conditional.** `## Test plan` appears when the change
has a manual verification path. `## Checklist` holds only items that
are machine-checkable or genuinely never skippable.

**Manual test plans attach when any of these hold**: the change lacks
automated coverage, it touches a user-facing or CLI-facing flow, it is
a bug fix (reproduce, fix, verify), or it changes an external contract.
Format is numbered steps, each with its expected result. Gherkin was
rejected for PR bodies: its ceremony suits a persisted BDD suite, not a
one-off verification note.

**Enforcement lands on four surfaces**, because a template with no
consumer drifts:

1. `plugins/sanctum/skills/pr-prep/modules/pr-template.md`, the source
   of record that ships with the plugin.
2. `plugins/sanctum/agents/pr-agent.md` and
   `plugins/sanctum/commands/prepare-pr.md`, synced to the same names.
3. `.github/PULL_REQUEST_TEMPLATE.md` plus a
   `.github/PULL_REQUEST_TEMPLATE/` directory of size-tiered variants.
4. A pytest contract in `plugins/sanctum/tests/`, so deleting a section
   from any copy turns a test red.

## Rejected alternatives

**Six fixed prose headings.** Closest to the literal request and the
reason this ADR exists. Rejected on the checklist-fatigue finding: Who,
Where, and When are blank on most PRs, and a heading that is usually
blank teaches contributors to skim past headings that are not.

**Two required fields with the rest self-pruning.** The nearest match
to the research recommendation, using
`<!-- delete if not applicable -->` comments. Rejected because deletion
loses information: a reader cannot tell an omitted blast radius from a
blast radius of none. The table keeps the assertion.

**Dynamic risk-scaled templates.** GitHub has no conditional template
logic and no UI chooser for alternates (community discussion #13768 is
open). The supported mechanism is separate files under
`.github/PULL_REQUEST_TEMPLATE/` selected by a `?template=` query
parameter, which is what this ADR adopts.

## Consequences

Routine PRs land at roughly fifteen lines, with all six dimensions
answered. Large or risky PRs grow through the prose sections and the
test plan rather than by acquiring new headings.

The contract test is the load-bearing part. Without it the three copies
drift again, which is the state this ADR was written to end. The test
anchors on section names, so renaming a section is a deliberate act
that updates the test in the same commit.

The size-tiered variants add three files that GitHub cannot surface in
its own UI. Contributors reach them through links in `CONTRIBUTING`
guidance or a crafted new-PR URL. If those links go unused, the
variants should be folded back into the default template rather than
maintained as dead weight.

## Sources

- Bacchelli and Bird, "Expectations, Outcomes, and Challenges of
  Modern Code Review", ICSE 2013.
  <https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/ICSE202013-codereview.pdf>
- Google, `eng-practices` CL descriptions.
  <https://github.com/google/eng-practices/blob/master/review/developer/cl-descriptions.md>
- "Predicting Code Review Completion Time in Modern Code Review",
  arXiv:2109.15141. <https://arxiv.org/pdf/2109.15141>
- "How AI Coding Agents Communicate: PR Description Characteristics",
  arXiv:2602.17084. <https://arxiv.org/html/2602.17084>
- Ghiculescu, "Accidental Bureaucracy" (checklist attention budget).
  <https://ghiculescu.substack.com/p/accidental-bureaucracy>
- Shopify Engineering, "On the Importance of Pull Request Discipline".
  <https://shopify.engineering/on-the-importance-of-pull-request-discipline>
- dbt Labs, "The Exact GitHub Pull Request Template We Use".
  <https://docs.getdbt.com/blog/analytics-pull-request-template>
- GitHub Docs, creating a pull request template.
  <https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository>
- GitHub community discussion #13768, template chooser UI.
  <https://github.com/orgs/community/discussions/13768>
