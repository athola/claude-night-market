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
    'Run before merging a substantial Python change, or when inheriting unfamiliar Python. args.paths lists what to review; args.lenses narrows the specialists. Returns merged findings; it edits nothing.',
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
  { key: 'types', agentType: 'parseltongue:python-pro', brief: 'Run mypy and report unsound typing: Any where a type is knowable, ignores with no error code, and signatures that lie about what they return.' },
  { key: 'performance', agentType: 'parseltongue:python-optimizer', brief: 'Profile or read for complexity. Report loops whose cost is superlinear in a quantity that grows, and repeated work that could be hoisted. State the measurement, or say it is a read rather than a measurement.' },
  { key: 'tests', agentType: 'parseltongue:python-tester', brief: 'Report branches with no test, and tests that would still pass if the behavior they name were broken. The second is the more valuable finding.' },
]

const specialists = input.lenses
  ? SPECIALISTS.filter((specialist) => input.lenses.includes(specialist.key))
  : SPECIALISTS

const swept = await parallel(
  specialists.map((specialist) => () =>
    agent(
      `Review ${target} on one dimension only. ${specialist.brief}\n\nStay inside your dimension; the other three are covered. Report only what you can point at with a file and a line.`,
      {
        label: `sweep:${specialist.key}`,
        phase: 'Specialists',
        agentType: specialist.agentType,
        schema: FINDINGS,
      },
    ),
  ),
)

const reports = swept.filter(Boolean)
const findings = reports.flatMap((report) =>
  (report.findings || []).map((finding) => ({ ...finding, lens: report.lens })),
)

if (findings.length < 2) {
  log(`${findings.length} findings; nothing to merge`)
  return { paths, findings, merged: null }
}

const digest = findings
  .map((finding) => `[${finding.lens}] ${finding.location}: ${finding.problem}`)
  .join('\n')

const merged = await agent(
  `These findings came from four specialists that could not see each other. Merge them.\n\n${digest}\n\nWhere two specialists point at the same location, decide whether they found one cause or two, and say which. A function that is both untested and superlinear is one finding about a function nobody has exercised, not two. Rank by what a maintainer should fix first.`,
  { label: 'merge', phase: 'Merge' },
)

log(`${findings.length} findings from ${reports.length} specialists over ${paths.length} paths`)

return { paths, findings, merged }
