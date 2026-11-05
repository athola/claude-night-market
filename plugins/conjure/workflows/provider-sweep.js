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
    'Run during setup, or when delegation is failing and the cause is unclear. args.providers narrows the set. Returns a per-provider verdict with its remedy. It installs nothing and changes no credentials.',
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

const KNOWN = ALL_PROVIDERS.join(', ')
const selection = input.providers ?? null
// A string would pass `.includes` as a substring match, so only a list
// is a selection.
if (selection !== null && !Array.isArray(selection)) {
  return {
    started: false,
    reason: 'providers-not-a-list',
    next: 'Pass args.providers as a list of provider names. Omit it to run every provider.',
  }
}
const providers = selection ? ALL_PROVIDERS.filter((name) => selection.includes(name)) : ALL_PROVIDERS
// A misspelled provider must not dispatch an agent at nothing.
const unknown = (selection || []).filter((name) => !ALL_PROVIDERS.includes(name))
if (unknown.length) log(`unknown provider ${unknown.join(', ')}. Known providers: ${KNOWN}`)
if (!providers.length) {
  return {
    started: false,
    reason: 'no-providers-selected',
    next: `Name one or more known providers in args.providers: ${KNOWN}. Omit it to run every provider.`,
    unknown,
  }
}

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

// The provider comes from the roster position, not from the name the
// agent wrote, which may read Gemini or gemini-cli.
const verdicts = probed
  .map((verdict, index) => verdict && { ...verdict, provider: providers[index] })
  .filter(Boolean)
const ready = verdicts.filter((verdict) => verdict.callable).map((v) => v.provider)
// A probe that returned nothing says nothing about the provider. Folding it
// into "not callable" would report a dead agent as a broken machine.
const unreported = providers.filter((provider, index) => !probed[index])

if (unreported.length) {
  log(`no verdict from ${unreported.join(', ')}. Those providers are unprobed, not uncallable`)
}
if (ready.length) {
  log(`available to conjure: ${ready.join(', ')}`)
} else if (verdicts.length) {
  log(`no probed provider is callable on this machine (${verdicts.length} probed)`)
}

return {
  ready,
  blocked: verdicts.filter((verdict) => !verdict.callable),
  unreported,
}
