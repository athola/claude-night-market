# Multi-Metric Evaluation Methodology

How to combine RICE, WSJF, Kano, and related models when
prioritizing a feature backlog. Each model encodes a
different assumption about what makes a feature worth
building. This module shows the formulas, where each model
fits, and how to combine them when no single model is
enough on its own.

## The Models at a Glance

| Model | Origin | Output | Captures |
|-------|--------|--------|----------|
| RICE | Intercom (Sean McBride, 2017) | Number | Reach * Impact * Confidence / Effort |
| WSJF | SAFe (Scaled Agile) | Number | (Value, Time, and Risk) / Effort |
| Kano | Noriaki Kano (1984) | Category | Basic, Performance, Delighter, Indifferent, Reverse |
| MoSCoW | DSDM Consortium (1994) | Bucket | Must, Should, Could, Won't |
| Cost-of-Delay | Don Reinertsen (2009) | $ / week | Value lost per week of delay |

Single-model use is rare in practice. Most teams converge
on a hybrid: RICE for a base score, WSJF to raise time-
critical items, Kano to gate basics. The rest of this
module explains why and how.

## Model 1: RICE

```
RICE = (Reach * Impact * Confidence) / Effort
```

| Factor | Unit | Typical scale |
|--------|------|---------------|
| Reach | users / period | absolute count |
| Impact | satisfaction delta | 0.25, 0.5, 1, 2, 3 |
| Confidence | probability | 0.5, 0.8, 1.0 |
| Effort | person-months | 0.5, 1, 2, 5, 10 |

**Best for**: large user-facing roadmaps where reach is
measurable and a single team can absorb most items.

**Worst for**: backlogs dominated by infrastructure or
compliance work where "reach" is meaningless or every item
shares similar reach.

**Worked example**:

```
Feature: Auto-save drafts
  Reach:      8,000 users / quarter
  Impact:     1.0 (significant satisfaction)
  Confidence: 0.8
  Effort:     2 person-months

RICE = (8000 * 1.0 * 0.8) / 2 = 3200
```

## Model 2: WSJF

Weighted Shortest Job First. From SAFe; treats
prioritization as a cost-of-delay optimization.

```
WSJF = Cost_of_Delay / Job_Size

Cost_of_Delay = User_Value + Time_Criticality + Risk_Reduction
Job_Size      = Effort estimate
```

Each input uses a Fibonacci scale: 1, 2, 3, 5, 8, 13, 20.

| Factor | Question |
|--------|----------|
| User_Value | How much does the user/business gain? |
| Time_Criticality | What does delay cost? Does the value decay? |
| Risk_Reduction | Does this open future options or de-risk? |
| Job_Size | How much work? |

**Best for**: backlogs with strong time pressure and many
items where deferral has measurable cost. Common in
SAFe-aligned organizations.

**Worst for**: small teams without explicit
cost-of-delay numbers; reduces to "gut feel times Fibonacci".

**Worked example**:

```
Feature: GDPR consent banner
  User_Value:        5
  Time_Criticality:  20  (regulatory deadline)
  Risk_Reduction:    13
  Job_Size:          3

WSJF = (5 + 20 + 13) / 3 = 12.67
```

Compare with the auto-save example: WSJF would put
auto-save at roughly (8 + 3 + 2) / 5 = 2.6, far below the
GDPR item, even though RICE might rank them similarly.
WSJF surfaces the deadline.

## Model 3: Kano

Kano classifies features by user reaction, not score.

| Class | If present | If absent |
|-------|-----------|-----------|
| Basic | Expected; no joy | Strong dissatisfaction |
| Performance | Linear satisfaction | Linear dissatisfaction |
| Delighter | Joy | No reaction |
| Indifferent | No reaction | No reaction |
| Reverse | Dissatisfaction | Satisfaction |

**Source**: Noriaki Kano et al., "Attractive Quality and
Must-Be Quality" (1984).

**Best for**: avoiding the most common backlog mistake:
shipping a Delighter while a Basic is still missing.

**Worst for**: numeric ranking. Kano gives categories, not
scores. Pair it with RICE or WSJF for the actual ordering.

**How to classify**: present users with two questions per
feature:

```
Functional:    "How would you feel if X were present?"
Dysfunctional: "How would you feel if X were absent?"
```

Each answered on a 5-point scale from "I like it" to "I
dislike it". The answer pair maps to a Kano category via a
fixed table (see Berger et al. 1993).

## When Each Model Fits

