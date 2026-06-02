# Research Basis: Assisted Mastery and the Verification Spine

The evidence base behind this skill and its sibling
`imbue:graduated-implementation`. The SKILL.md Overview summarizes the
load-bearing findings; this module preserves the full tables,
cross-domain mechanism, and citations for auditing the claims. It also
records the six workflow principles this research recommended, four of
which this skill and its siblings now implement.

## Thesis

The problem with AI-generated code is not the tool: it is blind trust
of the tool's output. Experienced developers catch the flaws (bad
architecture, hallucinated APIs, over-abstraction, outdated syntax);
novices cannot, because you cannot verify what you do not understand.
The historical fix for the analogous problem (novices copy-pasting
from Stack Overflow) was not to ban the source: it was to force
learners through implementation, trial-and-error, and explicit
tradeoff reasoning until they understood the ramifications of design
decisions. The design question for any coding-agent workflow is
therefore: does it force understanding and verification, or does it
enable blind acceptance?

## Thread A: the flaws are real and measured

| Claim | Evidence | Number |
|-------|----------|--------|
| APIs/packages hallucinated | Spracklen 2024, 576k samples | 5.2% (commercial) to 21.7% (open) of packages do not exist |
| Hallucinations are predictable attack targets | Socket / Lasso | 58% recur across reruns; `huggingface-cli` PoC drew 30k+ downloads |
| Better benchmarks do not fix it | Krishna 2025 | hallucination rate inversely correlated with HumanEval score |
| AI code is less secure, felt more secure | Perry 2023 (Stanford RCT) | assisted users wrote less secure code yet believed it more secure |
| Self-refinement makes it worse | Shukla 2025 | +37.6% critical vulnerabilities after 5 refine rounds |
| Speedup is partly illusory | METR 2025 (RCT, 16 experienced devs) | 19% slower with AI; believed they were 20% faster |
| Quality pressure at scale | GitClear 2024, 153M lines | churn projected to double vs pre-AI baseline; reuse falling |
| Offloading erodes thinking | Gerlich 2025, n=666 | cognitive offloading vs critical thinking r = -0.75 |

