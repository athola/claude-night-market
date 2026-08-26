---
module: ceremony-audit
description: Manual review lenses for passthrough mappers, twin types, speculative DTOs, and single-implementation interfaces that separate layers which never diverge
parent_skill: architecture-review
category: architecture
tags:
- ceremony
- mapping
- dto
- boundaries
- review-lens
---

# Ceremony Audit Lenses

Four patterns where a codebase pays for a separation it does not have.
Each one is machinery that would be load-bearing if the layers it divides
had actually diverged. They have not, so it is not.

These are **manual review lenses**, not an AST detector. No T-*/S-*
automation backs them, so the detector-test rule in `architecture-review`
does not apply here. The reviewer applies them by reading the code. This
follows the precedent set by
`performance-review/modules/memory-allocation-lenses.md`.

The governing question, asked of every finding: **what need does this
ceremony serve today?** Not what need it might serve. Not what a pattern
book says it serves.

## The Four Signals

| Signal | Detection | Verdict |
|--------|-----------|---------|
| Passthrough mapper | Every field is a 1:1 copy. No transform, no rename, no filter | Delete the mapper and share the type |
| Twin types | Two types in different layers, structurally identical field-for-field | Collapse to one until they diverge |
| Speculative DTO | The DTO mirrors its entity exactly and no external contract pins its shape | Delete it, and reintroduce on divergence |
| Interface with one implementation | One impl, no test double, no second consumer planned | Inline it (Karpathy AP-3) |

## Applying The Lenses

### Lens 1: Passthrough Mapper

Read the mapper body. If every assignment is `dst.x = src.x` with no
transform, no rename, no filtering, and no defaulting, the mapper's only
effect is to convert a type into an identical type.

Ask what the two types are for. If the answer is "layering," that is the
name of a rule, not a need.

### Lens 2: Twin Types

Two types, one per layer, with the same fields and the same meanings. The
duplication is usually justified as "keeping the layers independent," but
independence you never exercise is independence you are paying for and not
using. Collapse them. The divergence protocol in
`Skill(archetypes:architecture-paradigm-domain-driven)` makes the later
split cost one rename and one copy constructor.

### Lens 3: Speculative DTO

A DTO exists to hold a response shape steady while the model behind it
moves. If no external contract pins the shape, nothing is being held
steady and the DTO is a copy with a different name. The test is whether
some consumer outside your deploy unit depends on the shape.

### Lens 4: Interface With One Implementation

One implementation, no test double using it, no second implementation
planned. The interface is an indirection with a single destination. Inline
it. This is Karpathy AP-3 (Strategy Pattern for One Function) at the type
level, and it is the same instinct that says a utility-named skill
with fewer than two inbound consumers should be folded back into its
first consumer.

## Reporting

Each finding must name the *need* the ceremony would serve. If no current
need can be named, **the ceremony is the finding**. Write it up as such,
with the location and the verbatim anchor that `citation_verifier.py`
expects.

Do not recommend deleting a boundary a reader might be relying on without
first checking the counter-signal below.

## Counter-signal: Do Not Over-Correct

**A mapper at an IO boundary is load-bearing even when it looks like a
passthrough today.** Its job is not to transform the fields it currently
copies. Its job is to stop future internal fields from silently escaping
across the wire. Delete it and the next field someone adds to the domain
object appears in the serialized payload for free.

The audit **must not flag it**. When Lens 1 or Lens 3 lands on a type that
crosses a network or other IO boundary, the finding is void.

This mirrors the anti-goals discipline in `Skill(scribe:slop-detector)`:
an audit that cannot say what it refuses to flag will eventually delete
something that was holding the roof up.

Related: the IO boundary rule in
`Skill(archetypes:architecture-paradigm-domain-driven)`, which is the
positive statement of the same constraint. The rule that binds new
work is the same one this lens audits old work against: no DTO,
mapper, command object, or layer boundary without a named, current
need, stated in the pull request that adds it.
