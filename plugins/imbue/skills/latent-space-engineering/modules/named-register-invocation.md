---
name: named-register-invocation
description: Name a published standard to pull a whole writing register into
  output at a cost of one line. Cheaper and coarser than exemplar injection,
  with a known mid-session decay.
parent_skill: imbue:latent-space-engineering
category: methodology
estimated_tokens: 700
---

# Named register invocation

Naming a published standard pulls a whole writing register into a
model's output at a cost of one line. It is the cheapest style transfer
available, and its evidence base is thinner than its popularity.

## The technique

An operator added three lines to a personal `CLAUDE.md`:

```markdown
## Communication style
Use ASD-STE-100 when you speak to the operator.
```

ASD-STE100 is Simplified Technical English, a controlled language built
so a technician reading a second language can follow an aircraft
maintenance procedure without misreading it. It sets short sentence
limits, bans the passive voice in procedures, allows only simple
tenses, and fixes one meaning per word.

The operator wrote none of that. The name carried it.

## Why it costs so little

`modules/style-gene-transfer.md` achieves style transfer by injecting a
50-200 line exemplar and prices that at medium to high token cost, per
its own effectiveness table. Naming a standard reaches for the same
latent region with a single sentence.

| Approach | Context cost | Precision |
|----------|--------------|-----------|
| Exemplar injection | 50-200 lines | High, and specific to the exemplar |
| Named register | 1 line | Coarse, and only as good as the model's prior |

The trade is real. An exemplar transfers the exact voice in front of
you. A name transfers whatever the model associates with that name,
which you do not control and cannot inspect.

## The precondition

The technique works only when the model already holds a strong,
consistent prior for the name. That is a property of the standard's
presence in training data, not of the standard's quality.

Good candidates share three traits: a widely published specification,
a stable name, and a distinctive output style. ASD-STE100, Chicago
Manual of Style, and RFC 2119 keyword usage qualify. An internal style
guide, a paywalled standard, or a name that collides with a common word
does not.

Test before relying on it. Ask the model to describe the register in
its own words. A vague or wrong answer means the name is carrying
nothing, and the instruction is costing a line for no return.

## The known failure mode

The constraint decays. Practitioners in the thread that popularized
this technique report that output drifts back toward the model's
default register partway through a long session, without any
instruction being retracted.

That is the argument for pairing a named register with a deterministic
check. Guidance decays across a long context. Counting does not.
`Skill(scribe:simplified-technical-english)` is the worked example: the
one-line invocation sets the register, and `scribe.ste` measures
whether the register actually held.

## What the evidence supports

Being honest about this matters more than the technique does.

| Claim | Support |
|-------|---------|
| A named standard shifts output style | Strong. Directly observable in any session. |
| It is cheaper than exemplar injection | Strong. One line against 50-200. |
| It beats a generic instruction such as "write clearly" | **No controlled study found.** |
| It reduces measurable style violations by a specific amount | **One self-published benchmark, self-scored.** |
| The effect persists across a long session | **Contradicted by practitioner reports.** |

The widely cited number comes from a repository whose author publishes
the caveats that disqualify it as proof: the scoring linter is
regex-only with no passive-voice or part-of-speech detection, each cell
is a single generation, and the judge is the same model family that
produced the output.

Cite the technique as a cheap default worth trying. Do not cite a
percentage.

## When to reach for it

Use a named register when the output has a reader with a job to do:
operator replies, runbooks, error text, and agent-to-agent instructions.

Prefer exemplar injection when matching a specific existing voice, when
the target style has no published name, or when precision matters more
than context budget.

Use neither when the text is reasoning that a human will weigh. A
register that compresses is the wrong tool for prose whose value is the
qualification it carries.
