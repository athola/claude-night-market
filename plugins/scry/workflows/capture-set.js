// Several recordings captured at once, because each one is mostly
// waiting for a process that does not know about the others.
//
// A terminal recording waits on the command it is recording. A browser
// recording waits on page loads. Captured in sequence, a documentation
// set of six flows is the sum of six waits, and a failure in the fourth
// leaves the fifth and sixth uncaptured for a reason unrelated to them.
// Captured in parallel, the wall clock is the slowest single flow, and a
// failed capture is reported alongside the ones that worked.

export const meta = {
  name: 'capture-set',
  description:
    'Capture several terminal or browser recordings in parallel and report which flows failed without stopping the rest',
  whenToUse:
    'Run when refreshing a documentation set with more than one recording. args.flows describes each capture. Returns the produced assets and the failed flows with their cause.',
  phases: [{ title: 'Capture', detail: 'one agent per flow' }],
}

const input = args || {}
const flows = input.flows || []

if (!flows.length) {
  log('capture-set.js started with no flows')
  return {
    started: false,
    reason: 'no-flows',
    next: 'Pass args.flows as a list of {name, kind, script} where kind is "terminal" or "browser".',
  }
}

const CAPTURE = {
  type: 'object',
  required: ['flow', 'captured'],
  properties: {
    flow: { type: 'string' },
    captured: { type: 'boolean' },
    asset: { type: 'string' },
    failure: { type: 'string' },
  },
}

const captured = await parallel(
  flows.map((flow, index) => () =>
    agent(
      `Capture one recording. Follow Skill(scribe:session-replay) for a terminal capture, or the browser recording path in scry for a browser one.\n\nFlow: ${flow.name || `flow-${index + 1}`}\nKind: ${flow.kind || 'terminal'}\nScript: ${flow.script || '(none given)'}\n\nConfirm the produced asset exists and is non-empty before reporting captured=true. A recorder that exits 0 having written nothing is the failure mode here, so check the file rather than the exit code. If the capture fails, report why and stop; do not retry with a different flow.`,
      { label: `capture:${flow.name || index + 1}`, phase: 'Capture', schema: CAPTURE },
    ),
  ),
)

const results = captured.filter(Boolean)
const failed = results.filter((result) => !result.captured)

log(`${results.length - failed.length} of ${flows.length} flows captured`)

return {
  assets: results.filter((result) => result.captured).map((result) => result.asset),
  failed,
}
