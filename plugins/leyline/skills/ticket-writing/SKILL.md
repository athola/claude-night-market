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

## Shape

```markdown
<What changes, or what was decided. One or two sentences.>

Why: <one to three sentences, or one sentence and a link>
Done when: <only if the title does not already say>
Links: <merge request, ADR, spec, parent>
```

The title names the outcome. Use at most three headings. Delete any heading a
template supplies when it has nothing under it.

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

- [ ] First screen answers what and why, or links to why
- [ ] Merge request and ticket reference each other
- [ ] No empty headings, restated diff, or pasted document
