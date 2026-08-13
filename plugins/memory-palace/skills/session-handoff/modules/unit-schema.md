# Unit Schema

One thread of work becomes one unit per type. The fields exist so a
future reader can recognize a topic has history and grasp its state
without opening the transcript.

## Fields

```
Thread: short, specific, matchable label
Type:   finding | decision | open-thread | state
Date:   YYYY-MM-DD from the turn timestamps, not today's date
State:  what landed by the end of the session, 1-2 sentences
Why:    the load-bearing reasoning and what was rejected
Open:   what remains unresolved
Ref:    the session this came from
Files:  paths this claim rests on, when it rests on any
```

`Thread` is a retrieval key. Phrase it the way a later session would ask
about the topic, not the way this session happened to describe it.
"Decay curve per unit type" beats "the thing we changed in the model".

`Date` and `Ref` are always required. `Why` and `Open` are omitted
entirely when the transcript gives nothing to put in them. An empty
field is better absent than filled with a guess.

## Declaring Dependencies

`Files` is how a claim states what it depends on. Name a path when the
claim would stop being true if that file changed, and leave it out
otherwise. A unit about how a tool behaves usually names nothing; a
unit about how this repository wires something usually names one or
two files.

Do not guess at paths. A wrong path produces a staleness signal about
a file the claim never rested on, which trains the reader to ignore
the signal.

The writer names the files. The capture path fingerprints them into
`file_digests` and the reader compares. That split is deliberate: the
model knows which files matter and cannot hash them reliably, and the
hook can hash but cannot judge relevance.

## Choosing the Type

| Ask | Type |
|-----|------|
| Will this still be true in a year regardless of this project? | `finding` |
| Is this a choice we could revisit and reverse? | `decision` |
| Is this a question still waiting on an answer? | `open-thread` |
| Is this a status that a week of work would invalidate? | `state` |

Type drives retention, so a wrong type is a correctness bug rather than
a labeling nit. Filing a status update as a `finding` keeps it alive for
a year and lets a later session act on something long since false.

## The Split Rule

When a thread bundles a durable finding with the transient action that
produced it, emit two units with different types.
Each then ages at the right rate.

Wrong, because one shelf life has to serve both:

```
Thread: Recall hook latency
Type:   state
State:  Found that UserPromptSubmit hooks run on every prompt, so we
        made the token check exit before importing anything.
```

Right:

```
Thread: UserPromptSubmit hook cost
Type:   finding
State:  UserPromptSubmit hooks run on every prompt, so a module-level
        import is paid even when the hook does nothing.

Thread: Recall hook import placement
Type:   state
State:  Moved the memory_palace imports inside the functions that use
        them and added a test asserting they stay there.
```

The finding stays useful next year. The state change stops mattering as
soon as the code moves again.

## Open Threads Carry the State of Thinking

A binary open/closed marker loses the middle of a decision. Record where
the thinking landed instead, so the next session resumes the thread
rather than restarting it.

Wrong:

```
Open: Decide how retrieval ranking works.
```

Right:

```
Open: Ranking. Semantic-only was rejected after finding that similarity
      cannot express that a decision was later revised. Leaning toward
      similarity times a type-aware decay weight. Still open: whether
      the weight is computed in the index or by the caller.
```

The second version tells a later session what was already settled, what
was rejected and why, and precisely which question remains.

## Anti-Patterns

| Pattern | Why it fails |
|---------|--------------|
| One unit per tool call | Sub-steps are not threads; fold them into the parent |
| Transcript-order dumping | Units are keyed by topic, not chronology |
| A unit inferring a decision nobody made | Fidelity beats coverage; omit instead |
| Restating the prompt as a `Thread` | Labels must match how the topic is later asked about |
