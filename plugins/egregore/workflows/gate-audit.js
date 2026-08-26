// Ask of every gate in the autonomous pipeline: can this one fail?
//
// A gate that always answers yes is worse than no gate, because the
// pipeline reports a check that did not happen. This branch found four
// of them in one sweep, and each was found by reading a gate closely
// enough to construct the input it should reject. That reading is the
// same work per gate and it does not share state, so it fans out.
//
// The verification stage is the point. A gate audit that reports "looks
// correct" has done nothing; each finding has to name the input that
// walks past the gate, and a second agent has to try to make that input
// fail before the finding is reported.

export const meta = {
  name: 'gate-audit',
  description:
    'Check each pipeline gate for whether it can return a failing verdict, and prove each finding with an input that walks past it',
  whenToUse:
    'Run before trusting an unattended egregore run, or after changing a gate. args.gates names the gates to audit. Returns findings that carry a concrete bypass; it changes no gate.',
  phases: [
    { title: 'Read', detail: 'one agent per gate' },
    { title: 'Prove', detail: 'construct the input that walks past it' },
  ],
}

const input = args || {}

const DEFAULT_GATES = [
  'plugins/egregore/scripts/handoff_gate.py',
  'plugins/egregore/scripts/scope.py',
  'plugins/egregore/scripts/verdict.py',
  'plugins/egregore/scripts/night_run.py',
]

const gates = input.gates || DEFAULT_GATES

const READING = {
  type: 'object',
  required: ['gate', 'suspects'],
  properties: {
    gate: { type: 'string' },
    suspects: {
      type: 'array',
      items: {
        type: 'object',
        required: ['check', 'why'],
        properties: {
          check: { type: 'string' },
          why: { type: 'string' },
          candidateInput: { type: 'string' },
        },
      },
    },
  },
}

const PROOF = {
  type: 'object',
  required: ['reachable', 'reasoning'],
  properties: {
    reachable: { type: 'boolean' },
    reasoning: { type: 'string' },
    input: { type: 'string' },
  },
}

const audited = await pipeline(
  gates,
  (gate) =>
    agent(
      `Read ${gate}. For each check it performs, decide whether a realistic input exists that the check should reject and does not.\n\nLook for: a condition that reads a field the caller controls, a comparison that normalizes away the difference it is testing, a branch that returns the passing verdict on an exception, and a check whose subject is not the thing the gate names. Report suspects with the input you think walks past. An empty list is a valid answer.`,
      { label: `read:${gate.split('/').pop()}`, phase: 'Read', schema: READING },
    ),
  (reading, gate) =>
    parallel(
      (reading?.suspects || []).map((suspect) => () =>
        agent(
          `Decide whether this gate bypass is real. Read ${gate}, then trace the candidate input through the check by hand.\n\nCheck: ${suspect.check}\nClaimed weakness: ${suspect.why}\nCandidate input: ${suspect.candidateInput || '(none offered)'}\n\nReport reachable=true only if you can state the exact input and the exact line that lets it through. Default to reachable=false.`,
          { label: `prove:${suspect.check}`, phase: 'Prove', schema: PROOF },
        ).then((proof) => ({ gate, ...suspect, proof })),
      ),
    ),
)

const real = audited
  .flat()
  .filter(Boolean)
  .filter((entry) => entry.proof && entry.proof.reachable)

log(`${real.length} reachable gate bypasses across ${gates.length} gates`)

return { gates, bypasses: real }
