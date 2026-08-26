// One agent per delegation provider, asking each the same question:
// can this machine actually call you right now, and if not, why not.
//
// The sequential path spawns up to sixteen subprocesses and reports the
// first failure it meets. That is the wrong shape for setup, where an
// operator wants the whole picture before deciding which one CLI to fix.
// Fanning out gets every provider's verdict at once, and separates the
// three causes that a failed delegation collapses into one: the binary
// is absent, the credential is absent or rejected, or the binary and
// credential are fine and the model is not pulled.

export const meta = {
  name: 'provider-sweep',
  description:
    'Ask every delegation provider in parallel whether this machine can call it, and separate a missing binary from a rejected credential',
  whenToUse:
    'Run during setup, or when delegation is failing and the cause is unclear. args.providers narrows the set. Returns a per-provider verdict with its remedy; it installs nothing and changes no credentials.',
  phases: [{ title: 'Probe', detail: 'one agent per provider' }],
}

const input = args || {}

const ALL_PROVIDERS = [
  'gemini',
  'qwen',
  'minimax',
  'glm',
  'muse',
  'codex',
  'opencode',
  'glimmer',
]

const providers = input.providers || ALL_PROVIDERS

const VERDICT = {
  type: 'object',
  required: ['provider', 'callable', 'cause'],
  properties: {
    provider: { type: 'string' },
    callable: { type: 'boolean' },
    cause: {
      type: 'string',
      enum: [
        'ready',
        'binary-missing',
        'credential-missing',
        'credential-rejected',
        'model-missing',
        'unknown',
      ],
    },
    evidence: { type: 'string' },
    remedy: { type: 'string' },
  },
}

const probed = await parallel(
  providers.map((provider) => () =>
    agent(
      `Determine whether conjure can delegate to '${provider}' on this machine right now.\n\nRun \`python3 plugins/conjure/scripts/delegation_setup.py --doctor\` from the repository root and read the row for this provider. Read Skill(conjure:provider-setup) for what the columns mean.\n\nClassify the cause precisely. Three of these CLIs exit 0 over a rejected credential, so exit status is not the signal: read the output text. Report the evidence you actually saw, not what the table implies. Change nothing and install nothing.`,
      { label: `probe:${provider}`, phase: 'Probe', schema: VERDICT },
    ),
  ),
)

const verdicts = probed.filter(Boolean)
const ready = verdicts.filter((verdict) => verdict.callable).map((v) => v.provider)

log(
  ready.length
    ? `available to conjure: ${ready.join(', ')}`
    : 'no provider is callable on this machine',
)

return {
  ready,
  blocked: verdicts.filter((verdict) => !verdict.callable),
  unreported: providers.filter(
    (provider) => !verdicts.some((verdict) => verdict.provider === provider),
  ),
}
