---
name: architecture-paradigm-domain-driven
role: library
description: Models a business in its own language. Use when the domain has real business rules to capture.
alwaysApply: false
category: architectural-pattern
tags:
- architecture
- domain-driven-design
- ubiquitous-language
- bounded-context
- anti-ceremony
dependencies: []
tools: []
usage_patterns:
- paradigm-implementation
- domain-modeling
- legacy-decomposition
- adr-support
complexity: intermediate
model_hint: standard
estimated_tokens: 1400
---

# The Domain-Driven Design Paradigm

Design for the future, build for now.

DDD is modeling a business in the business's own language. The goal is not
to avoid structure. It is to avoid structure you cannot back out of, and to
defer structure you do not yet need.

## What DDD Is

Ubiquitous language, bounded contexts, and a model built by talking to the
people who do the work. The measure of a domain model is whether a person
in the business would recognize their own job in it.

## What DDD Is Not

Clean Architecture. Mandatory layering. A mapper between every tier. A
count of design patterns applied before the first line of business logic is
written.

These are DDD-adjacent choices. Each has its own justification, and none of
them is entailed by DDD. Wanting to decouple an API from the domain is a
good reason to add a DTO. "This is what DDD requires" is not, because it
does not.

## Strategic Design Is The Core

The building blocks are not the point, and this is not the repo's opinion.
Evans said so himself, ten years after the book, about the book:

> "things like the entities and value objects [..] [People] come away
> thinking that that's really the core of DDD, whereas, in fact, it's
> really not."

> "I really think that the way I arranged the book gives people the wrong
> emphasis, so that's the biggest part of what I do is rearrange those
> things."

