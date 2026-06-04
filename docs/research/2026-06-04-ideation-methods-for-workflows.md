# Ideation Methods Beyond TRIZ: Research Synthesis

Source investigated: `smixs/creative-director-skill` (MIT, ~64
stars) and the ideation concepts it bundles. Channels run: academic
literature, practitioner discourse, GitHub code and prior art.

## Thesis

The value of `creative-director-skill` for our workflows is not its
20-method catalog. Most named ideation methods have weak individual
evidence, so importing them wholesale is cargo-cult. The value is
three meta-ideas, two of which are backed by strong recent evidence:

1. Select a few methods from different categories rather than one, and
   rotate them across passes. This is the lever against LLM mode
   collapse, which is well documented.
2. Structure the reasoning, not the output. Reasoning scaffolds raise
   diversity; rigid output schemas collapse it.
3. Cap originality against a canon and score with calibration anchors,
   so "novel" and "good" are measured, not asserted.

The methods themselves are a supporting cast: keep the few that port
to technical problem-solving (SCAMPER, SIT subtraction and task
unification, morphological analysis, inversion, cross-domain analogy,
which TRIZ already covers) and skip the rest.

## What the repo actually is

A structured advertising-creative skill: a five-phase cycle (intake,
insight, ideation, evaluate and refine, articulate) over 20+ methods
routed by a `method-selection-matrix.md`, scored against six weighted
criteria, and capped for originality against 571 campaign cards
(1950 to 2025) carrying YAML frontmatter. The implementation is
mostly markdown plus data with three small Python maintenance
scripts. Enforcement of the good parts (rotation, originality cap,
anti-inflation scoring) is prompt-only. That is the gap: nobody moves
these into testable code.

## Evidence base, by method

Grades are conservative. The split is wide.

- **Morphological analysis (Zwicky)**: mixed-to-strong, applied. Long
  engineering-design and policy track record (Ritchey). Ports
  strongly to software: parameterized enumeration of a solution
  space. Risk: combinatorial explosion.
- **Systematic Inventive Thinking (SIT) / templates**: mixed-to-
  strong, but the strong evidence is advertising and CPG domain
  (Goldenberg, Mazursky, Solomon, 1999, in Marketing Science, JMR,
  and Science). Subtraction and task unification port to software
  cleanly; attribute dependency maps to adaptive behavior.
- **SCAMPER**: weak-to-mixed. Small-N education studies measuring
  fluency proxies, not shipped quality. The most directly portable
  checklist for LLM use even so.
- **Six Thinking Hats**: weak. Maps to multi-persona prompting, which
  borrows credibility from the LLM persona literature rather than its
  own.
- **Synectics**: weak evidence, but its analogy mechanism is what
  LLMs do well (cross-domain transfer).
- **Reverse brainstorming / provocation (PO)**: anecdotal. Inversion
  still maps usefully to pre-mortems and threat modeling.
- **Bisociation (Koestler)**: anecdotal as a method, influential as
  theory, with a real computational-creativity research lineage.
- **Oblique Strategies (Eno)**: purely anecdotal. A random-restart
  nudge with no measurement.

Cross-cutting caveat: the brainstorming meta-analyses (Diehl and
Stroebe; Mullen et al.) find nominal groups (individuals generating
alone, then pooling) beat interactive groups. Evaluate every method
as an individual scaffold, not a group ritual.

## The LLM diversity evidence (the real prize)

This literature is strong and recent, and it is what makes the
meta-patterns worth implementing.

- Mode collapse and homogenization are documented. "Echoes in AI"
  (PNAS, 2025) shows LLM outputs are measurably less diverse than
  human corpora. Doshi and Hauser show LLM idea access makes
  individual outputs more creative yet the corpus more homogeneous, a
  tragedy of the commons for collective creativity.
- Lightweight interventions restore diversity: verbalized sampling
  (arXiv 2510.01171, 1.6 to 2.1x diversity gains, training-free),
  diverse personas, and chain-of-thought (arXiv 2602.20408 shows CoT
  reduces fixation and personas restore collective diversity).
- The sharp nuance: "The Price of Format" (arXiv 2505.18949) finds
  rigid output templates induce semantic similarity; minimal output
  formatting maximizes diversity. So a SCAMPER or hats reasoning
  scaffold can help, but forcing a rigid output schema can collapse
  the very diversity the method was meant to create.

## Practitioner consensus (value-to-overhead)

