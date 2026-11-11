---
name: ticket-writing
description: Writes tickets a reader can assess at a glance, with the why inline or a link away. Use when creating or editing Jira, GitLab, GitHub, or other tracker tickets.
alwaysApply: false
category: conventions
tags:
- tickets
- issues
- jira
- gitlab
- github
- traceability
dependencies:
- git-platform
- decision-journal
complexity: beginner
estimated_tokens: 700
progressive_loading: true
modules:
- modules/tracker-mechanics.md
role: library
---

# Ticket Writing

## When To Use

- Creating or editing a ticket in any tracker
- Filing deferred work from a review or a workflow
- Recording a decision on a ticket

## When NOT To Use

- Writing the ADR or spec itself (see `Skill(leyline:decision-journal)`)
- Writing a merge request description (see `Skill(sanctum:pr-prep)`)

## The Glance Test

Picture a reader arriving from the merge request. On the first screen of the
ticket, without scrolling or opening a comment, they can answer two questions:
what was decided, and why. If the why is too long for that screen, they find
one link to the document that holds it. A ticket failing this test is not done.

## Project template first

A team that edits tickets by hand has already settled on a shape. Before
writing, read three recent tickets of the same type in the same project,
written or edited by a person, and copy their headings, heading level, and
markup. A tracker template (see tracker mechanics) counts as the same signal.
Keep every heading that shape uses. Where the samples put `N/A` under an
empty heading, do the same.

This rule comes from one private Jira project. The labels reviewers deleted
most were `Why:` and `Done when:` from the default shape below, plus `Repro:`
and `h2.` headings. Of 67 tickets with description edits, 42 end in one of
these two shapes:

```markdown
### Impact                 ### Summary
### Expected behavior      ### Context
### Actual behavior        ### Acceptance criteria
### Steps to reproduce     ### Other information
### Environment
### Workarounds
### Other information
```

A rewrite tool produced some of these headings. The team kept them, and
that is the signal: copy the shape a project keeps, whatever wrote it
first. The wording fixes reviewers made by hand:

- Title: component prefix if the project uses one, then the symptom a user
  sees ("Cancelled download not shown in the downloads list"), not the
  mechanism.
- Expected behavior and acceptance criteria use "should". Actual behavior
  uses the present tense.
- A ticket states the problem and how to tell it is fixed. How the code
  changes belongs in the merge request.
- One action per step, one criterion per bullet.
- Contractions are fine. Prefer the common word over the clipped one:
  "synced" over "landed", "immediately" over "at once".

## Default shape

Use this only when the project shows no shape of its own.

```markdown
<What changes, or what was decided. One or two sentences.>

Why: <one to three sentences, or one sentence and a link>
Done when: <only if the title does not already say>
Links: <merge request, ADR, spec, parent>
```

The title names the outcome. Use at most three headings. Delete any heading a
template supplies when it has nothing under it.

## Editing a ticket you wrote

Read the live description before every edit, diff it against what you last
wrote, and change only the sentence that needs it. If a person changed it,
patch their text and never regenerate it from your draft. In the observed
project, one ticket lost a reviewer's restructure that way and had to be
restored from the changelog.

## Inline Or Link

| Situation | Ticket carries |
|-----------|----------------|
| One reason, nothing contested | Why inline, one to three sentences |
| Options were weighed, the choice outlives this work, or the reasoning already exists | Decision plus link |
| Parent ticket already states the reason | Parent link |
| Self-evident change: typo, version bump | Title and merge request link |

Decision plus link means one sentence naming the choice, then the link. The
sentence keeps the ticket readable when the reader lacks access to the document
or it has moved. Do not paste the document into the ticket, because two copies
drift apart. Link durable things: an ADR, a spec path, a merge request. Screen
captures and chat threads do not qualify, so restate what they showed.

Decide in the description, not in comments. When a decision changes, edit the
first lines and leave the history in comments.

## Work Type

- Tasks and stories follow the shape above.
- Bugs need expected behavior, actual behavior, and steps to reproduce, even
  when that runs longer. Nobody can recover those from the merge request.
- Investigations end with the finding and a link to the write-up.

## Cut

Restated diffs, implementation steps, empty headings, filler openers,
promotional adjectives. Never put secrets or credentials in a ticket. Before
saving a long generated body, run `Skill(scribe:slop-detector)`.

## Example

```markdown
Before: Run the lint script on merge request pipelines. Closed by !14.
After:  Run the lint script on merge request pipelines. Why: format and clippy
        failures only surfaced after merge. Closed by !14.
```

The first version says what. Only the second lets the reader judge the work.

## Link Both Ways

A ticket and a merge request must each point at the other, in a place tools can
find. See [tracker mechanics](modules/tracker-mechanics.md) for what each
tracker reads.

## Evidence

No study found measures ticket length or glanceability, so the shape above is
judgment. The link rule has data: only 60% of commits linked to issues across
six projects ([Rath 2018](https://arxiv.org/abs/1804.02433)), and 47% of release
artifacts lacked trace links ([Nath 2025](https://arxiv.org/abs/2511.18187)). See
ADR-0028 for the decision.

## Exit Criteria

- [ ] Headings match three sampled tickets of the same type, or the default
  shape is used because the project has none
- [ ] An edit to an existing ticket changed only the live text it targeted
- [ ] First screen answers what and why, or links to why
- [ ] Merge request and ticket reference each other
- [ ] No empty headings, restated diff, or pasted document
