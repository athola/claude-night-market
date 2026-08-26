// One specification read four ways, because the defects that matter in a
// spec are not visible from a single reading.
//
// A spec can be internally consistent and still untestable. It can be
// testable and still miss the case that breaks it. It can cover every
// case and contradict a constitution rule three documents away. These
// are four different reads, and a single reviewer asked whether a spec
// is good does the first one and reports.
//
// The gap report at the end is the deliverable: not four reviews, but
// the list of things that have to be settled before the spec is ready
// for planning.

export const meta = {
  name: 'spec-review',
  description:
    'Read one specification through four independent lenses and report what must be settled before planning starts',
  whenToUse:
    'Run when a spec is drafted and before /speckit-plan. args.spec is the path; args.constitution points at the rules it must not contradict. Returns blocking gaps; it edits no spec.',
  phases: [
    { title: 'Lenses', detail: 'four independent readings' },
    { title: 'Gaps', detail: 'what blocks planning' },
  ],
}

const input = args || {}
const spec = input.spec

if (!spec) {
  log('spec-review.js started with no spec')
  return {
    started: false,
    reason: 'no-spec',
    next: 'Pass args.spec as the path to the specification to review.',
  }
}

const constitution = input.constitution || 'the project constitution, if one exists'

const FINDINGS = {
  type: 'object',
  required: ['lens', 'findings'],
  properties: {
    lens: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['requirement', 'problem'],
        properties: {
          requirement: { type: 'string' },
          problem: { type: 'string' },
          blocking: { type: 'boolean' },
        },
      },
    },
  },
}

const LENSES = [
  {
    key: 'testability',
    brief:
      'For each requirement, write the test that would prove it. Report every requirement where you cannot, and say what is missing: a threshold, an actor, an observable outcome.',
  },
  {
    key: 'consistency',
    brief:
      'Find requirements that contradict each other, and terms used with two meanings in different sections. A term defined nowhere and used as though defined is the same defect.',
  },
  {
    key: 'coverage',
    brief:
      'Find the cases the spec does not mention: the empty input, the concurrent caller, the partial failure, the actor without permission. Report the ones whose absence would change the design.',
  },
  {
    key: 'constitution',
    brief: `Read ${constitution} and report where this spec contradicts it. A contradiction the spec does not acknowledge is blocking; one it acknowledges with a reason is a decision to record.`,
  },
]

const read = await parallel(
  LENSES.map((lens) => () =>
    agent(
      `Read ${spec} through one lens only. ${lens.brief}\n\nMark a finding blocking when planning cannot honestly proceed without settling it. Stay inside your lens; three other readers have the rest.`,
      {
        label: `read:${lens.key}`,
        phase: 'Lenses',
        agentType: 'spec-kit:spec-analyzer',
        schema: FINDINGS,
      },
    ),
  ),
)

const reports = read.filter(Boolean)
const findings = reports.flatMap((report) =>
  (report.findings || []).map((finding) => ({ ...finding, lens: report.lens })),
)
const blocking = findings.filter((finding) => finding.blocking)

if (!findings.length) {
  log(`${spec}: no findings from ${reports.length} lenses`)
  return { spec, findings: [], blocking: [], gaps: null }
}

const digest = findings
  .map((finding) => `[${finding.lens}]${finding.blocking ? ' BLOCKING' : ''} ${finding.requirement}: ${finding.problem}`)
  .join('\n')

const gaps = await agent(
  `These findings came from four blind readings of ${spec}. Write what must be settled before planning starts.\n\n${digest}\n\nWhere two lenses found the same underlying gap, say it once. A requirement that is both untestable and uncovered is one gap about a requirement nobody has thought through. Order by what blocks the most downstream work, and state plainly if nothing blocks.`,
  { label: 'gaps', phase: 'Gaps' },
)

log(`${findings.length} findings on ${spec}, ${blocking.length} blocking`)

return { spec, findings, blocking, gaps }
