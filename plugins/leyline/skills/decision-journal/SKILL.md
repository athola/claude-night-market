---
name: decision-journal
description: Decision journal (tradeoffs, lessons learned), deferred-capture contract ([Deferred] issues, CLI args, source labels), storage templates. Use to log a lesson.
alwaysApply: false
modules:
- modules/deferred-capture.md
- modules/storage-templates.md
- modules/template-patterns.md
- modules/lifecycle-stages.md
- modules/storage-patterns.md
---

# Decision Journal Contract

## When To Use

- A workflow has just made a decision and needs to record the tradeoff:
  what was chosen, what was rejected, what was sacrificed.
- A workflow has hit a failed approach, rework, or blocker and needs to
  record the lesson.
- Building or validating a consumer hook that writes to the journal.
- Building or validating a plugin's deferred-capture wrapper, or adding a
  source label (load `modules/deferred-capture.md`).
- Choosing a template, maturity stage, or file name for stored knowledge
  (load `modules/storage-templates.md`).

## When NOT To Use

- Scaffolding the files at project init (that is `attune:project-init`).
- Recording a full architecture decision that warrants a numbered ADR in
  `docs/adr/`. Reference its number from a journal entry instead of
  duplicating it.

This is a convention and a helper rather than a hard runtime
dependency. Consumers degrade gracefully when leyline is absent
(see Fallback).

## What This Captures, And Why

AI-assisted work tends to narrate tool output ("the agent built X") and lose
the human reasoning: the decision, the road not taken, and the honest rework
nobody mentions. Two append-only logs, co-located with the code, fix that:

- `docs/tradeoffs.md` records decisions **and the alternatives sacrificed**.
- `docs/lessons-learned.md` records insights, failed approaches, and rework,
  framed blamelessly.

## Files And Discipline

Both files are in `docs/` (co-location is the strongest anti-staleness
lever). Each is a single append-only running log with a scannable
`## Active index` at the top and an `## Archive` section at the bottom.

1. Append-only. An accepted entry is never edited or deleted. Only its
   `Status` changes.
2. Supersede, do not overwrite. A reversal adds a new entry, flips the old
   entry's status to `superseded-by: <new-id>`, and links both ways.
3. Stable IDs (`TR-001`, `LL-001`) so links from PRs, commits, and code
   never break.
4. Every entry links back to its PR, commit, or issue.

Status vocabularies:

- Tradeoffs: `proposed -> accepted -> (superseded-by: TR-NNN | deprecated)`
- Lessons: `open -> actioned -> closed`

## Capture UX: Draft And Confirm

When a workflow reaches a decision or lesson point:

1. Draft the entry from the live context of the phase (the options weighed,
   what was given up, the failure and its root cause).
2. Show the draft to the human and let them confirm or edit.
3. Append it. Tradeoffs start `proposed`, and lessons start `open`.

Do not auto-write without the confirm step. The point is to capture the
human reasoning.

## CLI Interface

Run the helper from leyline:

    python3 ${LEYLINE}/scripts/journal_append.py <tradeoffs|lessons> \
      --project-root <repo-root> \
      --title "<short title>" \
      [--phase <phase>] [--status <status>] \
      [--field key=value ...] \
      [--json '<full field object>'] \
      [--supersedes TR-NNN] \
      [--dry-run]

The helper assigns the next ID, renders the template, inserts the entry above
the `## Archive` marker, updates the active index, and (with `--supersedes`)
flips the prior entry's status and adds backlinks. It is idempotent: appending
an entry whose substantive fields already appear is a no-op.

### Tradeoff fields

`title` (required), `context`, `drivers` (list), `options` (list of
`{name, pros, cons, chosen}`), `decision`, `ystatement`,
`consequences_positive`, `consequences_negative`, `phase`, `deciders`,
`links`. Prefer `--json` for the list-valued fields. `status` and `date`
are auto-set (`proposed` / today) but can be overridden.

### Lesson fields

`title` (required), `what_happened`, `what_went_well`, `what_didnt_work`,
`root_cause`, `action`, `category`, `owner`, `phase`, `links`. `status`
and `date` are auto-set (`open` / today) but can be overridden.

## Fallback (leyline Absent)

The entry template ships inside each scaffolded file as an HTML-comment footer
(`<!-- ENTRY TEMPLATE ... -->`). When the helper is unavailable, a consumer (or
a human) copies that block into the section above `## Archive`, assigns the
next sequential ID, fills it in, and adds an index row by hand. The fallback
template covers the same core sections as the canonical one so entries stay
consistent across the two paths.

## Consumer Hook Shape

Each workflow adds one block at its natural endpoint:

    Record to the decision journal (draft + confirm):
    - If leyline is installed: run journal_append.py for a {tradeoff|lesson},
      drafting fields from this phase's context; show the draft; append on
      confirm.
    - Fallback (leyline absent): append to docs/{tradeoffs|lessons-learned}.md
      using the footer ENTRY TEMPLATE; assign the next sequential ID.

## Compliance Test

    python3 ${LEYLINE}/scripts/journal_append.py tradeoffs \
      --title "Compliance check" --field context="verify" --dry-run

Must print a rendered entry containing `## TR-001:` and write nothing.

## Related Contracts

- `modules/deferred-capture.md`: the CLI, issue template, label
  taxonomy, duplicate detection, and JSON output that every plugin
  deferred-capture wrapper implements. Load it when building or checking
  a wrapper.
- `modules/storage-templates.md`: seedling, growing, evergreen, and
  reference templates, the promotion lifecycle, and naming conventions.
  Load it when organizing a knowledge store. Detail is in
  `template-patterns`, `lifecycle-stages`, and `storage-patterns`.

## Exit Criteria

- [ ] `docs/tradeoffs.md` and `docs/lessons-learned.md` exist with a
  `## Active index` and an `## Archive` section.
- [ ] A new entry has a unique `TR-NNN`/`LL-NNN` id and an index row.
- [ ] Superseding an entry flips the old status to `superseded-by: <id>` and
  adds bidirectional links. The old entry is not deleted.
- [ ] Re-running the same append is a no-op (idempotency holds).
- [ ] A consumer with leyline absent still produces a correctly shaped entry
  from the in-file ENTRY TEMPLATE.

The last criterion holds even for consumers that name `leyline` in their
`dependencies`.
That field is marketplace metadata; no installer acts on it, so
`spec-kit` or `imbue` can be installed without leyline present.
The fallback guards that boundary. Do not remove it as leftover code.
See `docs/metadata.md`, "What `dependencies` Does Not Mean".
