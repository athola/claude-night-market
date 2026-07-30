# Verifier Integrity

Proof-of-work proves that a check passed. This module proves the check
was worth passing. They are different claims, and the gap between them
is where confident, green, wrong work ships.

## The two failure modes

A passing verifier can mislead in two independent ways:

1. **The spec is wrong.** The check confirms the code does what the
   spec says; it cannot confirm the spec says what you meant. A
   machine-checked proof "adheres to a formal specification but not
   necessarily to original human intent." Autoformalization research
   finds its dominant failure is a syntactically valid, type-correct
   statement that means the wrong thing; property-based-testing studies
   found roughly 10% of specs in strong verified-code benchmarks were
   underspecified.
2. **The check is hollow.** A test that passes no matter what the code
   does is not evidence. `assert True`, a mock that returns the
   expected value, a property that never triggers, an integration test
   whose service is stubbed to always succeed: all green, all worthless.

Independent verification (`modules/independent-verification.md`) answers
a different question: *who* verifies. This module answers *whether the
verification is real at all.* Both are required; neither substitutes for
the other.

## Guard 1: validate the spec separately from the code

Before trusting a green check, confirm the check encodes the actual
requirement, not a restatement of the implementation.

- State the acceptance criterion in terms of observable behavior the
  user cares about, then confirm the test asserts exactly that. See
  `modules/acceptance-criteria.md`.
- Cross-check the spec with an independent signal: a differential
  example, a second phrasing of the requirement, or human review. The
  higher the blast radius, the more this matters.
- Watch for the tautology: a test derived from the implementation
  ("assert the function returns what the function returns") verifies
  nothing. The check must be derivable from the requirement without
  reading the implementation.

## Guard 2: prove the check can fail (fake-resistance)

A check earns trust only by going red when the behavior it guards
breaks. Demonstrate it, do not assume it.

- **Revert-test / mutation.** Break the behavior on purpose (revert the
  fix, flip a condition, return a wrong constant) and confirm the check
  fails. If it stays green, the check does not test what you think.
  `sanctum:validate-pr` applies exactly this to prove a regression test
  is a genuine guard; the Iron Law coverage gate
  (`modules/iron-law-enforcement.md`) tracks mutation coverage for the
  same reason.
- A single mutation that survives is a hole in the gate, not a rounding
  error. Close it or document why it is acceptable.

## Guard 3: prefer executable checks over an LLM judge

For anything correctness-bearing, the completion signal should be
something that *runs*, not something a model asserts. Executable tests
catch spec-faithfulness failures that an LLM-as-judge misses, and LLM
self-verification is unreliable: models are frequently no better at
judging their output than at producing it, and self-critique can degrade
it. An LLM judge is acceptable only for genuinely subjective criteria
where no executable check exists, and even then it must be independent
of the producer (`modules/independent-verification.md`).

## Guard 4: prefer property-based checks where a property exists

Example-based tests confirm the cases you thought of. A property or
invariant confirms a class of cases, including the ones you did not.
Where a property holds (round-trips, idempotence, ordering,
conservation, "output is always non-negative"), assert the property and
fuzz the inputs rather than pinning three hand-picked examples. LLMs are
good at inferring such properties from types and docstrings; this is a
cheap, fake-resistant verifier that fits an agent loop today. See
`Skill(leyline:testing-quality-standards)`. Tightening types so illegal
states are unrepresentable (`prefer-invariants-over-fallbacks`) is the
same move at compile time.

## Guard 5: repair from the verifier's localized feedback

When a real check fails, the error is high-value context, not just a
red light. Feed the specific failure (location, expected-versus-actual,
remaining goal) back and repair the failing fragment, rather than
regenerating the whole artifact and hoping. Cap the repair attempts;
after the cap, surface the failure instead of forcing a green.

## Guard 6: match verifier strength to blast radius

Verification effort should scale with cost-of-error, not prestige. A
throwaway augmentation or a data-munging script does not need a property
suite; an automation that runs without a human in the loop and whose
failure is expensive (auth, money, migrations, concurrency) earns the
full treatment: spec review, mutation-proven checks, and independent
verification. Applying maximal verification everywhere trains reviewers
to rubber-stamp, the exact degradation it exists to prevent.

