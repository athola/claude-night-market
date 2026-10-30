// Four specialists over the same Python, because "review this" returns
// whatever the reviewer happens to be good at.
//
// parseltongue ships four agents with genuinely different training:
// linting, typing, performance, testing. Asked as one question, a
// session answers with lint findings, because those are the ones you can
// see without running anything. Asked as four, the performance agent
// profiles and the testing agent reads coverage, and both produce
// findings the lint pass structurally cannot.

export const meta = {
  name: 'python-sweep',
  description:
    'Run the lint, type, performance and test specialists over the same Python in parallel and merge their findings',
  whenToUse:
    'Run before merging a substantial Python change, or when inheriting unfamiliar Python. args.paths lists what to review. args.lenses narrows the specialists. Returns merged findings. It edits nothing.',
  phases: [
    { title: 'Specialists', detail: 'four agents, four questions' },
    { title: 'Merge', detail: 'find where two specialists point at one cause' },
  ],
}

const input = args || {}
const paths = input.paths || []

if (!paths.length) {
  log('python-sweep.js started with no paths')
  return {
    started: false,
    reason: 'no-paths',
    next: 'Pass args.paths as the Python files or directories to review.',
  }
}

const target = paths.join(' ')

const FINDINGS = {
  type: 'object',
  required: ['lens', 'findings'],
  properties: {
    lens: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['location', 'problem'],
        properties: {
          location: { type: 'string' },
          problem: { type: 'string' },
          fix: { type: 'string' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
      },
    },
  },
}

const SPECIALISTS = [
  { key: 'lint', agentType: 'parseltongue:python-linter', brief: 'Run ruff and report what it finds, plus anything suppressed without a stated reason. A blanket suppression is a finding whatever the rule was.' },
  { key: 'types', agentType: 'parseltongue:python-pro', brief: 'Run mypy and report unsound typing. Look for Any where a type is knowable, ignores with no error code, and signatures that lie about their return.' },
  { key: 'performance', agentType: 'parseltongue:python-optimizer', brief: 'Profile or read for complexity. Report loops whose cost is superlinear in a quantity that grows, and repeated work that could be hoisted. State the measurement, or say it is a read rather than a measurement.' },
  { key: 'tests', agentType: 'parseltongue:python-tester', brief: 'Report branches with no test, and tests that would still pass if the behavior they name were broken. The second is the more valuable finding.' },
]

const KNOWN = SPECIALISTS.map((specialist) => specialist.key).join(', ')
const selection = input.lenses ?? null
// A string would pass `.includes` as a substring match, so only a list
// is a selection.
if (selection !== null && !Array.isArray(selection)) {
  return {
    started: false,
    reason: 'lenses-not-a-list',
    next: 'Pass args.lenses as a list of lens names. Omit it to run every lens.',
  }
}
const specialists = selection
  ? SPECIALISTS.filter((specialist) => selection.includes(specialist.key))
  : SPECIALISTS
// A misspelled lens must not read as a clean review.
const unknown = (selection || []).filter((name) => !SPECIALISTS.some((s) => s.key === name))
if (unknown.length) log(`unknown lens ${unknown.join(', ')}. Known lenses: ${KNOWN}`)
if (!specialists.length) {
  return {
    started: false,
    reason: 'no-lenses-selected',
    next: `Name one or more known lenses in args.lenses: ${KNOWN}. Omit it to run every lens.`,
    unknown,
  }
}

const swept = await parallel(
  specialists.map((specialist) => () =>
    agent(
      `Review ${target} on one dimension only. ${specialist.brief}\n\nStay inside your dimension. The other three are covered. Report only what you can point at with a file and a line.`,
      {
        label: `sweep:${specialist.key}`,
        phase: 'Specialists',
        agentType: specialist.agentType,
        schema: FINDINGS,
      },
    ),
  ),
)

// A specialist that returned nothing left its lens unreviewed. A
// dropped tests lens would otherwise read as full coverage.
const missing = specialists.filter((specialist, index) => !swept[index]).map((s) => s.key)
// The lens comes from the roster, not from the agent's own report, so
// reviewed and missing share one vocabulary.
const reports = swept
  .map((report, index) => report && { ...report, lens: specialists[index].key })
  .filter(Boolean)
const findings = reports.flatMap((report) =>
  (report.findings || []).map((finding) => ({ ...finding, lens: report.lens })),
)
const coverage = { reviewed: reports.map((report) => report.lens), missing }

if (missing.length) log(`no report from ${missing.join(', ')}. Those lenses are unreviewed, not clean`)

if (findings.length < 2) {
  log(`${findings.length} findings. Nothing to merge`)
  return { paths, findings, merged: null, coverage }
}

const digest = findings
  .map((finding) => `[${finding.lens}] ${finding.location}: ${finding.problem}`)
  .join('\n')

const merged = await agent(
  `These findings came from four specialists that could not see each other. Merge them.\n\n${digest}\n\nWhere two specialists point at the same location, decide whether they found one cause or two, and say which. A function that is both untested and superlinear is one finding about a function nobody has exercised, not two. Rank by what a maintainer should fix first.`,
  { label: 'merge', phase: 'Merge' },
)
// A dead merge agent returns the same null as the skip path above.
const failed = merged ? null : 'merge'
if (failed) log('no result from the merge stage. The findings are unmerged, not merged clean')

log(`${findings.length} findings from ${reports.length} specialists over ${paths.length} paths`)

return { paths, findings, merged, coverage, failed }
