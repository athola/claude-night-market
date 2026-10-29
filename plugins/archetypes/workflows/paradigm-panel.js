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
    'Run when an architecture decision is open and several paradigms are defensible. args.requirements states what the system must do. args.candidates names the paradigms to score, defaulting to a spread. Returns a ranking for a human to decide from.',
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

// Short names of the paradigm skills on disk, each read as
// Skill(archetypes:architecture-paradigm-<name>). A test compares the two.
const PREFIX = 'architecture-paradigm-'
const PARADIGMS = [
  'client-server',
  'cqrs-es',
  'domain-driven',
  'event-driven',
  'functional-core',
  'hexagonal',
  'layered',
  'microkernel',
  'microservices',
  'modular-monolith',
  'pipeline',
  'serverless',
  'service-based',
  'space-based',
]
const DEFAULT_CANDIDATES = ['domain-driven', 'event-driven', 'layered', 'client-server']

const KNOWN = PARADIGMS.join(', ')
const selection = input.candidates ?? null
if (selection !== null && !Array.isArray(selection)) {
  return {
    started: false,
    reason: 'candidates-not-a-list',
    next: 'Pass args.candidates as a list of paradigm names. Omit it to score the default spread.',
  }
}
// The skill name and the short name both select a paradigm.
const named = (selection || DEFAULT_CANDIDATES).map((name) => {
  const text = String(name)
  return text.startsWith(PREFIX) ? text.slice(PREFIX.length) : text
})
const candidates = named.filter((name) => PARADIGMS.includes(name))
const unknown = named.filter((name) => !PARADIGMS.includes(name))
if (unknown.length) log(`unknown paradigm ${unknown.join(', ')}. Known paradigms: ${KNOWN}`)
if (!candidates.length) {
  return {
    started: false,
    reason: 'no-candidates-selected',
    next: `Name one or more known paradigms in args.candidates: ${KNOWN}. Omit it to score the default spread.`,
    unknown,
  }
}

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
      `Read Skill(archetypes:${PREFIX}${paradigm}) and score it against these requirements, on a 0-10 scale.\n\nRequirements:\n${requirements}\n\nScore the fit, not the paradigm's reputation. List what it fits and what it costs. If a requirement disqualifies it outright, say which one and score it 0. Do not compare it to other paradigms. You are scoring one.`,
      { label: `score:${paradigm}`, phase: 'Score', schema: SCORE },
    ),
  ),
)

// A paradigm whose scorer returned nothing was not scored; leaving it
// out of the ranking silently would read as "it lost".
const unscored = candidates.filter((paradigm, index) => !scored[index])
// The paradigm comes from the roster, not from the agent's own report.
const ranked = scored
  .map((score, index) => score && { ...score, paradigm: candidates[index] })
  .filter(Boolean)
  .sort((left, right) => right.score - left.score)

if (unscored.length) log(`no score for ${unscored.join(', ')}. They are unscored, not last`)

if (!ranked.length) {
  return { started: true, ranked: [], comparison: null, unscored, failed: 'score' }
}

const summary = ranked
  .map((entry) => `${entry.paradigm}: ${entry.score} (costs: ${entry.costs.join('; ')})`)
  .join('\n')

const comparison = await agent(
  `These paradigms were scored independently against one requirement set. Write the comparison a human needs to decide.\n\n${summary}\n\nRequirements:\n${requirements}\n\nName what the top-scoring paradigm gives up that the runner-up keeps. If the top two are within a point, say these requirements do not determine the choice. Name the requirement that would break the tie.`,
  { label: 'compare', phase: 'Compare' },
)
// A dead compare agent must not read as a run with nothing to compare.
const failed = comparison ? null : 'compare'
if (failed) log('no result from the compare stage. The ranking has no written comparison')

log(`${ranked.length} paradigms scored, leader ${ranked[0].paradigm} at ${ranked[0].score}`)

return { ranked, comparison, unscored, failed }