```
Backlog has clear users and reach measurable?
  Yes -> RICE base
  No  -> skip RICE

Items have time-critical deadlines or value decay?
  Yes -> WSJF overlay
  No  -> skip WSJF

Backlog mixes table-stakes and aspirational features?
  Yes -> Kano gate
  No  -> skip Kano

Stakeholders need narrative buckets, not numbers?
  Yes -> MoSCoW translation layer
  No  -> skip MoSCoW
```

| Backlog shape | First model | Second |
|---------------|-------------|--------|
| Consumer product, many features | RICE | Kano gate |
| Enterprise SaaS with deadlines | WSJF | RICE |
| New product, no users yet | Kano and MoSCoW | RICE later |
| Regulated domain | WSJF | Cost-of-Delay |
| Internal tooling | RICE with reach=team_size | Kano |

## The Hybrid Used in This Skill

The `feature-review` skill combines RICE-like value /
cost ratios, WSJF time criticality, and Kano gating. The
formula is documented in `modules/scoring-framework.md`:

```
Value = weighted_avg(Reach, Impact, Business_Value, Time_Criticality)
Cost  = weighted_avg(Effort, Risk, Complexity)
Score = (Value / Cost) * Confidence
```

Kano enters as a hard gate before scoring. Any feature
classified Basic that is absent today is bumped above the
ranked list. The Score then orders everything else.

```
1. Classify every feature with Kano.
2. Pull all missing Basics to the top, ordered by user impact.
3. Score the rest with the Value/Cost formula.
4. Rank by Score; apply confidence multiplier.
5. Sensitivity-check the top 10 with +/- 20% weight perturbation.
```

## Worked Example: Combining RICE, WSJF, and Kano

A team scores three candidates for the next sprint.

```text
Candidates:
  A: Auto-save drafts
  B: GDPR consent banner
  C: Dark mode

Step 1 (Kano):
  A: Performance  (more frequent saves = more value)
  B: Basic        (legally required; absent today)
  C: Delighter

Step 2: Pull Basics. B is bumped to top of queue.

Step 3: Score A and C with hybrid:
  A: Value=4.75, Cost=2.67, Conf=0.8 -> 1.42
  C: Value=2.25, Cost=2.00, Conf=0.9 -> 1.01

Step 4: WSJF check on B for sizing:
  WSJF(B) = (5 + 20 + 13) / 3 = 12.67
  Confirms B is the largest cost-of-delay item.

Step 5: Sprint order:
  1. B (regulatory Basic)
  2. A (Score 1.42)
  3. C (Score 1.01)

Sensitivity: vary all weights by +/- 20%. Order is stable
in 18 of 20 perturbations. Fragile case: if Time
Criticality weight drops below 0.10, A and C swap. Action:
keep weight at the documented 0.20.
```

## Anti-Patterns

**Single-model orthodoxy.** Picking RICE because the blog
post said so, then shoehorning every item into a "reach"
estimate that does not exist. If the model does not fit
the input, change the model.

**Hidden recalibration.** Reweighting Impact from 1.0 to
3.0 mid-quarter to make a favored project rank higher.
Track weight history in version control; flag mid-cycle
changes.

**Confidence rubber-stamping.** Every item scored at
Confidence 1.0. Confidence 1.0 means "I would bet the
quarter on this estimate". Real backlogs cluster around
0.5 to 0.8.

**Score inflation by Fibonacci jump.** "It feels like an 8"
when the difference between 5 and 8 should be a 60% larger
investment. Force a comparison: "Is this 60% bigger than
the last 5 we shipped?"

**Aggregating Kano with a number.** Kano is categorical.
Adding "Basic = 5, Performance = 3, Delighter = 1" to a
score creates the illusion of math.

**Ignoring the Pareto front.** When two items tie on
Score but trade off on different axes (one scales reach,
one buys time), report both and let humans pick. Do not
break ties with a third decimal place.

## Pitfalls Specific to AI/Plugin Backlogs

**Reach is a mirage.** Plugin reach is bounded by who
installs the plugin, not by the addressable market. Use
"installed teams" as the reach unit, not "potential users".

**Effort underestimates evals.** A new skill is not done
when the prose is written. Add the cost of subagent test
authoring to Effort or the score will overpromise.

**Confidence collapses on token-driven features.** New
context-window or prompt features cannot be confidently
estimated until measured against real workloads. Hold
Confidence at 0.5 until benchmarks land.

**Kano Basics drift.** A Delighter (auto-completion) can
become a Basic in two release cycles. Re-classify the
Basic set quarterly.

## Cross-Reference

See `modules/scoring-framework.md` for the per-factor
scales used in this skill,
`modules/tradeoff-dimensions.md` for the quality axes
applied after prioritization, and
`plugins/leyline/skills/evaluation-framework/modules/multi-metric-evaluation-methodology.md`
for the math behind aggregation rules.