Honest discourse is thinner and more skeptical than vendor copy.
Ranked for a "stuck, try these" checklist:

1. Individual-first generation, then pool (brainwriting). Strongest
   evidence, near-zero overhead.
2. Reverse the question. Cheap five-to-fifteen-minute unblocker.
3. Constraint provocation ("solve it with 10x less time"). High
   ceiling, needs an attentive facilitator.
4. Oblique Strategies, domain-adapted. Good for naming and design
   vibe-checks, useless for pure debugging per programmer reports.
5. SCAMPER. Low-risk generic checklist, unverified by first-hand
   engineering accounts.
6. Six Thinking Hats. Reserve for facilitated group reviews.
7. SIT and morphological analysis. Insufficient discourse; treat as
   experimental despite the better academic base.

For LLM work: ask for N explicitly distinct approaches, rotate
personas, raise temperature, then try verbalized sampling if outputs
still collapse and diversity is worth the token cost.

## Prior art and licensing

- `smixs/creative-director-skill` (MIT): the only prior art with all
  four meta-patterns (routing, rotation, originality cap, anti-
  inflation scoring), but prompt-enforced. Vendor the schema and
  rubric structure with attribution; do not vendor the 571 ad cards
  (domain mismatch).
- de Bono auto-router in `human-avatar/skills-for-humanity` (MIT,
  147 stars): a describe-then-route interaction pattern.
- Oblique Strategies decks: `jakedahn/oblique-skill` (MIT) is a safe
  data pull; `joelparkerhenderson/oblique-strategies` has an
  unspecified license, so verify before vendoring.
- `JohannesBuchner/zwicky-morphological-analysis` is GPL-3.0:
  re-implement the algorithm, do not vendor the code into a
  permissive plugin.

## Implications for our workflows

1. We have one ideation method (`tome:triz`, cross-domain analogy).
   The cheap, high-value addition is a small catalog of methods
   that port to technical work, with a selector that picks across
   categories and rotates to avoid repetition. TRIZ becomes one entry
   in that catalog, not the whole offering.
2. Code-backed rotation and category-diverse selection are the gap no
   prior art fills (all are prompt-only). This is where a tested
   implementation earns its place and serves our recurring
   anti-mode-collapse goal.
3. Make "structure the reasoning, not the output" a first-class design
   rule. The selector should hand the agent diverse reasoning prompts,
   not a rigid output schema, per "The Price of Format".
4. Resist porting Six Hats, Oblique Strategies, and bisociation as
   headline features. Their individual evidence is anecdotal; include
   only the ones that port and earn it, and label evidence honestly.
5. Originality capping against a canon is powerful but needs a
   tome-relevant corpus, which we do not have. Defer it; do not
   vendor an advertising canon to fake it.

## Sources

LLM diversity (primary):

- Verbalized Sampling: https://arxiv.org/abs/2510.01171
- The Price of Format: https://arxiv.org/abs/2505.18949
- Barriers to Diversity in LLM-Generated Ideas:
  https://arxiv.org/abs/2602.20408
- Echoes in AI (PNAS, 2025):
  https://www.pnas.org/doi/10.1073/pnas.2504966122
- Diverse AI Personas Mitigate Homogenization:
  https://arxiv.org/abs/2504.13868

Ideation methods:

- Goldenberg et al., Inventive Templates of New Products (JMR, 1999):
  https://journals.sagepub.com/doi/abs/10.1177/002224379903600205
- Goldenberg et al., Fundamental Templates of Quality Ads (Marketing
  Science, 1999): https://pubsonline.informs.org/doi/10.1287/mksc.18.3.333
- Boonpracha, SCAMPER for product design (2023):
  https://www.sciencedirect.com/science/article/abs/pii/S1871187123000524
- Ritchey, Applications of General Morphological Analysis:
  https://www.swemorph.com/pdf/gma.pdf
- Diehl and Stroebe, Productivity Loss in Brainstorming Groups:
  https://homepages.se.edu/cvonbergen/files/2013/01/Productivity-Loss-In-Brainstorming_Toward-the-Solution-of-a-Riddle.pdf

Prior art:

- creative-director-skill: https://github.com/smixs/creative-director-skill
- skills-for-humanity: https://github.com/human-avatar/skills-for-humanity
- oblique-skill: https://github.com/jakedahn/oblique-skill
- zwicky-morphological-analysis (GPL-3.0):
  https://github.com/JohannesBuchner/zwicky-morphological-analysis
