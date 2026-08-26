// Health of several initiatives at once, because the API calls dominate
// and they are independent.
//
// A pulse over one milestone is mostly waiting on GitHub. Over six it is
// six times the waiting, done in sequence, for a report nobody reads
// until all six are in. The fan-out turns the wall clock into the
// slowest single milestone, and the roll-up at the end is what a
// programme lead actually asked for: not six reports, but the one
// sentence about which initiative is in trouble.

export const meta = {
  name: 'initiative-pulse',
  description:
    'Gather delivery health for several GitHub milestones in parallel and roll them up into one programme view',
  whenToUse:
    'Run for a programme review across more than one milestone. args.milestones lists them; args.repo overrides the current repository. Returns per-milestone health plus the roll-up; it changes no issue.',
  phases: [
    { title: 'Pulse', detail: 'one agent per milestone' },
    { title: 'Roll-up', detail: 'name the initiative in trouble' },
  ],
}

const input = args || {}
const milestones = input.milestones || []

if (!milestones.length) {
  log('initiative-pulse.js started with no milestones')
  return {
    started: false,
    reason: 'no-milestones',
    next: 'Pass args.milestones as a list of milestone names or numbers.',
  }
}

const repo = input.repo || 'the current repository'

const PULSE = {
  type: 'object',
  required: ['milestone', 'openIssues', 'closedIssues', 'risk'],
  properties: {
    milestone: { type: 'string' },
    openIssues: { type: 'number' },
    closedIssues: { type: 'number' },
    risk: { type: 'string', enum: ['on-track', 'at-risk', 'blocked'] },
    blockers: { type: 'array', items: { type: 'string' } },
    staleIssues: { type: 'array', items: { type: 'string' } },
  },
}

const pulsed = await parallel(
  milestones.map((milestone) => () =>
    agent(
      `Gather delivery health for milestone '${milestone}' in ${repo}, following Skill(minister:github-initiative-pulse).\n\nUse the gh CLI. Report open and closed counts, issues with no activity for over two weeks, and anything explicitly blocked. Classify risk from what you found, not from the count alone: a milestone with two open issues that are both blocked is worse than one with twenty that are moving.`,
      { label: `pulse:${milestone}`, phase: 'Pulse', schema: PULSE },
    ),
  ),
)

const pulses = pulsed.filter(Boolean)

if (!pulses.length) {
  log('no milestone returned a pulse')
  return { repo, pulses: [], rollUp: null }
}

const digest = pulses
  .map((pulse) => `${pulse.milestone}: ${pulse.risk}, ${pulse.openIssues} open / ${pulse.closedIssues} closed${pulse.blockers?.length ? `, blocked on ${pulse.blockers.join('; ')}` : ''}`)
  .join('\n')

const rollUp = await agent(
  `These milestones were measured independently. Write the programme view.\n\n${digest}\n\nLead with the initiative most likely to miss and why. Where two milestones are blocked on the same thing, say so: that is the finding a per-milestone report cannot produce. Do not rank by issue count.`,
  { label: 'roll-up', phase: 'Roll-up' },
)

log(`${pulses.length} milestones measured, ${pulses.filter((p) => p.risk !== 'on-track').length} not on track`)

return { repo, pulses, rollUp }