## Progress Tracking

- `proof:verifier-integrity-checked`: the completion check has been
  shown to encode the real requirement and to fail when the behavior
  breaks (spec validated, at least one mutation/revert confirmed red).

Record, as part of the evidence log, which mutation was applied and that
the check went red, alongside the passing run. A green run plus a proven
red-on-break is far stronger evidence than a green run alone.

## When This Does Not Apply

Low-stakes, reversible, easily-isolated changes do not need spec
cross-validation or mutation proofs; standard proof-of-work evidence is
enough. Reserve the full integrity check for changes where a
convincing-but-wrong green check would be expensive to trust. The point
is not more ceremony; it is real evidence exactly where it pays.

## Evidence Format

```markdown
[V1] Check: [the test/gate claimed to prove the behavior]
     Encodes requirement: [the observable behavior, stated from intent]
     Fake-resistance: [mutation applied] -> [check went RED: yes/no]
     Independence: [executable / who verified, if high-stakes]
     Passing run: [command + output reference]
```

## Reusable verifier techniques

Techniques from the formal-methods literature that transfer to an
ordinary agentic coding loop:

| Technique | Source | Application |
|-----------|--------|-------------|
| Prover-verifier game (helpful vs sneaky) | arXiv 2407.13692 | Gate on a small independent checker; spawn an adversarial test-writer that tries to slip a wrong-but-passing solution past it |
| Error-driven targeted repair | Baldur (arXiv 2303.04910), APOLLO | Feed the checker's localized error back; repair only the failing fragment; cap attempts |
| Mutation / revert-test | anti-cargo-cult, `sanctum:validate-pr` | Prove the check goes red when behavior breaks; a check that never fails is not a check |
| Property-based verifier gate | Anthropic PBT, arXiv 2506.18315 | Infer invariants, fuzz inputs, use as the completion gate for non-math code |
| Autoformalize-then-check | Draft-Sketch-Prove (arXiv 2210.12283) | Freeze a checkable skeleton (signatures, contracts, tests), fill and verify the gaps; review the spec, not just the code |
| Best-of-N with external verifier | arXiv 2506.18203, 2402.08115 | Accept only what a sound external verifier passes; never self-judge |

Two findings bound how far this goes. First, the generator must never
be its own judge: LLM self-verification is unreliable, models are
frequently no better at judging their own output than at producing it,
and self-critique can degrade performance (arXiv 2402.08115). The
generator-verifier asymmetry is real but only pays off with a
genuinely independent, sound verifier.

Second, and more limiting: **a green check is not correctness.** A
machine-checked pass proves the code satisfies the spec, never that
the spec captured human intent. The property-based-testing solver work
found underspecification in about 10% of specs in state-of-the-art
verified-code benchmarks. Spec-writing, not proof-search, is the wall,
and LLMs are weakest exactly there. Match verifier strength to blast
radius: specs earn their cost for automations with high cost-of-error,
and are wasted on augmentations and easily-isolated errors.

## Sources

- Prover-Verifier Games improve legibility
  (https://arxiv.org/abs/2407.13692)
- Baldur: whole-proof generation and repair
  (https://arxiv.org/abs/2303.04910)
- Draft, Sketch, and Prove (https://arxiv.org/abs/2210.12283)
- On the self-verification limitations of LLMs
  (https://arxiv.org/abs/2402.08115)
- Property-based testing to bridge LLM code generation and validation
  (https://arxiv.org/abs/2506.18315)
- Finding bugs with Claude and property-based testing
  (https://www.anthropic.com/research/property-based-testing)
- Automatic formal verification for code generation, Logical
  Intelligence
  (https://logicalintelligence.com/blog/automatic-formal-verification-for-code-generation)
- Using formal methods at work, Hillel Wayne
  (https://www.hillelwayne.com/post/using-formal-methods/)

Evidence gaps to respect when quoting the above: the
spec-is-the-oracle problem is unsolved, most real code has no formal
spec (so "checked" is not "correct"), and the benchmarks behind these
numbers are math-skewed (miniF2F, ProofNet, PutnamBench) while
code-side verified-generation benchmarks are early and small.
