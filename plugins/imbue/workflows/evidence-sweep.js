// Every completion claim in a change, checked against the evidence that
// is supposed to back it.
//
// proof-of-work says a claim needs a command that ran and output that
// was captured. What it cannot do from inside one session is notice the
// claim that quietly has neither, because the session that wrote the
// claim is the session being asked. One agent per claim, none of them
// carrying the reasoning that produced the claim, is what makes the
// check adversarial rather than confirmatory.

export const meta = {
  name: 'evidence-sweep',
  description:
    'Check each completion claim in a change against the evidence offered for it, and report the ones running on assertion alone',
  whenToUse:
    'Run before a pull request, or when reviewing one. args.claims lists the statements to check; args.diff scopes what counts as evidence. Returns unsupported claims with what would settle each.',
  phases: [{ title: 'Check', detail: 'one agent per claim' }],
}

const input = args || {}
const claims = input.claims || []

if (!claims.length) {
  log('evidence-sweep.js started with no claims')
  return {
    started: false,
    reason: 'no-claims',
    next: 'Pass args.claims as the list of statements to verify. Extracting them from a PR body is the caller\'s job, because deciding what counts as a claim is a judgment this workflow should not make silently.',
  }
}

const scope = input.diff || 'the working tree'

const CHECK = {
  type: 'object',
  required: ['claim', 'supported', 'reason'],
  properties: {
    claim: { type: 'string' },
    supported: { type: 'boolean' },
    reason: { type: 'string' },
    whatWouldSettleIt: { type: 'string' },
  },
}

const checked = await parallel(
  claims.map((claim, index) => () =>
    agent(
      `Check one claim against the evidence available in ${scope}. Follow Skill(imbue:proof-of-work).\n\nClaim ${index + 1}: ${claim}\n\nSupported means a command ran and its output shows what the claim says. "The code looks correct", "this should work" and "the syntax is valid" are not evidence. A test that exists is not evidence that it passed, and a test that passed is not evidence that it would fail if the behavior regressed.\n\nWhen the claim is unsupported, name the single command that would settle it.`,
      { label: `check:${index + 1}`, phase: 'Check', schema: CHECK },
    ),
  ),
)

const results = checked.filter(Boolean)
const unsupported = results.filter((result) => !result.supported)

log(`${unsupported.length} of ${results.length} claims run on assertion alone`)

return { scope, checked: results, unsupported }