Source: SE-Radio Episode 226, "Eric Evans on Domain-Driven Design at 10
Years" ([video](https://www.youtube.com/watch?v=GogQor9WG-c)). Quotes as
transcribed by [The Core of Domain-Driven
Design](https://www.angulararchitects.io/en/blog/the-core-of-domain-driven-design/),
which also cites his DDD Europe 2016 keynote criticizing the
"over-emphasis on building blocks."

What the core actually is: discovering subdomains and drawing bounded
contexts, in language the business already speaks. Entities, value objects,
and aggregates are how a model reaches code once it exists. They are the
translation, not the thing being translated.

Read the rest of this skill in that light. Every mechanism below is
optional machinery serving a model you found by talking to people.

## When To Use

- The domain has business rules a domain expert could argue about.
- The team can talk to the people who do the work being modeled.
- The system is expected to grow into complexity you cannot yet name.

## When NOT To Use

- Domains with no meaningful business rules (CRUD over a form).
- Single-actor tools with no business vocabulary to share.
- Anything where the model would be a database schema with a new name.

## Build For Now

Once a domain exists, create the data store and one concrete data object.
Pass that object from the repository into the business layer. At the start
of a project, pass it out to the view as well.

That is a legitimate starting state, not technical debt. One object moving
through every layer is the cheapest thing that can work, and it is the
shape the divergence protocol below is designed to split.

## The Divergence Protocol

The DTO arrives at the moment of divergence, not in anticipation of it.

**Trigger**: the view's response shape must hold for contract reasons while
the domain model needs to change.

**Move**: the old data object becomes the view DTO. The new domain object
gains a translation into it. Where fields differ, a copy constructor maps
them, in either direction as needed.

That is the whole mechanism. It works because the starting state (one
shared object) is the same shape as the ending state's DTO, so the split
costs one rename and one translation function. This is why "we might need a
DTO later" is not a reason to build one now: later is cheap.

## Shared-Type Options When Shapes Overlap

Ordered by cost:

1. **Same type in every layer.** The default. If the objects look the same
   everywhere, use the same object.
2. **Builder**, when different contexts select different subsets of one
   fixed field set.
3. **Shared base class** with per-context subclasses (entity, DTO, domain
   object, JSON representation). Each context adds its own fields on top of
   a shared core. This reduces duplication when several contexts genuinely
   share that core.

Option 3 carries a cost worth stating plainly: inheritance couples the
layers. Changing the base changes every context at once, which is the
opposite of the flexibility the divergence protocol buys. It also feeds
straight into the boundary hazard below. Reach for it when duplication is
the larger present pain, and reach for it knowing what it trades away.

## The IO Boundary Rule

Do not reuse a data type across a network or other IO boundary without
validating that you are not sharing something you should not.

This is the one non-negotiable constraint in this skill. Everything else
here can be deferred, dropped, or added later. This cannot.

Option 3 is where it bites hardest: a field added to a shared base class
appears silently in every serialized representation that inherits it,
including the one crossing the wire. The convenience is real and so is the
leak.

### Request DTOs Earn Their Keep Here

When two or more systems exchange commands over a network and **do not
deploy atomically**, a versioned request DTO lets you introduce a new shape
while continuing to serve the old one, and migrate the systems one at a
time. Without it, any change to the command shape requires every system to
update simultaneously, which fails the moment one update fails or one
release waits on an app store, an IT department, or another team.

That is a deployment constraint, not a DDD principle. Name it as such when
you justify the DTO, so the next reader knows which force put it there and
when it can go.

## Strangling An Existing Application Into Domains

Never in one pass. A refactor that tries to do every layer at once does not
land. Per domain, in order:

1. **Data layer.** Split fetching into a reasonable domain boundary.
2. **Business layer.** One business entity, responsible for one domain.
3. **Strangle** existing call sites over to that domain.
4. **View layer.** Last.

Then repeat for the next domain. Keep the implementation simple until a
need for more appears.

## Adoption Steps

1. **Build the language.** Talk to the people in the business. Write down
   the terms they use, and use exactly those terms in code.
2. **Draw the bounded contexts.** Name where one meaning of a term stops
   and another starts. A term meaning two things is two contexts.
3. **Create the store and one data object.** Pass it through the layers.
4. **Wait for divergence.** Apply the protocol above when the contract and
   the model actually pull apart, not before.
5. **Audit the boundaries.** Every type crossing IO gets its fields read.

## Key Deliverables

- A glossary of domain terms that a domain expert would sign off on.
- A context map naming each bounded context and its relationships.
- An ADR recording which ceremony was adopted and which need drove it.
- A field audit for every type crossing an IO boundary.

## Risks and Mitigations

- **Ceremony without need**:
  - **Mitigation**: Name the current need in the pull request that adds
    any DTO, mapper, command object, or layer boundary, and apply the
    `ceremony-audit` lens in `Skill(pensive:architecture-review)`. A mapper
    whose fields are all 1:1 copies is a mapper with no job.
- **Anemic model**:
  - **Mitigation**: If the domain objects carry no behavior and every rule
    lives in a service, the model is a schema with a new name. Move the
    rules onto the objects that own them, or accept that this domain does
    not need DDD.
- **Silent field leak across a boundary**:
  - **Mitigation**: The IO boundary rule above. Treat shared base classes
    as a leak risk, not just a duplication fix.

## Concrete Components

These vocabulary items name the concrete tools and abstractions that show
up when the paradigm is implemented. They are not required dependencies and
they are not part of the skill's ``tools:`` frontmatter (which is reserved
for Claude Code tool restrictions). Use this list to disambiguate during
architecture discussions.

- ``ubiquitous-language-glossary``: the term list the business and the code
  both use, maintained as a first-class artifact
- ``context-map``: names each bounded context and the relationships between
  them, including where one term changes meaning
- ``copy-constructor``: the translation introduced at the moment of
  divergence, mapping fields between a domain object and its view DTO

## Exit Criteria

- [ ] The domain model uses terms a person in the business would recognize
      without translation.
- [ ] Every mapper in the codebase has at least one field that is not a 1:1
      copy, or a documented contract reason to exist.
- [ ] Every type crossing an IO boundary has had its fields audited for
      what they expose.
- [ ] A decomposition in progress names which domain is being strangled and
      which layer it has reached.
