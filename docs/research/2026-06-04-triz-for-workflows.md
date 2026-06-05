# TRIZ for Software Workflows: Research Synthesis

Source list investigated: `heshenxian1/awesome-triz`. Channels run:
academic literature, practitioner discourse, GitHub code/data.

## Thesis

The value of TRIZ for our workflows is not the full apparatus. It is
two lightweight, domain-portable ideas (the 40 Inventive Principles as
a brainstorming checklist, and Ideality/IFR as a framing heuristic).
The contradiction matrix, ARIZ, and Substance-Field analysis carry the
most overhead and the most documented criticism, so importing them
wholesale would add complexity in exchange for the weakest parts of the
method.

## What awesome-triz actually contains

It is a curated link list (67 stars, last updated 2019), not code or
data. Its 25 links resolve to canonical resources: the TRIZ Body of
Knowledge, the TRIZ Journal case archive, the Altshuller foundation,
ETRIA, a scientific-effects database, and a tri-lingual glossary. The
substance is the methodology those links point to, not the list.

## Canonical tool structure (verified)

Primary source: the MATRIZ TRIZ Body of Knowledge (2012), read
directly. Corroborated by IIT Bombay course material and the TRIZ
Journal.

- **40 Inventive Principles**: exactly 40, numbered. The BoK adds 10
  further principles in section 5.1.2. Our `triz.py` list matches the
  canonical names.
- **Contradiction Matrix**: a 39x39 table, same 39 engineering
  parameters on both axes. Rows = parameter to improve; columns =
  parameter that worsens. Asymmetric. Each non-empty cell holds 1 to 4
  principle numbers. Many cells are empty.
- **Separation Principles** (for physical contradictions): four
  canonical forms, separation in time, in space, on condition, and
  between part and whole. Low overhead, only four.
- **ARIZ-85C**: a roughly nine-step algorithm (formulate problem, build
  Su-Field model, formulate IFR, list resources, search analogues,
  resolve the contradiction, generate concepts, apply resources, verify
  no new drawbacks).
- **Su-Field analysis and 76 Standard Solutions**: grouped into five
  classes (13, 23, 6, 17, 17 = 76).
- **Laws of Technical System Evolution**: including increasing
  ideality, transition to super-systems, increasing dynamism, and
  transition from macro- to micro-levels.
- **Ideality / Ideal Final Result**: the ideal system performs the
  function without itself existing; ideality is useful functions over
  harmful functions plus cost.

**Scope caveat (load-bearing):** the BoK explicitly limits canonical
TRIZ to technological systems and states that non-technological
applications are not yet codified. Every software, process, and
management application below is a non-canonical reinterpretation, not
part of the official method.

## Documented software applications

A real lineage exists. Rea (TRIZ Journal, 2001) mapped the 40
principles to software analogs, leaving six unmapped because they are
material-specific. Fulbright (2004) completed the remaining six. Mann
(2004) developed software-specific parameter interpretations. The
mapping is a 1:1 re-skinning, for example Segmentation to
modularization, Dynamics to runtime configurability, Preliminary action
to precomputation and caching. A 2011 Procedia paper and a 2019 MDPI
paper apply the matrix to software-architecture quality trade-offs
(performance vs maintainability and similar). Practitioner advocacy
(Big Agile) maps contradictions to sprint problem-solving and
retrospectives, but reports no measured outcomes.

## Critiques (the cargo-cult to avoid)

- The matrix is frozen since 1985 and the empty-box problem collapses
  its selectivity. Advocates concede it is hard to map real problems
  onto the 39 parameters.
- Retrofitting: TRIZ literature tends to back-explain existing patents
  rather than demonstrate forward inventive power (Cavallucci, "Why
  TRIZ Popularity is Declining").
- Weak empirical and scientific validation outside the patent corpus
  it was derived from.
- Ideality is subjective; useful-over-harmful is judgment-dependent.
- Hacker News consensus: useful as a "stuck? try these" checklist;
  dismissed as "painting by numbers for engineers" when taken as
  doctrine.

Best value-to-overhead idea by cross-source consensus: the 40
Principles used as a checklist, plus Ideality as a framing question.

## Reusable data and prior art (GitHub)

- `NickScherbakov/Heinrich-The-Inventing-Machine` (Apache-2.0): ships
  `39_parameters.yaml`, `40_principles.yaml`, `contradiction_matrix.csv`
  (sparse, 161 populated cells), `effects_database.json`. The only
  confirmed vendorable data source. Matrix is sparse, verify coverage
  before treating as canonical.
- `smixs/creative-director-skill` (64 stars, MIT, active): an LLM agent
  skill bundling TRIZ, SCAMPER, Synectics, and other ideation methods as
  modules. Closest analogue to our `tome:triz` skill.
- `shuojiangcn/AutoTRIZ-Repository`: LLM-driven full TRIZ reasoning loop
  with a Markdown case base.
- The software 40-principle mapping (Rea/Fulbright/Mann) exists only in
  papers and one blog. No GitHub artifact. If we want it, we author it.

## Implications for our workflows

1. `tome:triz` advertises "Full matrix" and "full TRIZ" at deeper
   depths but implements a six-entry hand-authored catalog. Close
   that gap honestly.
2. The most-praised idea, Ideality/IFR, is buried as a template string
   inside contradiction formulation. Promote it to a first-class step.
3. The four separation principles are cheap and missing; they fit
   physical contradictions (mutually exclusive requirements on one
   parameter).
4. The cross-domain field-bridging in our skill is its strongest,
   most tome-aligned idea. Strengthen it rather than burying it under
   matrix machinery.
5. Resist vendoring the full matrix as the headline feature. If we add
   it at all, add it as an optional grounding lookup with an explicit
   note on the empty-box and frozen-1985 limitations.

## Sources

- MATRIZ TRIZ Body of Knowledge (2012):
  https://matriz.org/wp-content/uploads/2012/07/TRIZ-Body-of-Knowledge-final.pdf
- MATRIZ contradiction-matrix reference:
  https://wiki.matriz.org/docs/triz/problem-solving-tools-5890/contradictions/engineering-contradiction-5995/contradiction-matrix-6026/
- 76 Standard Solutions (TRIZ Journal):
  https://the-trizjournal.com/seventy-six-standard-solutions-relate-40-principles-inventive-problem-solving/
- TRIZ for Software, inventive principles (TRIZ Journal):
  https://the-trizjournal.com/triz-software-using-inventive-principles/
- TRIZ for software architecture (Procedia, 2011):
  https://www.sciencedirect.com/science/article/pii/S1877705811001767
- TRIZ for Digital Systems Engineering (MDPI Systems, 2019):
  https://www.mdpi.com/2079-8954/7/3/39
- AutoTRIZ (arXiv 2403.13002, 2024):
  https://arxiv.org/abs/2403.13002
- Semantic TRIZ systematic review (PMC):
  https://pmc.ncbi.nlm.nih.gov/articles/PMC10788813/
- Why TRIZ Popularity is Declining (Cavallucci et al.):
  https://www.researchgate.net/publication/316940926_Why_TRIZ_Popularity_is_Declining
- TRIZ matrix criticism (TRIZ Consulting Group):
  https://www.triz-consulting.de/about-triz/triz-matrix/?lang=en
- Heinrich data source (Apache-2.0):
  https://github.com/NickScherbakov/Heinrich-The-Inventing-Machine
- creative-director-skill (LLM ideation modules):
  https://github.com/smixs/creative-director-skill
