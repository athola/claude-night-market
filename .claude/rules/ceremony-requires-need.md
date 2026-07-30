**No DTO, mapper, command object, or layer boundary without a named,
current need!**

Design for the future, build for now. The goal is not to avoid structure.
It is to avoid structure you cannot back out of, and to defer structure you
do not yet need.

"We might need it later" is not a need. Later is cheap, and the divergence
protocol below is what makes it cheap.

## The rule

- **If objects look the same in every layer, use the same object.** One
  concrete data object passing from the repository through the business
  layer and out to the view is a legitimate starting state, not technical
  debt.
- **When shapes diverge, copy-construct. Do not pre-split.** The trigger is
  a response shape that must hold for contract reasons while the model
  changes. The move: the old object becomes the view DTO, and a copy
  constructor maps the fields that differ.
- **Name the need in the PR.** Any new mapper, DTO, command object, or
  layer boundary states which need put it there. A reviewer who cannot find
  the need deletes the ceremony.

## Boundary exception (this rule never argues against it)

Types crossing a network or other IO boundary get their fields audited for
what they expose. A field added to a shared base class appears silently in
every serialized representation that inherits it, including the one on the
wire.

A **versioned request DTO is justified** whenever the systems exchanging it
do not deploy atomically: it lets you serve a new shape and the old one at
once, and migrate systems one at a time. That is a deployment constraint,
not a DDD principle. Say so when you justify it, so the next reader knows
which force put it there and when it can go.

A mapper at an IO boundary is load-bearing even when it looks like a
passthrough today. Do not delete it.

## Detection

`Skill(pensive:architecture-review)` module `modules/ceremony-audit.md`
carries four manual lenses:

| Signal | Verdict |
|--------|---------|
| Passthrough mapper (every field a 1:1 copy) | Delete it, share the type |
| Twin types (structurally identical across layers) | Collapse until they diverge |
| Speculative DTO (no external contract pins the shape) | Delete, reintroduce on divergence |
| Interface with one implementation, no test double | Inline it (Karpathy AP-3) |

## Why this rule exists

Clean Architecture is a set of trade-offs, not a dogma, and its most common
failure in this repo's problem space is mapping between layers that never
actually diverge. Every passthrough mapper is a file to keep in sync, a
place for a field to go missing, and a cost paid for a flexibility never
exercised.

Domain-Driven Design is modeling a business in the business's own language.
Layering, mapping, DTOs, and command objects are DDD-*adjacent* choices,
each with its own justification, and none of them is entailed by DDD. Want
to decouple an API from the domain? Add a DTO. Do not want that decoupling?
Do not. Neither answer is more or less DDD than the other.

## Sibling rules

- `Skill(imbue:scope-guard)`: worthiness scoring for the feature itself.
- `Skill(leyline:additive-bias-defense)`: burden of proof on every addition.
- `prefer-invariants-over-fallbacks.md`: the same instinct applied to
  defensive code. Both rules say: do not build machinery for a case you
  cannot name.
- `shared-utility-consumer-rule.md`: the same instinct applied to skills.

## References

- `Skill(archetypes:architecture-paradigm-domain-driven)`: the paradigm,
  the divergence protocol, and the IO boundary rule.
- `plugins/pensive/skills/architecture-review/modules/ceremony-audit.md`:
  the review lens.
- `plugins/archetypes/tests/test_ddd_paradigm.py` and
  `plugins/pensive/tests/skills/test_ceremony_audit.py`: the contract.
  Each assertion anchors on a clause unique to the passage it guards, so
  deleting that passage turns the test red.