The expert-vs-novice gap is itself documented. A study of LLM-assisted
debugging (arXiv 2505.08063) found novices fall into "rabbitholes of
over-reliance" because they cannot verify output they do not
understand. Simon Willison's position is the same from the other side:
LLMs amplify existing expertise, because experts can spec precisely
and judge viability. The contrarian view (Ptacek, "My AI Skeptic
Friends Are All Nuts") argues skepticism is often craft gatekeeping:
included for tension, but the controlled studies (Perry, METR) weigh
against the strong form of it.

## Thread B: how expertise is actually built

The learning-science literature explains why blind acceptance fails to
build skill, and what does:

- **Productive failure** (Kapur 2008; meta-analysis Sinha & Kapur
  2019): struggling with a problem before instruction produces deeper
  understanding and transfer than being handed the answer.
- **Deliberate practice** (Ericsson 1993): expertise comes from
  effortful practice at the edge of ability with feedback, not from
  exposure to finished solutions.
- **Desirable difficulties** (Bjork 1994, 2011): conditions that slow
  apparent performance (reduced feedback, effortful retrieval) improve
  long-term retention.
- **Cognitive Load Theory and the expertise reversal effect** (Sweller
  & Cooper 1985; Kalyuga 2003): scaffolding that helps a novice
  actively harms an expert. Support must **fade** as competence grows.
  This is the assistance dilemma.
- **Google effect** (Sparrow 2011): when a tool will hold the answer,
  we remember where to find it rather than the content itself.

An agent that always produces the finished diff is maximally helpful
to throughput and maximally harmful to skill: it is permanent
scaffolding that never fades, and it offloads exactly the reasoning
that builds judgment.

## Thread C (TRIZ): the convergent cross-domain mechanism

The contradiction: more tool autonomy and output volume (speed)
degrades human understanding, verification, and retained skill
(quality). Five high-stakes domains converged independently on the
same three-part resolution:

1. **Insert an intermediary verification step before the irreversible
   effect.** Aviation pre-flight, WHO surgical checklist
   (complications down up to 40%), nuclear STAR, finance four-eyes.
   The aid never directly causes the consequential outcome without a
   gate.
2. **Force the reasoning and state to be spoken aloud and closed
   back.** Surgical read-back, nuclear three-way communication,
   aviation mode call-outs, cognitive-apprenticeship visible thinking.
   Tacit belief becomes a challengeable statement.
3. **Make autonomy graduated and reversible, with a pre-licensed
   trigger to downgrade it.** Aviation automation tiers and "children
   of the magenta," apprenticeship fading, the two-challenge takeover
   rule.

The single strongest rule, from automation-bias research (medicine:
correct decision support cut errors ~40%, but incorrect support raised
them ~25-33% and reduced independent verification): the agent must
never be the sole verifier of its own high-stakes output, and
verification effort must be designed to rise, not fall, exactly when
the agent is most confident.

## Thread D (code): mechanisms already built in the wild

| Project | Mechanism | Maps to |
|---------|-----------|---------|
| nizos/tdd-guard | hook blocks impl without a failing test | Iron Law / intermediary gate |
| obra/superpowers | TDD + verification-before-completion skills | proof-of-work |
| zl190/agent-gates | 5 gates (spec, diagnosis, test, QC, evidence) | layered verification |
| brennhill/sloppy-joe | dependency firewall: blocks hallucinated/typosquatted packages | package-hallucination defense |
| rsionnach/sloppylint | AST lint for hallucinated imports + over-abstraction | over-abstraction guard |
| cs-wangchong/LLM-Deprecated-API | detects deprecated APIs, 145 mappings | outdated-syntax detection |
| github/spec-kit | spec-first, tests must fail before code | think-first + Iron Law |
| npryce/adr-tools | architecture decision records | decision journal |
| andrewvaughan/agent-council | multi-persona vote with recorded tradeoffs | war-room |

## What this means for night-market

This codebase already implements most of the verification spine:
`imbue:proof-of-work` (STAR/evidence), `imbue:scope-guard`
(over-abstraction), `imbue:rigorous-reasoning` (anti-sycophancy),
`imbue:karpathy-principles` (think-first),
`leyline:decision-journal` (ADRs), `attune:war-room` (council), and
the two-challenge rule in the global CLAUDE.md.

The gaps this research exposed, now closed on this branch:

1. **The assistance dilemma** (this skill, `imbue:assisted-mastery`):
   visible reasoning, explain/produce modes, and fading scaffolding.
2. **Active package-hallucination defense**
   (`imbue:dependency-verification` plus the
   `guard_package_hallucination.py` hook).
3. **Graduated autonomy** (`imbue:graduated-implementation` plus the
   `guard_scope_ramp.py` hook, and the
   `leyline:risk-classification` automation-tiers module).
4. **Independent verification for high-stakes changes**
   (`imbue:proof-of-work` independent-verification module: the
   producing agent may not be its own sole verifier).

## The six recommended principles

1. Verification effort must rise with agent confidence and blast
   radius, not fall.
2. For high-stakes changes, the producing agent may not be the sole
   verifier.
3. The agent's reasoning (assumptions, alternatives, why rejected)
   must be visible and sized to blast radius, not hidden behind a
   finished diff.
4. Assistance should be choosable and fade-able: an explain mode that
   builds the human's judgment, distinct from a produce mode for
   throughput.
5. Any suggested dependency must be proven to exist before it is
   recommended or installed.
6. Tradeoffs must be surfaced before a design is chosen, not
   reconstructed after.

## Provenance

Originally captured as research session 19c28f3c (2026-06-01;
channels: code, discourse, academic, triz). Session 3dfdba53 (see
`graduated-implementation` `modules/research-basis.md`) extended it
with the graduated-practice advancement criterion.

## Sources

Full citations are embedded inline above. Primary controlled studies:
Perry et al. 2023 (arXiv 2211.03622), METR 2025 (arXiv 2507.09089),
Spracklen et al. 2024 (arXiv 2406.10279). Pedagogy: Kapur 2008,
Ericsson et al. 1993, Bjork & Bjork 2011, Sweller & Cooper 1985,
Kalyuga et al. 2003, Sparrow et al. 2011. Cross-domain: WHO Surgical
Safety Checklist, NRC human-performance tools (STAR), CRM
two-challenge rule, four-eyes principle.
