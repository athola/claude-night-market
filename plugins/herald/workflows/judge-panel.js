// Three independent judges on one completion claim, because a single
// judge asked "is this done" agrees with the claim it was shown.
//
// herald's Stop-hook judge decides whether a session's work is finished.
// The failure mode it exists to catch is a session reporting completion
// it cannot support, and a judge that has read the session's own summary
// inherits the same reasoning that produced the claim. Independent
// judges with different lenses do not: the one asked whether the tests
// actually ran does not care how convincing the summary was.
//
// A majority is the verdict. A split is reported as a split, because a
// two-to-one on completion is information a human wants.

export const meta = {
  name: 'judge-panel',
  description:
    'Judge one completion claim through three independent lenses and report the verdict with any dissent',
  whenToUse:
    'Run when a completion claim carries real cost if wrong, such as ending an unattended run. args.claim is what was claimed; args.evidence is what was offered. Returns a verdict and every dissenting opinion.',
  phases: [{ title: 'Judge', detail: 'three lenses, no shared reasoning' }],
}

const input = args || {}
const claim = input.claim

if (!claim) {
  log('judge-panel.js started with no claim')
  return {
    started: false,
    reason: 'no-claim',
    next: 'Pass args.claim describing what was reported complete, and args.evidence with what was offered to support it.',
  }
}

const evidence = input.evidence || '(none offered)'

const VERDICT = {
  type: 'object',
  required: ['lens', 'complete', 'reason'],
  properties: {
    lens: { type: 'string' },
    complete: { type: 'boolean' },
    reason: { type: 'string' },
    missing: { type: 'array', items: { type: 'string' } },
  },
}

const LENSES = [
  {
    key: 'execution',
    brief:
      'Did the work actually run? Look for command output, exit codes and test counts. A claim that something "should work" or "is correct" is not evidence that it ran. Judge only this.',
  },
  {
    key: 'scope',
    brief:
      'Does the work cover what was asked, or a narrower thing that was easier? Compare the claim against the original request. Report anything in the request that the claim does not touch. Judge only this.',
  },
  {
    key: 'regression',
    brief:
      'Could this have broken something it does not mention? Look for changes whose blast radius exceeds what the evidence covers. Judge only this.',
  },
]

const judged = await parallel(
  LENSES.map((lens) => () =>
    agent(
      `Judge one completion claim through a single lens. ${lens.brief}\n\nClaim: ${claim}\n\nEvidence offered:\n${evidence}\n\nDo not weigh the other lenses; another judge has them. Answer complete=false when your lens is not satisfied, even if the work looks good on other grounds.`,
      { label: `judge:${lens.key}`, phase: 'Judge', schema: VERDICT },
    ),
  ),
)

const verdicts = judged.filter(Boolean)

if (!verdicts.length) {
  log('no judge returned a verdict')
  return { claim, verdict: 'unknown', verdicts: [], dissent: [] }
}

const satisfied = verdicts.filter((verdict) => verdict.complete)
const dissent = verdicts.filter((verdict) => !verdict.complete)
const verdict = satisfied.length > verdicts.length / 2 ? 'complete' : 'incomplete'

log(`${verdict}: ${satisfied.length} of ${verdicts.length} judges satisfied`)

return { claim, verdict, verdicts, dissent }
