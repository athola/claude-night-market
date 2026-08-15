# Archive Pattern

Completed work is frozen, not deleted, and stays reachable through an
index rather than through the active tree.

## The Problem

When a body of work finishes, its files become dead weight where they
sit. They clutter the active listing, they get pulled in by routines
that no longer apply, and nothing signals whether the work is finished
or merely dormant.

Both obvious moves are wrong. Deleting discards a record that still has
value, and the value usually surfaces months later when someone asks why
a decision was made. Leaving everything in place obscures what is live,
which is the cost this skill's promote/archive/hold triage exists to
avoid in the first place.

## The Structure

```
<root>/
  Archive/
    ARCHIVE_INDEX.md          inventory of what is archived
    Topic Name - YYYY-MM/     frozen, completion date only
  Active Topic/               live work stays at root
```

Name folders with the completion date alone. The start date is history
and belongs in the record; the completion date answers the question
actually asked at a glance, which is how recent this is. Dates sort
correctly and read unambiguously.

## Write a Closing Note Before Archiving

Before moving anything, append a **closing note** to its status record:
what completed, the archive date, and a pointer to any successor. This
makes the archive self-documenting. Someone reading the archived record
later understands why it stops where it does and where the remaining
work went, without needing to reconstruct that from surrounding files.

Skipping the note is the single most common way an archive becomes an
attic.

## Two Layers of Discoverability

1. **`ARCHIVE_INDEX.md`** carries a few lines per archived item: what it
   covered, when it completed, where it sits, and the key files inside.
   This is the layer future sessions actually read.
2. **The governing document** carries the convention, so the archive is
   reachable from the standard startup path without adding to startup
   reads.

The index is what makes archiving cheaper than deleting. Without it,
`Archive/` is a directory nobody lists and the record is lost in
practice even though it survives on disk.

## Relationship to Capture Triage

This module and the promote/archive/hold triage in the parent skill
solve the same problem at two scales. Triage decides whether an
individual capture drains or accumulates. This decides what happens to
a completed body of work once its captures are settled.

The shared rule: nothing is deleted for being old, and nothing stays in
the active listing for having once been active.

## Seeding a Successor

When leftover work becomes a new effort, seed it with current data only.
Read each file against the present state rather than copying it forward.
Carrying stale files into a successor is how an archive's contents leak
back into active work and get treated as current.
