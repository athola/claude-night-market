// A judge panel over architecture paradigms, because the choice is wide
// and one pass through it converges early.
//
// archetypes ships fifteen paradigm skills. Asked to pick one, a single
// session reads three or four and commits, and the paradigm it commits
// to correlates with reading order rather than with fit. This scores
// candidates independently and reports the runner-up with its score, so
// the decision is auditable and the second choice stays visible.
//
// The panel does not decide. It produces a ranked comparison against
// the requirements it was given; a human picks and records an ADR.

export const meta = {
  name: 'paradigm-panel',
  description:
    'Score candidate architecture paradigms independently against one requirement set and return a ranked comparison',
  whenToUse:
    'Run when an architecture decision is open and several paradigms are defensible. args.requirements states what the system must do; args.candidates names the paradigms to score, defaulting to a spread. Returns a ranking for a human to decide from.',
  phases: [
    { title: 'Score', detail: 'one judge per candidate paradigm' },
    { title: 'Compare', detail: 'rank, and name what the winner gives up' },
  ],
}

const input = args || {}
const requirements = input.requirements

if (!requirements) {
  log('paradigm-panel.js started with no requirements')
  return {
    started: false,
    reason: 'no-requirements',
    next: 'Pass args.requirements describing what the system must do. Scoring paradigms without them ranks fashion.',
  }
}

const DEFAULT_CANDIDATES = [
  'architecture-paradigm-domain-driven',
  'architecture-paradigm-event-driven',
  'architecture-paradigm-layered',
  'architecture-paradigm-client-server',
]

const candidates = input.candidates || DEFAULT_CANDIDATES

const SCORE = {
  type: 'object',
  required: ['paradigm', 'score', 'fits', 'costs'],
  properties: {
    paradigm: { type: 'string' },
    score: { type: 'number' },
    fits: { type: 'array', items: { type: 'string' } },
    costs: { type: 'array', items: { type: 'string' } },
    disqualifying: { type: 'string' },
  },
}

const scored = await parallel(
  candidates.map((paradigm) => () =>
    agent(
      `Read Skill(archetypes:${paradigm}) and score it against these requirements, on a 0-10 scale.\n\nRequirements:\n${requirements}\n\nScore the fit, not the paradigm's reputation. List what it fits and what it costs. If a requirement disqualifies it outright, say which one and score it 0. Do not compare it to other paradigms; you are scoring one.`,
      { label: `score:${paradigm}`, phase: 'Score', schema: SCORE },
    ),
  ),
)

const ranked = scored
  .filter(Boolean)
  .sort((left, right) => right.score - left.score)

if (!ranked.length) {
  return { started: true, ranked: [], comparison: null }
}

const summary = ranked
  .map((entry) => `${entry.paradigm}: ${entry.score} (costs: ${entry.costs.join('; ')})`)
  .join('\n')

const comparison = await agent(
  `These paradigms were scored independently against one requirement set. Write the comparison a human needs to decide.\n\n${summary}\n\nRequirements:\n${requirements}\n\nName what the top-scoring paradigm gives up that the runner-up keeps. If the top two are within a point, say the choice is not determined by these requirements and name the requirement that would break the tie.`,
  { label: 'compare', phase: 'Compare' },
)

log(`${ranked.length} paradigms scored, leader ${ranked[0].paradigm} at ${ranked[0].score}`)

return { ranked, comparison }
